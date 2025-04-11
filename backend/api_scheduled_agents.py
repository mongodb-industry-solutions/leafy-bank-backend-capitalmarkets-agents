from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from scheduled_agents import ScheduledAgents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service
scheduled_agents_service = ScheduledAgents()

# Create the router
router = APIRouter(prefix="/scheduled-agents", tags=["Scheduled Agents"])

class MessageResponse(BaseModel):
    status: str
    

### Scheduled Agents Endpoints ###

@router.post("/execute-market-analysis-workflow", response_model=MessageResponse)
async def execute_market_analysis_workflow():
    """
    Execute the market analysis workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_market_analysis_workflow()
    except Exception as e:
        logging.error(f"Error executing market analysis workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-market-news-workflow", response_model=MessageResponse)
async def execute_market_news_workflow():
    """
    Execute the market news workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_market_news_workflow()
    except Exception as e:
        logging.error(f"Error executing market news workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    