from tools.db.mdb import MongoDBConnector
from tools.states.agent_market_analysis_state import MarketAnalysisAgentState, PortfolioAllocation
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class PortfolioAllocationTools(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("PORTFOLIO_COLLECTION", "portfolio_allocation")
        self.collection = self.get_collection(self.collection_name)
        logger.info("PortfolioAllocationTools initialized")

    def check_portfolio_allocation(self, state: MarketAnalysisAgentState) -> dict:
        """Query the portfolio_allocation collection"""
        message = "[Tool] Check portfolio allocation."
        logger.info(message)

        # Query the collection
        results = list(self.collection.find({}, {"symbol": 1, "description": 1, "allocation_percentage": 1, "_id": 0}))
        
        # Transform the results into the required format
        portfolio_allocation = [
            {
                "asset": result["symbol"],
                "description": result["description"],
                "allocation_percentage": result["allocation_percentage"]
            }
            for result in results
        ]

        # Update the state with the portfolio allocation
        state.portfolio_allocation = [
            PortfolioAllocation(**allocation) for allocation in portfolio_allocation
        ]
        
        # Append the message to the updates list
        state.updates.append(message)

        # Set the next step in the state
        state.next_step = "asset_trends_node"

        return { "portfolio_allocation": portfolio_allocation }

# Initialize the PortfolioAllocationTools
portfolio_allocation_tools = PortfolioAllocationTools()

# Define tools
def check_portfolio_allocation_tool(state: MarketAnalysisAgentState) -> dict:
    """Query the portfolio_allocation collection"""
    return portfolio_allocation_tools.check_portfolio_allocation(state=state)

if __name__ == "__main__":
    # Example usage
    logger.info("Fetching Portfolio Allocation...")
    # Initialize the state
    state = MarketAnalysisAgentState()
    # Check portfolio allocation
    allocation = check_portfolio_allocation_tool(state)

    # Print the updated state
    print("\nUpdated State:")
    print(state)