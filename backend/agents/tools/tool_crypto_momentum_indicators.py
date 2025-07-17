from db.mdb import MongoDBConnector
from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState, CryptoMomentumIndicator, MomentumIndicator
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
CRYPTO_RSI_PERIOD = int(os.getenv("CRYPTO_RSI_PERIOD", 14))    # 14-day RSI
CRYPTO_VOLUME_PERIOD = int(os.getenv("CRYPTO_VOLUME_PERIOD", 21))  # 21-day volume average
CRYPTO_VWAP_PERIOD = int(os.getenv("CRYPTO_VWAP_PERIOD", 14))    # 14-day VWAP

class CryptoMomentumTool(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None):
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("CRYPTO_TIMESERIES_COLLECTION", "binanceCryptoData")
        self.collection = self.get_collection(self.collection_name)
        logger.info("CryptoMomentumTool initialized")

    def calculate_rsi(self, symbol: str, period: int = CRYPTO_RSI_PERIOD) -> tuple:
        """
        Calculate RSI using Wilder's smoothing method (industry standard).
        Returns tuple of (rsi_value, price_date)
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

    def calculate_volume_analysis(self, symbol: str, period: int = CRYPTO_VOLUME_PERIOD) -> tuple:
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

    def calculate_vwap(self, symbol: str, period: int = CRYPTO_VWAP_PERIOD) -> tuple:
        """
        Calculate VWAP (Volume Weighted Average Price) for a crypto symbol.
        VWAP = Calculate VWAP using typical price (HLC/3) and volume
        Returns tuple of (vwap_value, current_price, price_date)
        """
        pipeline = [
            {"$match": {"symbol": symbol}},
            {"$sort": {"timestamp": -1}},
            {"$limit": period}
        ]
        
        data = list(self.collection.aggregate(pipeline))
        if len(data) < period:
            return None, None, None
            
        # Calculate VWAP using typical price (HLC/3) and volume
        total_pv = 0  # Price × Volume
        total_volume = 0
        
        for record in data:
            # Use typical price (High + Low + Close) / 3
            typical_price = (record["high"] + record["low"] + record["close"]) / 3
            volume = record["volume"]
            
            total_pv += typical_price * volume
            total_volume += volume
        
        if total_volume == 0:
            return None, None, None
            
        vwap = total_pv / total_volume
        current_price = data[0]["close"]  # Most recent closing price
        price_date = data[0]["timestamp"].strftime("%Y-%m-%d")
        
        return round(vwap, 6), current_price, price_date

    def analyze_momentum_indicator(self, indicator_type: str, value: float, asset_type: str, symbol: str = "", **kwargs) -> str:
        """
        Analysis focusing on RSI, Volume, and VWAP with enhanced insights.
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
                
        elif indicator_type == "Volume":
            volume_ratio = kwargs.get("volume_ratio", 0)
            # Fix volume ratio display precision - avoid showing 0.0x
            vol_ratio_display = max(0.1, volume_ratio)
            
            if volume_ratio > 2:
                return f"Exceptionally high volume ({volume_ratio:.1f}x average). Strong conviction in price movement."
            elif volume_ratio > 1.5:
                return f"Above average volume ({volume_ratio:.1f}x average). Increased market interest."
            elif volume_ratio < 0.7:
                return f"Below average volume ({vol_ratio_display:.1f}x average). Low market activity."
            else:
                return f"Normal volume levels ({volume_ratio:.1f}x average). Standard trading activity."
                
        elif indicator_type == "VWAP":
            current_price = kwargs.get("current_price", 0)
            vwap_value = value
            
            # Special handling for stablecoins
            if asset_type == "Stablecoin":
                deviation_from_vwap = abs((current_price - vwap_value) / vwap_value) * 100
                if deviation_from_vwap > 0.5:
                    return f"Price {current_price:.4f} vs VWAP {vwap_value:.4f}. Stablecoin showing {deviation_from_vwap:.2f}% deviation from volume-weighted average."
                else:
                    return f"Price {current_price:.4f} vs VWAP {vwap_value:.4f}. Stablecoin trading close to volume-weighted average, maintaining stability."
            
            # Cryptocurrency VWAP analysis
            price_vs_vwap = ((current_price - vwap_value) / vwap_value) * 100
            
            if price_vs_vwap > 5:
                return f"Price {current_price:.2f} is {price_vs_vwap:.1f}% above VWAP {vwap_value:.2f}. Strong bullish sentiment with institutional buying pressure."
            elif price_vs_vwap > 2:
                return f"Price {current_price:.2f} is {price_vs_vwap:.1f}% above VWAP {vwap_value:.2f}. Moderate bullish momentum with volume support."
            elif price_vs_vwap < -5:
                return f"Price {current_price:.2f} is {abs(price_vs_vwap):.1f}% below VWAP {vwap_value:.2f}. Strong bearish pressure, potential value opportunity."
            elif price_vs_vwap < -2:
                return f"Price {current_price:.2f} is {abs(price_vs_vwap):.1f}% below VWAP {vwap_value:.2f}. Moderate bearish sentiment, watch for reversal."
            else:
                return f"Price {current_price:.2f} trading near VWAP {vwap_value:.2f} ({price_vs_vwap:+.1f}%). Balanced market with neutral sentiment."
                
        return "Insufficient data for analysis."

    def calculate_crypto_momentum_indicators(self, state: CryptoAnalysisAgentState) -> dict:
        """
        Calculate momentum indicators focusing on RSI, Volume, and VWAP analysis.
        Each asset gets one CryptoMomentumIndicator with nested MomentumIndicator objects.
        """
        message = "[Tool] Calculate crypto momentum indicators."
        logger.info(message)

        crypto_momentum_indicators = []
        
        for allocation in state.portfolio_allocation:
            symbol = allocation.asset
            asset_type = allocation.asset_type
            momentum_indicators = []

            # Calculate RSI
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

            # Volume analysis
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
                    fluctuation_answer=f"{symbol} volume is {current_vol_formatted} vs {CRYPTO_VOLUME_PERIOD}-day avg of {avg_vol_formatted} on {vol_date}.",
                    diagnosis=vol_diagnosis
                )
                momentum_indicators.append(vol_momentum_indicator)

            # VWAP analysis
            vwap_value, current_price, vwap_date = self.calculate_vwap(symbol)
            if vwap_value is not None:
                vwap_diagnosis = self.analyze_momentum_indicator("VWAP", vwap_value, asset_type, symbol, current_price=current_price)
                
                # Format VWAP and price appropriately
                if vwap_value >= 1:
                    vwap_formatted = f"${vwap_value:,.2f}"
                    price_formatted = f"${current_price:,.2f}"
                else:
                    vwap_formatted = f"${vwap_value:.6f}"
                    price_formatted = f"${current_price:.6f}"
                
                vwap_momentum_indicator = MomentumIndicator(
                    indicator_name="VWAP",
                    fluctuation_answer=f"{symbol} VWAP ({CRYPTO_VWAP_PERIOD}-day) is {vwap_formatted} vs current price {price_formatted} on {vwap_date}.",
                    diagnosis=vwap_diagnosis
                )
                momentum_indicators.append(vwap_momentum_indicator)

            # Create CryptoMomentumIndicator with RSI + Volume + VWAP
            if momentum_indicators:
                crypto_momentum_indicator = CryptoMomentumIndicator(
                    asset=symbol,
                    momentum_indicators=momentum_indicators
                )
                crypto_momentum_indicators.append(crypto_momentum_indicator)

        # Update state
        state.report.crypto_momentum_indicators = crypto_momentum_indicators
        state.updates.append(message)
        state.next_step = "crypto_portfolio_overall_diagnosis_node"

        return {"crypto_momentum_indicators": crypto_momentum_indicators, "updates": state.updates, "next_step": state.next_step}


# Initialize the CryptoMomentumTool
crypto_momentum_indicators_tool = CryptoMomentumTool()

# Define tools
def calculate_crypto_momentum_indicators_tool(state: CryptoAnalysisAgentState) -> dict:
    """
    Calculate crypto momentum indicators (RSI, Volume, and VWAP analysis) for portfolio assets.
    """
    return crypto_momentum_indicators_tool.calculate_crypto_momentum_indicators(state=state)

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
            )
        ],
        next_step="crypto_momentum_indicators_node",
    )

    # Use the tool to calculate crypto momentum indicators
    momentum = calculate_crypto_momentum_indicators_tool(state)

    # Print the updated state
    print("\nUpdated Crypto State:")
    print(state)