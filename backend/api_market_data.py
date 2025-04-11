from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from service_market_data import MarketDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
market_data_service = MarketDataService()

# Create the router
router = APIRouter(prefix="/market", tags=["Market Data"])

class AssetPrice(BaseModel):
    close_price: float
    timestamp: datetime

class MessageResponse(BaseModel):
    assets_close_price: Dict[str, AssetPrice]

class AssetDataPoint(BaseModel):
    _id: Optional[str] = None  # Make _id optional to avoid validation errors
    symbol: str
    timestamp: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    date_load_iso_utc: Optional[str] = None
    
class RecentDataResponse(BaseModel):
    assets_data: Dict[str, List[AssetDataPoint]]


### Market Data Endpoints ###

@router.post("/fetch-assets-close-price", response_model=MessageResponse)
async def fetch_assets_close_price():
    """
    Fetch the latest close price for all assets.

    Returns:
        MessageResponse: An object containing the assets close prices.
    """
    try:
        close_prices = market_data_service.fetch_assets_close_price()
        return MessageResponse(assets_close_price=close_prices)
    except Exception as e:
        logging.error(f"Error fetching assets close price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-recent-assets-data", response_model=RecentDataResponse)
async def fetch_recent_assets_data(limit: int = Query(3, description="Number of recent data points to retrieve per asset")):
    """
    Fetch the most recent data points for all assets.

    Args:
        limit: Number of recent data points to retrieve per asset. Default is 3.

    Returns:
        RecentDataResponse: An object containing the recent data points for each asset.
    """
    try:
        recent_data = market_data_service.fetch_most_recent_assets_data(limit=limit)
        # Debug the response to ensure _id is included
        if recent_data and len(recent_data) > 0:
            first_symbol = next(iter(recent_data))
            if recent_data[first_symbol] and len(recent_data[first_symbol]) > 0:
                logger.debug(f"Sample data point keys: {recent_data[first_symbol][0].keys()}")
        
        return RecentDataResponse(assets_data=recent_data)
    except Exception as e:
        logging.error(f"Error fetching recent assets data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))