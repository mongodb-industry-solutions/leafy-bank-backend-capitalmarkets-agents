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
    REAINTRATREARAT10Y: MacroIndicator

class MessageResponse(BaseModel):
    macro_indicators: MacroIndicatorsResponse = None


### Macro Indicators Data Endpoints ###

@router.post("/fetch-most-recent-macro-indicators", response_model=MessageResponse)
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