from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging
from typing import Dict, List, Optional
from datetime import datetime
from service_portfolio_data import (
    PortfolioDataService,
    EQUITY_PORTFOLIO_ID,
    CRYPTO_PORTFOLIO_ID,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
portfolio_data_service = PortfolioDataService()

# BIAN service-domain routes mounted at root (no /portfolio prefix). Verb in the URL,
# instance id (portfolioId) in the path. Bodies/responses are camelCase (wire = storage).
router = APIRouter(tags=["InvestmentPortfolio"])

class AssetAllocation(BaseModel):
    binanceSymbol: Optional[str] = None
    allocationPercentage: str
    allocationNumber: int
    allocationDecimal: float
    description: str
    assetType: str

class PortfolioAllocationResponse(BaseModel):
    portfolioAllocation: Dict[str, AssetAllocation]

class PerformanceDataPoint(BaseModel):
    date: datetime
    percentageOfDailyReturn: float
    percentageOfCumulativeReturn: float

class PerformanceResponse(BaseModel):
    portfolioPerformance: List[PerformanceDataPoint]


def _allocation_to_camel(allocation: Dict[str, dict]) -> Dict[str, dict]:
    """Translate the service's internal snake_case allocation dicts to camelCase wire shape."""
    camel = {}
    for symbol, data in allocation.items():
        entry = {
            "allocationPercentage": data["allocation_percentage"],
            "allocationNumber": data["allocation_number"],
            "allocationDecimal": data["allocation_decimal"],
            "description": data["description"],
            "assetType": data["asset_type"],
        }
        if data.get("binance_symbol") is not None:
            entry["binanceSymbol"] = data["binance_symbol"]
        camel[symbol] = entry
    return camel


### InvestmentPortfolioPlanning — allocation (BIAN SD) ###

@router.get(
    "/InvestmentPortfolioPlanning/{portfolio_id}/Retrieve",
    response_model=PortfolioAllocationResponse,
    response_model_exclude_none=True,
)
async def retrieve_portfolio_allocation(portfolio_id: str):
    """
    Retrieve portfolio allocation for a portfolio instance.

    The equity (PORT-0001) and crypto (PORT-0002) portfolios live in one folded
    collection, selected by the portfolioId in the path.

    Returns:
        PortfolioAllocationResponse: camelCase allocation keyed by asset symbol.
    """
    try:
        if portfolio_id == EQUITY_PORTFOLIO_ID:
            allocation = portfolio_data_service.fetch_portfolio_allocation()
        elif portfolio_id == CRYPTO_PORTFOLIO_ID:
            allocation = portfolio_data_service.fetch_crypto_portfolio_allocation()
        else:
            raise HTTPException(status_code=404, detail=f"Unknown portfolioId: {portfolio_id}")
        return PortfolioAllocationResponse(portfolioAllocation=_allocation_to_camel(allocation))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving portfolio allocation for {portfolio_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


### InvestmentPortfolioAnalysis — performance (BIAN SD) ###

@router.get(
    "/InvestmentPortfolioAnalysis/{portfolio_id}/PerformanceAnalysis/Retrieve",
    response_model=PerformanceResponse,
)
async def retrieve_portfolio_performance(
    portfolio_id: str,
    days: int = Query(30, description="Number of days of performance data to retrieve"),
):
    """
    Retrieve the last N days of performance for a portfolio instance, newest first.

    Args:
        portfolio_id: Portfolio instance id (PORT-0001 today — single performance series).
        days: Number of days of performance data to retrieve. Default is 30.
    """
    try:
        performance = portfolio_data_service.fetch_most_recent_portfolio_performance(days=days)
        points = [
            {
                "date": doc["date"],
                "percentageOfDailyReturn": doc["percentage_of_daily_return"],
                "percentageOfCumulativeReturn": doc["percentage_of_cumulative_return"],
            }
            for doc in performance
        ]
        return PerformanceResponse(portfolioPerformance=points)
    except Exception as e:
        logging.error(f"Error retrieving portfolio performance for {portfolio_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
