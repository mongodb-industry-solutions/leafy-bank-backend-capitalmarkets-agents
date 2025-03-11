from datetime import datetime
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent_llm import get_llm
from agent_macro_indicators_tools import tools
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MacroIndicatorsAgentDefinition:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.system_message = (
            "You are a Macro Indicators Agent responsible for evaluating fluctuations over three key indicators: GDP, Interest Rate, and Unemployment Rate."
            " Use the provided tools to assess the fluctuations and provide a recommended action based on your analysis."
            " The output should be in JSON format with the following structure:"
            "\n{{"
            "\n  \"indicator\": \"(Macro Indicator symbol here)\","
            "\n  \"fluctuation_answer\": \"(The literal response coming from the tool used)\","
            "\n  \"recommended_action\": \"(Include a recommended action here knowing that current investment portfolio includes investment on Equities, Bonds, Real Estate and Commodities)\""
            "\n}}"
            " Ensure that the fluctuation_answer and recommended_action do not exceed 150 characters each."
            " Prefix your response with FINAL ANSWER so the team knows to stop."
            " The answer must be composed by the FINAL ANSWER prefix, plus a JSON with 3 objects (one for each indicator)."
            " You have access to the following tools: {tool_names}."
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
logger.info("Macro Indicators Agent LLM loaded successfully.")
macro_indicators_agent = MacroIndicatorsAgentDefinition(llm, tools)
chatbot_agent = macro_indicators_agent.get_agent()
logger.info("Macro Indicators Agent created and ready to use.")