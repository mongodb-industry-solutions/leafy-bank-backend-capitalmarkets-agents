from langchain.agents import tool
from mdb import MongoDBConnector
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MarketNewsAgentTools(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("NEWS_COLLECTION", "financial_news")
        self.collection = self.get_collection(self.collection_name)
        logger.info("MarketNewsAgentTools initialized")

    def assess_news(self) -> str:
        pass

# Initialize the MarketNewsAgentTools
market_news_agent_tools = MarketNewsAgentTools()

# Define tools
@tool
def assess_news() -> str:
    "Assess News."
    return market_news_agent_tools.assess_news()

tools = [assess_news]

if __name__ == "__main__":
    # Example usage
    logger.info("Assessing News...")
    print(market_news_agent_tools.assess_news())