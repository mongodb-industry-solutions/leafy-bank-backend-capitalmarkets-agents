from agents.agent_market_analysis_graph import create_workflow_graph as create_agent_market_analysis_graph
from agents.tools.states.agent_market_analysis_state import MarketAnalysisAgentState

from agents.agent_market_news_graph import create_workflow_graph as create_agent_market_news_graph
from agents.tools.states.agent_market_news_state import MarketNewsAgentState

from agents.agent_crypto_analysis_graph import create_workflow_graph as create_agent_crypto_analysis_graph
from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState

from agents.agent_crypto_social_media_graph import create_workflow_graph as create_agent_crypto_news_graph
from agents.tools.states.agent_crypto_social_media_state import CryptoSocialMediaAgentState

from agents.agent_market_social_media_graph import create_workflow_graph as create_agent_market_social_media_graph
from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState

from agents.tools.persist_report import PersistReportInMongoDB

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import time
import logging
import datetime as dt
from datetime import timezone

from scheduler import Scheduler
import pytz

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ScheduledAgents:
    def __init__(self):
        """
        Scheduler for running market analysis and market news workflows.
        """
        self.utc = pytz.UTC
        self.scheduler = Scheduler(tzinfo=timezone.utc)
        logger.info("ScheduledAgents initialized")

    def run_agent_market_analysis_workflow(self) -> dict:
        """
        Runs the market analysis workflow using the MarketAnalysisAgentState.
        This function creates an initial state for the workflow, invokes the workflow graph,
        and saves the final state to MongoDB.

        Returns:
            dict: A dictionary containing the status of the workflow execution.

        Raises:
            Exception: If an error occurs during the workflow execution.
        """

        try: 
            # Initial state for the workflow
            initial_state = MarketAnalysisAgentState(
                portfolio_allocation=[],  # Initialize as an empty list
                report={
                    "asset_trends": [],  # Initialize as an empty list
                    "macro_indicators": [],  # Initialize as an empty list
                    "market_volatility_index": {},  # Initialize as an empty MarketVolatilityIndex
                    "overall_diagnosis": None  # No diagnosis at the start
                },
                next_step="portfolio_allocation_node",  # Start with the portfolio allocation node
                updates=["Starting the market analysis workflow."]  # Initial update message
            )
            
            # Create the workflow graph
            graph = create_agent_market_analysis_graph()
            final_state = graph.invoke(input=initial_state)

            # Print the final state
            logger.info("\nFinal State:")
            logger.info(final_state)

            # Get the collection name from environment variables
            reports_market_analysis_coll = os.getenv("REPORTS_COLLECTION_MARKET_ANALYSIS", "reports_market_analysis")

            # Persist the final state to MongoDB
            # Initialize the PersistReportInMongoDB class
            persist_data = PersistReportInMongoDB(collection_name=reports_market_analysis_coll)
            # Save the market analysis report
            persist_data.save_market_analysis_report(final_state)
            # Return the status of the workflow execution
            return {"status": "Market analysis workflow completed successfully."}
        except Exception as e:
            logger.error(f"Error in run_agent_market_analysis_workflow: {e}")
            return {"status": "Error occurred during market analysis workflow."}

    def run_agent_market_news_workflow(self) -> dict:
        """
        Runs the financial news processing workflow.
        This function creates an initial state for the workflow, invokes the workflow graph,
        and saves the final state to MongoDB.

        Returns:
            dict: A dictionary containing the status of the workflow execution.

        Raises:
            Exception: If an error occurs during the workflow execution.
        """
        try: 
            # Initial state for the workflow
            initial_state = MarketNewsAgentState(
                portfolio_allocation=[],  # Initialize as an empty list
                report={
                    "asset_news": [],  # Initialize as an empty list
                    "asset_news_sentiments": [],  # Initialize as an empty list
                    "overall_news_diagnosis": None  # No diagnosis at the start
                },
                next_step="portfolio_allocation_node",  # Start with the portfolio allocation node
                updates=["Starting the market news workflow."]  # Initial update message
            )
            
            # Create the workflow graph
            graph = create_agent_market_news_graph()
            final_state = graph.invoke(input=initial_state)

            # Print the final state
            logger.info("\nFinal State:")
            logger.info(final_state)

            # Add this after processing the workflow and obtaining final_state
            # Get the collection name from environment variables
            reports_market_news_coll = os.getenv("REPORTS_COLLECTION_MARKET_NEWS", "reports_market_news")

            # Persist the final state to MongoDB
            # Initialize the PersistReportInMongoDB class
            persist_data = PersistReportInMongoDB(collection_name=reports_market_news_coll)
            # Save the market news report
            persist_data.save_market_news_report(final_state)
            # Return the status of the workflow execution
            return {"status": "Market news workflow completed successfully."}
        except Exception as e:
            logger.error(f"Error in run_agent_market_news_workflow: {e}")
            return {"status": "Error occurred during market news workflow."}
        
    def run_agent_crypto_analysis_ws(self) -> dict:
        """
        Runs the crypto analysis workflow using the CryptoAnalysisAgentState.
        This function creates an initial state for the workflow, invokes the workflow graph,
        and saves the final state to MongoDB.

        Returns:
            dict: A dictionary containing the status of the workflow execution.

        Raises:
            Exception: If an error occurs during the workflow execution.
        """
        try:
            # Initial state for the workflow
            initial_state = CryptoAnalysisAgentState(
                portfolio_allocation=[],  # Initialize as an empty list
                report={
                    "crypto_analysis": [],  # Initialize as an empty list
                    "overall_crypto_diagnosis": None  # No diagnosis at the start
                },
                next_step="portfolio_allocation_node",  # Start with the portfolio allocation node
                updates=["Starting the crypto analysis workflow."]  # Initial update message
            )
            
            # Create the workflow graph
            graph = create_agent_crypto_analysis_graph()
            final_state = graph.invoke(input=initial_state)

            # Print the final state
            logger.info("\nFinal State:")
            logger.info(final_state)

            # Get the collection name from environment variables
            reports_crypto_analysis_coll = os.getenv("REPORTS_COLLECTION_CRYPTO_ANALYSIS", "reports_crypto_analysis")

            # Persist the final state to MongoDB
            # Initialize the PersistReportInMongoDB class
            persist_data = PersistReportInMongoDB(collection_name=reports_crypto_analysis_coll)
            # Save the crypto analysis report
            persist_data.save_crypto_analysis_report(final_state)
            # Return the status of the workflow execution
            return {"status": "Crypto analysis workflow completed successfully."}
        except Exception as e:
            logger.error(f"Error in run_agent_crypto_analysis_ws: {e}")
            return {"status": "Error occurred during crypto analysis workflow."}
               
    def run_agent_crypto_sm_ws(self) -> dict:
        """
        Runs the crypto news workflow using the CryptoSocialMediaAgentState.
        This function creates an initial state for the workflow, invokes the workflow graph,
        and saves the final state to MongoDB.

        Returns:
            dict: A dictionary containing the status of the workflow execution.

        Raises:
            Exception: If an error occurs during the workflow execution.
        """
        try:
            # Initial state for the workflow
            initial_state = CryptoSocialMediaAgentState(
                portfolio_allocation=[],  # Initialize as an empty list
                report={
                    "asset_subreddits": [],  # Initialize as an empty list
                    "asset_sm_sentiments": []  # Initialize as an empty list
                },
                next_step="portfolio_allocation_node",  # Start with the portfolio allocation node
                updates=["Starting the crypto social media workflow."]  # Initial update message
            )
            
            # Create the workflow graph
            graph = create_agent_crypto_news_graph()
            final_state = graph.invoke(input=initial_state)

            # Print the final state
            logger.info("\nFinal State:")
            logger.info(final_state)

            # Get the collection name from environment variables
            reports_crypto_sm_coll = os.getenv("REPORTS_COLLECTION_CRYPTO_SM", "reports_crypto_sm")

            # Persist the final state to MongoDB
            # Initialize the PersistReportInMongoDB class
            persist_data = PersistReportInMongoDB(collection_name=reports_crypto_sm_coll)
            # Save the crypto social media sentiment report
            persist_data.save_crypto_sm_report(final_state)
            # Return the status of the workflow execution
            return {"status": "Crypto analysis workflow completed successfully."}
        except Exception as e:
            logger.error(f"Error in run_agent_crypto_analysis_ws: {e}")
            return {"status": "Error occurred during crypto analysis workflow."}
                   
    def run_agent_market_sm_ws(self) -> dict:
        """
        Runs the market social media workflow using the MarketSocialMediaAgentState.
        This function creates an initial state for the workflow, invokes the workflow graph,
        and saves the final state to MongoDB.

        Returns:
            dict: A dictionary containing the status of the workflow execution.

        Raises:
            Exception: If an error occurs during the workflow execution.
        """
        try:
            # Initial state for the workflow
            initial_state = MarketSocialMediaAgentState(
                portfolio_allocation=[],  # Initialize as an empty list
                report={
                    "asset_subreddits": [],  # Initialize as an empty list
                    "asset_sm_sentiments": []  # Initialize as an empty list
                },
                next_step="portfolio_allocation_node",  # Start with the portfolio allocation node
                updates=["Starting the market social media workflow."]  # Initial update message
            )

            # Create the workflow graph
            graph = create_agent_market_social_media_graph()
            final_state = graph.invoke(input=initial_state)

            # Print the final state
            logger.info("\nFinal State:")
            logger.info(final_state)

            # Get the collection name from environment variables
            reports_market_sm_coll = os.getenv("REPORTS_COLLECTION_MARKET_SM", "reports_market_sm")

            # Persist the final state to MongoDB
            # Initialize the PersistReportInMongoDB class
            persist_data = PersistReportInMongoDB(collection_name=reports_market_sm_coll)
            # Save the market social media sentiment report
            persist_data.save_market_sm_report(final_state)
            # Return the status of the workflow execution
            return {"status": "Market social media workflow completed successfully."}
        except Exception as e:
            logger.error(f"Error in run_agent_market_sm_ws: {e}")
            return {"status": "Error occurred during market social media workflow."}

    def schedule_jobs(self):
        """
        Schedules the jobs for the market analysis and market news workflows.
        """
        # Define the schedule for the market analysis workflow
        agent_market_analysis_workflow_time = dt.time(hour=5, minute=0, tzinfo=timezone.utc)
        self.scheduler.daily(agent_market_analysis_workflow_time, self.run_agent_market_analysis_workflow)
        # Define the schedule for the market news workflow
        agent_market_news_workflow_time = dt.time(hour=5, minute=10, tzinfo=timezone.utc)
        self.scheduler.daily(agent_market_news_workflow_time, self.run_agent_market_news_workflow)
        # Define the schedule for the crypto analysis workflow
        agent_crypto_analysis_workflow_time = dt.time(hour=7, minute=0, tzinfo=timezone.utc)
        self.scheduler.daily(agent_crypto_analysis_workflow_time, self.run_agent_crypto_analysis_ws)
        
        logger.info("Scheduled jobs configured!")

    def start(self):
        """
        Starts the scheduler.
        """
        self.schedule_jobs()
        logger.info("Schedule Jobs overview:")
        logger.info(self.scheduler)
        while True:
            self.scheduler.exec_jobs()
            time.sleep(1)
