import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ReportDataService(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None):
        """
        Service for manipulating Report data.
        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
        """
        super().__init__(uri, database_name, appname)
        self.collections = {
            "market_analysis": os.getenv("REPORTS_COLLECTION_MARKET_ANALYSIS"),
            "market_news": os.getenv("REPORTS_COLLECTION_MARKET_NEWS"),
            "market_sm": os.getenv("REPORTS_COLLECTION_MARKET_SM"),
            "crypto_analysis": os.getenv("REPORTS_COLLECTION_CRYPTO_ANALYSIS"),
            "crypto_news": os.getenv("REPORTS_COLLECTION_CRYPTO_NEWS"),
            "crypto_sm": os.getenv("REPORTS_COLLECTION_CRYPTO_SM")
        }
        logger.info("ReportDataService initialized")

    @staticmethod
    def _process_object_ids(obj):
        """
        Recursively process nested ObjectIds and convert them to strings.
        
        Args:
            obj: The object to process (dict, list, or any other type)
        """
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if isinstance(value, ObjectId):
                    obj[key] = str(value)
                elif isinstance(value, (dict, list)):
                    ReportDataService._process_object_ids(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    ReportDataService._process_object_ids(item)

    def _fetch_most_recent_report(self, collection_key: str, report_type: str):
        """
        Generic method to fetch the most recent report from any collection.
        
        Args:
            collection_key (str): The key in self.collections dictionary
            report_type (str): Human-readable report type for logging
            
        Returns:
            dict: A dictionary containing the most recent report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        try:
            collection_name = self.collections[collection_key]
            
            if not collection_name:
                logger.warning(f"Collection name not found for {collection_key}")
                return {}
            
            # Create a pipeline to get the most recent report
            pipeline = [
                {
                    "$sort": {"timestamp": -1}  # Sort by timestamp in descending order
                },
                {
                    "$limit": 1  # Limit to only the most recent document
                },
                {
                    "$project": {
                        "report_embedding": 0  # Exclude the report_embedding field
                    }
                }
            ]
            
            # Execute the aggregation pipeline
            result = list(self.db[collection_name].aggregate(pipeline))
            
            # If no result found, return empty dict
            if not result:
                logger.info(f"No {report_type} report found")
                return {}
                
            # Get the first (and only) document
            report = result[0]
            
            # Convert ObjectId to string for proper serialization
            if "_id" in report:
                report["_id"] = str(report["_id"])
            
            # Process any nested ObjectIds in the report
            self._process_object_ids(report)
            
            logger.info(f"Retrieved most recent {report_type} report from {report.get('timestamp')}")
            return report
            
        except Exception as e:
            logger.error(f"Error retrieving {report_type} report: {e}")
            return {}

    def fetch_most_recent_market_analysis_report(self):
        """
        Get the most recent market analysis report.
        
        Returns:
            dict: A dictionary containing the most recent market analysis report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("market_analysis", "market analysis")

    def fetch_most_recent_market_news_report(self):
        """
        Get the most recent market news report.
        
        Returns:
            dict: A dictionary containing the most recent market news report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("market_news", "market news")

    def fetch_most_recent_market_sm_report(self):
        """
        Get the most recent market social media report.
        
        Returns:
            dict: A dictionary containing the most recent market social media report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("market_sm", "market social media")

    def fetch_most_recent_crypto_analysis_report(self):
        """
        Get the most recent crypto analysis report.
        
        Returns:
            dict: A dictionary containing the most recent crypto analysis report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("crypto_analysis", "crypto analysis")

    def fetch_most_recent_crypto_news_report(self):
        """
        Get the most recent crypto news report.
        
        Returns:
            dict: A dictionary containing the most recent crypto news report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("crypto_news", "crypto news")

    def fetch_most_recent_crypto_sm_report(self):
        """
        Get the most recent crypto social media report.
        
        Returns:
            dict: A dictionary containing the most recent crypto social media report with ObjectId converted to string.
                 Returns empty dict if no report is found or an error occurs.
        """
        return self._fetch_most_recent_report("crypto_sm", "crypto social media")


if __name__ == "__main__":
    # Example usage
    report_service = ReportDataService()
    
    # Test all report types
    print("Testing Market Analysis Report:")
    market_analysis = report_service.fetch_most_recent_market_analysis_report()
    print(f"Market Analysis Report: {bool(market_analysis)}")
    
    print("\nTesting Market News Report:")
    market_news = report_service.fetch_most_recent_market_news_report()
    print(f"Market News Report: {bool(market_news)}")
    
    print("\nTesting Market Social Media Report:")
    market_sm = report_service.fetch_most_recent_market_sm_report()
    print(f"Market SM Report: {bool(market_sm)}")
    
    print("\nTesting Crypto Analysis Report:")
    crypto_analysis = report_service.fetch_most_recent_crypto_analysis_report()
    print(f"Crypto Analysis Report: {bool(crypto_analysis)}")
    
    print("\nTesting Crypto News Report:")
    crypto_news = report_service.fetch_most_recent_crypto_news_report()
    print(f"Crypto News Report: {bool(crypto_news)}")
    
    print("\nTesting Crypto Social Media Report:")
    crypto_sm = report_service.fetch_most_recent_crypto_sm_report()
    print(f"Crypto SM Report: {bool(crypto_sm)}")