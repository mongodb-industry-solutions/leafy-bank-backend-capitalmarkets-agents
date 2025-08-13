import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class PortfolioDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None):
        """
        Service for manipulating Portfolio data.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
        """
        super().__init__(uri, database_name, appname)
        self.collections = {
            "allocation": os.getenv("PORTFOLIO_COLLECTION"),
            "performance": os.getenv("PORTFOLIO_PERFORMANCE_COLLECTION"),
            "crypto_allocation": os.getenv("CRYPTO_PORTFOLIO_COLLECTION")
        }
        logger.info("PortfolioDataService initialized")

    def fetch_portfolio_allocation(self):
        """
        Get portfolio allocation data.

        Returns:
            dict: A dictionary containing the portfolio allocation data.
        """
        try:
            collection_name = self.collections["allocation"]
            # Query to get all portfolio allocation data
            result = self.db[collection_name].find()

            # Process the result and construct the portfolio_allocation dictionary
            portfolio_allocation = {}
            for doc in result:
                symbol = doc["symbol"]
                allocation_data = {
                    "allocation_percentage": doc["allocation_percentage"],
                    "allocation_number": doc["allocation_number"],
                    "allocation_decimal": doc["allocation_decimal"],
                    "description": doc["description"],
                    "asset_type": doc["asset_type"]
                }
                portfolio_allocation[symbol] = allocation_data

            logger.info(f"Retrieved portfolio allocation for {len(portfolio_allocation)} assets")
            return portfolio_allocation
        except Exception as e:
            logger.error(f"Error retrieving portfolio allocation: {e}")
            return {}

    def fetch_crypto_portfolio_allocation(self):
        """
        Get crypto portfolio allocation data.

        Returns:
            dict: A dictionary containing the crypto portfolio allocation data.
        """
        try:
            collection_name = self.collections["crypto_allocation"]
            # Query to get all crypto portfolio allocation data
            result = self.db[collection_name].find()

            # Process the result and construct the crypto_portfolio_allocation dictionary
            crypto_portfolio_allocation = {}
            for doc in result:
                symbol = doc["symbol"]
                allocation_data = {
                    "binance_symbol": doc.get("binance_symbol"),
                    "allocation_percentage": doc["allocation_percentage"],
                    "allocation_number": doc["allocation_number"],
                    "allocation_decimal": doc["allocation_decimal"],
                    "description": doc["description"],
                    "asset_type": doc["asset_type"]
                }
                crypto_portfolio_allocation[symbol] = allocation_data

            logger.info(f"Retrieved crypto portfolio allocation for {len(crypto_portfolio_allocation)} assets")
            return crypto_portfolio_allocation
        except Exception as e:
            logger.error(f"Error retrieving crypto portfolio allocation: {e}")
            return {}
            
    def fetch_most_recent_portfolio_performance(self, days=30):
        """
        Get the last 30 days of portfolio performance data.
        
        Args:
            days (int, optional): Number of days of performance data to retrieve. Defaults to 30.
            
        Returns:
            list: A list of portfolio performance documents sorted by date (newest to oldest).
                  Each document contains date, daily return percentage and cumulative return percentage.
        """
        try:
            collection_name = self.collections["performance"]
            
            # Create a pipeline to sort by date and limit to the specified number of days
            pipeline = [
                {
                    "$sort": {"date": -1}  # Sort by date in descending order (newest first)
                },
                {
                    "$limit": days  # Limit to the specified number of days
                },
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},  # Convert ObjectId to string
                        "date": 1,
                        "percentage_of_daily_return": 1,
                        "percentage_of_cumulative_return": 1
                    }
                }
            ]
            
            # Execute the aggregation pipeline
            result = self.db[collection_name].aggregate(pipeline)
            
            # Convert to list and process results
            portfolio_performance = list(result)
            
            logger.info(f"Retrieved portfolio performance data for the last {len(portfolio_performance)} days")
            return portfolio_performance
        except Exception as e:
            logger.error(f"Error retrieving portfolio performance data: {e}")
            return []

if __name__ == "__main__":
    # Example usage
    portfolio_data_service = PortfolioDataService()
    
    # Test fetch_portfolio_allocation
    print("Portfolio Allocation:")
    portfolio_allocation = portfolio_data_service.fetch_portfolio_allocation()
    for symbol, data in portfolio_allocation.items():
        print(f"Symbol: {symbol}, Allocation: {data['allocation_percentage']}, Description: {data['description']}")
    
    # Test fetch_crypto_portfolio_allocation
    print("\nCrypto Portfolio Allocation:")
    crypto_portfolio_allocation = portfolio_data_service.fetch_crypto_portfolio_allocation()
    for symbol, data in crypto_portfolio_allocation.items():
        print(f"Symbol: {symbol}, Binance Symbol: {data['binance_symbol']}, Allocation: {data['allocation_percentage']}, Description: {data['description']}, Asset Type: {data['asset_type']}")
    
    # Test fetch_most_recent_portfolio_performance
    print("\nPortfolio Performance (last 30 days):")
    portfolio_performance = portfolio_data_service.fetch_most_recent_portfolio_performance()
    for data in portfolio_performance:
        print(f"Date: {data['date']}, Daily Return: {data['percentage_of_daily_return']}%, Cumulative Return: {data['percentage_of_cumulative_return']}%")