import logging
import httpx
import trafilatura
import asyncio
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from backend.config.settings import settings
from backend.schemas.campaign import TargetCompany
from backend.graphs.state import AgentState
from backend.services.neon_db import save_target_company

logger = logging.getLogger(__name__)

class CandidateCompany(BaseModel):
    name: str
    website: str
    description: str
    relevance_reason: str

class CandidateList(BaseModel):
    candidates: List[CandidateCompany]

class ResearchData(BaseModel):
    recent_news: List[str]
    key_challenges: List[str]
    strategic_priorities: List[str]

class TargetDiscoveryAgent:
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
        self.candidate_llm = self.llm.with_structured_output(CandidateList)
        self.research_llm = self.llm.with_structured_output(ResearchData)
        
        self.discovery_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional lead prospector. Based on the target criteria and my company's offerings, "
                       "identify REAL candidate companies from the search results. Provide their name, website, description, and relevance. "
                       "ONLY include companies that appear to be active and legitimate."),
            ("user", "Target Criteria: {filters}\nMy Offerings: {offerings}\n\nSearch Results:\n{search_results}")
        ])

        self.research_prompt = ChatPromptTemplate.from_messages([
            ("system", "Analyze the extracted text from a company's website. "
                       "Extract: 'recent_news', 'key_challenges', and 'strategic_priorities'. "
                       "If specific news is missing, summarize their recent focus areas from the text. "
                       "NEVER hallucinate specific news events if not found."),
            ("user", "Company: {company_name}\nWebsite Content:\n{content}")
        ])

    async def verify_domain(self, url: str) -> bool:
        """Verify the domain is alive using a real-world User-Agent."""
        if not url: return False
        if not url.startswith("http"): url = "https://" + url
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
        try:
            async with httpx.AsyncClient(follow_redirects=True, verify=False, headers=headers) as client:
                try:
                    response = await client.head(url, timeout=7.0)
                    if response.status_code < 500: return True
                except:
                    response = await client.get(url, timeout=10.0)
                    return response.status_code < 500
        except Exception as e:
            logger.warning(f"Domain verification failed for {url}: {e}")
            return False
        return False

    async def deep_scrape(self, url: str) -> str:
        """Scrape text using Trafilatura."""
        try:
            downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
            if not downloaded: return ""
            return await asyncio.to_thread(trafilatura.extract, downloaded) or ""
        except Exception as e:
            logger.warning(f"Scraping failed for {url}: {e}")
            return ""

    async def run(self, state: AgentState) -> AgentState:
        try:
            print("\n--- TargetDiscoveryAgent (Ultra-Robust Engine) ---")
            campaign = state.get("campaign_data")
            if not campaign: return state

            filters = campaign.target_filters
            profile = campaign.user_company_profile
            offerings = ", ".join(profile.key_offerings) if profile else campaign.product_description
            
            industries_str = ", ".join(filters.industries) if filters.industries else "Innovative"
            locations_str = ", ".join(filters.locations) if filters.locations else "UK"
            
            # Diverse queries to find a broad range of companies
            queries = [
                f"top {industries_str} companies in {locations_str} website list",
                f"leading {industries_str} enterprises in {locations_str} official sites",
                f"largest {industries_str} firms in {locations_str} directory"
            ]
            
            final_targets = []
            seen_websites = set()

            for query in queries:
                if len(final_targets) >= 2: break
                
                print(f"  🔍 Searching: {query}")
                search_results = await self.search.ainvoke({"query": query})
                
                chain = self.discovery_prompt | self.candidate_llm
                res = await chain.ainvoke({
                    "filters": str(filters),
                    "offerings": offerings,
                    "search_results": str(search_results)
                })
                
                for candidate in res.candidates:
                    if len(final_targets) >= 2: break
                    if candidate.website in seen_websites: continue
                    seen_websites.add(candidate.website)

                    print(f"  📡 Checking: {candidate.name} ({candidate.website})")
                    
                    if not await self.verify_domain(candidate.website):
                        print(f"    ❌ Domain dead. Skipping.")
                        continue
                    
                    site_content = await self.deep_scrape(candidate.website)
                    if not site_content or len(site_content.strip()) < 100:
                        print(f"    ⚠️ Thin content ({len(site_content.strip()) if site_content else 0} chars). Skipping.")
                        continue
                    
                    print(f"    🔍 Extracting intel from {len(site_content)} chars...")
                    research_data = await (self.research_prompt | self.research_llm).ainvoke({
                        "company_name": candidate.name,
                        "content": site_content[:12000]
                    })
                    
                    target = TargetCompany(
                        name=candidate.name,
                        website=candidate.website,
                        description=candidate.description,
                        source="Tavily + Deep Research",
                        relevance_score=10,
                        recent_news=research_data.recent_news or ["Recently active in their sector."],
                        key_challenges=research_data.key_challenges or [f"Managing {industries_str} market shifts."],
                        strategic_priorities=research_data.strategic_priorities or ["Expanding digital innovation."]
                    )
                    
                    final_targets.append(target)
                    print(f"    ✅ MATCH ADDED: {target.name}")
                    
                    campaign_id = state.get("campaign_id")
                    if campaign_id:
                        await save_target_company(campaign_id, target.dict())

            state["target_companies"] = final_targets
            state["current_agent"] = "TargetDiscoveryAgent"
            print(f"--- Process Complete. Found {len(final_targets)} real companies. ---\n")

        except Exception as e:
            error_msg = f"Panic in TargetDiscoveryAgent: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            
        return state
