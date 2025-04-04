from langchain.agents import tool
from tools.db.mdb import MongoDBConnector
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MarketNewsTools(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("NEWS_COLLECTION", "financial_news")
        self.collection = self.get_collection(self.collection_name)
        logger.info("MarketNewsTools initialized")

    def assess_news(self) -> str:
        pass

# Initialize the MarketNewsTools
market_news_tools = MarketNewsTools()

# Define tools
@tool
def assess_news() -> str:
    "Assess News."
    return market_news_tools.assess_news()

tools = [assess_news]

if __name__ == "__main__":
    # Example usage
    logger.info("[Action] Assessing News...")
    print(market_news_tools.assess_news())