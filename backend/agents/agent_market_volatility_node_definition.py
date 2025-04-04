
import functools
from langchain_core.messages import AIMessage, ToolMessage

from langgraph.prebuilt import ToolNode
from agent_market_volatility_definition import chatbot_agent
from backend.agents.tools.market_volatility_tools import tools

# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


chatbot_node = functools.partial(agent_node, agent=chatbot_agent, name="Market Volatility Agent Chatbot")
tool_node = ToolNode(tools, name="tools")