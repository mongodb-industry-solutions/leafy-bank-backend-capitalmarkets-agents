import logging
from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from service_loader import LoaderService

from service_market_data import MarketDataService
from service_portfolio_data import PortfolioDataService
from service_macro_indicators_data import MacroIndicatorDataService
from service_financial_news_data import FinancialNewsDataService
from backend.vector_store_mdb import VectorStoreMongoDB

from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@app.get("/")
async def read_root(request: Request):
    return {"message": "Server is running"}

# Initialize services
loader_service = LoaderService()
market_data_service = MarketDataService()
portfolio_data_service = PortfolioDataService()
macro_indicator_data_service = MacroIndicatorDataService()
financial_news_data_service = FinancialNewsDataService()
vector_store_query = VectorStoreMongoDB()

class DateRequest(BaseModel):
    date_str: str

    @field_validator('date_str')
    def validate_date_str(cls, value):
        if not value.isdigit() or len(value) != 8:
            raise ValueError("date_str must be in '%Y%m%d' format")

        date = datetime.strptime(value, "%Y%m%d")
        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")

        if value >= current_date:
            raise ValueError(
                "date_str cannot be the current date or a future date")

        return value

@app.post("/load-yfinance-market-data")
async def load_yfinance_market_data(date_str: DateRequest):
    """
    Load Yahoo Finance market data for the given date.

    Args:
        date_str (DateRequest): The request body containing the date in "%Y%m%d" format.

    Returns:
        dict: A message indicating the process completion.
    """
    try:
        loader_service.load_yfinance_market_data(date_str.date_str)
        return {"message": f"Yahoo Finance market data loading process completed for date {date_str.date_str}"}
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Error loading Yahoo Finance market data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-pyfredapi-macroeconomic-data")
async def load_pyfredapi_macroeconomic_data(date_str: DateRequest):
    """
    Load PyFredAPI macroeconomic data for the given date.

    Args:
        date_str (DateRequest): The request body containing the date in "%Y%m%d" format.

    Returns:
        dict: A message indicating the process completion.
    """
    try:
        loader_service.load_pyfredapi_macroeconomic_data(date_str.date_str)
        return {"message": f"PyFredAPI macroeconomic data loading process completed for date {date_str.date_str}"}
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Error loading PyFredAPI macroeconomic data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-recent-financial-news")
async def load_recent_financial_news():
    """
    Load recent financial news data.

    Args:
        request (Request): The request object.

    Returns:
        dict: A message indicating the process completion.
    """
    try:
        loader_service.load_recent_financial_news()
        return {"message": "Financial News processing completed"}
    except Exception as e:
        logging.error(f"Error loading recent financial news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-assets-close-price")
async def fetch_assets_close_price():
    """
    Fetch the latest close price for all assets.

    Returns:
        dict: A dictionary containing the assets and their close prices.
    """
    try:
        close_prices = market_data_service.fetch_assets_close_price()
        return close_prices
    except Exception as e:
        logging.error(f"Error fetching assets close price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-portfolio-allocation")
async def fetch_portfolio_allocation():
    """
    Fetch portfolio allocation data.

    Returns:
        dict: A dictionary containing the portfolio allocation data.
    """
    try:
        portfolio_allocation = portfolio_data_service.fetch_portfolio_allocation()
        return portfolio_allocation
    except Exception as e:
        logging.error(f"Error fetching portfolio allocation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-most-recent-macro-indicators")
async def fetch_most_recent_macro_indicators():
    """
    Fetch the most recent macroeconomic indicators.

    Returns:
        dict: A dictionary containing the most recent macroeconomic indicators.
    """
    try:
        macro_indicators = macro_indicator_data_service.fetch_most_recent_macro_indicators()
        return macro_indicators
    except Exception as e:
        logging.error(f"Error fetching most recent macro indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calc-overall-sentiment-for-all")
async def calc_overall_sentiment_for_all():
    """
    Calculate the overall sentiment score for all symbols.

    Returns:
        dict: A dictionary containing the symbol, overall sentiment score, category, and number of articles.
    """
    try:
        sentiment_scores = financial_news_data_service.calc_overall_sentiment_for_all()
        return sentiment_scores
    except Exception as e:
        logging.error(f"Error calculating overall sentiment for all symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class SymbolRequest(BaseModel):
    symbol: str

@app.post("/calc-overall-sentiment-for-symbol")
async def calc_overall_sentiment_for_symbol(request: SymbolRequest):
    """
    Calculate the overall sentiment score for a specific symbol.

    Args:
        request (SymbolRequest): The request body containing the symbol.

    Returns:
        dict: A dictionary containing the symbol, overall sentiment score, category, and number of articles.
    """
    try:
        sentiment_score = financial_news_data_service.calc_overall_sentiment_for_symbol(request.symbol)
        return sentiment_score
    except Exception as e:
        logging.error(f"Error calculating overall sentiment for symbol {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class ArticleQueryRequest(BaseModel):
    query: str
    n: int = 10

@app.post("/lookup-articles")
async def lookup_articles_endpoint(request: ArticleQueryRequest):
    """
    Look up articles in the vector store based on the query.

    Args:
        request (ArticleQueryRequest): The request body containing the query and number of articles to return.

    Returns:
        str: A string representation of the search results.
    """
    try:
        result = vector_store_query.lookup_articles(query=request.query, n=request.n)
        return result
    except Exception as e:
        logging.error(f"Error looking up articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))