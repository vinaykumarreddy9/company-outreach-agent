import asyncio
import logging
import os
import sys
from backend.agents.target_discovery import TargetDiscoveryAgent
from backend.schemas.campaign import Campaign, CampaignFilters, CompanyProfile
from backend.graphs.state import AgentState
from dotenv import load_dotenv

# Fix for Psycopg + Asyncio on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    print("\n" + "="*50)
    print("TESTING TARGET DISCOVERY AGENT IN ISOLATION")
    print("="*50)
    
    agent = TargetDiscoveryAgent()
    
    # Mocked Industry Filters for discovery - Focused on Manufacturing
    filters = CampaignFilters(
        industries=["Industrial Manufacturing"],
        locations=["United Kingdom"],
        company_size="100-500 employees"
    )

    # Output from previous UserIntelligenceAgent for "Digiotai Solutions"
    profile = CompanyProfile(
        company_name="Digiotai Solutions",
        value_proposition="Empowering industrial enterprises with intelligent digital solutions that unlock peak performance, drive operational excellence, and create sustainable value.",
        key_offerings=[
            "Enterprise AI automation", 
            "Intelligent lead aggregation", 
            "IoT solutions for industrial operations", 
            "Digital transformation services"
        ],
        target_audience="Industrial enterprises across manufacturing, maritime, and heavy machinery sectors.",
        strategic_positioning="Leading force in industrial digital transformation, bridging operational technology and digital innovation."
    )
    
    campaign = Campaign(
        name="Industrial AI Outreach",
        user_company_name="Digiotai Solutions",
        user_company_profile=profile,
        product_description="Enterprise AI automation for industrial supply chain optimization",
        target_filters=filters
    )
    
    state: AgentState = {
        "campaign_id": "test-campaign-123",
        "campaign_data": campaign,
        "target_companies": [],
        "decision_makers": [],
        "email_drafts": [],
        "errors": [],
        "current_agent": "UserIntelligenceAgent"
    }
    
    print(f"Targeting: {filters.industries} in {filters.locations}")
    print(f"Using Profile: {profile.company_name} - {profile.value_proposition[:100]}...")
    print("\nStarting Consolidated Discovery & Research...")
    
    try:
        updated_state = await agent.run(state)
        
        if updated_state["errors"]:
            print("\nErrors Encountered:")
            for err in updated_state["errors"]:
                print(f"  - {err}")
        
        targets = updated_state.get("target_companies", [])
        
        print(f"\n✅ DISCOVERY COMPLETE. FOUND {len(targets)} COMPANIES.")
        
        with open("tests/discovery_test_result.txt", "w", encoding="utf-8") as f:
            f.write("TARGET DISCOVERY AGENT OUTPUT\n")
            f.write("="*30 + "\n")
            
            for i, company in enumerate(targets, 1):
                output = [
                    f"\n[COMPANY {i}]",
                    f"Name: {company.name}",
                    f"Website: {company.website}",
                    f"Description: {company.description}",
                    f"Relevance Score: {company.relevance_score}",
                    f"Recent News: {', '.join(company.recent_news[:2])}",
                    f"Key Challenges: {', '.join(company.key_challenges[:3])}",
                    f"Strategic Priorities: {', '.join(company.strategic_priorities[:3])}"
                ]
                for line in output:
                    print(line)
                    f.write(line + "\n")
            
            f.write("\n" + "="*30)
            
        print("\nFull results written to tests/discovery_test_result.txt")
            
    except Exception as e:
        print(f"\nPanic during discovery test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
