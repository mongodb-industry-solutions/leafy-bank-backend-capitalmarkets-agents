import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CryptoAssetSuggestions(MongoDBConnector):
    """Service class for generating crypto asset suggestions."""
    def __init__(self, uri=None, database_name: str = None, appname: str = None):
        """
        Initialize the CryptoAssetSuggestions service.
        
        Args:
            uri (str, optional): MongoDB connection URI
            database_name (str, optional): Target database name
            appname (str, optional): Application name for MongoDB connection
        """
        super().__init__(uri, database_name, appname)
        self.collections = {
            "crypto_analysis": os.getenv("REPORTS_COLLECTION_CRYPTO_ANALYSIS"),
            "portfolio_allocation": os.getenv("CRYPTO_PORTFOLIO_COLLECTION")
        }
        logger.info("CryptoAssetSuggestions initialized")

    def fetch_crypto_suggestions_trend_based(self):
        """
        Generate crypto asset allocation suggestions based on moving average trend analysis.
        
        Returns:
            list: List of dictionaries containing crypto suggestions with detailed MA values and trend analysis
        """
        try:
            # Fetch latest crypto analysis report
            crypto_analysis_collection = self.collections["crypto_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ]
            result = list(self.db[crypto_analysis_collection].aggregate(pipeline))
            logger.info(f"Fetched {len(result)} crypto analysis report(s)")

            if not result:
                logger.error("No crypto analysis report found")
                return []

            crypto_analysis = result[0].get("report", {})
            
            if not crypto_analysis.get("crypto_trends"):
                logger.warning("No crypto trends found in the crypto analysis report")
                return []

            # Extract portfolio allocation from the report
            portfolio_allocation = {}
            if "portfolio_allocation" in result[0]:
                for asset_data in result[0]["portfolio_allocation"]:
                    symbol = asset_data["asset"]
                    portfolio_allocation[symbol] = {
                        "allocation_percentage": asset_data.get("allocation_percentage"),
                        "description": asset_data.get("description"),
                        "asset_type": asset_data.get("asset_type")
                    }

            # Generate suggestions based on trend analysis
            suggestions = []
            
            for trend_data in crypto_analysis.get("crypto_trends", []):
                asset_symbol = trend_data.get("asset")
                diagnosis = trend_data.get("diagnosis", "")
                fluctuation_answer = trend_data.get("fluctuation_answer", "")
                
                # Extract MA values from fluctuation_answer
                ma_values = self._extract_ma_values(fluctuation_answer)
                
                # Get asset details from portfolio allocation
                asset_details = portfolio_allocation.get(asset_symbol, {})
                asset_type = asset_details.get("asset_type", "Cryptocurrency")
                description = asset_details.get("description", asset_symbol)
                
                # Create detailed trend analysis
                crypto_indicators = []
                
                # MA9 Analysis
                if ma_values.get("close") and ma_values.get("ma9"):
                    ma9_indicator = self._create_ma_indicator("MA9", ma_values["close"], ma_values["ma9"], asset_symbol)
                    crypto_indicators.append(ma9_indicator)
                
                # MA21 Analysis  
                if ma_values.get("close") and ma_values.get("ma21"):
                    ma21_indicator = self._create_ma_indicator("MA21", ma_values["close"], ma_values["ma21"], asset_symbol)
                    crypto_indicators.append(ma21_indicator)
                
                # MA50 Analysis
                if ma_values.get("close") and ma_values.get("ma50"):
                    ma50_indicator = self._create_ma_indicator("MA50", ma_values["close"], ma_values["ma50"], asset_symbol)
                    crypto_indicators.append(ma50_indicator)
                
                # Overall Trend Summary
                overall_trend = {
                    "indicator": "Overall Trend Analysis",
                    "action": "MONITOR",
                    "explanation": diagnosis,
                    "price_data": ma_values,
                    "note": f"Based on moving average positioning: {diagnosis}"
                }
                crypto_indicators.append(overall_trend)
                
                suggestion = {
                    "asset": asset_symbol,
                    "asset_type": asset_type,
                    "description": description,
                    "crypto_indicators": crypto_indicators
                }
                
                suggestions.append(suggestion)
            
            logger.info(f"Generated {len(suggestions)} crypto suggestions based on trend analysis")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating crypto trend-based suggestions: {e}", exc_info=True)
            return []

    def fetch_crypto_suggestions_momentum_based(self):
        """
        Generate crypto asset allocation suggestions based on momentum indicators with detailed values.
        
        Returns:
            list: List of dictionaries containing crypto suggestions with detailed momentum indicator values
        """
        try:
            # Fetch latest crypto analysis report
            crypto_analysis_collection = self.collections["crypto_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ]
            result = list(self.db[crypto_analysis_collection].aggregate(pipeline))
            logger.info(f"Fetched {len(result)} crypto analysis report(s)")

            if not result:
                logger.error("No crypto analysis report found")
                return []

            crypto_analysis = result[0].get("report", {})
            
            if not crypto_analysis.get("crypto_momentum_indicators"):
                logger.warning("No crypto momentum indicators found in the crypto analysis report")
                return []

            # Extract portfolio allocation from the report
            portfolio_allocation = {}
            if "portfolio_allocation" in result[0]:
                for asset_data in result[0]["portfolio_allocation"]:
                    symbol = asset_data["asset"]
                    portfolio_allocation[symbol] = {
                        "allocation_percentage": asset_data.get("allocation_percentage"),
                        "description": asset_data.get("description"),
                        "asset_type": asset_data.get("asset_type")
                    }

            # Generate suggestions based on momentum analysis
            suggestions = []
            
            for momentum_data in crypto_analysis.get("crypto_momentum_indicators", []):
                asset_symbol = momentum_data.get("asset")
                momentum_indicators_data = momentum_data.get("momentum_indicators", [])
                
                # Get asset details from portfolio allocation
                asset_details = portfolio_allocation.get(asset_symbol, {})
                asset_type = asset_details.get("asset_type", "Cryptocurrency")
                description = asset_details.get("description", asset_symbol)
                
                # Create detailed momentum indicators
                crypto_indicators = []
                
                for indicator_data in momentum_indicators_data:
                    indicator_name = indicator_data.get("indicator_name")
                    fluctuation_answer = indicator_data.get("fluctuation_answer", "")
                    diagnosis = indicator_data.get("diagnosis", "")
                    
                    if indicator_name == "RSI":
                        rsi_indicator = self._create_rsi_indicator(fluctuation_answer, diagnosis, asset_symbol)
                        crypto_indicators.append(rsi_indicator)
                    elif indicator_name == "Volume":
                        volume_indicator = self._create_volume_indicator(fluctuation_answer, diagnosis, asset_symbol)
                        crypto_indicators.append(volume_indicator)
                    elif indicator_name == "VWAP":
                        vwap_indicator = self._create_vwap_indicator(fluctuation_answer, diagnosis, asset_symbol)
                        crypto_indicators.append(vwap_indicator)
                
                suggestion = {
                    "asset": asset_symbol,
                    "asset_type": asset_type,
                    "description": description,
                    "crypto_indicators": crypto_indicators
                }
                
                suggestions.append(suggestion)
            
            logger.info(f"Generated {len(suggestions)} crypto suggestions based on momentum analysis")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating crypto momentum-based suggestions: {e}", exc_info=True)
            return []

    def fetch_crypto_suggestions_comprehensive(self):
        """
        Generate comprehensive crypto asset allocation suggestions with all indicator details.
        
        Returns:
            list: List of dictionaries containing comprehensive crypto analysis with all indicator values
        """
        try:
            # Fetch latest crypto analysis report
            crypto_analysis_collection = self.collections["crypto_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ]
            result = list(self.db[crypto_analysis_collection].aggregate(pipeline))
            logger.info(f"Fetched {len(result)} crypto analysis report(s)")

            if not result:
                logger.error("No crypto analysis report found")
                return []

            crypto_analysis = result[0].get("report", {})
            overall_diagnosis = result[0].get("report", {}).get("overall_diagnosis", "")

            # Extract portfolio allocation from the report
            portfolio_allocation = {}
            if "portfolio_allocation" in result[0]:
                for asset_data in result[0]["portfolio_allocation"]:
                    symbol = asset_data["asset"]
                    portfolio_allocation[symbol] = {
                        "allocation_percentage": asset_data.get("allocation_percentage"),
                        "description": asset_data.get("description"),
                        "asset_type": asset_data.get("asset_type")
                    }

            # Create trend analysis lookup
            trend_analysis = {}
            for trend_data in crypto_analysis.get("crypto_trends", []):
                asset_symbol = trend_data.get("asset")
                trend_analysis[asset_symbol] = trend_data

            # Create momentum analysis lookup
            momentum_analysis = {}
            for momentum_data in crypto_analysis.get("crypto_momentum_indicators", []):
                asset_symbol = momentum_data.get("asset")
                momentum_analysis[asset_symbol] = momentum_data

            # Generate comprehensive suggestions
            suggestions = []
            
            for asset_symbol in portfolio_allocation.keys():
                trend_data = trend_analysis.get(asset_symbol, {})
                momentum_data = momentum_analysis.get(asset_symbol, {})
                asset_details = portfolio_allocation[asset_symbol]
                
                # Combine all indicators
                crypto_indicators = []
                
                # Add trend indicators
                if trend_data:
                    fluctuation_answer = trend_data.get("fluctuation_answer", "")
                    ma_values = self._extract_ma_values(fluctuation_answer)
                    diagnosis = trend_data.get("diagnosis", "")
                    
                    # Add moving average analyses
                    if ma_values.get("close") and ma_values.get("ma9"):
                        ma9_indicator = self._create_ma_indicator("MA9", ma_values["close"], ma_values["ma9"], asset_symbol)
                        crypto_indicators.append(ma9_indicator)
                    
                    if ma_values.get("close") and ma_values.get("ma21"):
                        ma21_indicator = self._create_ma_indicator("MA21", ma_values["close"], ma_values["ma21"], asset_symbol)
                        crypto_indicators.append(ma21_indicator)
                    
                    if ma_values.get("close") and ma_values.get("ma50"):
                        ma50_indicator = self._create_ma_indicator("MA50", ma_values["close"], ma_values["ma50"], asset_symbol)
                        crypto_indicators.append(ma50_indicator)
                
                # Add momentum indicators
                if momentum_data:
                    momentum_indicators_data = momentum_data.get("momentum_indicators", [])
                    
                    for indicator_data in momentum_indicators_data:
                        indicator_name = indicator_data.get("indicator_name")
                        fluctuation_answer = indicator_data.get("fluctuation_answer", "")
                        diagnosis = indicator_data.get("diagnosis", "")
                        
                        if indicator_name == "RSI":
                            rsi_indicator = self._create_rsi_indicator(fluctuation_answer, diagnosis, asset_symbol)
                            crypto_indicators.append(rsi_indicator)
                        elif indicator_name == "Volume":
                            volume_indicator = self._create_volume_indicator(fluctuation_answer, diagnosis, asset_symbol)
                            crypto_indicators.append(volume_indicator)
                        elif indicator_name == "VWAP":
                            vwap_indicator = self._create_vwap_indicator(fluctuation_answer, diagnosis, asset_symbol)
                            crypto_indicators.append(vwap_indicator)
                
                suggestion = {
                    "asset": asset_symbol,
                    "asset_type": asset_details.get("asset_type", "Cryptocurrency"),
                    "description": asset_details.get("description", asset_symbol),
                    "crypto_indicators": crypto_indicators
                }
                
                suggestions.append(suggestion)
            
            logger.info(f"Generated {len(suggestions)} comprehensive crypto suggestions")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating comprehensive crypto suggestions: {e}", exc_info=True)
            return []

    @staticmethod
    def _extract_ma_values(fluctuation_answer):
        """
        Extract moving average values from fluctuation_answer string.
        Based on format: "ETH close price is $3,371.35, MA9 is $3,368.93, MA21 is $3,367.09, and MA50 is $3,361.92."
        """
        ma_values = {}
        
        # Extract close price - handles both $ and non-$ formats, with or without commas
        close_patterns = [
            r"close price is \$?([\d,]+\.?\d*)",
            r"(\w+) close price is \$?([\d,]+\.?\d*)"
        ]
        
        for pattern in close_patterns:
            close_match = re.search(pattern, fluctuation_answer)
            if close_match:
                # Get the last group which should be the price
                price_str = close_match.groups()[-1].replace(",", "")
                ma_values["close"] = float(price_str)
                break
        
        # Extract MA9 - handles various formats
        ma9_patterns = [
            r"MA9 is \$?([\d,]+\.?\d*)",
            r"MA10 is \$?([\d,]+\.?\d*)",  # fallback for MA10
            r"short[_ ]?ma.*?\$?([\d,]+\.?\d*)"
        ]
        
        for pattern in ma9_patterns:
            ma9_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if ma9_match:
                price_str = ma9_match.group(1).replace(",", "")
                ma_values["ma9"] = float(price_str)
                break
        
        # Extract MA21 - handles various formats
        ma21_patterns = [
            r"MA21 is \$?([\d,]+\.?\d*)",
            r"MA20 is \$?([\d,]+\.?\d*)",  # fallback for MA20
            r"mid[_ ]?ma.*?\$?([\d,]+\.?\d*)"
        ]
        
        for pattern in ma21_patterns:
            ma21_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if ma21_match:
                price_str = ma21_match.group(1).replace(",", "")
                ma_values["ma21"] = float(price_str)
                break
        
        # Extract MA50 - handles various formats
        ma50_patterns = [
            r"MA50 is \$?([\d,]+\.?\d*)",
            r"long[_ ]?ma.*?\$?([\d,]+\.?\d*)"
        ]
        
        for pattern in ma50_patterns:
            ma50_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if ma50_match:
                price_str = ma50_match.group(1).replace(",", "")
                ma_values["ma50"] = float(price_str)
                break
        
        logger.debug(f"Extracted MA values: {ma_values} from: {fluctuation_answer}")
        return ma_values

    @staticmethod
    def _create_ma_indicator(ma_type, close_price, ma_value, asset_symbol):
        """Create moving average indicator with detailed analysis."""
        percentage_diff = ((close_price - ma_value) / ma_value) * 100
        
        if percentage_diff > 0:
            trend_direction = "above"
            suggestion = "Price above moving average suggests upward momentum"
        elif percentage_diff < 0:
            trend_direction = "below"
            suggestion = "Price below moving average suggests downward momentum"
        else:
            trend_direction = "at"
            suggestion = "Price at moving average suggests consolidation"
        
        # Format prices based on value
        if close_price >= 1:
            close_formatted = f"${close_price:,.2f}"
            ma_formatted = f"${ma_value:,.2f}"
        else:
            close_formatted = f"${close_price:.6f}"
            ma_formatted = f"${ma_value:.6f}"
        
        return {
            "indicator": f"{ma_type} Moving Average Analysis",
            "action": "MONITOR",
            "explanation": f"{asset_symbol} close price is {close_formatted}, and its {ma_type} is {ma_formatted}.",
            "trend_direction": trend_direction,
            "percentage_difference": f"{percentage_diff:+.2f}%",
            "suggestion": suggestion,
            "note": f"Price vs. {ma_type}: {suggestion}"
        }

    @staticmethod
    def _create_rsi_indicator(fluctuation_answer, diagnosis, asset_symbol):
        """
        Create RSI indicator with detailed analysis.
        Based on format: "ETH RSI (14-day) is 60.27 on 2025-07-16."
        """
        # Extract RSI value - handles various formats
        rsi_patterns = [
            r"RSI.*?is ([\d.]+)",
            r"RSI.*?([\d.]+)",
            r"(\d+\.?\d*)\s*RSI"
        ]
        
        rsi_value = None
        for pattern in rsi_patterns:
            rsi_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if rsi_match:
                rsi_value = float(rsi_match.group(1))
                break
        
        # Determine RSI interpretation
        if rsi_value:
            if rsi_value > 70:
                rsi_interpretation = "Overbought condition - potential sell signal"
            elif rsi_value < 30:
                rsi_interpretation = "Oversold condition - potential buy signal"
            elif rsi_value > 50:
                rsi_interpretation = "Bullish momentum - above neutral"
            else:
                rsi_interpretation = "Bearish momentum - below neutral"
        else:
            rsi_interpretation = "RSI value not available"
        
        return {
            "indicator": "RSI Analysis",
            "action": "MONITOR",
            "explanation": fluctuation_answer,
            "rsi_value": rsi_value,
            "diagnosis": diagnosis,
            "interpretation": rsi_interpretation,
            "suggestion": diagnosis,
            "note": f"RSI Trend: {fluctuation_answer}"
        }

    @staticmethod
    def _create_volume_indicator(fluctuation_answer, diagnosis, asset_symbol):
        """
        Create Volume indicator with detailed analysis.
        Based on format: "ETH volume is 344.96 vs 21-day avg of 296.58 on 2025-07-16."
        """
        # Extract volume values - handles various formats
        volume_patterns = [
            r"volume is ([\d,]+(?:\.\d+)?)",
            r"volume.*?([\d,]+(?:\.\d+)?)"
        ]
        
        avg_patterns = [
            r"avg of ([\d,]+(?:\.\d+)?)",
            r"average.*?([\d,]+(?:\.\d+)?)",
            r"vs.*?([\d,]+(?:\.\d+)?).*?avg"
        ]
        
        current_volume = None
        avg_volume = None
        
        for pattern in volume_patterns:
            volume_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if volume_match:
                current_volume = float(volume_match.group(1).replace(",", ""))
                break
        
        for pattern in avg_patterns:
            avg_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if avg_match:
                avg_volume = float(avg_match.group(1).replace(",", ""))
                break
        
        volume_ratio = None
        if current_volume and avg_volume and avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            if volume_ratio > 1.5:
                volume_interpretation = "High trading activity - increased market interest"
            elif volume_ratio < 0.7:
                volume_interpretation = "Low trading activity - reduced market interest"
            else:
                volume_interpretation = "Normal trading activity"
        else:
            volume_interpretation = "Volume data not available"
        
        return {
            "indicator": "Volume Analysis",
            "action": "MONITOR",
            "explanation": fluctuation_answer,
            "current_volume": current_volume,
            "avg_volume": avg_volume,
            "volume_ratio": f"{volume_ratio:.1f}x" if volume_ratio else None,
            "diagnosis": diagnosis,
            "interpretation": volume_interpretation,
            "suggestion": diagnosis,
            "note": f"Volume Trend: {fluctuation_answer}"
        }

    @staticmethod
    def _create_vwap_indicator(fluctuation_answer, diagnosis, asset_symbol):
        """
        Create VWAP indicator with detailed analysis.
        Based on format: "ETH VWAP (14-day) is $3,368.43 vs current price $3,371.35 on 2025-07-16."
        """
        # Extract VWAP and current price - handles various formats
        vwap_patterns = [
            r"VWAP.*?is \$?([\d,]+\.?\d*)",
            r"VWAP.*?\$?([\d,]+\.?\d*)"
        ]
        
        price_patterns = [
            r"current price \$?([\d,]+\.?\d*)",
            r"vs.*?\$?([\d,]+\.?\d*)",
            r"price \$?([\d,]+\.?\d*)"
        ]
        
        vwap_value = None
        current_price = None
        
        for pattern in vwap_patterns:
            vwap_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if vwap_match:
                vwap_value = float(vwap_match.group(1).replace(",", ""))
                break
        
        for pattern in price_patterns:
            price_match = re.search(pattern, fluctuation_answer, re.IGNORECASE)
            if price_match:
                current_price = float(price_match.group(1).replace(",", ""))
                break
        
        price_vs_vwap = None
        if vwap_value and current_price:
            percentage_diff = ((current_price - vwap_value) / vwap_value) * 100
            price_vs_vwap = f"{percentage_diff:+.1f}%"
            
            if percentage_diff > 1:
                vwap_interpretation = "Price significantly above VWAP - strong buying pressure"
            elif percentage_diff < -1:
                vwap_interpretation = "Price significantly below VWAP - strong selling pressure"
            else:
                vwap_interpretation = "Price near VWAP - balanced market sentiment"
        else:
            vwap_interpretation = "VWAP data not available"
        
        return {
            "indicator": "VWAP Analysis",
            "action": "MONITOR",
            "explanation": fluctuation_answer,
            "vwap_value": vwap_value,
            "current_price": current_price,
            "price_vs_vwap": price_vs_vwap,
            "diagnosis": diagnosis,
            "interpretation": vwap_interpretation,
            "suggestion": diagnosis,
            "note": f"VWAP Trend: {fluctuation_answer}"
        }