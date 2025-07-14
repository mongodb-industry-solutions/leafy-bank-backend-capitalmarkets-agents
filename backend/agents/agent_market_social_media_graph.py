from langgraph.graph import END, StateGraph

from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState
from agents.tools.tool_portfolio_allocation import check_portfolio_allocation_tool
from agents.tools.tool_social_media_retrieval import fetch_social_media_submissions_tool
from agents.tools.tool_social_media_sentiment_calc import calculate_social_media_sentiment_tool
from agents.tools.tool_social_media_sentiment_summary import generate_social_media_sentiment_summary_tool


# --- Create LangGraph StateGraph ---
def create_workflow_graph(checkpointer=None):
    """
    Create a workflow graph for the Crypto News Agent.
    This graph defines the sequence of operations that the agent will perform to analyze social media sentiment.
    """
    # Define the state of the agent
    graph = StateGraph(MarketSocialMediaAgentState)

    # Define the nodes
    graph.add_node("portfolio_allocation_node", check_portfolio_allocation_tool)
    graph.add_node("social_media_sentiment_node", fetch_social_media_submissions_tool)
    graph.add_node("social_media_sentiment_calc_node", calculate_social_media_sentiment_tool)
    graph.add_node("social_media_sentiment_summary_node", generate_social_media_sentiment_summary_tool)
    
    # Define the edges
    graph.add_edge("portfolio_allocation_node", "social_media_sentiment_node")
    graph.add_edge("social_media_sentiment_node", "social_media_sentiment_calc_node")
    graph.add_edge("social_media_sentiment_calc_node", "social_media_sentiment_summary_node")
    graph.add_edge("social_media_sentiment_summary_node", END)

    # Set the entry point
    graph.set_entry_point("portfolio_allocation_node")
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


if __name__ == '__main__':

    # Graph Compilation and visualisation
    graph = create_workflow_graph()

    # Print the graph in ASCII format
    ascii_graph = graph.get_graph().draw_ascii()
    print(ascii_graph)
