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
    indicators (GDP, Interest Rate, Unemployment Rate), to provide investment recommendations
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

        This method:
        1. Retrieves the latest market analysis report
        2. Gets current portfolio allocation data
        3. Analyzes macroeconomic indicators (GDP, interest rates, unemployment)
        4. Applies predefined investment rules based on indicator directions
        5. Generates balanced action recommendations (KEEP/REDUCE) for each asset
        
        Returns:
            list: List of dictionaries containing asset suggestions with actions and explanations
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
            logger.info(f"Portfolio Allocation: {portfolio_allocation}")

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
                elif indicator_name == "Interest Rate":
                    if "up by" in fluctuation:
                        interest_rate_direction = "up"
                    elif "down by" in fluctuation:
                        interest_rate_direction = "down"
                elif indicator_name == "Unemployment Rate":
                    if "up by" in fluctuation:
                        unemployment_direction = "up"
                    elif "down by" in fluctuation:
                        unemployment_direction = "down"

            logger.info(f"Indicator directions - GDP: {gdp_direction}, Interest Rate: {interest_rate_direction}, Unemployment: {unemployment_direction}")

            # Generate macroeconomic-based actions for each asset class
            # Each tuple contains (action, explanation)
            equity_actions = []
            bond_actions = []
            real_estate_actions = []
            commodity_actions = []

            # GDP rules - economic growth impact on asset classes
            if gdp_direction == "up":
                # Rising GDP typically benefits stocks due to better corporate earnings
                equity_actions.append(("KEEP", "Keep due to rising GDP supporting equity assets."))
                # Rising GDP often leads to inflation concerns and higher rates, negative for bonds
                bond_actions.append(("REDUCE", "Reduce due to rising GDP favoring equity over bonds."))
                # Strong economy supports commodity demand for production
                commodity_actions.append(("KEEP", "Keep commodities due to stronger growth increasing demand for raw materials."))
            elif gdp_direction == "down":
                # Economic contraction typically harms equities due to falling earnings
                equity_actions.append(("REDUCE", "Reduce due to declining GDP."))
                # Flight to safety during economic downturns benefits bonds
                bond_actions.append(("KEEP", "Keep due to declining GDP favoring bond assets."))
                # Slowing economic activity reduces commodity demand
                commodity_actions.append(("REDUCE", "Reduce commodities due to economic slowdown reducing industrial demand."))

            # Interest Rate rules - monetary policy impact on asset classes
            if interest_rate_direction == "up":
                # Higher yield on new issuances can be attractive for income investors
                bond_actions.append(("KEEP", "Keep due to rising interest rates favoring bond assets."))
                # Higher financing costs and higher discount rates on future cash flows
                real_estate_actions.append(("REDUCE", "Reduce due to rising interest rates impacting real estate."))
                # Higher rates strengthen currency making commodities more expensive, reducing demand
                commodity_actions.append(("REDUCE", "Reduce commodities due to rising rates strengthening USD and lowering inflation expectations."))
            elif interest_rate_direction == "down":
                # Lower rates decrease yield on new bond issuances
                bond_actions.append(("REDUCE", "Reduce due to falling interest rates."))
                # Lower financing costs benefit real estate valuations
                real_estate_actions.append(("KEEP", "Keep due to declining interest rates favoring real estate assets."))
                # Lower rates tend to weaken currency and increase inflation expectations
                commodity_actions.append(("KEEP", "Keep commodities due to falling interest rates increasing inflation hedge appeal."))

            # Unemployment Rate rules - labor market impact on asset classes
            if unemployment_direction == "up":
                # Rising unemployment signals potential consumer spending reduction
                equity_actions.append(("REDUCE", "Reduce due to rising unemployment rate."))
                # Reduced economic activity decreases demand for raw materials
                commodity_actions.append(("REDUCE", "Reduce commodities as rising unemployment indicates weakening demand."))
            elif unemployment_direction == "down":
                # Improving labor market supports consumer spending and corporate earnings
                equity_actions.append(("KEEP", "Keep due to declining unemployment rate supporting equity assets."))
                # Stronger economic activity increases commodity demand
                commodity_actions.append(("KEEP", "Keep commodities as lower unemployment supports economic expansion and consumption."))

            # Generate final suggestions considering conflicting signals
            suggestions = []
            for symbol, data in portfolio_allocation.items():
                asset_type = data["asset_type"]
                
                # Default to neutral stance if no signals present
                action = "KEEP"
                explanation = "No significant macroeconomic changes affecting this asset."
                note = None  # Initialize note as None
                
                # Determine which set of actions apply to this asset type
                applicable_actions = []
                if asset_type == "Equity":
                    applicable_actions = equity_actions
                elif asset_type == "Bonds":
                    applicable_actions = bond_actions
                elif asset_type == "Real Estate":
                    applicable_actions = real_estate_actions
                elif asset_type == "Commodity":
                    applicable_actions = commodity_actions
                
                # Handle conflicting signals by balancing them rather than prioritizing REDUCE
                # Count the number of KEEP vs REDUCE signals for this asset class
                keep_count = len([act for act, _ in applicable_actions if act == "KEEP"])
                reduce_count = len([act for act, _ in applicable_actions if act == "REDUCE"])
                
                # Determine action based on signal balance
                if keep_count == 0 and reduce_count == 0:
                    # No signals present, keep default
                    pass
                elif keep_count > reduce_count:
                    # More signals suggesting to keep
                    action = "KEEP"
                    # Take the first KEEP explanation as representative
                    keep_explanations = [exp for act, exp in applicable_actions if act == "KEEP"]
                    explanation = keep_explanations[0]
                    if reduce_count > 0:
                        # Add conflicting signals as a note
                        note = f"{reduce_count} conflicting indicator(s) suggested reduction"
                elif reduce_count > keep_count:
                    # More signals suggesting to reduce
                    action = "REDUCE"
                    # Take the first REDUCE explanation as representative
                    reduce_explanations = [exp for act, exp in applicable_actions if act == "REDUCE"]
                    explanation = reduce_explanations[0]
                    if keep_count > 0:
                        # Add conflicting signals as a note
                        note = f"{keep_count} conflicting indicator(s) suggested keeping"
                else:
                    # Equal signals - use conservative approach but note the conflict
                    action = "REDUCE"  # Conservative bias in case of equal signals
                    reduce_explanations = [exp for act, exp in applicable_actions if act == "REDUCE"]
                    explanation = reduce_explanations[0]
                    note = "Equal conflicting signals present, using conservative stance"

                # Construct the suggestion with separate note field
                suggestion = {
                    "asset": symbol,
                    "action": action,
                    "asset_type": asset_type,
                    "description": data["description"],
                    "explanation": explanation
                }
                
                # Add note field only if there's a note
                if note:
                    suggestion["note"] = note
                
                suggestions.append(suggestion)

            logger.info(f"Generated {len(suggestions)} asset suggestions")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating asset suggestions: {e}")
            return []