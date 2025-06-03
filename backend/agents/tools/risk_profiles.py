import logging
import os
from dotenv import load_dotenv
from db.mdb import MongoDBConnector

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class RiskProfiles(MongoDBConnector):
    def __init__(self, collection_name: str = None, uri: str = None, database_name: str = None, appname: str = None):
        """
        RiskProfiles class to retrieve and update risk profiles from MongoDB.

        Args:
            collection_name (str, optional): The collection name. Defaults to the RISK_PROFILES_COLLECTION env variable.
            uri (str, optional): MongoDB URI. Defaults to parent class value.
            database_name (str, optional): Database name. Defaults to parent class value.
            appname (str, optional): Application name. Defaults to parent class value.
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name or os.getenv("RISK_PROFILES_COLLECTION", "risk_profiles")
        self.collection = self.get_collection(self.collection_name)
        # Ensure unique index on risk_id
        self.collection.create_index("risk_id", unique=True)
        logger.info("RiskProfiles initialized")

    def _get_default_profile(self) -> dict:
        """
        Retrieve the default risk profile (with risk_id 'BALANCE').

        Returns:
            dict: The default risk profile document.

        Raises:
            ValueError: If the default profile is not found.
        """
        default = self.collection.find_one({"risk_id": "BALANCE"})
        if default:
            logger.info("Default risk profile 'BALANCE' retrieved.")
            return default
        else:
            logger.error("Default risk profile 'BALANCE' not found.")
            raise ValueError("Default risk profile 'BALANCE' not found.")

    def get_active_risk_profile(self) -> dict:
        """
        Retrieve the single active risk profile from the collection.
        This method ensures that exactly one profile is active.
        In case of error, it returns the default risk profile.

        Returns:
            dict: The active risk profile document or the default one if an error occurs.

        Raises:
            Exception: The original exception if the default profile cannot be retrieved.
        """
        try:
            active_profiles = list(self.collection.find({"active": True}))
            if len(active_profiles) == 1:
                logger.info("Successfully retrieved the active risk profile.")
                return active_profiles[0]
            elif len(active_profiles) == 0:
                logger.error("No active risk profile found.")
                raise ValueError("No active risk profile found.")
            else:
                logger.error("Multiple active risk profiles found. There must be exactly one active risk profile.")
                raise ValueError("Multiple active risk profiles found.")
        except Exception as e:
            logger.exception("Error retrieving active risk profile. Returning default profile 'BALANCE'.")
            try:
                return self._get_default_profile()
            except Exception as ex:
                raise e from ex

    def set_active_risk_profile(self, risk_id: str) -> dict:
        """
        Set a specific risk profile as active and mark the rest as inactive.
        In case of error, returns the default risk profile.
        
        Args:
            risk_id (str): The risk_id of the profile to be set as active.
        
        Returns:
            dict: The updated active risk profile document or the default profile if an error occurs.
        
        Raises:
            Exception: The original exception if an error occurs and default profile retrieval fails.
        """
        try:
            # Deactivate all profiles
            deactivation_result = self.collection.update_many(
                {"active": True},
                {"$set": {"active": False}}
            )
            logger.info("Deactivated %d profiles.", deactivation_result.modified_count)

            # Activate the profile with the specified risk_id
            activation_result = self.collection.update_one(
                {"risk_id": risk_id},
                {"$set": {"active": True}}
            )
            if activation_result.modified_count == 0:
                logger.error("Risk profile with risk_id '%s' not found or already active.", risk_id)
                raise ValueError(f"Risk profile with risk_id '{risk_id}' not found.")

            updated_profile = self.collection.find_one({"risk_id": risk_id})
            if not updated_profile:
                logger.error("Could not retrieve the risk profile with risk_id '%s' after update.", risk_id)
                raise ValueError(f"Could not retrieve the risk profile with risk_id '{risk_id}' after update.")

            logger.info("Successfully set risk profile '%s' as active.", risk_id)
            return updated_profile
        except Exception as e:
            logger.exception("Error setting active risk profile. Returning default profile 'BALANCE'.")
            try:
                return self._get_default_profile()
            except Exception as ex:
                raise e from ex

# ==================
# Example usage
# ==================
if __name__ == "__main__":
    profiler = RiskProfiles()
    try:
        active_profile = profiler.get_active_risk_profile()
        logger.info("Current active risk profile: %s", active_profile)
    except Exception as error:
        logger.error(error)

    try:
        new_active_profile = profiler.set_active_risk_profile("BALANCE")
        logger.info("New active risk profile: %s", new_active_profile)
    except Exception as error:
        logger.error(error)