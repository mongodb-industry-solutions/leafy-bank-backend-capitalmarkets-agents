from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict, Any
from service_stablecoins_market_cap_data import StablecoinsMarketCapDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
stablecoins_market_cap_data_service = StablecoinsMarketCapDataService()

# Create the router
router = APIRouter(prefix="/stablecoins", tags=["Stablecoins Market Cap Data"])

class StablecoinsResponse(BaseModel):
    data: List[Dict[str, Any]]
    count: int
    message: Optional[str] = None


### Stablecoins Market Cap Data Endpoints ###

@router.get("/fetch-most-recent-stablecoins-market-cap", response_model=StablecoinsResponse)
async def fetch_most_recent_stablecoins_market_cap():
    """
    Fetch the most recent stablecoins market cap data.

    Returns:
        StablecoinsResponse: Object containing stablecoins market cap data.
    """
    try:
        stablecoins_data = stablecoins_market_cap_data_service.fetch_most_recent_stablecoins_market_cap()
        
        if not stablecoins_data:
            return StablecoinsResponse(
                data=[],
                count=0,
                message="No stablecoin market cap data found"
            )
        
        return StablecoinsResponse(
            data=stablecoins_data,
            count=len(stablecoins_data)
        )
        
    except Exception as e:
        logger.error(f"Error fetching most recent stablecoins market cap data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
