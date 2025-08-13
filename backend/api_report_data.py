from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict
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
router = APIRouter(prefix="/reports", tags=["Reports Data"])

### Common/Shared Models ###

class AssetAllocation(BaseModel):
    asset: str
    description: str
    allocation_percentage: str

class CryptoPortfolioAllocation(BaseModel):
    asset: str
    asset_type: str
    description: str
    allocation_percentage: str

class SentimentScore(BaseModel):
    neutral: Optional[float] = None
    negative: Optional[float] = None
    positive: Optional[float] = None

### Market Analysis Report Models ###

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

class MarketAnalysisReport(BaseModel):
    _id: str
    portfolio_allocation: List[AssetAllocation]
    report: MarketAnalysisReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Market News Report Models ###

class AssetNews(BaseModel):
    asset: str
    headline: str
    description: str
    source: str
    posted: str
    link: str
    sentiment_score: Optional[SentimentScore] = None

class AssetNewsSummary(BaseModel):
    asset: str
    final_sentiment_score: Optional[float] = None
    sentiment_category: Optional[str] = None
    total_news: Optional[int] = None
    average_positive: Optional[float] = None
    average_negative: Optional[float] = None
    average_neutral: Optional[float] = None
    confidence_level: Optional[float] = None
    sentiment_summary: Optional[str] = None

class MarketNewsReportContent(BaseModel):
    asset_news: List[AssetNews]
    asset_news_sentiments: List[AssetNewsSummary]
    overall_news_diagnosis: str

class MarketNewsReport(BaseModel):
    _id: str
    portfolio_allocation: List[AssetAllocation]
    report: MarketNewsReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Market Social Media Report Models ###

class Comment(BaseModel):
    id: Optional[str] = None
    author: Optional[str] = None
    body: Optional[str] = None
    score: Optional[int] = None
    create_at_utc: Optional[str] = None

class AssetSubreddit(BaseModel):
    asset: str
    subreddit: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    author_fullname: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    create_at_utc: Optional[str] = None
    score: Optional[int] = None
    num_comments: Optional[int] = None
    comments: List[Comment] = []
    ups: Optional[int] = None
    downs: Optional[int] = None
    sentiment_score: Optional[SentimentScore] = None

class AssetSocialMediaSentiment(BaseModel):
    asset: str
    final_sentiment_score: Optional[float] = None
    sentiment_category: Optional[str] = None
    total_submissions: Optional[int] = None
    recent_submissions: Optional[int] = None
    average_positive: Optional[float] = None
    average_negative: Optional[float] = None
    average_neutral: Optional[float] = None
    total_engagement_score: Optional[int] = None
    total_comments: Optional[int] = None
    total_ups: Optional[int] = None
    confidence_level: Optional[float] = None
    sentiment_summary: Optional[str] = None

class MarketSocialMediaReportContent(BaseModel):
    asset_subreddits: List[AssetSubreddit]
    asset_sm_sentiments: List[AssetSocialMediaSentiment]
    overall_news_diagnosis: str

class MarketSocialMediaReport(BaseModel):
    _id: str
    portfolio_allocation: List[AssetAllocation]
    report: MarketSocialMediaReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Crypto Analysis Report Models ###

class CryptoAssetTrend(BaseModel):
    asset: str
    fluctuation_answer: str
    diagnosis: str

class MomentumIndicator(BaseModel):
    indicator_name: str
    fluctuation_answer: str
    diagnosis: str

class CryptoMomentumIndicator(BaseModel):
    asset: str
    momentum_indicators: List[MomentumIndicator]

class CryptoAnalysisReportContent(BaseModel):
    crypto_trends: List[CryptoAssetTrend]
    crypto_momentum_indicators: List[CryptoMomentumIndicator]
    overall_diagnosis: str

class CryptoAnalysisReport(BaseModel):
    _id: str
    portfolio_allocation: List[CryptoPortfolioAllocation]
    report: CryptoAnalysisReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Crypto News Report Models ###

class CryptoAssetNews(BaseModel):
    asset: str
    headline: str
    description: str
    source: str
    posted: str
    link: str
    sentiment_score: Optional[SentimentScore] = None

class CryptoAssetNewsSummary(BaseModel):
    asset: str
    final_sentiment_score: Optional[float] = None
    sentiment_category: Optional[str] = None
    total_news: Optional[int] = None
    average_positive: Optional[float] = None
    average_negative: Optional[float] = None
    average_neutral: Optional[float] = None
    confidence_level: Optional[float] = None
    sentiment_summary: Optional[str] = None

class CryptoNewsReportContent(BaseModel):
    asset_news: List[CryptoAssetNews]
    asset_news_sentiments: List[CryptoAssetNewsSummary]
    overall_news_diagnosis: str

class CryptoNewsReport(BaseModel):
    _id: str
    portfolio_allocation: List[CryptoPortfolioAllocation]
    report: CryptoNewsReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Crypto Social Media Report Models ###

class CryptoAssetSubreddit(BaseModel):
    asset: str
    subreddit: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    author_fullname: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    create_at_utc: Optional[str] = None
    score: Optional[int] = None
    num_comments: Optional[int] = None
    comments: List[Comment] = []
    ups: Optional[int] = None
    downs: Optional[int] = None
    sentiment_score: Optional[SentimentScore] = None

