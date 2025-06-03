from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List
from agents.tools.risk_profiles import RiskProfiles
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the service instance
risk_profiles_service = RiskProfiles()

# Create the router
router = APIRouter(prefix="/risk-profiles", tags=["Risk Profiles"])

class RiskProfile(BaseModel):
    risk_id: str
    short_description: str
    active: bool

@router.get("/", response_model=List[RiskProfile])
def list_risk_profiles():
    """
    List all risk profiles stored in the database.
    """
    try:
        profiles_cursor = risk_profiles_service.collection.find({})
        profiles = []
        for doc in profiles_cursor:
            profiles.append({
                "risk_id": doc["risk_id"],
                "short_description": doc.get("short_description", ""),
                "active": doc["active"]
            })
        return profiles
    except Exception as e:
        logger.exception("Error listing risk profiles.")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active", response_model=RiskProfile)
def get_active_risk_profile():
    """
    Retrieve the currently active risk profile.
    The RiskProfiles class handles fallback to the default profile if needed.
    """
    try:
        profile = risk_profiles_service.get_active_risk_profile()
        return {
            "risk_id": profile["risk_id"],
            "short_description": profile.get("short_description", ""),
            "active": profile["active"]
        }
    except Exception as e:
        logger.exception("Error retrieving active risk profile.")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/active", response_model=RiskProfile)
def set_active_risk_profile(risk_id: str = Body(..., embed=True)):
    """
    Update the active risk profile.
    All existing profiles will be deactivated and the given risk_id will be activated.
    In case of an error, the default profile is returned.
    """
    try:
        updated_profile = risk_profiles_service.set_active_risk_profile(risk_id)
        return {
            "risk_id": updated_profile["risk_id"],
            "short_description": updated_profile.get("short_description", ""),
            "active": updated_profile["active"]
        }
    except Exception as e:
        logger.exception("Error updating active risk profile.")
        raise HTTPException(status_code=500, detail=str(e))