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

class AssetSuggestion(BaseModel):
    asset: str
    action: str
    asset_type: str
    description: str
    explanation: str
    note: Optional[str] = None

class MessageResponse(BaseModel):
    asset_suggestions: List[AssetSuggestion]

### Asset Suggestions Endpoints ###

@router.post("/fetch-asset-suggestions-macro-indicators-based", response_model=MessageResponse)
async def fetch_asset_suggestions_macro_indicators_based():
    """
    Fetch asset suggestions based on the current portfolio and market conditions.
    
    Rules applied:
    - GDP:
        - Up → Keep Equity assets, Reduce Bond assets, Keep Commodity assets
        - Down → Reduce Equity assets, Keep Bond assets, Reduce Commodity assets
    - Interest Rate:
        - Up → Keep Bond assets, Reduce Real Estate assets, Reduce Commodity assets
        - Down → Reduce Bond assets, Keep Real Estate assets, Keep Commodity assets
    - Unemployment Rate:
        - Up → Reduce Equity assets, Reduce Commodity assets
        - Down → Keep Equity assets, Keep Commodity assets

    Returns:
        MessageResponse: An object containing the asset suggestions with actions (KEEP or REDUCE)
                         and optional notes about conflicting signals.
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