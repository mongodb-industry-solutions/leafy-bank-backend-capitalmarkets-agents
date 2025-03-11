import operator
from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, AIMessage

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from agent_macro_indicators_node_definition import chatbot_node, tool_node
from agent_macro_indicators_chat_history import temp_mem

import pprint
from typing import Dict, List

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage


# State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str


# Agentic Workflow Definition
workflow = StateGraph(AgentState)

workflow.add_node("chatbot", chatbot_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("chatbot")
workflow.add_conditional_edges("chatbot", tools_condition, {
                               "tools": "tools", END: END})

workflow.add_edge("tools", "chatbot")


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
                    new_messages.append(ToolMessage(content=msg))
    return new_messages


if __name__ == '__main__':

    # Graph Compiliation and visualisation
    graph = workflow.compile()

    # Print the graph in ASCII format
    ascii_graph = graph.get_graph().draw_ascii()
    print(ascii_graph)

    initial_content = "Analyze the fluctuation over three key macro indicators: GDP, Interest Rate, and Unemployment Rate and provide a recommended action based on your analysis."

    # Process and View Response
    events = graph.stream(
        {
            "messages": [
                HumanMessage(
                    content=initial_content
                )
            ]
        },
        {"recursion_limit": 15},
    )

    for event in events:
        print("Event:")
        pprint.pprint(event)
        print("---")

        new_messages = process_event(event)
        if new_messages:
            temp_mem.add_messages(new_messages)

    print("\nFinal state of temp_mem:")
    if hasattr(temp_mem, "messages"):
        for msg in temp_mem.messages:
            print(f"Type: {msg.__class__.__name__}")
            print(f"Content: {msg.content}")
            if msg.additional_kwargs:
                print("Additional kwargs:")
                pprint.pprint(msg.additional_kwargs)
            print("---")
    else:
        print("temp_mem does not have a 'messages' attribute")
