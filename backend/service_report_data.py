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
            "market_news": os.getenv("REPORTS_COLLECTION_MARKET_NEWS")
        }
        logger.info("ReportDataService initialized")

    def fetch_most_recent_market_analysis_report(self):
        """
        Get the most recent market analysis report.
        This function retrieves the most recent market analysis report from the database.
        
        Returns:
            dict: A dictionary containing the most recent market analysis report with ObjectId converted to string.
                Returns empty dict if no report is found or an error occurs.
        """
        try:
            collection_name = self.collections["market_analysis"]
            
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
                logger.info("No market analysis report found")
                return {}
                
            # Get the first (and only) document
            report = result[0]
            
            # Convert ObjectId to string for proper serialization
            if "_id" in report:
                report["_id"] = str(report["_id"])
            
            # Process any nested ObjectIds
            def process_object_ids(obj):
                if isinstance(obj, dict):
                    for key, value in list(obj.items()):
                        if isinstance(value, ObjectId):
                            obj[key] = str(value)
                        elif isinstance(value, dict):
                            process_object_ids(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) or isinstance(item, list):
                                    process_object_ids(item)
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, dict) or isinstance(item, list):
                            process_object_ids(item)
            
            # Process any nested ObjectIds in the report
            process_object_ids(report)
            
            logger.info(f"Retrieved most recent market analysis report from {report.get('timestamp')}")
            return report
            
        except Exception as e:
            logger.error(f"Error retrieving market analysis report: {e}")
            return {}

    def fetch_most_recent_market_news_report(self):
        """
        Get the most recent market news report.
        This function retrieves the most recent market news report from the database.
        
        Returns:
            dict: A dictionary containing the most recent market news report with ObjectId converted to string.
                Returns empty dict if no report is found or an error occurs.
        """
        try:
            collection_name = self.collections["market_news"]
            
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
                logger.info("No market news report found")
                return {}
                
            # Get the first (and only) document
            report = result[0]
            
            # Convert ObjectId to string for proper serialization
            if "_id" in report:
                report["_id"] = str(report["_id"])
            
            # Process any nested ObjectIds
            def process_object_ids(obj):
                if isinstance(obj, dict):
                    for key, value in list(obj.items()):
                        if isinstance(value, ObjectId):
                            obj[key] = str(value)
                        elif isinstance(value, dict):
                            process_object_ids(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) or isinstance(item, list):
                                    process_object_ids(item)
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, dict) or isinstance(item, list):
                            process_object_ids(item)
            
            # Process any nested ObjectIds in the report
            process_object_ids(report)
            
            logger.info(f"Retrieved most recent market news report from {report.get('timestamp')}")
            return report
            
        except Exception as e:
            logger.error(f"Error retrieving market news report: {e}")
            return {}