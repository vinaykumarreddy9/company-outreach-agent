import pytest
from backend.agents.user_intelligence import UserIntelligenceAgent
from backend.schemas.campaign import Campaign, CampaignFilters
from backend.graphs.state import AgentState

def test_user_intelligence_agent():
    print("\n--- Testing UserIntelligenceAgent ---")
    agent = UserIntelligenceAgent()
    
    campaign = Campaign(
        name="DigiotAI Service",
        user_company_name="DigiotAI Solutions",
        product_description="AI Lead Generation",
        target_filters=CampaignFilters(industries=["Tech"])
    )
    
    state: AgentState = {
        "campaign_data": campaign,
        "target_companies": [],
        "decision_makers": [],
        "errors": [],
        "current_agent": ""
    }
    
    final_state = agent.run(state)
    
    # Check if campaign_data was enriched
    assert final_state["campaign_data"].company_mission is not None
    assert len(final_state["errors"]) == 0
    print(f"Success: Enriched company mission: {final_state['campaign_data'].company_mission[:50]}...")

if __name__ == "__main__":
    test_user_intelligence_agent()
