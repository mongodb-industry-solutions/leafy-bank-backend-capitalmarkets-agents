import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MacroIndicatorDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("PYFREDAPI_COLLECTION")):
        """
        Service for manipulating macroeconomic indicators data.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "pyfredapiMacroeconomicIndicators".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        logger.info("MacroIndicatorDataService initialized")

    def fetch_most_recent_macro_indicators(self):
        """
        Get the most recent macroeconomic indicators.

        Returns:
            dict: A dictionary containing the most recent macroeconomic indicators.
        """
        try:
            # The aggregation pipeline is used here to efficiently query and process the data within MongoDB.
            # This approach is optimal because:
            # 1. It reduces the amount of data transferred over the network by performing the computation on the server side.
            # 2. It leverages MongoDB's optimized aggregation framework, which is designed for high performance and scalability.
            # 3. It simplifies the code by allowing us to express complex data transformations in a declarative manner.

            # The pipeline consists of two stages:
            # 1. $sort: Sorts the documents by the "date" field in descending order.
            # 2. $group: Groups the documents by the "series_id" field and selects the first document in each group,
            #            which corresponds to the most recent document due to the previous sorting stage.
            pipeline = [
                {
                    "$sort": {"date": -1}
                },
                {
                    "$group": {
                        "_id": "$series_id",
                        "title": {"$first": "$title"},
                        "frequency": {"$first": "$frequency"},
                        "frequency_short": {"$first": "$frequency_short"},
                        "units": {"$first": "$units"},
                        "units_short": {"$first": "$units_short"},
                        "date": {"$first": "$date"},
                        "value": {"$first": "$value"}
                    }
                }
            ]

            # Execute the aggregation pipeline
            result = self.db[self.collection_name].aggregate(pipeline)

            # Process the result and construct the macro_indicators dictionary
            macro_indicators = {}
            for doc in result:
                series_id = doc["_id"]
                macro_indicators[series_id] = {
                    "title": doc["title"],
                    "frequency": doc["frequency"],
                    "frequency_short": doc["frequency_short"],
                    "units": doc["units"],
                    "units_short": doc["units_short"],
                    "date": doc["date"],
                    "value": doc["value"]
                }

            logger.info(f"Retrieved most recent macro indicators for {len(macro_indicators)} series")
            return macro_indicators
        except Exception as e:
            logger.error(f"Error retrieving most recent macro indicators: {e}")
            return {}

    def get_macro_indicators_trend(self):
        """
        Get the trend direction for each macroeconomic indicator by comparing the two most recent values.
        
        Returns:
            dict: A dictionary containing the trend information for each macro indicator.
                Format: {series_id: {'title': title, 'arrow_direction': 'ARROW_UP/ARROW_DOWN/EQUAL'}}
        """
        try:
            # Aggregation pipeline to get the two most recent values for each series_id
            pipeline = [
                {
                    "$sort": {"date": -1}  # Sort by date in descending order
                },
                {
                    "$group": {
                        "_id": "$series_id",
                        "title": {"$first": "$title"},
                        "latest_values": {"$push": {"date": "$date", "value": "$value"}},
                    }
                },
                {
                    "$project": {
                        "title": 1,
                        "latest_values": {"$slice": ["$latest_values", 2]}  # Get only the first 2 values
                    }
                }
            ]

            # Execute the aggregation pipeline
            result = self.db[self.collection_name].aggregate(pipeline)

            # Process the result to determine trend direction
            trend_indicators = {}
            for doc in result:
                series_id = doc["_id"]
                title = doc["title"]
                
                # Skip if we don't have at least 2 values to compare
                if len(doc["latest_values"]) < 2:
                    continue
                    
                latest_value = doc["latest_values"][0]["value"]
                previous_value = doc["latest_values"][1]["value"]
                latest_date = doc["latest_values"][0]["date"]
                previous_date = doc["latest_values"][1]["date"]
                
                # Determine trend direction
                if latest_value > previous_value:
                    arrow_direction = "ARROW_UP"
                elif latest_value < previous_value:
                    arrow_direction = "ARROW_DOWN"
                else:
                    arrow_direction = "EQUAL"
                
                trend_indicators[series_id] = {
                    "title": title,
                    "arrow_direction": arrow_direction,
                    "latest_value": latest_value,
                    "latest_date": latest_date,
                    "previous_value": previous_value,
                    "previous_date": previous_date
                }

            logger.info(f"Retrieved trend direction for {len(trend_indicators)} macro indicators")
            return trend_indicators
        except Exception as e:
            logger.error(f"Error retrieving macro indicators trend: {e}")
            return {}

if __name__ == "__main__":

    import pprint
    # Example usage
    macro_indicator_data_service = MacroIndicatorDataService()
    
    most_recent_macro_indicators = macro_indicator_data_service.fetch_most_recent_macro_indicators()
    pprint.pprint(most_recent_macro_indicators)

    trend_indicators = macro_indicator_data_service.get_macro_indicators_trend()
    pprint.pprint(trend_indicators)