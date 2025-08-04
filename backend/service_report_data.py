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

    def get_consolidated_risk_profile(self):
        """
        Determine the consolidated risk profile across all report types by analyzing
        the most recent report from each collection.
        
        Looks for "[Action] Using risk profile: " in the updates field of each report
        and counts occurrences of each risk profile (BALANCE, HIGH_RISK, CONSERVATIVE, LOW_RISK).
        
        Returns:
            dict: A dictionary containing:
                - "counts": dict with counts for each risk profile
                - "result": str with the most common risk profile. In case of a tie, returns "BALANCE" if present,
                           otherwise "CONSERVATIVE". Default is "BALANCE" if no risk profile is found.
        """
        # Define valid risk profiles
        valid_risk_profiles = ["BALANCE", "HIGH_RISK", "CONSERVATIVE", "LOW_RISK"]
        
        # Initialize accumulator for risk profile counts
        risk_profile_counts = {profile: 0 for profile in valid_risk_profiles}
        
        # List of all report fetch methods
        report_methods = [
            self.fetch_most_recent_market_analysis_report,
            self.fetch_most_recent_market_news_report,
            self.fetch_most_recent_market_sm_report,
            self.fetch_most_recent_crypto_analysis_report,
            self.fetch_most_recent_crypto_news_report,
            self.fetch_most_recent_crypto_sm_report
        ]
        
        # Process each report
        for method in report_methods:
            try:
                report = method()
                
                # Skip if report is empty
                if not report:
                    # Default to BALANCE if no report found
                    risk_profile_counts["BALANCE"] += 1
                    continue
                
                # Get updates field
                updates = report.get("updates", [])
                
                # Look for risk profile in updates
                risk_profile_found = False
                for update in updates:
                    if "[Action] Using risk profile: " in update:
                        # Extract the risk profile
                        for profile in valid_risk_profiles:
                            if profile in update:
                                risk_profile_counts[profile] += 1
                                risk_profile_found = True
                                logger.info(f"Found risk profile {profile} in {method.__name__}")
                                break
                        
                        if risk_profile_found:
                            break
                
                # If no risk profile found, default to BALANCE
                if not risk_profile_found:
                    risk_profile_counts["BALANCE"] += 1
                    logger.info(f"No risk profile found in {method.__name__}, defaulting to BALANCE")
                    
            except Exception as e:
                logger.error(f"Error processing report from {method.__name__}: {e}")
                # Default to BALANCE on error
                risk_profile_counts["BALANCE"] += 1
        
        # Find the risk profile with the most occurrences
        max_count = max(risk_profile_counts.values())
        
        # Get all profiles with the max count (to handle ties)
        top_profiles = [profile for profile, count in risk_profile_counts.items() if count == max_count]
        
        # Apply tiebreaker rules
        if len(top_profiles) == 1:
            result = top_profiles[0]
        elif "BALANCE" in top_profiles:
            result = "BALANCE"
        elif "CONSERVATIVE" in top_profiles:
            result = "CONSERVATIVE"
        else:
            # Fallback to first in the tie (should not happen with our rules)
            result = top_profiles[0]
        
        logger.info(f"Risk profile counts: {risk_profile_counts}")
        logger.info(f"Consolidated risk profile: {result}")
        
        return {
            "counts": risk_profile_counts,
            "result": result
        }


if __name__ == "__main__":
    # Example usage
    report_service = ReportDataService()
    
    # # Test all report types
    # print("Testing Market Analysis Report:")
    # market_analysis = report_service.fetch_most_recent_market_analysis_report()
    # print(f"Market Analysis Report: {bool(market_analysis)}")
    
    # print("\nTesting Market News Report:")
    # market_news = report_service.fetch_most_recent_market_news_report()
    # print(f"Market News Report: {bool(market_news)}")
    
    # print("\nTesting Market Social Media Report:")
    # market_sm = report_service.fetch_most_recent_market_sm_report()
    # print(f"Market SM Report: {bool(market_sm)}")
    
    # print("\nTesting Crypto Analysis Report:")
    # crypto_analysis = report_service.fetch_most_recent_crypto_analysis_report()
    # print(f"Crypto Analysis Report: {bool(crypto_analysis)}")
    
    # print("\nTesting Crypto News Report:")
    # crypto_news = report_service.fetch_most_recent_crypto_news_report()
    # print(f"Crypto News Report: {bool(crypto_news)}")
    
    # print("\nTesting Crypto Social Media Report:")
    # crypto_sm = report_service.fetch_most_recent_crypto_sm_report()
    # print(f"Crypto SM Report: {bool(crypto_sm)}")
    
    print("\nTesting Consolidated Risk Profile:")
    risk_profile_data = report_service.get_consolidated_risk_profile()
    print(f"Risk Profile Counts: {risk_profile_data['counts']}")
    print(f"Consolidated Risk Profile Result: {risk_profile_data['result']}")