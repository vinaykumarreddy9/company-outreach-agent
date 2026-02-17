import logging
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from backend.config.settings import settings
from backend.schemas.campaign import DecisionMaker, TargetCompany
from backend.graphs.state import AgentState
from backend.services.neon_db import save_decision_maker, save_target_company
from backend.services.apollo import get_work_email

logger = logging.getLogger(__name__)

class CandidatePerson(BaseModel):
    name: str
    role: str
    role_category: str = Field(..., description="The category number (1-6) this person falls into.")
    linkedin_url: str
    is_current: bool = Field(..., description="Confirm if the person currently works at the company.")
    relevance_reason: str

class CandidatePersonList(BaseModel):
    people: List[CandidatePerson]

class DecisionMakerFinderAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.search = TavilySearch(
            max_results=10,
            tavily_api_key=settings.TAVILY_API_KEY
        )
        self.structured_llm = self.llm.with_structured_output(CandidatePersonList)
        
        self.categories = {
            "1": "Founder / Co-Founder",
            "2": "CEO / Managing Director",
            "3": "CTO / Head of Technology",
            "4": "COO / Head of Operations",
            "5": "Director / Head of Department",
            "6": "Product / Program / Strategy Head"
        }

        self.identification_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional executive recruiter and lead prospector. "
                       "Your goal is to identify the top 5 REAL decision makers at a specific company. "
                       "Assign each person to one of these categories:\n"
                       "1. Founder / Co-Founder\n"
                       "2. CEO / Managing Director\n"
                       "3. CTO / Head of Technology\n"
                       "4. COO / Head of Operations\n"
                       "5. Director / Head of Department\n"
                       "6. Product / Program / Strategy Head\n\n"
                       "STRICT RULES:\n"
                       "1. ONLY include people who currently work at the company.\n"
                       "2. Provide their full name, exact role, LinkedIn URL, and the category number.\n"
                       "3. BE CERTAIN of the identity. If search data is ambiguous, skip that person."),
            ("user", "Company Name: {company_name}\nTarget Categories: {categories}\nSearch Results:\n{search_results}")
        ])

    async def run(self, state: AgentState) -> AgentState:
        try:
            print("\n--- DecisionMakerFinderAgent (Identity-First Engine) ---")
            campaign = state.get("campaign_data")
            target_companies = state.get("target_companies", [])
            campaign_id = state.get("campaign_id")
            
            if not campaign or not target_companies:
                print("  ⚠️ No target companies found. Skipping.")
                return state

            all_decision_makers = []
            
            for company in target_companies:
                print(f"  🏢 Identifying leadership at {company.name}...")
                
                domain = company.website.replace("https://", "").replace("http://", "").split("/")[0] if company.website else f"{company.name.lower().replace(' ', '')}.com"
                if domain.startswith("www."): domain = domain[4:]

                # BREADDTH-FIRST SEARCH PASSES
                queries = [
                    f"leadership team {company.name} {domain} executive profiles linkedin",
                    f"{company.name} {domain} management team staff directory linkedin"
                ]
                
                processed_names = set()
                comp_dm_count = 0
                
                for query in queries:
                    if comp_dm_count >= 5: break
                    
                    print(f"    🔍 Searching: {query}")
                    search_response = await self.search.ainvoke({"query": query})
                    
                    # IDENTITY GATE
                    candidate_res = await (self.identification_prompt | self.structured_llm).ainvoke({
                        "company_name": company.name,
                        "categories": str(self.categories),
                        "search_results": str(search_response)
                    })
                    
                    verified_candidates = [p for p in candidate_res.people if p.is_current and p.name not in processed_names]
                    if not verified_candidates: continue
                    
                    print(f"    ✨ Found {len(verified_candidates)} candidate profiles. Starting Apollo enrichment...")

                    for candidate in verified_candidates:
                        if comp_dm_count >= 5: break
                        processed_names.add(candidate.name)

                        print(f"    📡 Enriching: {candidate.name} ({candidate.role})")
                        
                        try:
                            email = await get_work_email(candidate.name, domain)
                        except Exception as e:
                            logger.error(f"Apollo error: {e}")
                            email = None
                        
                        if not email:
                            print(f"      ⚠️ No verified email found for {candidate.name}. Skipping.")
                            continue

                        dm = DecisionMaker(
                            name=candidate.name,
                            role=candidate.role,
                            role_category=candidate.role_category,
                            email=email,
                            linkedin=candidate.linkedin_url,
                            company_name=company.name,
                            email_source="apollo",
                            status="new"
                        )
                        
                        all_decision_makers.append(dm)
                        comp_dm_count += 1
                        print(f"    ✅ SUCCESS: Added {candidate.name} (Cat {candidate.role_category})")

                        # PERSIST
                        if campaign_id:
                            try:
                                company_id_db = await save_target_company(campaign_id, company.dict())
                                if company_id_db:
                                    await save_decision_maker(campaign_id, company_id_db, dm.dict())
                            except Exception as e:
                                logger.error(f"Failed to persist {dm.name}: {e}")

            state["decision_makers"] = all_decision_makers
            state["current_agent"] = "DecisionMakerFinderAgent"
            print(f"--- Process Complete. Found {len(all_decision_makers)} verified leads. ---\n")

        except Exception as e:
            error_msg = f"Panic in DecisionMakerFinderAgent: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            
        return state
