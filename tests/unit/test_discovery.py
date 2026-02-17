import pytest
from backend.agents.target_discovery import TargetDiscoveryAgent
from backend.services.neon_db import create_campaign
from backend.schemas.campaign import Campaign, CampaignFilters
from backend.graphs.state import AgentState

def test_discovery_agent():
    print("\n--- Testing TargetDiscoveryAgent ---")
    agent = TargetDiscoveryAgent()
    
    # Setup state
    campaign_id = create_campaign(name="Test Discovery", product_description="AI Agents")
    campaign_filters = CampaignFilters(
        industries=["AI Automation"],
        locations=["San Francisco"]
    )
    campaign = Campaign(
        name="Test Discovery Campaign",
        user_company_name="DigiotAI Solutions",
        product_description="AI Agents for automation",
        target_filters=campaign_filters
    )
    
    state: AgentState = {
        "campaign_data": campaign,
        "campaign_id": campaign_id,
        "target_companies": [],
        "decision_makers": [],
        "errors": [],
        "current_agent": ""
    }
    
    # Run agent
    final_state = agent.run(state)
    
    # Assertions
    assert len(final_state["target_companies"]) > 0, "No companies found"
    assert len(final_state["errors"]) == 0, f"Errors found: {final_state['errors']}"
    print(f"Success: Found {len(final_state['target_companies'])} companies.")

if __name__ == "__main__":
    test_discovery_agent()
