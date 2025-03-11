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

class MarketVolatilityAgentTools(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("YFINANCE_TIMESERIES_COLLECTION", "yfinanceMarketData")
        self.collection = self.get_collection(self.collection_name)
        logger.info("MarketVolatilityAgentTools initialized")

    def get_most_recent_value(self):
        """
        Get the most recent value for the VIX.
        """
        result = list(self.collection.find({"symbol": "VIX"}).sort("timestamp", -1).limit(1))
        return result[0] if len(result) > 0 else None

    def get_previous_value(self, current_date):
        """
        Get the previous value for the VIX before the given date.
        """
        # Convert current_date to datetime
        current_datetime = datetime.combine(current_date, datetime.min.time())
        result = list(self.collection.find({
            "symbol": "VIX",
            "timestamp": {"$lt": current_datetime}
        }).sort("timestamp", -1).limit(1))
        return result[0] if len(result) > 0 else None

    def assess_vix(self) -> str:
        """
        Assess the VIX and provide the fluctuation with respect to the previous period.
        """
        vix_data = self.get_most_recent_value()
        if not vix_data:
            return "No VIX data available."

        current_vix_value = round(vix_data["close"], 2)
        current_vix_date = vix_data["timestamp"].strftime("%Y-%m-%d")

        previous_vix_data = self.get_previous_value(vix_data["timestamp"].date())
        if not previous_vix_data:
            return "Not enough VIX data to assess."

        previous_vix_value = round(previous_vix_data["close"], 2)
        previous_vix_date = previous_vix_data["timestamp"].strftime("%Y-%m-%d")

        fluctuation = round(current_vix_value - previous_vix_value, 2)
        percentage_change = round((fluctuation / previous_vix_value) * 100, 2)

        return (
            f"VIX close price is {current_vix_value:.2f} (reported on: {current_vix_date}), "
            f"previous close price value was: {previous_vix_value:.2f} (reported on: {previous_vix_date}), "
            f"percentage change: {percentage_change:.2f}%"
        )

# Initialize the MarketVolatilityAgentTools
market_volatility_agent_tools = MarketVolatilityAgentTools()

# Define tools
@tool
def assess_vix() -> str:
    "Assess the VIX and provide the fluctuation with respect to the previous period."
    return market_volatility_agent_tools.assess_vix()

tools = [assess_vix]

if __name__ == "__main__":
    # Example usage
    logger.info("Assessing VIX...")
    print(market_volatility_agent_tools.assess_vix())