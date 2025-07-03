from db.mdb import MongoDBConnector
from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState, CryptoAssetTrend
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

# Constants - Crypto-optimized MA periods
CRYPTO_SHORT_MA = int(os.getenv("CRYPTO_SHORT_MA", 10))  # Short-term trend (10 days)
CRYPTO_LONG_MA = int(os.getenv("CRYPTO_LONG_MA", 20))    # Medium-term trend (20 days)

class CryptoAssetTrendsTool(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("CRYPTO_TIMESERIES_COLLECTION", "binanceCryptoData")
        self.collection = self.get_collection(self.collection_name)
        logger.info("CryptoAssetTrendsTool initialized")

    def calculate_moving_average(self, symbol: str, period: int) -> float:
        """
        Calculate the moving average for a given crypto symbol and period.
        """
        pipeline = [
            {"$match": {"symbol": symbol}},
            {"$sort": {"timestamp": -1}},
            {"$limit": period},
            {"$group": {
                "_id": None,
                "moving_average": {"$avg": "$close"}
            }}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["moving_average"] if result else None

    def get_last_closing_price(self, symbol: str) -> tuple:
        """
        Get the last closing price and timestamp for a given crypto symbol.
        Returns tuple of (close_price, formatted_date)
        """
        result = list(self.collection.find({"symbol": symbol}).sort("timestamp", -1).limit(1))
        if result:
            close_price = result[0]["close"]
            # Extract date from timestamp and format it
            timestamp = result[0]["timestamp"]
            formatted_date = timestamp.strftime("%Y-%m-%d")
            return close_price, formatted_date
        return None, None

    def analyze_crypto_trend(self, symbol: str, last_price: float, short_ma: float, long_ma: float, asset_type: str, price_date: str) -> tuple:
        """
        Analyze crypto trend using dual MA system and return trend direction and diagnosis.
        """
        if asset_type == "Stablecoin":
            # Stablecoins should trade close to $1
            deviation_pct = abs((last_price - 1.0) / 1.0) * 100
            if deviation_pct > 0.5:
                return "depeg_risk", f"Stablecoin showing {deviation_pct:.2f}% deviation from peg. Monitor for stability."
            else:
                return "stable", f"Stablecoin maintaining peg stability. Safe for portfolio stability."
        
        # Cryptocurrency analysis using dual MA system
        # Golden Cross (bullish) vs Death Cross (bearish)
        ma_signal = "bullish" if short_ma > long_ma else "bearish"
        
        # Price position relative to MAs
        short_ma_diff = ((last_price - short_ma) / short_ma) * 100
        long_ma_diff = ((last_price - long_ma) / long_ma) * 100
        
        # Determine trend strength and direction using actual database date
        if short_ma_diff > 3 and long_ma_diff > 5:
            trend = "strong_uptrend"
            diagnosis = f"Strong bullish momentum. {price_date} close price {short_ma_diff:.1f}% above MA{CRYPTO_SHORT_MA}. Consider profit-taking."
        elif short_ma_diff < -3 and long_ma_diff < -5:
            trend = "strong_downtrend"
            diagnosis = f"Strong bearish momentum. {price_date} close price {abs(short_ma_diff):.1f}% below MA{CRYPTO_SHORT_MA}. Potential buying opportunity."
        elif ma_signal == "bullish" and short_ma_diff > 0:
            trend = "uptrend"
            diagnosis = f"Bullish trend confirmed. {price_date} close price above both Moving Averages (MA{CRYPTO_SHORT_MA} and MA{CRYPTO_LONG_MA})."
        elif ma_signal == "bearish" and short_ma_diff < 0:
            trend = "downtrend"
            diagnosis = f"Bearish trend confirmed. {price_date} close price below both Moving Averages (MA{CRYPTO_SHORT_MA} and MA{CRYPTO_LONG_MA})."
        else:
            trend = "sideways"
            diagnosis = f"Mixed signals. {price_date} close price consolidating between MA{CRYPTO_SHORT_MA} and MA{CRYPTO_LONG_MA}."
        
        return trend, diagnosis

    def calculate_crypto_trends(self, state: CryptoAnalysisAgentState) -> dict:
        """
        Assess the trend of all digital assets using crypto-optimized dual MA analysis.
        """
        message = "[Tool] Calculate crypto asset trends."
        logger.info(message)

        crypto_trends = []
        for allocation in state.portfolio_allocation:
            symbol = allocation.asset

            # Calculate both short and long moving averages
            short_ma = self.calculate_moving_average(symbol, CRYPTO_SHORT_MA)
            long_ma = self.calculate_moving_average(symbol, CRYPTO_LONG_MA)
            
            if short_ma is None or long_ma is None:
                logger.warning(f"Not enough data to calculate MAs for {symbol}.")
                continue

            # Get the last closing price and its actual date from database
            last_closing_price, price_date = self.get_last_closing_price(symbol)
            if last_closing_price is None or price_date is None:
                logger.warning(f"Not enough data to retrieve the last closing price for {symbol}.")
                continue

            # Format prices appropriately for crypto
            price_formatted = f"${last_closing_price:,.2f}" if last_closing_price >= 1 else f"${last_closing_price:.6f}"
            short_ma_formatted = f"${short_ma:,.2f}" if short_ma >= 1 else f"${short_ma:.6f}"
            long_ma_formatted = f"${long_ma:,.2f}" if long_ma >= 1 else f"${long_ma:.6f}"
            
            # Analyze trend using dual MA system with actual database date
            trend, diagnosis = self.analyze_crypto_trend(
                symbol, last_closing_price, short_ma, long_ma, allocation.asset_type, price_date
            )

            # Create fluctuation answer with dual MA info (keeping same structure)
            fluctuation_answer = f"{symbol} close price is {price_formatted}, MA{CRYPTO_SHORT_MA} is {short_ma_formatted}, and MA{CRYPTO_LONG_MA} is {long_ma_formatted}."

            # Create a CryptoAssetTrend object (keeping exact same structure)
            crypto_trend = CryptoAssetTrend(
                asset=symbol,
                fluctuation_answer=fluctuation_answer,
                diagnosis=diagnosis
            )
            crypto_trends.append(crypto_trend)

        # Update the state with the digital crypto asset trends
        state.report.crypto_trends = crypto_trends

        # Append the message to the updates list
        state.updates.append(message)

        # Set the next step in the state for crypto workflow
        state.next_step = "crypto_momentum_indicators_node"

        return {"crypto_trends": crypto_trends, "updates": state.updates, "next_step": state.next_step}


# Initialize the CryptoAssetTrendsTool
crypto_trends_tool = CryptoAssetTrendsTool()

# Define tools
def calculate_crypto_trends_tool(state: CryptoAnalysisAgentState) -> dict:
    """
    Assess the trend of digital crypto assets using crypto-optimized dual MA analysis.
    """
    return crypto_trends_tool.calculate_crypto_trends(state=state)

if __name__ == "__main__":
    from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState, PortfolioAllocation

    # Initialize the state with crypto assets for testing
    state = CryptoAnalysisAgentState(
        portfolio_allocation=[
            PortfolioAllocation(
                asset="BTC", asset_type="Cryptocurrency", description="Bitcoin", allocation_percentage="45%"
            ),
            PortfolioAllocation(
                asset="ETH", asset_type="Cryptocurrency", description="Ethereum", allocation_percentage="20%"
            ),
            PortfolioAllocation(
                asset="FDUSD", asset_type="Stablecoin", description="First Digital USD", allocation_percentage="10%"
            ),
            PortfolioAllocation(
                asset="USDC", asset_type="Stablecoin", description="USD Coin", allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="XRP", asset_type="Cryptocurrency", description="XRP", allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="SOL", asset_type="Cryptocurrency", description="Solana", allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="DOGE", asset_type="Cryptocurrency", description="Dogecoin", allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="ADA", asset_type="Cryptocurrency", description="Cardano", allocation_percentage="5%"
            )
        ],
        next_step="crypto_trends_node",
    )

    # Use the tool to calculate digital crypto asset trends
    trends = calculate_crypto_trends_tool(state)

    # Print the updated state
    print("\nUpdated Crypto State:")
    print(state)