import asyncio
import logging
import os
import sys
from backend.agents.decision_maker_finder import DecisionMakerFinderAgent
from backend.schemas.campaign import Campaign, CampaignFilters, TargetCompany
from backend.graphs.state import AgentState
from dotenv import load_dotenv

# Fix for Psycopg + Asyncio on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
logging.basicConfig(level=logging.INFO)

async def test_dm_finder_cope():
    print("\n==================================================")
    print("TESTING DECISION MAKER FINDER: COPE TECHNOLOGY")
    print("==================================================")
    
    agent = DecisionMakerFinderAgent()
    
    campaign = Campaign(
        name="Electronics Manufacturing Outreach",
        user_company_name="Digiotai Solutions",
        product_description="AI-driven assembly optimization for electronics.",
        target_filters=CampaignFilters(
            industries=["Electronics Manufacturing"],
            locations=["United Kingdom"]
        )
    )

    target_company = TargetCompany(
        name="Cope Technology Ltd",
        website="https://www.cope-technology.co.uk",
        description="Specialists in PCB design and electronic assembly services.",
        relevance_score=10,
        recent_news=["Consistently delivering high-quality PCB solutions."],
        key_challenges=["Managing complex electronic assembly requirements."],
        strategic_priorities=["Proactive customer service and technical excellence."]
    )

    state: AgentState = {
        "campaign_id": "test-campaign-cope",
        "campaign_data": campaign,
        "target_companies": [target_company],
        "decision_makers": [],
        "errors": [],
        "current_agent": "None"
    }

    result_state = await agent.run(state)
    
    print("\n==============================")
    print("RESULTS FOR COPE TECHNOLOGY")
    print("==============================")
    
    found_dms = result_state.get("decision_makers", [])
    for i, dm in enumerate(found_dms):
        print(f"\n[LEAD {i+1}]")
        print(f"Name: {dm.name}")
        print(f"Role: {dm.role}")
        print(f"Category: {dm.role_category}")
        print(f"LinkedIn: {dm.linkedin}")
        print(f"Email: {dm.email}")

if __name__ == "__main__":
    asyncio.run(test_dm_finder_cope())
