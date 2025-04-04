from datetime import datetime
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent_llm import get_llm

from tools.portfolio_allocation_tools import check_portfolio_allocation_tool
from tools.market_volatility_tools import assess_vix_tool
from tools.macro_indicators_tools import assess_gdp_tool, assess_interest_rate_tool, assess_unemployment_rate_tool
from tools.asset_trends_tools import assess_symbol_trend_tool

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MarketAnalysisAgentDefinition:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.system_message = (
                "You are a Market Analysis Agent tasked with analyzing portfolio trends, macroeconomic indicators, and market volatility. "
                "Your mission is to generate a comprehensive JSON-formatted report based on the provided data and tools. "
                "Follow these steps to complete your analysis:"
                "\n\n1. **Portfolio Allocation Analysis**:"
                " - Review the portfolio allocation and provide a list of assets with their respective allocation percentages and descriptions."
                "\n\n2. **Asset Trend Analysis**:"
                " - For each asset, calculate its Moving Average (MA) over a specified period."
                " - Compare the last closing price with the MA to determine the trend:"
                "   - If the last closing price is above the MA, it indicates an uptrend."
                "   - If the last closing price is below the MA, it indicates a downtrend."
                "\n\n3. **Macroeconomic Indicator Analysis**:"
                " - Assess fluctuations in key macroeconomic indicators: GDP, Interest Rate, and Unemployment Rate."
                " - Provide insights into how these changes may impact the portfolio."
                "\n\n4. **Market Volatility Analysis**:"
                " - Evaluate the VIX (Volatility Index) to assess market sentiment and volatility risks."
                " - Note that a VIX baseline typically ranges between 12 and 20."
                "\n\n**Output Requirements:**"
                " - The output must be a JSON-formatted report with the following structure:"
                "\n```json"
                "\n{{"
                "\n  \"asset_trends\": ["
                "\n    {{"
                "\n      \"asset\": \"(The asset symbol here)\","
                "\n      \"fluctuation_answer\": \"(The literal response from the tool used)\","
                "\n      \"diagnosis\": \"(Include a diagnosis or recommended action)\""
                "\n    }},"
                "\n    ... (repeat for each asset)"
                "\n  ],"
                "\n  \"macro_indicators\": ["
                "\n    {{"
                "\n      \"macro_indicator\": \"(Macro indicator symbol here)\","
                "\n      \"fluctuation_answer\": \"(The literal response from the tool used)\","
                "\n      \"diagnosis\": \"(Include a diagnosis or recommended action)\""
                "\n    }},"
                "\n    ... (repeat for each indicator)"
                "\n  ],"
                "\n  \"market_volatility_index\": {{"
                "\n    \"volatility_index\": \"(The market volatility index symbol (VIX))\","
                "\n    \"fluctuation_answer\": \"(The literal response from the tool used)\","
                "\n    \"diagnosis\": \"(Include a diagnosis or recommended action)\""
                "\n  }},"
                "\n  \"overall_diagnosis\": \"(A general diagnosis of the portfolio)\""
                "\n}}"
                "\n```"
                "\n\n**Rules:**"
                " - Ensure that `fluctuation_answer` and `diagnosis` do not exceed 100 characters each."
                " - Ensure that `overall_diagnosis` does not exceed 150 characters."
                " - Do not include anything other than the JSON report in the output."
                " - Prefix your response with `FINAL ANSWER` to signal completion."
                "\n\nYou have access to the following tools: {tool_names}."
                "\nCurrent time: {time}."
            )
        self.agent = self.create_agent()

    def create_agent(self):
        """Create an agent"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.system_message,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        prompt = prompt.partial(system_message=self.system_message)
        prompt = prompt.partial(time=lambda: str(datetime.now()))
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in self.tools]))

        return prompt | self.llm.bind_tools(self.tools)

    def get_agent(self):
        return self.agent
    

llm = get_llm()
logger.info("Market Analysis Agent LLM loaded successfully.")
tools = [check_portfolio_allocation_tool, assess_symbol_trend_tool, assess_gdp_tool, assess_interest_rate_tool, assess_unemployment_rate_tool, assess_vix_tool]
market_analysis_agent_definition = MarketAnalysisAgentDefinition(llm, tools)
market_analysis_agent = market_analysis_agent_definition.get_agent()
logger.info("Market Analysis Agent created and ready to use.")