
import functools
from langchain_core.messages import AIMessage, ToolMessage

from langgraph.prebuilt import ToolNode
from agent_market_analysis_definition import market_analysis_agent

from tools.portfolio_allocation_tools import check_portfolio_allocation_tool
from tools.market_volatility_tools import assess_vix_tool
from tools.macro_indicators_tools import assess_gdp_tool, assess_interest_rate_tool, assess_unemployment_rate_tool
from tools.asset_trends_tools import assess_symbol_trend_tool

portfolio_allocation_tools = [check_portfolio_allocation_tool]
macro_indicators_tools = [assess_gdp_tool, assess_interest_rate_tool, assess_unemployment_rate_tool]
market_volatility_tools = [assess_vix_tool]
asset_trends_tools = [assess_symbol_trend_tool]

from states.agent_market_analysis_state import MarketAnalysisAgentState

# Helper function to create a node for a given agent
def agent_node(state: MarketAnalysisAgentState, agent, name):
    # Initialize the state if it is None
    if state["portfolio_allocation"] is None:
        state["portfolio_allocation"] = {}
    if state["report"] is None:
        state["report"] = {}

    # Invoke the agent with the current state
    result = agent.invoke(state)

    # Convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        # Wrap the ToolMessage content in an AIMessage
        result = AIMessage(
            content=result.content,
            additional_kwargs=result.additional_kwargs,
            name=name,
        )
    elif isinstance(result, dict):
        # Handle raw dictionary results
        result = AIMessage(
            content=str(result),
            additional_kwargs={},
            name=name,
        )

    # Update the state with the result
    return {
        "portfolio_allocation": state["portfolio_allocation"],
        "report": state["report"],
        "messages": [result],  # Ensure the last message is an AIMessage
        "sender": name,
    }

# Market Analysis Agent
market_analysis_agent_node = functools.partial(agent_node, agent=market_analysis_agent, name="Market Analysis Agent")

# Portfolio Allocation
portfolio_allocation_tool_node = ToolNode(portfolio_allocation_tools, name="portfolio_allocation_tools")

# Asset Trends
asset_trends_tool_node = ToolNode(asset_trends_tools, name="asset_trends_tools")

# Macro Indicators
macro_indicators_tool_node = ToolNode(macro_indicators_tools, name="macro_indicators_tools")

# Market Volatility
market_volatility_tool_node = ToolNode(market_volatility_tools, name="market_volatility_tools")
