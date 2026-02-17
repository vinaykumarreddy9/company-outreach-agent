from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config.settings import settings
from backend.schemas.campaign import Campaign
from backend.graphs.state import AgentState
from backend.services.neon_db import create_campaign, update_campaign_basic
import logging

logger = logging.getLogger(__name__)

class ContextPlanningAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.structured_llm = self.llm.with_structured_output(Campaign)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert sales campaign planner. Your goal is to analyze the user's request and extract structured campaign details. "
                       "The user will provide their company name, their offerings/products, and target company filters (industry, size, revenue, etc.). "
                       "Extract: \n"
                       "1. 'user_company_name': The user's own company.\n"
                       "2. 'product_description': What they are selling.\n"
                       "3. 'target_filters': Filters for companies they want to reach out to (industries, locations, roles, company_size, revenue/profit ranges).\n"
                       "Pay close attention to financial constraints "
                       "(e.g., 'turnover' maps to 'revenue', 'profit' maps to 'profit'). distinguish between minimum and maximum values."),
            ("user", "{input}")
        ])

    async def run(self, state: AgentState) -> AgentState:
        try:
            print(f"Running ContextPlanningAgent (async) with input: {state['user_input']}")
            
            # Preserve existing name if possible
            existing_name = None
            if state.get("campaign_id"):
                from backend.services.neon_db import get_campaign_details
                details = await get_campaign_details(state["campaign_id"])
                if details and "campaign" in details:
                    existing_name = details["campaign"]["name"]

            chain = self.prompt | self.structured_llm
            campaign = await chain.ainvoke({"input": state["user_input"]})
            
            # If we had an existing name, respect it over the LLM's guess
            if existing_name:
                campaign.name = existing_name

            # Persist Campaign
            if state.get("campaign_id"):
                campaign_id = state["campaign_id"]
                await update_campaign_basic(campaign_id, campaign.name, campaign.product_description)
                print(f"Existing Campaign '{campaign.name}' updated with ID: {campaign_id}")
            else:
                campaign_id = await create_campaign(campaign.name, campaign.product_description)
                if campaign_id:
                    print(f"New Campaign '{campaign.name}' persisted with ID: {campaign_id}")
                    state["campaign_id"] = campaign_id
            
            state["campaign_data"] = campaign
            state["current_agent"] = "ContextPlanningAgent"
            print(f"ContextPlanningAgent completed. Campaign: {campaign.name}")
        except Exception as e:
            error_msg = f"Error in ContextPlanningAgent (async): {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
