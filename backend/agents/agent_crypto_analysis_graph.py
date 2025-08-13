from langgraph.graph import END, StateGraph

from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState
from agents.tools.tool_portfolio_allocation import check_portfolio_allocation_tool
from agents.tools.tool_crypto_trends import calculate_crypto_trends_tool
from agents.tools.tool_crypto_momentum_indicators import calculate_crypto_momentum_indicators_tool
from agents.tools.tool_crypto_portfolio_overall_diagnosis import generate_overall_diagnosis_tool


# --- Create LangGraph StateGraph ---
def create_workflow_graph(checkpointer=None):
    """
    Create a workflow graph for the Crypto Analysis Agent.
    This graph defines the sequence of operations that the agent will perform to analyze the digital crypto assets and generate insights.
    """
    # Define the state of the agent
    graph = StateGraph(CryptoAnalysisAgentState)

    # Define the nodes
    graph.add_node("portfolio_allocation_node", check_portfolio_allocation_tool)
    graph.add_node("crypto_trends_node", calculate_crypto_trends_tool)
    graph.add_node("crypto_momentum_indicators_node", calculate_crypto_momentum_indicators_tool)
    graph.add_node("crypto_portfolio_overall_diagnosis_node", generate_overall_diagnosis_tool)

    # Define the edges
    graph.add_edge("portfolio_allocation_node", "crypto_trends_node")
    graph.add_edge("crypto_trends_node", "crypto_momentum_indicators_node")
    graph.add_edge("crypto_momentum_indicators_node", "crypto_portfolio_overall_diagnosis_node")
    graph.add_edge("crypto_portfolio_overall_diagnosis_node", END)

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