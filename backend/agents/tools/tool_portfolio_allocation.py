from agents.tools.db.mdb import MongoDBConnector
from typing import Union, TypeVar
import os
import logging
from dotenv import load_dotenv

# Import all state types
from agents.tools.states.agent_market_analysis_state import MarketAnalysisAgentState
from agents.tools.states.agent_market_news_state import MarketNewsAgentState
from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState
from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState
from agents.tools.states.agent_crypto_social_media_state import CryptoSocialMediaAgentState
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Type variable for state - updated to include CryptoNewsAgentState
StateType = TypeVar('StateType', MarketAnalysisAgentState, MarketNewsAgentState, MarketSocialMediaAgentState, CryptoAnalysisAgentState, CryptoSocialMediaAgentState, CryptoNewsAgentState)

class PortfolioAllocationTool(MongoDBConnector):
    def __init__(self, uri=None, database_name=None):
        super().__init__(uri, database_name)
        
        # Define both collection names explicitly
        self.traditional_assets_collection_name = os.getenv("PORTFOLIO_COLLECTION", "portfolio_allocation")
        self.cryptos_collection_name = os.getenv("CRYPTO_PORTFOLIO_COLLECTION", "crypto_portfolio_allocation")
        
        # Initialize both collections
        self.traditional_assets_collection = self.get_collection(self.traditional_assets_collection_name)
        self.cryptos_collection = self.get_collection(self.cryptos_collection_name)
        
        logger.info(f"PortfolioAllocationTool initialized with collections: {self.traditional_assets_collection_name}, {self.cryptos_collection_name}")

    def check_portfolio_allocation(self, state: Union[MarketAnalysisAgentState, MarketNewsAgentState, MarketSocialMediaAgentState, CryptoAnalysisAgentState, CryptoSocialMediaAgentState, CryptoNewsAgentState]) -> dict:
        """Query the appropriate portfolio allocation collection based on state type"""
        
        # Determine collection, message, and projection based on state type
        if isinstance(state, (CryptoAnalysisAgentState, CryptoSocialMediaAgentState, CryptoNewsAgentState)):
            message = "[Tool] Check crypto portfolio allocation."
            collection = self.cryptos_collection
            # Fields for crypto portfolio - matching CryptoAnalysisAgentState.CryptoPortfolioAllocation
            projection = {
                "symbol": 1, 
                "asset_type": 1, 
                "description": 1, 
                "allocation_percentage": 1, 
                "_id": 0
            }
        else:
            message = "[Tool] Check portfolio allocation."
            collection = self.traditional_assets_collection
            # Fields for traditional portfolio - matching MarketAnalysisAgentState.PortfolioAllocation
            projection = {
                "symbol": 1, 
                "description": 1, 
                "allocation_percentage": 1, 
                "_id": 0
            }
        
        logger.info(message)

        # Query the appropriate collection
        results = list(collection.find({}, projection))
        
        # Transform the results into the required format based on state type
        if isinstance(state, (CryptoAnalysisAgentState, CryptoSocialMediaAgentState, CryptoNewsAgentState)):
            portfolio_allocation = [
                {
                    "asset": result["symbol"],
                    "asset_type": result.get("asset_type"),
                    "description": result["description"],
                    "allocation_percentage": result["allocation_percentage"]
                }
                for result in results
            ]
        else:
            portfolio_allocation = [
                {
                    "asset": result["symbol"],
                    "description": result["description"],
                    "allocation_percentage": result["allocation_percentage"]
                }
                for result in results
            ]

        # Update the state with the portfolio allocation
        # Get the correct PortfolioAllocation class and next node based on state type
        if isinstance(state, MarketAnalysisAgentState):
            from agents.tools.states.agent_market_analysis_state import PortfolioAllocation
            next_node = "asset_trends_node"
        elif isinstance(state, CryptoAnalysisAgentState):
            from agents.tools.states.agent_crypto_analysis_state import CryptoPortfolioAllocation as PortfolioAllocation
            next_node = "crypto_trends_node"
        elif isinstance(state, CryptoSocialMediaAgentState):
            from agents.tools.states.agent_crypto_social_media_state import CryptoPortfolioAllocation as PortfolioAllocation
            next_node = "social_media_sentiment_node"
        elif isinstance(state, MarketSocialMediaAgentState):
            from agents.tools.states.agent_market_social_media_state import PortfolioAllocation
            next_node = "social_media_sentiment_node"
        elif isinstance(state, CryptoNewsAgentState):
            from agents.tools.states.agent_crypto_news_state import CryptoPortfolioAllocation as PortfolioAllocation
            next_node = "fetch_market_news_node"
        else:  # MarketNewsAgentState
            from agents.tools.states.agent_market_news_state import PortfolioAllocation
            next_node = "fetch_market_news_node"
            
        # Apply to state using the correct type
        state.portfolio_allocation = [
            PortfolioAllocation(**allocation) for allocation in portfolio_allocation
        ]
        
        # Append the message to the updates list
        state.updates.append(message)

        # Set the next step based on state type
        state.next_step = next_node

        return {"portfolio_allocation": portfolio_allocation, "updates": state.updates, "next_step": state.next_step}

