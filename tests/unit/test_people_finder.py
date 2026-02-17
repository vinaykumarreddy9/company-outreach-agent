import pytest
from backend.agents.decision_maker_finder import DecisionMakerFinderAgent
from backend.schemas.campaign import Campaign, TargetCompany, CampaignFilters
from backend.graphs.state import AgentState
from backend.services.neon_db import create_campaign

def test_decision_maker_finder_agent():
    print("\n--- Testing DecisionMakerFinderAgent ---")
    agent = DecisionMakerFinderAgent()
    
    campaign_id = create_campaign(name="DM Finder Test", product_description="AI Lead Gen")
    
    # Setup state with a real company to find people for
    target_company = TargetCompany(
        name="Google",
        website="https://google.com",
        description="Search engine and tech giant",
        relevance_score=10
    )
    
    campaign = Campaign(
        name="DM Finder Test",
        user_company_name="DigiotAI",
        product_description="AI Lead Gen",
        target_filters=CampaignFilters(roles=["Founder", "CEO"])
    )
    
    state: AgentState = {
        "campaign_data": campaign,
        "campaign_id": campaign_id,
        "target_companies": [target_company],
        "decision_makers": [],
        "errors": [],
        "current_agent": ""
    }
    
    final_state = agent.run(state)
    
    assert len(final_state["decision_makers"]) > 0, "No decision makers found for Scale AI"
    assert len(final_state["errors"]) == 0
    print(f"Success: Found {len(final_state['decision_makers'])} decision makers.")

if __name__ == "__main__":
    test_decision_maker_finder_agent()
