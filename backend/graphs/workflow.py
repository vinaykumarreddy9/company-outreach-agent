from langgraph.graph import StateGraph, END
from backend.graphs.state import AgentState
from backend.agents.orchestrator import ContextPlanningAgent
from backend.agents.user_intelligence import UserIntelligenceAgent
from backend.agents.target_discovery import TargetDiscoveryAgent
from backend.agents.decision_maker_finder import DecisionMakerFinderAgent
from backend.agents.email_drafter import EmailDraftingAgent

def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Initialize agents
    planner = ContextPlanningAgent()
    user_intel = UserIntelligenceAgent()
    target_discovery = TargetDiscoveryAgent()
    decision_maker_finder = DecisionMakerFinderAgent()
    email_drafter = EmailDraftingAgent()
    
    # Add nodes
    workflow.add_node("context_planning", planner.run)
    workflow.add_node("user_intelligence", user_intel.run)
    workflow.add_node("target_discovery", target_discovery.run)
    workflow.add_node("decision_maker_finder", decision_maker_finder.run)
    workflow.add_node("email_drafting", email_drafter.run)
    
    # Set entry point
    workflow.set_entry_point("context_planning")
    
    # Add edges
    workflow.add_edge("context_planning", "user_intelligence")
    workflow.add_edge("user_intelligence", "target_discovery")
    workflow.add_edge("target_discovery", "decision_maker_finder")
    workflow.add_edge("decision_maker_finder", "email_drafting")
    workflow.add_edge("email_drafting", END)
    
    return workflow.compile()

app_workflow = create_workflow()
