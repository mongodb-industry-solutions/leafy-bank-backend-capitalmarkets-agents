import logging
from db.mdb import MongoDBConnector
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AssetSuggestions(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None):
        """
        Service for manipulating Report data.
        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
        """
        super().__init__(uri, database_name, appname)
        self.collections = {
            "market_analysis": os.getenv("REPORTS_COLLECTION_MARKET_ANALYSIS"),
            "portfolio_allocation": os.getenv("PORTFOLIO_COLLECTION")
        }
        logger.info("AssetSuggestions initialized")

    def fetch_asset_suggestions(self):
        """
        Generate asset suggestions based on macroeconomic indicators and portfolio allocation.
        Rules:
        - GDP: Up → Increase Equity assets, Down → Increase Bond assets
        - Interest Rate: Up → Increase Bond assets, Down → Increase Real Estate assets
        - Unemployment Rate: Up → Reduce Equity assets, Down → Increase Equity assets
        
        Returns:
            list: A list of asset suggestions with action (KEEP or REDUCE), asset type, and explanation.
        """
        try:
            # Fetch the latest market analysis report
            market_analysis_collection = self.collections["market_analysis"]
            pipeline = [
                {"$sort": {"timestamp": -1}},  # Sort by timestamp in descending order
                {"$limit": 1}  # Limit to only the most recent document
            ]
            
            result = list(self.db[market_analysis_collection].aggregate(pipeline))
            if not result:
                logger.error("No market analysis report found")
                return []
                
            market_analysis = result[0].get("market_analysis_report", {})
            
            # Fetch portfolio allocation
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
            
            # Extract macroeconomic indicator directions from the fluctuation_answer field
            gdp_direction = "neutral"
            interest_rate_direction = "neutral"
            unemployment_direction = "neutral"
            
            for indicator in market_analysis.get("report", {}).get("macro_indicators", []):
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
            
            # Define asset action rules based on macro indicators
            equity_actions = []
            bond_actions = []
            real_estate_actions = []
            
            # Apply GDP rules
            if gdp_direction == "up":
                equity_actions.append(("KEEP", "Keep due to rising GDP supporting equity assets."))
                bond_actions.append(("REDUCE", "Reduce due to rising GDP favoring equity over bonds."))
            elif gdp_direction == "down":
                equity_actions.append(("REDUCE", "Reduce due to declining GDP."))
                bond_actions.append(("KEEP", "Keep due to declining GDP favoring bond assets."))
            
            # Apply Interest Rate rules
            if interest_rate_direction == "up":
                bond_actions.append(("KEEP", "Keep due to rising interest rates favoring bond assets."))
                real_estate_actions.append(("REDUCE", "Reduce due to rising interest rates impacting real estate."))
            elif interest_rate_direction == "down":
                bond_actions.append(("REDUCE", "Reduce due to falling interest rates."))
                real_estate_actions.append(("KEEP", "Keep due to declining interest rates favoring real estate assets."))
            
            # Apply Unemployment Rate rules
            if unemployment_direction == "up":
                equity_actions.append(("REDUCE", "Reduce due to rising unemployment rate."))
            elif unemployment_direction == "down":
                equity_actions.append(("KEEP", "Keep due to declining unemployment rate supporting equity assets."))
            
            # Generate asset suggestions
            suggestions = []
            for symbol, data in portfolio_allocation.items():
                asset_type = data["asset_type"]
                action = "KEEP"  # Default action
                explanation = "No significant macroeconomic changes affecting this asset."
                
                # Apply relevant actions based on asset type
                if asset_type == "Equity":
                    for act, exp in equity_actions:
                        if act == "REDUCE":
                            action = "REDUCE"
                            explanation = exp
                            break
                        elif act == "KEEP" and action != "REDUCE":
                            action = "KEEP"
                            explanation = exp
                
                elif asset_type == "Bonds":
                    for act, exp in bond_actions:
                        if act == "REDUCE":
                            action = "REDUCE"
                            explanation = exp
                            break
                        elif act == "KEEP" and action != "REDUCE":
                            action = "KEEP"
                            explanation = exp
                
                elif asset_type == "Real Estate":
                    for act, exp in real_estate_actions:
                        if act == "REDUCE":
                            action = "REDUCE"
                            explanation = exp
                            break
                        elif act == "KEEP" and action != "REDUCE":
                            action = "KEEP"
                            explanation = exp
                
                suggestions.append({
                    "asset": symbol,
                    "action": action,
                    "asset_type": asset_type,
                    "description": data["description"],
                    "explanation": explanation
                })
            
            logger.info(f"Generated {len(suggestions)} asset suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating asset suggestions: {e}")
            return []