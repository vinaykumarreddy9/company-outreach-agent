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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dm_finder():
    print("\n==================================================")
    print("TESTING DECISION MAKER FINDER AGENT")
    print("==================================================")
    
    agent = DecisionMakerFinderAgent()
    
    # Mocked Campaign
    campaign = Campaign(
        name="Digital Transformation for Siemens",
        user_company_name="Digiotai Solutions",
        product_description="AI-driven industrial automation and IoT solutions.",
        target_filters=CampaignFilters(
            industries=["Industrial Manufacturing"],
            locations=["United Kingdom"],
            company_size="Large"
        )
    )

    # Mocked Target Company
    target_company = TargetCompany(
        name="Brompton Bicycle",
        website="https://www.brompton.com",
        description="The iconic folding bike manufacturer.",
        relevance_score=10,
        recent_news=["Brompton launches new electric model."],
        key_challenges=["Global supply chain optimization."],
        strategic_priorities=["Expanding into the US market."]
    )

    state: AgentState = {
        "campaign_id": "test-campaign-id",
        "campaign_data": campaign,
        "target_companies": [target_company],
        "decision_makers": [],
        "errors": [],
        "current_agent": "None"
    }

    print(f"Targeting Leadership at: {target_company.name}...")
    
    # Run Agent
    result_state = await agent.run(state)
    
    print("\n==============================")
    print("DECISION MAKER FINDER OUTPUT")
    print("==============================")
    
    found_dms = result_state.get("decision_makers", [])
    if not found_dms:
        print("No Decision Makers Found.")
    else:
        for i, dm in enumerate(found_dms):
            print(f"\n[LEAD {i+1}]")
            print(f"Name: {dm.name}")
            print(f"Role: {dm.role}")
            print(f"Category: {dm.role_category}")
            print(f"LinkedIn: {dm.linkedin}")
            print(f"Email: {dm.email}")
            print(f"Source: {dm.email_source}")

    # Log results to file
    with open("tests/dm_finder_test_result.txt", "w") as f:
        f.write("DECISION MAKER FINDER AGENT OUTPUT\n")
        f.write("==============================\n")
        for i, dm in enumerate(found_dms):
            f.write(f"\n[LEAD {i+1}]\n")
            f.write(f"Name: {dm.name}\n")
            f.write(f"Role: {dm.role}\n")
            f.write(f"Category: {dm.role_category}\n")
            f.write(f"LinkedIn: {dm.linkedin}\n")
            f.write(f"Email: {dm.email}\n")
            f.write(f"Source: {dm.email_source}\n")
        f.write("\n==============================\n")
    
    print(f"\n✅ TEST COMPLETE. FOUND {len(found_dms)} LEADS.")
    print("Full results written to tests/dm_finder_test_result.txt")

if __name__ == "__main__":
    asyncio.run(test_dm_finder())
