from langchain.agents import tool
from mdb import MongoDBConnector
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

class MacroIndicatorsAgentTools(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("PYFREDAPI_COLLECTION", "pyfredapiMacroeconomicIndicators")
        self.collection = self.get_collection(self.collection_name)
        logger.info("MacroIndicatorsAgentTools initialized")

    def get_most_recent_value(self, series_id):
        """
        Get the most recent value for a given series_id.
        """
        result = list(self.collection.find({"series_id": series_id}).sort("date", -1).limit(1))
        return result[0] if len(result) > 0 else None

    def assess_gdp(self) -> str:
        """
        Assess the GDP and provide the fluctuation with respect to the previous period.
        """
        gdp_data = self.get_most_recent_value("GDP")
        if not gdp_data:
            return "No GDP data available."

        previous_gdp_data = list(self.collection.find({"series_id": "GDP", "date": {"$lt": gdp_data["date"]}}).sort("date", -1).limit(1))
        if len(previous_gdp_data) == 0:
            return "Not enough GDP data to assess."

        previous_gdp_value = round(previous_gdp_data[0]["value"], 2)
        previous_gdp_date = previous_gdp_data[0]["date"].strftime("%Y-%m-%d")
        current_gdp_value = round(gdp_data["value"], 2)
        current_gdp_date = gdp_data["date"].strftime("%Y-%m-%d")
        fluctuation = round(current_gdp_value - previous_gdp_value, 2)
        percentage_change = round((fluctuation / previous_gdp_value) * 100, 2)

        if current_gdp_value > previous_gdp_value:
            return f"GDP is up by +{percentage_change:.2f}% with respect to the previous period."
        elif current_gdp_value < previous_gdp_value:
            return f"GDP is down by -{abs(percentage_change):.2f}% with respect to the previous period."
        else:
            return f"GDP is neutral with respect to the previous period."

    def assess_interest_rate(self) -> str:
        """
        Assess the Interest Rate and provide the fluctuation with respect to the previous period.
        """
        interest_rate_data = self.get_most_recent_value("REAINTRATREARAT10Y")
        if not interest_rate_data:
            return "No Interest Rate data available."

        previous_interest_rate_data = list(self.collection.find({"series_id": "REAINTRATREARAT10Y", "date": {"$lt": interest_rate_data["date"]}}).sort("date", -1).limit(1))
        if len(previous_interest_rate_data) == 0:
            return "Not enough Interest Rate data to assess."

        previous_interest_rate_value = round(previous_interest_rate_data[0]["value"], 2)
        previous_interest_rate_date = previous_interest_rate_data[0]["date"].strftime("%Y-%m-%d")
        current_interest_rate_value = round(interest_rate_data["value"], 2)
        current_interest_rate_date = interest_rate_data["date"].strftime("%Y-%m-%d")
        fluctuation = round(current_interest_rate_value - previous_interest_rate_value, 2)

        if current_interest_rate_value > previous_interest_rate_value:
            return f"Interest Rate is up by +{fluctuation:.2f}% with respect to the previous period."
        elif current_interest_rate_value < previous_interest_rate_value:
            return f"Interest Rate is down by -{abs(fluctuation):.2f}% with respect to the previous period."
        else:
            return f"Interest Rate is neutral with respect to the previous period."

    def assess_unemployment_rate(self) -> str:
        """
        Assess the Unemployment Rate and provide the fluctuation with respect to the previous period.
        """
        unemployment_rate_data = self.get_most_recent_value("UNRATE")
        if not unemployment_rate_data:
            return "No Unemployment Rate data available."

        previous_unemployment_rate_data = list(self.collection.find({"series_id": "UNRATE", "date": {"$lt": unemployment_rate_data["date"]}}).sort("date", -1).limit(1))
        if len(previous_unemployment_rate_data) == 0:
            return "Not enough Unemployment Rate data to assess."

        previous_unemployment_rate_value = round(previous_unemployment_rate_data[0]["value"], 2)
        previous_unemployment_rate_date = previous_unemployment_rate_data[0]["date"].strftime("%Y-%m-%d")
        current_unemployment_rate_value = round(unemployment_rate_data["value"], 2)
        current_unemployment_rate_date = unemployment_rate_data["date"].strftime("%Y-%m-%d")
        fluctuation = round(current_unemployment_rate_value - previous_unemployment_rate_value, 2)

        if current_unemployment_rate_value > previous_unemployment_rate_value:
            return f"Unemployment Rate is up by +{fluctuation:.2f}% with respect to the previous period."
        elif current_unemployment_rate_value < previous_unemployment_rate_value:
            return f"Unemployment Rate is down by -{abs(fluctuation):.2f}% with respect to the previous period."
        else:
            return f"Unemployment Rate is neutral with respect to the previous period."

# Initialize the MacroIndicatorsAgentTools
macro_indicators_agent_tools = MacroIndicatorsAgentTools()

# Define tools
@tool
def assess_gdp() -> str:
    "Assess the GDP and provide the fluctuation with respect to the previous period."
    return macro_indicators_agent_tools.assess_gdp()

@tool
def assess_interest_rate() -> str:
    "Assess the Interest Rate and provide the fluctuation with respect to the previous period."
    return macro_indicators_agent_tools.assess_interest_rate()

@tool
def assess_unemployment_rate() -> str:
    "Assess the Unemployment Rate and provide the fluctuation with respect to the previous period."
    return macro_indicators_agent_tools.assess_unemployment_rate()

tools = [assess_gdp, assess_interest_rate, assess_unemployment_rate]

if __name__ == "__main__":
    # Example usage
    logger.info("Assessing GDP...")
    print(macro_indicators_agent_tools.assess_gdp())
    logger.info("Assessing Interest Rate...")
    print(macro_indicators_agent_tools.assess_interest_rate())
    logger.info("Assessing Unemployment Rate...")
    print(macro_indicators_agent_tools.assess_unemployment_rate())