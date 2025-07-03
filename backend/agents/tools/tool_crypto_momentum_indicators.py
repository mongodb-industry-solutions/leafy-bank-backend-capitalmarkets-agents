from db.mdb import MongoDBConnector
from states.agent_crypto_analysis_state import CryptoAnalysisAgentState, CryptoMomentumIndicator, MomentumIndicator
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

# Constants for crypto momentum analysis
RSI_PERIOD = int(os.getenv("RSI_PERIOD", 14))    # 14-day RSI
ATR_PERIOD = int(os.getenv("ATR_PERIOD", 14))    # 14-day ATR
VOLUME_PERIOD = int(os.getenv("VOLUME_PERIOD", 20))  # 20-day volume average

class CryptoMomentumTool(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("CRYPTO_TIMESERIES_COLLECTION", "binanceCryptoData")
        self.collection = self.get_collection(self.collection_name)
        logger.info("CryptoMomentumTool initialized")

    def calculate_rsi(self, symbol: str, period: int = RSI_PERIOD) -> tuple:
        """
        Calculate RSI using Wilder's smoothing method (industry standard).
        """
        pipeline = [
            {"$match": {"symbol": symbol}},
            {"$sort": {"timestamp": -1}},
            {"$limit": period * 2},  # Need more data for proper smoothing
            {"$sort": {"timestamp": 1}}
        ]
        
        data = list(self.collection.aggregate(pipeline))
        if len(data) < period + 1:
            return None, None
            
        # Calculate price changes
        price_changes = []
        for i in range(1, len(data)):
            change = data[i]["close"] - data[i-1]["close"]
            price_changes.append(change)
        
        if len(price_changes) < period:
            return None, None
            
        # Separate gains and losses
        gains = [max(change, 0) for change in price_changes]
        losses = [max(-change, 0) for change in price_changes]
        
        # Use Wilder's smoothing (industry standard)
        # First period: simple average
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Subsequent periods: exponential smoothing
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        price_date = data[-1]["timestamp"].strftime("%Y-%m-%d")
        return round(rsi, 2), price_date

    def calculate_atr(self, symbol: str, period: int = ATR_PERIOD) -> tuple:
        """
        Calculate ATR (Average True Range) for a crypto symbol.
        Returns tuple of (atr_value, atr_percentage, price_date)
        """
        pipeline = [
            {"$match": {"symbol": symbol}},
            {"$sort": {"timestamp": -1}},
            {"$limit": period + 1},
            {"$sort": {"timestamp": 1}}
        ]
        
        data = list(self.collection.aggregate(pipeline))
        if len(data) < period + 1:
            return None, None, None
            
        true_ranges = []
        for i in range(1, len(data)):
            current = data[i]
            previous = data[i-1]
            
            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr1 = current["high"] - current["low"]
            tr2 = abs(current["high"] - previous["close"])
            tr3 = abs(current["low"] - previous["close"])
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return None, None, None
            
        # Calculate ATR (simple moving average of true ranges)
        atr = sum(true_ranges[-period:]) / period
        
        # Calculate ATR as percentage of current price
        current_price = data[-1]["close"]
        atr_percentage = (atr / current_price) * 100
        
        # Get the date
        price_date = data[-1]["timestamp"].strftime("%Y-%m-%d")
        
        return round(atr, 6), round(atr_percentage, 2), price_date

    def calculate_volume_analysis(self, symbol: str, period: int = VOLUME_PERIOD) -> tuple:
        """
        Calculate volume analysis for a crypto symbol.
        Returns tuple of (current_volume, avg_volume, volume_ratio, price_date)
        """
        pipeline = [
            {"$match": {"symbol": symbol}},
            {"$sort": {"timestamp": -1}},
            {"$limit": period}
        ]
        
        data = list(self.collection.aggregate(pipeline))
        if len(data) < period:
            return None, None, None, None
            
        # Current volume (latest day)
        current_volume = data[0]["volume"]
        
        # Average volume over the period
        volumes = [d["volume"] for d in data]
        avg_volume = sum(volumes) / len(volumes)
        
        # Volume ratio (current vs average)
        volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0
        
        # Get the date
        price_date = data[0]["timestamp"].strftime("%Y-%m-%d")
        
        return current_volume, avg_volume, round(volume_ratio, 2), price_date

    def analyze_momentum_indicator(self, indicator_type: str, value: float, asset_type: str, symbol: str = "", **kwargs) -> str:
        """
        Enhanced analysis with asset-type specific logic.
        """
        if indicator_type == "RSI":
            # Special handling for stablecoins
            if asset_type == "Stablecoin":
                if 45 <= value <= 55:
                    return f"RSI at {value} normal for stablecoin. Price stability maintained around peg."
                elif value > 55:
                    return f"RSI at {value} elevated for stablecoin. Slight upward pressure from peg."
                else:
                    return f"RSI at {value} low for stablecoin. Slight downward pressure from peg."
            
            # Cryptocurrency RSI analysis
            if value >= 70:
                return f"RSI at {value} indicates overbought conditions. Consider taking profits or reducing position size."
            elif value <= 30:
                return f"RSI at {value} indicates oversold conditions. Strong buying opportunity for {symbol}."
            elif value >= 50:
                return f"RSI at {value} shows bullish momentum. Upward price pressure likely to continue."
            else:
                return f"RSI at {value} shows bearish momentum. Downward pressure may persist."
                
        elif indicator_type == "ATR":
            atr_percentage = kwargs.get("atr_percentage", 0)
            
            # Asset-specific ATR thresholds
            if asset_type == "Stablecoin":
                if atr_percentage > 0.1:
                    return f"High volatility for stablecoin (ATR {atr_percentage}%). Monitor peg stability."
                else:
                    return f"Normal stablecoin volatility (ATR {atr_percentage}%). Peg maintained."
            
            # Cryptocurrency ATR analysis
            if atr_percentage > 5:
                return f"High volatility (ATR {atr_percentage}% of price). Increase stop-losses and reduce position sizes."
            elif atr_percentage > 2:
                return f"Moderate volatility (ATR {atr_percentage}% of price). Normal trading conditions for {symbol}."
            else:
                return f"Low volatility (ATR {atr_percentage}% of price). Potential consolidation or breakout setup."
                
        elif indicator_type == "Volume":
            volume_ratio = kwargs.get("volume_ratio", 0)
            if volume_ratio > 2:
                return f"Exceptionally high volume ({volume_ratio:.1f}x average). Strong conviction in price movement."
            elif volume_ratio > 1.5:
                return f"Above average volume ({volume_ratio:.1f}x average). Increased market interest."
            elif volume_ratio < 0.7:
                return f"Below average volume ({volume_ratio:.1f}x average). Low market activity."
            else:
                return f"Normal volume levels ({volume_ratio:.1f}x average). Standard trading activity."
                
        return "Insufficient data for analysis."

    def calculate_crypto_momentum_indicators(self, state: CryptoAnalysisAgentState) -> dict:
        """
        Calculate momentum indicators with enhanced validation and asset-specific logic.
        """
        message = "[Tool] Calculate crypto momentum indicators."
        logger.info(message)

        crypto_momentum_indicators = []
        
        for allocation in state.portfolio_allocation:
            symbol = allocation.asset
            asset_type = allocation.asset_type
            momentum_indicators = []

            # Calculate RSI with validation
            rsi_value, rsi_date = self.calculate_rsi(symbol)
            if rsi_value is not None:
                # Validate RSI for stablecoins
                if asset_type == "Stablecoin" and (rsi_value < 40 or rsi_value > 60):
                    logger.warning(f"Unusual RSI {rsi_value} for stablecoin {symbol}. Data may be incomplete.")
                
                rsi_diagnosis = self.analyze_momentum_indicator("RSI", rsi_value, asset_type, symbol)
                rsi_momentum_indicator = MomentumIndicator(
                    indicator_name="RSI",
                    fluctuation_answer=f"{symbol} RSI (14-day) is {rsi_value} on {rsi_date}.",
                    diagnosis=rsi_diagnosis
                )
                momentum_indicators.append(rsi_momentum_indicator)

            # Calculate ATR with enhanced validation
            atr_value, atr_percentage, atr_date = self.calculate_atr(symbol)
            if atr_value is not None and atr_percentage is not None:
                # Validate ATR reasonableness
                if asset_type == "Cryptocurrency" and atr_percentage < 0.5:
                    logger.warning(f"Unusually low ATR {atr_percentage}% for {symbol}. Verify calculation.")
                
                atr_diagnosis = self.analyze_momentum_indicator("ATR", atr_value, asset_type, symbol, atr_percentage=atr_percentage)
                
                # Enhanced formatting
                atr_formatted = f"${atr_value:,.6f}" if atr_value < 1 else f"${atr_value:,.2f}"
                
                atr_momentum_indicator = MomentumIndicator(
                    indicator_name="ATR",
                    fluctuation_answer=f"{symbol} ATR (14-day) is {atr_formatted} ({atr_percentage}% of price) on {atr_date}.",
                    diagnosis=atr_diagnosis
                )
                momentum_indicators.append(atr_momentum_indicator)

            # Volume analysis with context
            current_vol, avg_vol, vol_ratio, vol_date = self.calculate_volume_analysis(symbol)
            if current_vol is not None:
                vol_diagnosis = self.analyze_momentum_indicator("Volume", current_vol, asset_type, symbol, volume_ratio=vol_ratio)
                
                # Smart volume formatting
                if current_vol > 1000:
                    current_vol_formatted = f"{current_vol:,.0f}"
                    avg_vol_formatted = f"{avg_vol:,.0f}"
                else:
                    current_vol_formatted = f"{current_vol:,.2f}"
                    avg_vol_formatted = f"{avg_vol:,.2f}"
                
                vol_momentum_indicator = MomentumIndicator(
                    indicator_name="Volume",
                    fluctuation_answer=f"{symbol} volume is {current_vol_formatted} vs {VOLUME_PERIOD}-day avg of {avg_vol_formatted} on {vol_date}.",
                    diagnosis=vol_diagnosis
                )
                momentum_indicators.append(vol_momentum_indicator)

            # Create CryptoMomentumIndicator only if we have valid indicators
            if momentum_indicators:
                crypto_momentum_indicator = CryptoMomentumIndicator(
                    asset=symbol,
                    momentum_indicators=momentum_indicators
                )
                crypto_momentum_indicators.append(crypto_momentum_indicator)

        # Update state
        state.report.crypto_momentum_indicators = crypto_momentum_indicators
        state.updates.append(message)
        state.next_step = "portfolio_overall_diagnosis_node"

        return {"crypto_momentum_indicators": crypto_momentum_indicators, "updates": state.updates, "next_step": state.next_step}


# Initialize the CryptoMomentumTool
crypto_momentum_indicators_tool = CryptoMomentumTool()

# Define tools
def calculate_crypto_momentum_indicators_tool(state: CryptoAnalysisAgentState) -> dict:
    """
    Calculate crypto momentum indicators (RSI, ATR, Volume analysis) for portfolio assets.
    """
    return crypto_momentum_indicators_tool.calculate_crypto_momentum_indicators(state=state)

if __name__ == "__main__":
    from states.agent_crypto_analysis_state import CryptoAnalysisAgentState, PortfolioAllocation

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
            )
        ],
        next_step="crypto_momentum_indicators_node",
    )

    # Use the tool to calculate crypto momentum indicators
    momentum = calculate_crypto_momentum_indicators_tool(state)

    # Print the updated state
    print("\nUpdated Crypto State:")
    print(state)