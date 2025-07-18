from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
from service_macro_indicators_data import MacroIndicatorDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
macro_indicator_data_service = MacroIndicatorDataService()

# Create the router
router = APIRouter(prefix="/macro-indicators", tags=["Macro Indicators Data"])

class MacroIndicator(BaseModel):
    title: str
    frequency: str
    frequency_short: str
    units: str
    units_short: str
    date: datetime
    value: float

class MacroIndicatorsResponse(BaseModel):
    GDP: MacroIndicator
    UNRATE: MacroIndicator
    DFF: MacroIndicator

class MessageResponse(BaseModel):
    macro_indicators: MacroIndicatorsResponse = None

class MacroIndicatorTrend(BaseModel):
    title: str
    arrow_direction: str
    latest_value: float
    latest_date: datetime
    previous_value: float
    previous_date: datetime

class MacroIndicatorsTrendResponse(BaseModel):
    GDP: MacroIndicatorTrend = None
    UNRATE: MacroIndicatorTrend = None
    DFF: MacroIndicatorTrend = None

class TrendMessageResponse(BaseModel):
    trend_indicators: dict = None


### Macro Indicators Data Endpoints ###

@router.get("/fetch-most-recent-macro-indicators", response_model=MessageResponse)
async def fetch_most_recent_macro_indicators():
    """
    Fetch the most recent macroeconomic indicators.

    Returns:
        MessageResponse: Object containing macro indicator data.
    """
    try:
        macro_indicators = macro_indicator_data_service.fetch_most_recent_macro_indicators()
        return MessageResponse(macro_indicators=macro_indicators)
    except Exception as e:
        logging.error(f"Error fetching most recent macro indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/fetch-macro-indicators-trend", response_model=TrendMessageResponse)
async def get_macro_indicators_trend():
    """
    Get the trend direction for each macroeconomic indicator by comparing the two most recent values.
    
    Returns:
        TrendMessageResponse: Object containing trend information for each macro indicator.
    """
    try:
        trend_indicators = macro_indicator_data_service.get_macro_indicators_trend()
        return TrendMessageResponse(trend_indicators=trend_indicators)
    except Exception as e:
        logging.error(f"Error fetching macro indicators trend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))