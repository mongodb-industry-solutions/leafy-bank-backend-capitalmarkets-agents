from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging
from typing import Dict, List
from datetime import datetime
from service_portfolio_data import PortfolioDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
portfolio_data_service = PortfolioDataService()

# Create the router
router = APIRouter(prefix="/portfolio", tags=["Portfolio Data"])

class AssetAllocation(BaseModel):
    allocation_percentage: str
    allocation_number: int
    allocation_decimal: float
    description: str
    asset_type: str

class MessageResponse(BaseModel):
    portfolio_allocation: Dict[str, AssetAllocation]

class PerformanceDataPoint(BaseModel):
    _id: str
    date: datetime
    percentage_of_daily_return: float
    percentage_of_cumulative_return: float

class PerformanceResponse(BaseModel):
    portfolio_performance: List[PerformanceDataPoint]


### Portfolio Data Endpoints ###

@router.post("/fetch-portfolio-allocation", response_model=MessageResponse)
async def fetch_portfolio_allocation():
    """
    Fetch portfolio allocation data.

    Returns:
        MessageResponse: An object containing the portfolio allocation data.
    """
    try:
        portfolio_allocation = portfolio_data_service.fetch_portfolio_allocation()
        return MessageResponse(portfolio_allocation=portfolio_allocation)
    except Exception as e:
        logging.error(f"Error fetching portfolio allocation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-portfolio-performance", response_model=PerformanceResponse)
async def fetch_portfolio_performance(days: int = Query(30, description="Number of days of performance data to retrieve")):
    """
    Fetch the last N days of portfolio performance data.
    
    Args:
        days: Number of days of performance data to retrieve. Default is 30.
    
    Returns:
        PerformanceResponse: An object containing the portfolio performance data sorted by date (newest first).
    """
    try:
        portfolio_performance = portfolio_data_service.fetch_most_recent_portfolio_performance(days=days)
        return PerformanceResponse(portfolio_performance=portfolio_performance)
    except Exception as e:
        logging.error(f"Error fetching portfolio performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))