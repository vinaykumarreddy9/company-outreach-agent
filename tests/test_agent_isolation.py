import asyncio
import logging
from backend.agents.user_intelligence import UserIntelligenceAgent
from backend.schemas.campaign import Campaign, CampaignFilters
from backend.graphs.state import AgentState
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    print("\n" + "="*50)
    print("TESTING USER INTELLIGENCE AGENT IN ISOLATION")
    print("="*50)
    
    agent = UserIntelligenceAgent()
    
    # Mocking the input state as expected by the agent
    campaign = Campaign(
        name="DigiotAI Outreach",
        user_company_name="Digiotai Solutions",
        product_description="Enterprise AI automation and intelligent lead aggregation",
        target_filters=CampaignFilters(industries=["Technology", "SaaS"])
    )
    
    state: AgentState = {
        "user_input": "Reach out to tech companies for Digiotai Solutions",
        "campaign_data": campaign,
        "target_companies": [],
        "decision_makers": [],
        "email_drafts": [],
        "scheduled_emails": [],
        "errors": [],
        "current_agent": "ContextPlanningAgent"
    }
    
    print(f"Input Company: {campaign.user_company_name}")
    print(f"Input Product: {campaign.product_description}")
    print("\nRunning Agent Deep Scan...")
    
    # Run the agent in isolation
    try:
        updated_state = await agent.run(state)
        
        with open("tests/isolation_test_result.txt", "w", encoding="utf-8") as f:
            if updated_state["errors"]:
                f.write("\nErrors Encountered:\n")
                for err in updated_state["errors"]:
                    f.write(f"  - {err}\n")
            else:
                profile = updated_state["campaign_data"].user_company_profile
                print("\n✅ AGENT OUTPUT (Company Profile):")
                print("-" * 30)
                if profile:
                    report = [
                        f"Company Name: {profile.company_name}",
                        f"Value Proposition: {profile.value_proposition}",
                        f"Key Offerings: {', '.join(profile.key_offerings)}",
                        f"Target Audience: {profile.target_audience}",
                        f"Strategic Positioning: {profile.strategic_positioning}"
                    ]
                    for line in report:
                        print(line)
                    
                    with open("tests/isolation_test_result.txt", "w", encoding="utf-8") as f:
                        f.write("\nAGENT OUTPUT (Company Profile):\n")
                        f.write("-" * 30 + "\n")
                        for line in report:
                            f.write(line + "\n")
                        f.write("-" * 30 + "\n")
                else:
                    print("Warning: Profile was not generated.")
                    with open("tests/isolation_test_result.txt", "w", encoding="utf-8") as f:
                        f.write("Warning: Profile was not generated.\n")
                
                print("-" * 30)
                print(f"Status: {updated_state['current_agent']} completed successfully.")
        
        print("\nTest completed. Results written to tests/isolation_test_result.txt")
            
    except Exception as e:
        print(f"\nPanic during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
