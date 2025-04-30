from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional
from service_asset_suggestions import AssetSuggestions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
asset_suggestions_service = AssetSuggestions()

# Create the router
router = APIRouter(prefix="/suggestions", tags=["Asset Suggestions"])

class MacroIndicatorSuggestion(BaseModel):
    """Model for a single indicator suggestion (macro or volatility)."""
    indicator: str
    action: str
    explanation: str
    sensitivity: Optional[str] = None  # Added for VIX indicators
    note: Optional[str] = None

class AssetSuggestion(BaseModel):
    """Model for an asset suggestion with granular indicator recommendations."""
    asset: str
    asset_type: str
    description: str
    macro_indicators: List[MacroIndicatorSuggestion]

class MessageResponse(BaseModel):
    """Response model containing a list of asset suggestions."""
    asset_suggestions: List[AssetSuggestion]

### Asset Suggestions Endpoints ###

@router.post("/fetch-asset-suggestions-macro-indicators-based", response_model=MessageResponse)
async def fetch_asset_suggestions_macro_indicators_based():
    """
    Fetch asset suggestions based on the current portfolio and market conditions.
    
    Each asset receives individual recommendations per macroeconomic indicator:
    
    Macro indicators analyzed:
    - GDP: Economic growth indicator
    - Effective Interest Rate: Cost of capital indicator  
    - Unemployment Rate: Labor market health indicator
    
    For each indicator, assets receive a recommendation (KEEP or REDUCE) with explanation
    based on the following rules:
    
    - GDP:
        - Up → Keep Equity assets, Reduce Bond assets, Keep Commodity assets
        - Down → Reduce Equity assets, Keep Bond assets, Reduce Commodity assets
    - Effective Interest Rate:
        - Up → Keep Bond assets, Reduce Real Estate assets, Reduce Commodity assets
        - Down → Reduce Bond assets, Keep Real Estate assets, Keep Commodity assets
    - Unemployment Rate:
        - Up → Reduce Equity assets, Reduce Commodity assets
        - Down → Keep Equity assets, Keep Commodity assets

    Returns:
        MessageResponse: An object containing asset suggestions with per-indicator actions,
                         explanations, and notes about conflicting signals.
    """
    try:
        suggestions = asset_suggestions_service.fetch_asset_suggestions_macro_indicators_based()
        if not suggestions:
            logger.warning("No asset suggestions generated")
            return MessageResponse(asset_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} asset suggestions")
        return MessageResponse(asset_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching asset suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-asset-suggestions-market-volatility-based", response_model=MessageResponse)
async def fetch_asset_suggestions_market_volatility_based():
    """
    Fetch asset suggestions based on the current portfolio and market volatility (VIX).
    
    Each asset receives a recommendation based on its VIX sensitivity:
    
    VIX ranges:
    - Above 20: Generally indicates high volatility/market fear
    - 12-20: Normal volatility range
    - Below 12: Low volatility/market complacency
    
    Asset VIX sensitivity levels:
    - High: QQQ, EEM, HYG - Most affected by volatility spikes
    - Neutral: SPY, XLE, VNQ, USO - Moderately affected by volatility
    - Low: TLT, LQD, GLD - Less affected or may benefit from volatility
    
    Recommendation rules:
    - High VIX (>20):
      - High sensitivity assets → REDUCE
      - Neutral sensitivity assets → REDUCE (less urgently)
      - Low sensitivity assets → KEEP
    - Low VIX (<12):
      - High sensitivity assets → KEEP (increase exposure)
      - Other assets → KEEP
    - Normal VIX (12-20):
      - All assets → KEEP

    Returns:
        MessageResponse: An object containing asset suggestions with VIX-based actions,
                         explanations, and notes about asset sensitivity levels.
    """
    try:
        suggestions = asset_suggestions_service.fetch_asset_suggestions_market_volatility_based()
        if not suggestions:
            logger.warning("No asset suggestions generated")
            return MessageResponse(asset_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} asset suggestions based on market volatility")
        return MessageResponse(asset_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching market volatility-based asset suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))