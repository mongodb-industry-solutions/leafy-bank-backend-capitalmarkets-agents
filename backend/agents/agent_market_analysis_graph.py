from langgraph.graph import END, StateGraph

from tools.states.agent_market_analysis_state import MarketAnalysisAgentState
from tools.portfolio_allocation_tools import check_portfolio_allocation_tool
from tools.asset_trends_tools import calculate_asset_trends_tool
from tools.macro_indicators_tools import assess_macro_indicators_tool
from tools.market_volatility_tools import assess_vix_tool
from tools.portfolio_overall_diagnosis_tools import generate_overall_diagnosis_tool


# --- Create LangGraph StateGraph ---
def create_workflow_graph(checkpointer=None):
    """
    Create a workflow graph for the Market Analysis Agent.
    This graph defines the sequence of operations that the agent will perform to analyze the market and generate insights.
    """
    # Define the state of the agent
    graph = StateGraph(MarketAnalysisAgentState)

    # Define the nodes
    graph.add_node("portfolio_allocation_node", check_portfolio_allocation_tool)
    graph.add_node("asset_trends_node", calculate_asset_trends_tool)
    graph.add_node("macro_indicators_node", assess_macro_indicators_tool)
    graph.add_node("market_volatility_node", assess_vix_tool)
    graph.add_node("portfolio_overall_diagnosis_node", generate_overall_diagnosis_tool)

    # Define the edges
    graph.add_edge("portfolio_allocation_node", "asset_trends_node")
    graph.add_edge("asset_trends_node", "macro_indicators_node")
    graph.add_edge("macro_indicators_node", "market_volatility_node")
    graph.add_edge("market_volatility_node", "portfolio_overall_diagnosis_node")
    graph.add_edge("portfolio_overall_diagnosis_node", END)

    # Set the entry point
    graph.set_entry_point("portfolio_allocation_node")
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


if __name__ == '__main__':

    # Graph Compiliation and visualisation
    graph = create_workflow_graph()

    # Print the graph in ASCII format
    ascii_graph = graph.get_graph().draw_ascii()
    print(ascii_graph)