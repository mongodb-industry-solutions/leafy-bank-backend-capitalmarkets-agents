import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AssetSuggestions(MongoDBConnector):
    """
    Service class for generating asset allocation suggestions based on macroeconomic indicators.
    
    This service analyzes the most recent market data, particularly focusing on macroeconomic 
    indicators (GDP, Effective Interest Rate, Unemployment Rate), to provide investment recommendations
    for different asset classes in a portfolio. The recommendations are rule-based and consider
    the traditional relationships between macro indicators and asset classes.
    """
    
    def __init__(self, uri=None, database_name: str = None, appname: str = None):
        """
        Initialize the AssetSuggestions service.
        
        Args:
            uri (str, optional): MongoDB connection URI
            database_name (str, optional): Target database name
            appname (str, optional): Application name for MongoDB connection
        """
        super().__init__(uri, database_name, appname)
        self.collections = {
            "market_analysis": os.getenv("REPORTS_COLLECTION_MARKET_ANALYSIS"),
            "portfolio_allocation": os.getenv("PORTFOLIO_COLLECTION")
        }
        logger.info("AssetSuggestions initialized")

    def fetch_asset_suggestions_macro_indicators_based(self):
        """
        Generate asset allocation suggestions based on the latest macroeconomic indicators coming from the market analysis report.
        
        Returns:
            list: List of dictionaries containing asset suggestions with per-indicator actions and explanations
        """
        try:
            # Fetch latest market analysis report
            market_analysis_collection = self.collections["market_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ]
            result = list(self.db[market_analysis_collection].aggregate(pipeline))
            logger.info(f"Fetched {len(result)} market analysis report(s)")

            if not result:
                logger.error("No market analysis report found")
                return []

            market_analysis = result[0].get("report", {})
            logger.info(f"Market Analysis Report: {market_analysis}")

            if not market_analysis.get("macro_indicators"):
                logger.warning("No macro indicators found in the market analysis report")
                return []

            # Fetch portfolio allocation data
            portfolio_collection = self.collections["portfolio_allocation"]
            portfolio_allocation = {}
            try:
                cursor = self.db[portfolio_collection].find()
                for doc in cursor:
                    symbol = doc["symbol"]
                    portfolio_allocation[symbol] = {
                        "allocation_percentage": doc.get("allocation_percentage"),
                        "allocation_number": doc.get("allocation_number"),
                        "allocation_decimal": doc.get("allocation_decimal"),
                        "description": doc.get("description"),
                        "asset_type": doc.get("asset_type")
                    }
            except Exception as e:
                logger.error(f"Error fetching portfolio allocation: {e}")
                return []

            logger.info(f"Fetched {len(portfolio_allocation)} portfolio allocation(s)")
            
            # Determine macroeconomic indicator directions
            gdp_direction = "neutral"
            interest_rate_direction = "neutral"
            unemployment_direction = "neutral"

            for indicator in market_analysis.get("macro_indicators", []):
                indicator_name = indicator.get("macro_indicator")
                fluctuation = indicator.get("fluctuation_answer", "").lower()

                if indicator_name == "GDP":
                    if "up by" in fluctuation:
                        gdp_direction = "up"
                    elif "down by" in fluctuation:
                        gdp_direction = "down"
                elif indicator_name == "Effective Interest Rate":
                    if "up by" in fluctuation:
                        interest_rate_direction = "up"
                    elif "down by" in fluctuation:
                        interest_rate_direction = "down"
                elif indicator_name == "Unemployment Rate":
                    if "up by" in fluctuation:
                        unemployment_direction = "up"
                    elif "down by" in fluctuation:
                        unemployment_direction = "down"

            logger.info(f"Indicator directions - GDP: {gdp_direction}, Effective Interest Rate: {interest_rate_direction}, Unemployment: {unemployment_direction}")

            # Define rules for each indicator and asset type combination based on business requirements
            # Each rule maps an indicator direction to asset type recommendations
            rules = {
                "GDP": {
                    "up": {
                        "Equity": ("KEEP", "Increase Equity assets due to rising GDP indicating economic growth."),
                        "Bonds": ("REDUCE", "Reduce Bond assets as rising GDP typically favors equity over fixed income."),
                        "Real Estate": ("KEEP", "Keep Real Estate as rising GDP supports property values and rental income."),
                        "Commodity": ("KEEP", "Keep Commodities as economic growth increases demand for raw materials.")
                    },
                    "down": {
                        "Equity": ("REDUCE", "Reduce Equity assets as declining GDP indicates economic contraction."),
                        "Bonds": ("KEEP", "Increase Bond assets as declining GDP favors safer fixed income investments."),
                        "Real Estate": ("REDUCE", "Reduce Real Estate as economic contraction may impact property values."),
                        "Commodity": ("REDUCE", "Reduce Commodities as economic slowdown decreases industrial demand.")
                    },
                    "neutral": {
                        "Equity": ("KEEP", "No change needed as GDP remains stable."),
                        "Bonds": ("KEEP", "No change needed as GDP remains stable."),
                        "Real Estate": ("KEEP", "No change needed as GDP remains stable."),
                        "Commodity": ("KEEP", "No change needed as GDP remains stable.")
                    }
                },
                "Effective Interest Rate": {
                    "up": {
                        "Equity": ("REDUCE", "Reduce Equity assets as higher rates increase cost of capital and discount future earnings."),
                        "Bonds": ("KEEP", "Increase Bond assets as rising rates provide better yields on new issuances."),
                        "Real Estate": ("REDUCE", "Reduce Real Estate as rising rates increase financing costs."),
                        "Commodity": ("REDUCE", "Reduce Commodities as rising rates strengthen currency and reduce inflation hedge appeal.")
                    },
                    "down": {
                        "Equity": ("KEEP", "Keep Equity assets as lower rates support corporate financing and valuations."),
                        "Bonds": ("REDUCE", "Reduce Bond assets as falling rates decrease yield on new issuances."),
                        "Real Estate": ("KEEP", "Increase Real Estate as declining rates lower financing costs and improve yields."),
                        "Commodity": ("KEEP", "Keep Commodities as falling rates may weaken currency and increase inflation risk.")
                    },
                    "neutral": {
                        "Equity": ("KEEP", "No change needed as interest rates remain stable."),
                        "Bonds": ("KEEP", "No change needed as interest rates remain stable."),
                        "Real Estate": ("KEEP", "No change needed as interest rates remain stable."),
                        "Commodity": ("KEEP", "No change needed as interest rates remain stable.")
                    }
                },
                "Unemployment Rate": {
                    "up": {
                        "Equity": ("REDUCE", "Reduce Equity assets as rising unemployment signals weaker consumer spending and earnings."),
                        "Bonds": ("KEEP", "Keep Bond assets as rising unemployment may lead to accommodative monetary policy."),
                        "Real Estate": ("REDUCE", "Reduce Real Estate as rising unemployment may impact demand and rental income."),
                        "Commodity": ("REDUCE", "Reduce Commodities as rising unemployment indicates weakening economic activity.")
                    },
                    "down": {
                        "Equity": ("KEEP", "Increase Equity assets as declining unemployment supports consumer spending and earnings."),
                        "Bonds": ("REDUCE", "Reduce Bond assets as improving labor market may lead to tighter monetary policy."),
                        "Real Estate": ("KEEP", "Keep Real Estate as improving employment supports housing demand."),
                        "Commodity": ("KEEP", "Keep Commodities as lower unemployment supports economic growth and consumption.")
                    },
                    "neutral": {
                        "Equity": ("KEEP", "No change needed as unemployment remains stable."),
                        "Bonds": ("KEEP", "No change needed as unemployment remains stable."),
                        "Real Estate": ("KEEP", "No change needed as unemployment remains stable."),
                        "Commodity": ("KEEP", "No change needed as unemployment remains stable.")
                    }
                }
            }
            
            # Generate suggestions with per-indicator recommendations
            suggestions = []
            indicators_directions = {
                "GDP": gdp_direction,
                "Effective Interest Rate": interest_rate_direction,
                "Unemployment Rate": unemployment_direction
            }
            
            for symbol, data in portfolio_allocation.items():
                asset_type = data["asset_type"]
                
                macro_indicators_suggestions = []
                for indicator, direction in indicators_directions.items():
                    action, explanation = rules[indicator][direction].get(
                        asset_type, 
                        ("KEEP", f"Default recommendation for {asset_type} under {indicator} {direction} condition.")
                    )
                    
                    # Determine if there are conflicting signals with other indicators
                    conflicts = []
                    for other_indicator, other_direction in indicators_directions.items():
                        if other_indicator != indicator:
                            other_action = rules[other_indicator][other_direction].get(asset_type, ("KEEP", ""))[0]
                            if other_action != action:
                                conflicts.append(other_indicator)
                    
                    indicator_suggestion = {
                        "indicator": indicator,
                        "action": action,
                        "explanation": explanation
                    }
                    
                    # Add note if there are conflicting signals
                    if conflicts:
                        indicator_suggestion["note"] = f"Conflicting signal with {', '.join(conflicts)}"
                    
                    macro_indicators_suggestions.append(indicator_suggestion)
                
                suggestion = {
                    "asset": symbol,
                    "asset_type": asset_type,
                    "description": data["description"],
                    "macro_indicators": macro_indicators_suggestions
                }
                
                suggestions.append(suggestion)
            
            logger.info(f"Generated {len(suggestions)} asset suggestions with granular indicator-based recommendations")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating asset suggestions: {e}", exc_info=True)
            return []

    def fetch_asset_suggestions_market_volatility_based(self):
        """
        Generate asset allocation suggestions based on the latest Market Volatility Index (VIX)
        from the market analysis report, considering each asset's VIX sensitivity and current trend.
        
        Returns:
            list: List of dictionaries containing asset suggestions with VIX-based actions and explanations
        """
        try:
            # Fetch latest market analysis report
            market_analysis_collection = self.collections["market_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ]
            result = list(self.db[market_analysis_collection].aggregate(pipeline))
            logger.info(f"Fetched {len(result)} market analysis report(s)")

            if not result:
                logger.error("No market analysis report found")
                return []

            market_analysis = result[0].get("report", {})
            logger.info(f"Market Analysis Report: {market_analysis}")

            # Extract VIX data
            volatility_data = market_analysis.get("market_volatility_index", {})
            if not volatility_data:
                logger.warning("No market volatility data found in the market analysis report")
                return []
                
            # Extract VIX value from fluctuation_answer
            vix_fluctuation = volatility_data.get("fluctuation_answer", "")
            vix_value = None
            
            # Parse the VIX value from the fluctuation_answer string
            import re
            vix_match = re.search(r"VIX close price is (\d+\.\d+)", vix_fluctuation)
            if vix_match:
                vix_value = float(vix_match.group(1))
                logger.info(f"Extracted VIX value: {vix_value}")
            else:
                logger.error(f"Could not extract VIX value from: {vix_fluctuation}")
                return []

            # Extract asset trends from the market analysis report
            asset_trends = {}
            for trend_data in market_analysis.get("asset_trends", []):
                asset_symbol = trend_data.get("asset")
                diagnosis = trend_data.get("diagnosis", "").lower()
                
                if "uptrend" in diagnosis:
                    asset_trends[asset_symbol] = "UPTREND"
                elif "downtrend" in diagnosis:
                    asset_trends[asset_symbol] = "DOWNTREND"
                else:
                    asset_trends[asset_symbol] = "NEUTRAL"
                    
            logger.info(f"Extracted trends for {len(asset_trends)} assets")

            # Fetch portfolio allocation data
            portfolio_collection = self.collections["portfolio_allocation"]
            portfolio_allocation = {}
            try:
                cursor = self.db[portfolio_collection].find()
                for doc in cursor:
                    symbol = doc["symbol"]
                    portfolio_allocation[symbol] = {
                        "allocation_percentage": doc.get("allocation_percentage"),
                        "allocation_number": doc.get("allocation_number"),
                        "allocation_decimal": doc.get("allocation_decimal"),
                        "description": doc.get("description"),
                        "asset_type": doc.get("asset_type")
                    }
            except Exception as e:
                logger.error(f"Error fetching portfolio allocation: {e}")
                return []

            logger.info(f"Fetched {len(portfolio_allocation)} portfolio allocation(s)")
            
            # Define VIX sensitivity for each asset
            vix_sensitivity = {
                "SPY": "NEUTRAL",  # S&P 500 ETF
                "QQQ": "HIGH",     # Nasdaq ETF
                "EEM": "HIGH",     # Emerging Markets ETF
                "XLE": "NEUTRAL",  # Energy Sector ETF
                "TLT": "LOW",      # Long-Term Treasury Bonds
                "LQD": "LOW",      # Investment-Grade Bonds
                "HYG": "HIGH",     # High-Yield Bonds
                "VNQ": "NEUTRAL",  # Real Estate ETF
                "GLD": "LOW",      # Gold ETF
                "USO": "NEUTRAL",  # Oil ETF
            }
            
            # Determine VIX state based on value
            if vix_value > 20:
                vix_state = "HIGH"
            elif vix_value < 12:
                vix_state = "LOW"
            else:
                vix_state = "NORMAL"
            
            logger.info(f"VIX state: {vix_state} ({vix_value})")
            
            # Generate suggestions based on VIX state, asset sensitivity and trend
            suggestions = []
            
            for symbol, data in portfolio_allocation.items():
                asset_description = data["description"]
                asset_type = data["asset_type"]
                sensitivity = vix_sensitivity.get(symbol, "NEUTRAL")
                asset_trend = asset_trends.get(symbol, "NEUTRAL")
                
                # Determine action based on both sensitivity and trend
                action = self._get_vix_action_with_trend(vix_state, sensitivity, asset_trend)
                explanation = self._get_vix_explanation_with_trend(symbol, vix_value, vix_state, sensitivity, asset_trend)
                
                # VIX-based recommendation
                vix_indicator = {
                    "indicator": "VIX",
                    "action": action,
                    "sensitivity": sensitivity,
                    "explanation": explanation
                }
                
                # Add note about trend if applicable
                note_parts = []
                if sensitivity != "NEUTRAL":
                    note_parts.append(f"{symbol} has {sensitivity} sensitivity to market volatility")
                if asset_trend != "NEUTRAL":
                    note_parts.append(f"Currently in {asset_trend}")
                    
                if note_parts:
                    vix_indicator["note"] = ". ".join(note_parts)
                
                suggestion = {
                    "asset": symbol,
                    "asset_type": asset_type,
                    "description": asset_description,
                    "macro_indicators": [vix_indicator]
                }
                
                suggestions.append(suggestion)
            
            logger.info(f"Generated {len(suggestions)} asset suggestions based on market volatility and asset trends")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating market volatility-based asset suggestions: {e}", exc_info=True)
            return []

    @staticmethod
    def _get_vix_action_with_trend(vix_state, sensitivity, asset_trend):
        """
        Determine the action based on VIX state, asset sensitivity, and trend.
        
        Args:
            vix_state (str): HIGH, LOW, or NORMAL
            sensitivity (str): HIGH, LOW, or NEUTRAL
            asset_trend (str): UPTREND, DOWNTREND, or NEUTRAL
            
        Returns:
            str: Action recommendation (KEEP or REDUCE)
        """
        # For HIGH sensitivity assets, VIX is the primary factor
        if sensitivity == "HIGH":
            if vix_state == "HIGH":
                return "REDUCE"
            elif vix_state == "LOW":
                return "KEEP"  # Means increase but keeping consistent with available actions
            else:  # NORMAL
                # For normal VIX, look at the asset's trend
                return "REDUCE" if asset_trend == "DOWNTREND" else "KEEP"
        
        # For NEUTRAL sensitivity assets, consider both VIX and trend
        elif sensitivity == "NEUTRAL":
            if vix_state == "HIGH" and asset_trend == "DOWNTREND":
                return "REDUCE"  # Strong signal to reduce
            elif vix_state == "LOW" and asset_trend == "UPTREND":
                return "KEEP"    # Strong signal to keep/increase
            elif asset_trend == "DOWNTREND":
                return "REDUCE"  # Prioritize trend for neutral sensitivity
            else:
                return "KEEP"    # Default to keep
        
        # For LOW sensitivity assets, trend is more important than VIX
        else:  # LOW sensitivity
            if asset_trend == "DOWNTREND":
                return "REDUCE"  # Even low sensitivity assets should be reduced in downtrend
            else:
                return "KEEP"    # Otherwise keep

    @staticmethod
    def _get_vix_explanation_with_trend(symbol, vix_value, vix_state, sensitivity, asset_trend):
        """
        Generate explanation for the VIX-based recommendation, considering asset trend.
        
        Args:
            symbol (str): Asset symbol
            vix_value (float): Current VIX value
            vix_state (str): HIGH, LOW, or NORMAL
            sensitivity (str): HIGH, LOW, or NEUTRAL
            asset_trend (str): UPTREND, DOWNTREND, or NEUTRAL
            
        Returns:
            str: Explanation text
        """
        # Build explanations based on both VIX and trend
        if sensitivity == "HIGH":
            # For high sensitivity, VIX is primary factor
            if vix_state == "HIGH":
                return f"{symbol} has high VIX sensitivity and volatility is elevated ({vix_value}). Reducing position advised."
            elif vix_state == "LOW":
                return f"{symbol} has high VIX sensitivity and volatility is low ({vix_value}). Favorable time to increase exposure."
            else:  # NORMAL VIX
                if asset_trend == "DOWNTREND":
                    return f"{symbol} shows downtrend movement despite normal volatility ({vix_value}). Reducing position advised."
                else:
                    return f"{symbol} has high sensitivity but VIX is at normal levels ({vix_value}). Current trend supports maintaining position."
        
        elif sensitivity == "NEUTRAL":
            # For neutral sensitivity, consider both factors equally
            if vix_state == "HIGH":
                if asset_trend == "DOWNTREND":
                    return f"{symbol} faces both elevated volatility ({vix_value}) and downward trend. Risk reduction advised."
                else:
                    return f"{symbol} faces elevated volatility ({vix_value}) but trend is not negative. Monitor closely."
            elif vix_state == "LOW":
                if asset_trend == "UPTREND":
                    return f"{symbol} benefits from low volatility ({vix_value}) and positive trend. Good conditions for exposure."
                else:
                    return f"{symbol} has low volatility ({vix_value}) but lacks upward momentum. Maintain current allocation."
            else:  # NORMAL VIX
                if asset_trend == "DOWNTREND":
                    return f"{symbol} shows downtrend despite normal volatility ({vix_value}). Consider reducing position."
                elif asset_trend == "UPTREND":
                    return f"{symbol} shows positive momentum with stable volatility ({vix_value}). Favorable conditions."
                else:
                    return f"{symbol} has neutral sensitivity and stable conditions. Maintain current allocation."
        
        else:  # LOW sensitivity
            # For low sensitivity, trend is more important than VIX
            if asset_trend == "DOWNTREND":
                return f"{symbol} has low VIX sensitivity but shows downward trend. Consider tactical reduction despite lower volatility risk."
            elif asset_trend == "UPTREND":
                return f"{symbol} has low VIX sensitivity and positive trend. Good candidate for stable returns in current conditions."
            else:
                if vix_state == "HIGH":
                    return f"{symbol} provides good diversification during high volatility ({vix_value}) due to low sensitivity. Maintain position."
                else:
                    return f"{symbol} has low volatility sensitivity. Current market conditions don't warrant position changes."