from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config.settings import settings
from backend.graphs.state import AgentState
from typing import List, Dict, Any
from backend.services.neon_db import save_email_draft, save_decision_maker, save_target_company
import logging

logger = logging.getLogger(__name__)

class EmailDraftingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7 
        )
        
        self.drafting_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert sales copywriter. Draft a personalized cold email to the decision maker. "
                       "STRICT RULES:\n"
                       "1. Use ONLY the provided information. Do NOT hallucinate or insert placeholders like '[Insert Company]' or '[Result]'.\n"
                       "2. If a specific detail (e.g., recent news) is 'N/A' or missing, WRITE AROUND IT or OMIT that part entirely.\n"
                       "3. Keep it under 150 words.\n"
                       "4. Be professional, direct, and value-driven.\n"
                       "5. Include a subject line.\n"
                       "6. Sign off as 'The {my_company} Team' if no specific sender name is provided. Do NOT use '[Your Name]'."),
            ("user", "My Company: {my_company}\nMy Product: {my_product}\nMy Value Prop: {my_value_prop}\n\n"
                     "Target Person: {person_name}, {person_role}\n"
                     "Target Company: {company_name}\n"
                     "Recent News: {news}\n"
                     "Challenges: {challenges}\n"
                     "Strategic Priorities: {priorities}")
        ])

    async def run(self, state: AgentState) -> AgentState:
        try:
            campaign = state.get("campaign_data")
            decision_makers = state.get("decision_makers", [])
            target_companies = state.get("target_companies", [])
            
            if not campaign or not decision_makers:
                print("Missing campaign or decision makers for EmailDraftingAgent.")
                return state

            print(f"Drafting emails (async) for {len(decision_makers)} people.")
            
            company_lookup = {c.name: c for c in target_companies}
            email_drafts = []
            
            for person in decision_makers:
                if not person.email:
                    print(f"Skipping email draft (async) for {person.name} ({person.company_name}) - No email found.")
                    continue

                company = company_lookup.get(person.company_name)
                if not company:
                    news = "N/A"
                    challenges = "N/A"
                    priorities = "N/A"
                else:
                    news = "; ".join(company.recent_news[:1]) if company.recent_news else "N/A"
                    challenges = "; ".join(company.key_challenges[:1]) if company.key_challenges else "N/A"
                    priorities = "; ".join(company.strategic_priorities[:1]) if company.strategic_priorities else "N/A"
                
                try:
                    chain = self.drafting_prompt | self.llm
                    response = await chain.ainvoke({
                        "my_company": campaign.user_company_name,
                        "my_product": campaign.product_description,
                        "my_value_prop": campaign.user_company_profile.value_proposition if campaign.user_company_profile else "N/A",
                        "person_name": person.name,
                        "person_role": person.role,
                        "company_name": person.company_name,
                        "news": news,
                        "challenges": challenges,
                        "priorities": priorities
                    })
                    
                    draft_content = response.content
                    
                    email_drafts.append({
                        "recipient_name": person.name,
                        "recipient_email": person.email,
                        "company": person.company_name,
                        "content": draft_content
                    })
                    
                    # Persist Email Draft
                    campaign_id = state.get("campaign_id")
                    if campaign_id:
                        try:
                            comp_data = {"name": person.company_name}
                            company_id = await save_target_company(campaign_id, comp_data)
                            if company_id:
                                dm_id = await save_decision_maker(campaign_id, company_id, person.dict())
                                if dm_id:
                                    subject = "Follow-up"
                                    body_text = draft_content
                                    if "Subject:" in draft_content:
                                        parts = draft_content.split("\n", 1)
                                        subject = parts[0].replace("Subject:", "").strip()
                                        body_text = parts[1].strip() if len(parts) > 1 else ""

                                    email_id = await save_email_draft(dm_id, subject, body_text, person.email)
                                    print(f"Persisted draft (async) for {person.name} (ID: {email_id})")
                        except Exception as e:
                            logger.error(f"Failed to persist draft for {person.name} asynchronously: {e}")

                    print(f"Drafted email (async) for {person.name}")
                    
                except Exception as e:
                    logger.error(f"Error drafting email for {person.name} asynchronously: {e}")
            
            state["email_drafts"] = email_drafts
            state["current_agent"] = "EmailDraftingAgent"
            
        except Exception as e:
            error_msg = f"Panic in EmailDraftingAgent (async): {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            
        return state