# Initialize the PortfolioAllocationTool
portfolio_allocation_tool = PortfolioAllocationTool()

# Define tools - this is the function used by all workflows
def check_portfolio_allocation_tool(state: Union[MarketAnalysisAgentState, MarketNewsAgentState, MarketSocialMediaAgentState, CryptoAnalysisAgentState, CryptoSocialMediaAgentState, CryptoNewsAgentState]) -> dict:
    """Query the appropriate portfolio allocation collection for any supported state type"""
    return portfolio_allocation_tool.check_portfolio_allocation(state=state)

if __name__ == "__main__":
    # Example usage with all state types
    from agents.tools.states.agent_market_analysis_state import MarketAnalysisAgentState
    from agents.tools.states.agent_market_news_state import MarketNewsAgentState
    from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState
    from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState
    from agents.tools.states.agent_crypto_social_media_state import CryptoSocialMediaAgentState
    from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState
    
    # Test with analysis state
    analysis_state = MarketAnalysisAgentState()
    analysis_result = check_portfolio_allocation_tool(analysis_state)
    print("\nAnalysis State Next Step:", analysis_state.next_step)
    print("Analysis Result:", analysis_result)
    print("Analysis State:", analysis_state)
    
    # Test with market social media state
    market_sm_state = MarketSocialMediaAgentState()
    market_sm_result = check_portfolio_allocation_tool(market_sm_state)
    print("\nMarket Social Media State Next Step:", market_sm_state.next_step)
    print("Market Social Media Result:", market_sm_result)
    print("Market Social Media State:", market_sm_state)

    # Test with market news state
    news_state = MarketNewsAgentState()
    news_result = check_portfolio_allocation_tool(news_state)
    print("\nNews State Next Step:", news_state.next_step)
    print("News Result:", news_result)
    print("News State:", news_state)
    
    # Test with crypto analysis state
    crypto_state = CryptoAnalysisAgentState()
    crypto_result = check_portfolio_allocation_tool(crypto_state)
    print("\nCrypto State Next Step:", crypto_state.next_step)
    print("Crypto Result:", crypto_result)
    print("Crypto State:", crypto_state)
    
    # Test with crypto social media state
    crypto_sm_state = CryptoSocialMediaAgentState()
    crypto_sm_result = check_portfolio_allocation_tool(crypto_sm_state)
    print("\nCrypto Social Media State Next Step:", crypto_sm_state.next_step)
    print("Crypto Social Media Result:", crypto_sm_result)
    print("Crypto Social Media State:", crypto_sm_state)
    
    # Test with crypto news state
    crypto_news_state = CryptoNewsAgentState()
    crypto_news_result = check_portfolio_allocation_tool(crypto_news_state)
    print("\nCrypto News State Next Step:", crypto_news_state.next_step)
    print("Crypto News Result:", crypto_news_result)
    print("Crypto News State:", crypto_news_state)