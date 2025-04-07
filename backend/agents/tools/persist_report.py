from tools.db.mdb import MongoDBConnector
from tools.states.agent_market_analysis_state import MarketAnalysisAgentState
from tools.states.agent_market_news_state import MarketNewsAgentState
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class PersistReportInMongoDB(MongoDBConnector):
    def __init__(self, collection_name: str, uri=None, database_name=None):
        """
        Initialize the PersistReportInMongoDB class.
        This class is responsible for persisting data to a MongoDB collection. It inherits from the MongoDBConnector class.

        Args:
            collection_name (str): Collection name to be used in MongoDB
            uri (_type_, optional): MongoDB URI. Defaults to None. If None, it will take the value from parent class.
            database_name (_type_, optional): Database Name. Defaults to None. If None, it will take the value from parent class.
        """
        super().__init__(uri, database_name)
        self.collection_name = collection_name
        self.collection = self.get_collection(self.collection_name)
        logger.info(f"PersistReportInMongoDB initialized with collection: {self.collection_name}")

    def save_market_analysis_report(self, final_state):
        """
        Save the market analysis report to the MongoDB collection.
        This method takes the final state of the workflow, prepares the report data, and inserts it into the MongoDB collection.
        If a report for the current date already exists, it will be replaced with the new one.

        Args:
            final_state: The final state of the workflow containing the report data.
        """
        try:
            logger.info("Saving market analysis report to MongoDB...")

            # Convert the final_state to a MarketAnalysisAgentState object if necessary
            if not isinstance(final_state, MarketAnalysisAgentState):
                final_state = MarketAnalysisAgentState.model_validate(final_state)

            # Get current date in UTC
            current_date = datetime.now(timezone.utc)
            date_string = current_date.strftime("%Y%m%d")  # Date in "YYYYMMDD" format

            # Prepare the report data
            report_data = {
                "portfolio_allocation": [allocation.model_dump() for allocation in final_state.portfolio_allocation],
                "report": final_state.report.model_dump(),
                "updates": final_state.updates,
                "timestamp": current_date,
                "date_string": date_string
            }

            # Check if a report for the current date already exists
            existing_report = self.collection.find_one({"date_string": date_string})
            
            if existing_report:
                # Update the existing report with the new data
                self.collection.replace_one({"_id": existing_report["_id"]}, report_data)
                logger.info(f"Existing report for date {date_string} updated with the most recent version.")
            else:
                # Insert a new report
                self.collection.insert_one(report_data)
                logger.info(f"New report for date {date_string} saved to MongoDB.")
                
        except Exception as e:
            logger.error(f"Error saving report to MongoDB: {e}")
            
    def save_market_news_report(self, final_state):
        """
        Save the market news report to the MongoDB collection.
        This method takes the final state of the workflow, prepares the report data, and inserts it into the MongoDB collection.
        If a report for the current date already exists, it will be replaced with the new one.

        Args:
            final_state: The final state of the workflow containing the news report data.
        """
        try:
            logger.info("Saving market news report to MongoDB...")

            # Convert the final_state to a MarketNewsAgentState object if necessary
            if not isinstance(final_state, MarketNewsAgentState):
                final_state = MarketNewsAgentState.model_validate(final_state)

            # Get current date in UTC
            current_date = datetime.now(timezone.utc)
            date_string = current_date.strftime("%Y%m%d")  # Date in "YYYYMMDD" format

            # Prepare the report data
            report_data = {
                "portfolio_allocation": [allocation.model_dump() for allocation in final_state.portfolio_allocation],
                "report": final_state.report.model_dump(),
                "updates": final_state.updates,
                "timestamp": current_date,
                "date_string": date_string
            }

            # Check if a report for the current date already exists
            existing_report = self.collection.find_one({"date_string": date_string})
            
            if existing_report:
                # Update the existing report with the new data
                self.collection.replace_one({"_id": existing_report["_id"]}, report_data)
                logger.info(f"Existing news report for date {date_string} updated with the most recent version.")
            else:
                # Insert a new report
                self.collection.insert_one(report_data)
                logger.info(f"New news report for date {date_string} saved to MongoDB.")
                
        except Exception as e:
            logger.error(f"Error saving news report to MongoDB: {e}")