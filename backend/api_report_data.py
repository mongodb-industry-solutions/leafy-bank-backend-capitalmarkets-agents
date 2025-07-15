from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional
from datetime import datetime
from service_report_data import ReportDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
report_data_service = ReportDataService()

# Create the router
router = APIRouter(prefix="/report", tags=["Report Data"])

# Pydantic models for response validation
class AssetAllocation(BaseModel):
    asset: str
    description: str
    allocation_percentage: str

class AssetTrend(BaseModel):
    asset: str
    fluctuation_answer: str
    diagnosis: str

class MacroIndicator(BaseModel):
    macro_indicator: str
    fluctuation_answer: str
    diagnosis: str

class MarketVolatility(BaseModel):
    volatility_index: str
    fluctuation_answer: str
    diagnosis: str

class MarketAnalysisReportContent(BaseModel):
    asset_trends: List[AssetTrend]
    macro_indicators: List[MacroIndicator]
    market_volatility_index: MarketVolatility
    overall_diagnosis: str

class AssetNews(BaseModel):
    asset: str
    headline: str
    description: str
    source: str
    posted: str
    link: str
    sentiment_score: float
    sentiment_category: str

class AssetNewsSummary(BaseModel):
    asset: str
    summary: str
    overall_sentiment_score: float
    overall_sentiment_category: str
    article_count: int

class MarketNewsReportContent(BaseModel):
    asset_news: List[AssetNews]
    asset_news_sentiments: List[AssetNewsSummary]
    overall_news_diagnosis: str

class MarketAnalysisReport(BaseModel):
    _id: str
    portfolio_allocation: List[AssetAllocation]
    report: MarketAnalysisReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

class MarketNewsReport(BaseModel):
    _id: str
    portfolio_allocation: List[AssetAllocation]
    report: MarketNewsReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

class MarketAnalysisResponse(BaseModel):
    market_analysis_report: Optional[MarketAnalysisReport] = None

class MarketNewsResponse(BaseModel):
    market_news_report: Optional[MarketNewsReport] = None

### Report Data Endpoints ###

@router.post("/fetch-most-recent-market-analysis-report", response_model=MarketAnalysisResponse)
async def fetch_most_recent_market_analysis_report():
    """
    Fetch the most recent market analysis report.

    Returns:
        MarketAnalysisResponse: An object containing the most recent market analysis report.
    """
    try:
        report = report_data_service.fetch_most_recent_market_analysis_report()
        if not report:
            return MarketAnalysisResponse(market_analysis_report=None)
        return MarketAnalysisResponse(market_analysis_report=report)
    except Exception as e:
        logging.error(f"Error fetching market analysis report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-most-recent-market-news-report", response_model=MarketNewsResponse)
async def fetch_most_recent_market_news_report():
    """
    Fetch the most recent market news report.

    Returns:
        MarketNewsResponse: An object containing the most recent market news report.
    """
    try:
        report = report_data_service.fetch_most_recent_market_news_report()
        if not report:
            return MarketNewsResponse(market_news_report=None)
        return MarketNewsResponse(market_news_report=report)
    except Exception as e:
        logging.error(f"Error fetching market news report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))