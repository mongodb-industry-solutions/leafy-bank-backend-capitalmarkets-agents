from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import threading
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
        return scheduled_agents_service.run_agent_market_analysis_wf()
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
        return scheduled_agents_service.run_agent_market_news_wf()
    except Exception as e:
        logging.error(f"Error executing market news workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-market-social-media-workflow", response_model=MessageResponse)
async def execute_market_social_media_workflow():
    """
    Execute the market social media workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_market_sm_wf()
    except Exception as e:
        logging.error(f"Error executing market social media workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/execute-crypto-analysis-workflow", response_model=MessageResponse)
async def execute_crypto_analysis_workflow():
    """
    Execute the crypto analysis workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_crypto_analysis_wf()
    except Exception as e:
        logging.error(f"Error executing crypto analysis workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/execute-crypto-news-workflow", response_model=MessageResponse)
async def execute_crypto_news_workflow():
    """
    Execute the crypto news workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_crypto_news_wf()
    except Exception as e:
        logging.error(f"Error executing crypto news workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/execute-crypto-social-media-workflow", response_model=MessageResponse)
async def execute_crypto_social_media_workflow():
    """
    Execute the crypto social media workflow.

    Returns:
        dict: A dictionary containing the status of the workflow execution.
    """
    try:
        return scheduled_agents_service.run_agent_crypto_sm_wf()
    except Exception as e:
        logging.error(f"Error executing crypto social media workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

##############################
## -- SCHEDULER OVERVIEW -- ##
##############################

@router.post("/scheduler-overview")
async def scheduler_overview():
    try:
        overview = str(scheduler.scheduler)
        overview_lines = overview.split("\n")
        overview_dict = {
            "max_exec": overview_lines[0].split(",")[0].split("=")[1].strip(),
            "tzinfo": overview_lines[0].split(",")[1].split("=")[1].strip(),
            "priority_function": overview_lines[0].split(",")[2].split("=")[1].strip(),
            "jobs": []
        }
        for line in overview_lines[3:]:
            if line.strip() and not line.startswith("--------"):
                parts = line.split()
                if len(parts) >= 8:
                    job = {
                        "type": parts[0],
                        "function": parts[1],
                        "due_at": f"{parts[2]} {parts[3]}",
                        "tzinfo": parts[4],
                        "due_in": parts[5]
                    }
                    # Replace function names
                    if job["function"] == "#is_workflow(..)":
                        job["function"] = "run_agent_market_analysis_wf"
                    elif job["function"] == "#ws_workflow(..)":
                        job["function"] = "run_agent_market_news_wf"
                    elif job["function"] == "#analysis_ws(..)":
                        job["function"] = "run_agent_crypto_analysis_wf"
                    elif job["function"] == "#arket_sm_ws(..)":
                        job["function"] = "run_agent_market_sm_wf"
                    elif job["function"] == "#pto_news_ws(..)":
                        job["function"] = "run_agent_crypto_news_wf"
                    elif job["function"] == "#rypto_sm_ws(..)":
                        job["function"] = "run_agent_crypto_sm_wf"
                    
                    # Add "d" to single digit due_in values
                    if job["due_in"].isdigit():
                        job["due_in"] += "d"
                    
                    overview_dict["jobs"].append(job)
                else:
                    job = {
                        "type": parts[0] if len(parts) > 0 else "",
                        "function": parts[1] if len(parts) > 1 else "",
                        "due_at": f"{parts[2]} {parts[3]}" if len(parts) > 3 else "",
                        "tzinfo": parts[4] if len(parts) > 4 else "",
                        "due_in": parts[5] if len(parts) > 5 else ""
                    }
                    # Replace function names
                    if job["function"] == "#is_workflow(..)":
                        job["function"] = "run_agent_market_analysis_wf"
                    elif job["function"] == "#ws_workflow(..)":
                        job["function"] = "run_agent_market_news_wf"
                    elif job["function"] == "#analysis_ws(..)":
                        job["function"] = "run_agent_crypto_analysis_wf"
                    elif job["function"] == "#arket_sm_ws(..)":
                        job["function"] = "run_agent_market_sm_wf"
                    elif job["function"] == "#pto_news_ws(..)":
                        job["function"] = "run_agent_crypto_news_wf"
                    elif job["function"] == "#rypto_sm_ws(..)":
                        job["function"] = "run_agent_crypto_sm_wf"
                    
                    # Add "d" to single digit due_in values
                    if job["due_in"].isdigit():
                        job["due_in"] += "d"
                    
                    overview_dict["jobs"].append(job)
        return {"overview": overview_dict}
    except Exception as e:
        logger.error(f"Error generating scheduler overview: {e}")
        return {"error": "Failed to generate scheduler overview"}

def start_scheduler():
    scheduler.start()

scheduler = ScheduledAgents()
scheduler_thread = threading.Thread(target=start_scheduler)
scheduler_thread.start()