class CryptoAssetSocialMediaSentiment(BaseModel):
    asset: str
    final_sentiment_score: Optional[float] = None
    sentiment_category: Optional[str] = None
    total_submissions: Optional[int] = None
    recent_submissions: Optional[int] = None
    average_positive: Optional[float] = None
    average_negative: Optional[float] = None
    average_neutral: Optional[float] = None
    total_engagement_score: Optional[int] = None
    total_comments: Optional[int] = None
    total_ups: Optional[int] = None
    confidence_level: Optional[float] = None
    sentiment_summary: Optional[str] = None

class CryptoSocialMediaReportContent(BaseModel):
    asset_subreddits: List[CryptoAssetSubreddit]
    asset_sm_sentiments: List[CryptoAssetSocialMediaSentiment]
    overall_news_diagnosis: str

class CryptoSocialMediaReport(BaseModel):
    _id: str
    portfolio_allocation: List[CryptoPortfolioAllocation]
    report: CryptoSocialMediaReportContent
    updates: List[str]
    timestamp: datetime
    date_string: str

### Response Models ###

class MarketAnalysisResponse(BaseModel):
    market_analysis_report: Optional[MarketAnalysisReport] = None

class MarketNewsResponse(BaseModel):
    market_news_report: Optional[MarketNewsReport] = None

class MarketSocialMediaResponse(BaseModel):
    market_sm_report: Optional[MarketSocialMediaReport] = None

class CryptoAnalysisResponse(BaseModel):
    crypto_analysis_report: Optional[CryptoAnalysisReport] = None

class CryptoNewsResponse(BaseModel):
    crypto_news_report: Optional[CryptoNewsReport] = None

class CryptoSocialMediaResponse(BaseModel):
    crypto_sm_report: Optional[CryptoSocialMediaReport] = None

class ConsolidatedRiskProfileResponse(BaseModel):
    counts: Dict[str, int]
    result: str

### Report Data Endpoints ###

@router.get("/fetch-most-recent-market-analysis-report", response_model=MarketAnalysisResponse)
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

@router.get("/fetch-most-recent-market-news-report", response_model=MarketNewsResponse)
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

@router.get("/fetch-most-recent-market-social-media-report", response_model=MarketSocialMediaResponse)
async def fetch_most_recent_market_sm_report():
    """
    Fetch the most recent market social media report.

    Returns:
        MarketSocialMediaResponse: An object containing the most recent market social media report.
    """
    try:
        report = report_data_service.fetch_most_recent_market_sm_report()
        if not report:
            return MarketSocialMediaResponse(market_sm_report=None)
        return MarketSocialMediaResponse(market_sm_report=report)
    except Exception as e:
        logging.error(f"Error fetching market social media report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-most-recent-crypto-analysis-report", response_model=CryptoAnalysisResponse)
async def fetch_most_recent_crypto_analysis_report():
    """
    Fetch the most recent crypto analysis report.

    Returns:
        CryptoAnalysisResponse: An object containing the most recent crypto analysis report.
    """
    try:
        report = report_data_service.fetch_most_recent_crypto_analysis_report()
        if not report:
            return CryptoAnalysisResponse(crypto_analysis_report=None)
        return CryptoAnalysisResponse(crypto_analysis_report=report)
    except Exception as e:
        logging.error(f"Error fetching crypto analysis report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-most-recent-crypto-news-report", response_model=CryptoNewsResponse)
async def fetch_most_recent_crypto_news_report():
    """
    Fetch the most recent crypto news report.

    Returns:
        CryptoNewsResponse: An object containing the most recent crypto news report.
    """
    try:
        report = report_data_service.fetch_most_recent_crypto_news_report()
        if not report:
            return CryptoNewsResponse(crypto_news_report=None)
        return CryptoNewsResponse(crypto_news_report=report)
    except Exception as e:
        logging.error(f"Error fetching crypto news report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-most-recent-crypto-social-media-report", response_model=CryptoSocialMediaResponse)
async def fetch_most_recent_crypto_sm_report():
    """
    Fetch the most recent crypto social media report.

    Returns:
        CryptoSocialMediaResponse: An object containing the most recent crypto social media report.
    """
    try:
        report = report_data_service.fetch_most_recent_crypto_sm_report()
        if not report:
            return CryptoSocialMediaResponse(crypto_sm_report=None)
        return CryptoSocialMediaResponse(crypto_sm_report=report)
    except Exception as e:
        logging.error(f"Error fetching crypto social media report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consolidated-risk-profile", response_model=ConsolidatedRiskProfileResponse)
async def get_consolidated_risk_profile():
    """
    Get the consolidated risk profile based on the most recent reports across all collections.
    
    This endpoint analyzes the most recent report from each collection (market analysis, 
    market news, market social media, crypto analysis, crypto news, crypto social media)
    and determines the most commonly used risk profile.
    
    Returns:
        ConsolidatedRiskProfileResponse: A dictionary containing:
            - counts: The count of each risk profile found across all reports
            - result: The determined risk profile based on the counts and tiebreaker rules
    """
    try:
        consolidated_profile = report_data_service.get_consolidated_risk_profile()
        return ConsolidatedRiskProfileResponse(**consolidated_profile)
    except Exception as e:
        logging.error(f"Error fetching consolidated risk profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))