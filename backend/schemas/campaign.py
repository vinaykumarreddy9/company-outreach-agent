from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class UserInput(BaseModel):
    query: str = Field(..., description="The natural language query describing the campaign.")

class CampaignFilters(BaseModel):
    locations: List[str] = Field(default_factory=list, description="Target locations.")
    industries: List[str] = Field(default_factory=list, description="Target industries.")
    roles: List[str] = Field(default_factory=list, description="Target roles.")
    company_size: Optional[str] = Field(None, description="Target company size range.")
    min_profit: Optional[float] = Field(None, description="Minimum profit requirement.")
    max_profit: Optional[float] = Field(None, description="Maximum profit requirement.")
    min_revenue: Optional[float] = Field(None, description="Minimum revenue/turnover requirement.")
    max_revenue: Optional[float] = Field(None, description="Maximum revenue/turnover requirement.")

class CompanyProfile(BaseModel):
    company_name: str = Field(..., description="The verified name of the company.")
    value_proposition: str = Field(..., description="The core value proposition of the company.")
    key_offerings: List[str] = Field(default_factory=list, description="Key products or services offered.")
    target_audience: str = Field(..., description="The inferred target audience.")
    strategic_positioning: str = Field(..., description="The company's market positioning.")

class TargetCompany(BaseModel):
    name: str = Field(..., description="The name of the company.")
    website: Optional[str] = Field(None, description="The company's website URL.")
    description: Optional[str] = Field(None, description="Brief description of the company.")
    source: str = Field("Tavily Search", description="The source of the lead.")
    relevance_score: int = Field(..., description="Relevance score from 1-10.")
    revenue: Optional[str] = Field(None, description="Estimated revenue/turnover.")
    company_size: Optional[str] = Field(None, description="Estimated company size.")
    # Research Data
    recent_news: List[str] = Field(default_factory=list, description="Recent news headlines or summaries.")
    key_challenges: List[str] = Field(default_factory=list, description="Inferred key challenges.")
    strategic_priorities: List[str] = Field(default_factory=list, description="Inferred strategic priorities.")

class ScheduledEmail(BaseModel):
    recipient_email: str = Field(..., description="Email address of the recipient.")
    subject: str = Field(..., description="Subject line of the email.")
    body: str = Field(..., description="Body content of the email.")
    scheduled_date: str = Field(..., description="ISO 8601 formatted date string for when to send.")
    status: str = Field("pending", description="Status: 'pending', 'sent', 'cancelled'.")
    type: str = Field("reminder", description="Type: 'reminder', 'reply'.")
    step: int = Field(1, description="Sequence number (e.g., 1 for first reminder).")

class DecisionMaker(BaseModel):
    name: str = Field(..., description="Full name of the decision maker.")
    role: str = Field(..., description="Job title or role.")
    role_category: Optional[str] = Field(None, description="The category of the role (1-6).")
    email: Optional[str] = Field(None, description="Email address.")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL.")
    company_name: str = Field(..., description="Name of the company they work for.")
    email_source: Optional[str] = Field(None, description="Source of the email (e.g., 'extracted', 'verified').")
    status: str = Field("new", description="Conversation status: 'new', 'contacted', 'needs_reply', 'lead', 'blacklisted'.")
    turn_count: int = Field(0, description="Number of conversation turns.")

class Campaign(BaseModel):
    name: str = Field(..., description="The name of the campaign.")
    user_company_name: str = Field(..., description="The name of the user's company.")
    user_company_profile: Optional[CompanyProfile] = Field(None, description="Enriched profile of the user's company.")
    product_description: str = Field(..., description="Description of the product or service.")
    target_filters: CampaignFilters = Field(..., description="Filters for identifying target companies.")
    email_template: Optional[str] = Field(None, description="Draft email template.")
    follow_up_strategy: Optional[str] = Field(None, description="Strategy for follow-up emails.")

class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    campaign: Optional[Campaign] = None
    target_companies: List[TargetCompany] = Field(default_factory=list, description="List of discovered target companies.")
    decision_makers: List[DecisionMaker] = Field(default_factory=list, description="List of identified decision makers.")
    email_drafts: List[Dict[str, Any]] = Field(default_factory=list, description="Generated email drafts.")
    scheduled_emails: List[ScheduledEmail] = Field(default_factory=list, description="List of scheduled follow-up emails.")
