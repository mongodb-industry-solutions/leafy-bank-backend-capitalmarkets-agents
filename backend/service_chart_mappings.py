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

class ChartMappingsDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("CHART_MAPPINGS_COLLECTION")):
        """
        Service to interact with the chart mappings collection in MongoDB.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "chartMappings".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        logger.info("ChartMappingsDataService initialized")

    def fetch_chart_mappings(self):
        """
        Get chart mappings from the database.

        Returns:
            dict: A dictionary containing the chart mappings by symbol.
        """
        try:
            # Connect to the collection
            collection = self.db[self.collection_name]
            
            # Fetch all chart mappings documents
            cursor = collection.find({})
            
            # Create the chart mappings dictionary
            chart_mappings = {}
            
            # Process each document
            for doc in cursor:
                symbol = doc.get("symbol")
                charts = doc.get("charts", {})
                
                if symbol:
                    chart_mappings[symbol] = {
                        "day": charts.get("day", ""),
                        "week": charts.get("week", ""),
                        "month": charts.get("month", "")
                    }
            
            logger.info(f"Successfully fetched chart mappings for {len(chart_mappings)} symbols")
            return chart_mappings
        
        except Exception as e:
            logger.error(f"Error fetching chart mappings: {str(e)}")
            return {}


if __name__ == "__main__":
    # Example usage
    service = ChartMappingsDataService()
    chart_mappings = service.fetch_chart_mappings()
    print(f"Retrieved mappings for {len(chart_mappings)} symbols")

    print("Chart Mappings:")
    print(chart_mappings)