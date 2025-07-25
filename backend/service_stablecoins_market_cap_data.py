import logging
from datetime import datetime
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

class StablecoinsMarketCapDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("COINGECKO_STABLECOIN_COLLECTION")):
        """
        Service for manipulating stablecoins market cap data.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "stablecoin_market_caps".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        logger.info("StablecoinsMarketCapDataService initialized")

    def fetch_most_recent_stablecoins_market_cap(self):
        """
        Get the most recent stablecoins market cap data.

        Returns:
            list: A list of dictionaries containing the most recent stablecoins market cap data.
        """
        try:
            logger.info("Fetching most recent stablecoins market cap data")
            
            # Get the collection
            collection = self.get_collection(self.collection_name)
            
            # First, find the most recent date in the collection
            latest_date_doc = collection.find_one(
                {},
                sort=[("Date", -1)]
            )
            
            if not latest_date_doc:
                logger.warning("No stablecoin market cap data found in collection")
                return []
            
            latest_date = latest_date_doc["Date"]
            logger.info(f"Latest date found: {latest_date}")
            
            # Get all documents for the latest date with explicit projection
            latest_data = list(collection.find(
                {"Date": latest_date},
                {
                    "_id": 0,
                    "Date": 1,
                    "Symbol": 1,
                    "Name": 1,
                    "Market Cap": 1,
                    "Trend (%)": 1,
                    "Trend direction": 1
                }
            ).sort([("Market Cap", -1)]))  # Sort by market cap descending
            
            logger.info(f"Found {len(latest_data)} stablecoin records for the latest date")
            
            return latest_data
            
        except Exception as e:
            logger.error(f"Error fetching most recent stablecoins market cap data: {str(e)}")
            raise e
