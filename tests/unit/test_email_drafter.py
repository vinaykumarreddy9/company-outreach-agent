import pytest
from backend.agents.email_drafter import EmailDraftingAgent
from backend.schemas.campaign import Campaign, TargetCompany, DecisionMaker, CampaignFilters
from backend.graphs.state import AgentState

def test_email_drafting_agent():
    print("\n--- Testing EmailDraftingAgent ---")
    agent = EmailDraftingAgent()
    
    target_company = TargetCompany(
        name="Scale AI",
        website="https://scale.com",
        description="Data labeling platform",
        relevance_score=10
    )
    
    dm = DecisionMaker(
        name="Alex Wang",
        role="CEO",
        email="alex@scale.com",
        company_name="Scale AI"
    )
    
    campaign = Campaign(
        name="Outbound Test",
        user_company_name="DigiotAI Solutions",
        product_description="Automated lead gen agents",
        target_filters=CampaignFilters(roles=["CEO"])
    )
    
    state: AgentState = {
        "campaign_data": campaign,
        "target_companies": [target_company],
        "decision_makers": [dm],
        "errors": [],
        "current_agent": ""
    }
    
    final_state = agent.run(state)
    
    assert len(final_state["errors"]) == 0
    # Check if drafts were generated (should be in state or logged)
    print("Success: Email drafting completed.")

if __name__ == "__main__":
    test_email_drafting_agent()
