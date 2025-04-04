from langchain_core.messages import BaseMessage, AIMessage

from langgraph.graph import END, StateGraph

from agent_market_analysis_nodes import market_analysis_agent_node, asset_trends_tool_node, macro_indicators_tool_node, market_volatility_tool_node, portfolio_allocation_tool_node
from states.agent_market_analysis_state import MarketAnalysisAgentState

import pprint
from typing import Dict, List

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage


# --- Create LangGraph StateGraph ---
def create_workflow_graph(checkpointer=None):
    # Agentic Workflow Definition
    graph = StateGraph(MarketAnalysisAgentState)

    # Define the nodes
    graph.add_node("market_analysis_agent", market_analysis_agent_node)
    graph.add_node("portfolio_allocation_tools", portfolio_allocation_tool_node)
    graph.add_node("assess_asset_trends", asset_trends_tool_node)
    graph.add_node("asset_macro_indicators", macro_indicators_tool_node)
    graph.add_node("market_volatility_tools", market_volatility_tool_node)

    # Define the edges
    graph.add_edge("market_analysis_agent", "portfolio_allocation_tools")
    graph.add_edge("portfolio_allocation_tools", "asset_trends_tools")
    graph.add_edge("asset_trends_tools", "macro_indicators_tools")
    graph.add_edge("macro_indicators_tools", "market_volatility_tools")
    graph.add_edge("market_volatility_tools", END)

    # Set the entry point
    graph.set_entry_point("market_analysis_agent")
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()



def process_event(event: Dict) -> List[BaseMessage]:
    new_messages = []
    for value in event.values():
        if isinstance(value, dict) and "messages" in value:
            for msg in value["messages"]:
                if isinstance(msg, BaseMessage):
                    new_messages.append(msg)
                elif isinstance(msg, dict) and "content" in msg:
                    new_messages.append(
                        AIMessage(
                            content=msg["content"],
                            additional_kwargs={"sender": msg.get("sender")},
                        )
                    )
                elif isinstance(msg, str):
                    # Convert string messages to AIMessage
                    new_messages.append(AIMessage(content=msg))
    return new_messages


if __name__ == '__main__':

    # Graph Compiliation and visualisation
    graph = create_workflow_graph()

    # Print the graph in ASCII format
    ascii_graph = graph.get_graph().draw_ascii()
    print(ascii_graph)

    initial_message = "Hello, I would like to analyze my portfolio."

    # Initial State
    initial_state: MarketAnalysisAgentState = {
        "portfolio_allocation": [],
        "report": {},
        "messages": [
                HumanMessage(
                    content=initial_message
                )
            ],
        "sender": ""
    }

    # Process and View Response
    events = graph.stream(initial_state,
        {"recursion_limit": 5},
    )

    for event in events:
        print("Event:")
        pprint.pprint(event)
        print("---")

        new_messages = process_event(event)