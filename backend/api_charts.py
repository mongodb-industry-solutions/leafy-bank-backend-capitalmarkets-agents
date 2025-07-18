from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
from service_chart_mappings import ChartMappingsDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
chart_mappings_data_service = ChartMappingsDataService()

# Create the router
router = APIRouter(prefix="/charts", tags=["Charts Data"])

class ChartPeriod(BaseModel):
    day: str
    week: str
    month: str

class MessageResponse(BaseModel):
    chart_mappings: dict[str, ChartPeriod]

### Charts Data Endpoints ###

@router.get("/fetch-chart-mappings", response_model=MessageResponse)
async def fetch_chart_mappings():
    """
    Fetch chart mappings from the database.

    Returns:
        MessageResponse: Object containing chart mappings data.
    """
    try:
        chart_mappings = chart_mappings_data_service.fetch_chart_mappings()
        return MessageResponse(chart_mappings=chart_mappings)
    except Exception as e:
        logging.error(f"Error fetching chart mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))