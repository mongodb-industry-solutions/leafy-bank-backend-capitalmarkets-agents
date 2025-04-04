from tools.db.mdb import MongoDBConnector
from tools.states.agent_market_analysis_state import MarketAnalysisAgentState
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class PersistData(MongoDBConnector):
    def __init__(self, collection_name: str, uri=None, database_name=None):
        """
        Initialize the PersistData class.
        This class is responsible for persisting data to a MongoDB collection. It inherits from the MongoDBConnector class.

        Args:
            collection_name (str): Collection name to be used in MongoDB
            uri (_type_, optional): MongoDB URI. Defaults to None. If None, it will take the value from parent class.
            database_name (_type_, optional): Database Name. Defaults to None. If None, it will take the value from parent class.
        """
        super().__init__(uri, database_name)
        self.collection_name = collection_name
        self.collection = self.get_collection(self.collection_name)
        logger.info(f"PersistData initialized with collection: {self.collection_name}")

    def save_market_analysis_report(self, final_state):
        """
        Save the market analysis report to the MongoDB collection.
        This method takes the final state of the workflow, prepares the report data, and inserts it into the MongoDB collection.
        The report data includes portfolio allocation, asset trends, macroeconomic indicators, market volatility index, and overall diagnosis.

        Args:
            final_state: The final state of the workflow containing the report data.
        """
        try:
            logger.info("Saving market analysis report to MongoDB...")

            # Convert the final_state to a MarketAnalysisAgentState object if necessary
            if not isinstance(final_state, MarketAnalysisAgentState):
                final_state = MarketAnalysisAgentState.model_validate(final_state)

            # Prepare the report data
            report_data = {
                "portfolio_allocation": [allocation.model_dump() for allocation in final_state.portfolio_allocation],
                "report": final_state.report.model_dump(),
                "updates": final_state.updates,
                "timestamp": datetime.now(timezone.utc),  # Current UTC timestamp
                "date_string": datetime.now(timezone.utc).strftime("%Y%m%d")  # Date in "YYYYMMDD" format
            }

            # Insert the report into the MongoDB collection
            self.collection.insert_one(report_data)
            logger.info("Report successfully saved to MongoDB.")
        except Exception as e:
            logger.error(f"Error saving report to MongoDB: {e}")