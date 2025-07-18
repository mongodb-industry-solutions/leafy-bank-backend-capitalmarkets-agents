import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv
from bson import ObjectId
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle MongoDB ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class CryptoDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("CRYPTO_TIMESERIES_COLLECTION")):
        """
        Service for manipulating Binance crypto data in MongoDB.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "binanceCryptoData".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        logger.info("CryptoDataService initialized")

    def fetch_assets_close_price(self):
        """
        Get the latest close price for all crypto assets.

        Returns:
            dict: A dictionary containing the crypto assets and their close prices.
        """
        try:
            # The aggregation pipeline is used here to efficiently query and process the data within MongoDB.
            # This approach is optimal because:
            # 1. It reduces the amount of data transferred over the network by performing the computation on the server side.
            # 2. It leverages MongoDB's optimized aggregation framework, which is designed for high performance and scalability.
            # 3. It simplifies the code by allowing us to express complex data transformations in a declarative manner.

            # The pipeline consists of two stages:
            # 1. $sort: Sorts the documents by the "timestamp" field in descending order.
            # 2. $group: Groups the documents by the "symbol" field and selects the first document in each group,
            # which corresponds to the latest document due to the previous sorting stage.
            pipeline = [
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$group": {
                        "_id": "$symbol",
                        "latest_close_price": {"$first": "$close"},
                        "latest_timestamp": {"$first": "$timestamp"}
                    }
                }
            ]

            # Execute the aggregation pipeline
            result = self.db[self.collection_name].aggregate(pipeline)

            # Process the result and construct the close_prices dictionary
            close_prices = {}
            for doc in result:
                symbol = doc["_id"]
                close_price = doc["latest_close_price"]
                timestamp = doc["latest_timestamp"]
                close_prices[symbol] = {
                    "close_price": close_price,
                    "timestamp": timestamp
                }

            logger.info(f"Retrieved close prices for {len(close_prices)} crypto assets")
            return close_prices
        except Exception as e:
            logger.error(f"Error retrieving crypto close prices: {e}")
            return {}

    def fetch_most_recent_assets_data(self, limit=3):
        """
        Get the most recent data points for all crypto assets.
        
        Args:
            limit (int, optional): Number of recent documents to fetch per symbol. Defaults to 3.
            
        Returns:
            dict: A dictionary where keys are crypto asset symbols and values are lists of recent data documents.
                 ObjectId values are converted to strings to ensure JSON serialization compatibility.
        """
        try:
            # This aggregation pipeline efficiently retrieves the latest documents for each symbol:
            # 1. $sort: Sorts all documents by timestamp in descending order (newest first)
            # 2. $group: Groups by symbol and creates an array of recent documents
            # 3. $project: Limits the array to the specified number of documents
            pipeline = [
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$group": {
                        "_id": "$symbol",
                        "recent_data": {
                            "$push": {
                                "_id": {"$toString": "$_id"},
                                "symbol": "$symbol",
                                "timestamp": "$timestamp",
                                "open": "$open",
                                "high": "$high",
                                "low": "$low",
                                "close": "$close",
                                "volume": "$volume",
                                "date_load_iso_utc": "$date_load_iso_utc"
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "recent_data": {"$slice": ["$recent_data", limit]}
                    }
                }
            ]
            
            # Execute the aggregation pipeline
            result = self.db[self.collection_name].aggregate(pipeline)
            
            # Process the results and handle ObjectId serialization
            assets_data = {}
            for doc in result:
                symbol = doc["_id"]
                
                # Process each document in recent_data to handle ObjectId
                recent_data = []
                for item in doc["recent_data"]:
                    # Ensure each document has its _id field preserved
                    if "_id" in item:
                        if isinstance(item["_id"], ObjectId):
                            item["_id"] = str(item["_id"])
                    else:
                        # Add a warning if _id is missing
                        logger.warning(f"Document for crypto symbol {symbol} is missing _id field")
                    
                    # Also handle nested ObjectIds if any exist
                    for key, value in item.items():
                        if isinstance(value, ObjectId):
                            item[key] = str(value)
                        elif isinstance(value, dict) and "$oid" in value:
                            item[key] = str(value["$oid"])
                    
                    recent_data.append(item)
                
                assets_data[symbol] = recent_data
                
            logger.info(f"Retrieved {limit} recent data points for {len(assets_data)} crypto assets")
            return assets_data
        except Exception as e:
            logger.error(f"Error retrieving recent crypto assets data: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    crypto_data_service = CryptoDataService()
    
    # Test fetch_assets_close_price
    close_prices = crypto_data_service.fetch_assets_close_price()
    for symbol, data in close_prices.items():
        print(f"Crypto Symbol: {symbol}, Close Price: {data['close_price']}, Timestamp: {data['timestamp']}")
    
    # Test fetch_most_recent_assets_data
    print("\nFetching recent crypto asset data:")
    recent_data = crypto_data_service.fetch_most_recent_assets_data()
    for symbol, data_points in recent_data.items():
        print(f"Crypto Symbol: {symbol}, Recent data points: {len(data_points)}")
        # Example of accessing the first data point if available
        if data_points:
            print(f"  Latest close: {data_points[0].get('close')}, timestamp: {data_points[0].get('timestamp')}")