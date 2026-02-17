from typing import List, Optional, Dict, Any, TypedDict
from backend.schemas.campaign import Campaign, UserInput, TargetCompany, DecisionMaker

class AgentState(TypedDict):
    user_input: str
    campaign_id: Optional[str]
    campaign_data: Optional[Campaign]
    target_companies: List[TargetCompany]
    decision_makers: List[DecisionMaker]
    email_drafts: List[Dict[str, Any]]
    validation_status: str
    errors: List[str]
    current_agent: str
