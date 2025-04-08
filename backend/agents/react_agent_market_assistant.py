import os
import asyncio
from dotenv import load_dotenv
from agent_llm import get_llm
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from tools.vogayeai.vogaye_ai_embeddings import VogayeAIEmbeddings
from tools.db.mdb import MongoDBConnector

from datetime import datetime, timezone

from pymongo import AsyncMongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from rich.console import Console

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize dotenv to load environment variables
load_dotenv()

# Initialize Rich for better output formatting and visualization
rich = Console()

# Initialize ChatBedrock LLM
llm = get_llm()

# Initialize Tavily
tavily = TavilySearchResults(max_results=3)

# Initialize the VoyageAI embeddings generator
embedding_model_id = os.getenv("EMBEDDINGS_MODEL_ID", "voyage-finance-2")
ve = VogayeAIEmbeddings(api_key=os.getenv("VOYAGE_API_KEY"))

# Initialize MongoDB collections for reports
market_collection_name = os.getenv("REPORTS_COLLECTION_MARKET_ANALYSIS", "reports_market_analysis")
news_collection_name = os.getenv("REPORTS_COLLECTION_MARKET_NEWS", "reports_market_news")
mongodb_connector = MongoDBConnector()
market_collection = mongodb_connector.get_collection(market_collection_name)
news_collection = mongodb_connector.get_collection(news_collection_name)

# Function to generate a new thread_id
def generate_thread_id():
    """Generate a unique thread_id based on current timestamp"""
    return f"thread_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

# Function to list available threads
async def list_available_threads(memory_collection):
    """List all available thread_ids from the MongoDB memory store"""
    threads = set()
    
    # Query all distinct thread_ids (which is a top-level field)
    try:
        cursor = memory_collection.find({}, {"thread_id": 1})
        async for doc in cursor:
            if "thread_id" in doc and doc["thread_id"]:
                threads.add(doc["thread_id"])
    except Exception as e:
        rich.print(f"[bright_red]Error retrieving thread IDs: {str(e)}[/bright_red]")
    
    return sorted(list(threads))  # Return sorted list of thread_ids

@tool
def market_analysis_reports_vector_search_tool(query: str, k: int = 1):
    """
    Perform a vector similarity search on market analysis reports for the CURRENT PORTFOLIO.
    
    IMPORTANT: This tool provides market analysis ONLY for assets in the current portfolio allocation.
    It is important to note that this tool DOES NOT provide real-time data or live updates.
    If someone asks for real-time data or live updates regarding assets that are not in the current portfolio, use the Tavily Search tool.
    
    Use this tool when you need:
    - Market trends and analysis for assets in the portfolio
    - Recent portfolio performance insights
    - Macroeconomic factors affecting the current portfolio
    - Asset-specific diagnostics for portfolio holdings
    
    Args:
        query (str): The search query about portfolio assets, market trends, etc.
        k (int, optional): Number of top results to return. Defaults to 1.
        
    Returns:
        dict: Contains relevant sections from the most recent market analysis report
             for the current portfolio.
    """
    try:
        rich.print(f"\n[Action] Searching portfolio market analysis for: {query}")
        
        # Get the most recent document for context information only
        most_recent = market_collection.find_one(
            {}, 
            sort=[("timestamp", -1)]
        )
        
        if not most_recent:
            return {"results": "No market analysis reports found for the current portfolio."}
        
        # Generate query embedding
        query_embedding = ve.get_embeddings(model_id=embedding_model_id, text=query)
        
        # Extract the date of the most recent report
        report_date = most_recent.get("date_string", "Unknown date")
        
        # Get portfolio assets list for context
        portfolio_assets = []
        try:
            for allocation in most_recent.get("portfolio_allocation", []):
                asset = allocation.get("asset", "Unknown")
                description = allocation.get("description", "")
                allocation_pct = allocation.get("allocation_percentage", "")
                portfolio_assets.append(f"{asset} ({description}): {allocation_pct}")
        except Exception as e:
            logger.error(f"Error extracting portfolio information: {e}")
        
        # Perform vector search across all documents
        pipeline = [
            {
                "$vectorSearch": {
                    "index": f"{market_collection_name}_report_vector_index",
                    "path": "report_embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 5,
                    "limit": k
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date_string": 1,
                    "report": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(market_collection.aggregate(pipeline))
        
        # If no results from vector search, just return the most recent document
        if not results:
            # Extract relevant information
            overall_diagnosis = most_recent.get("report", {}).get("overall_diagnosis", "No diagnosis available")
            asset_trends = most_recent.get("report", {}).get("asset_trends", [])
            asset_insights = []
            
            # Format asset trends information
            for trend in asset_trends[:5]:  # Limit to 5 assets for readability
                asset = trend.get("asset", "Unknown")
                diagnosis = trend.get("diagnosis", "No diagnosis")
                asset_insights.append(f"{asset}: {diagnosis}")
            
            return {
                "report_date": report_date,
                "portfolio_assets": portfolio_assets[:5],  # Show top 5 portfolio assets
                "overall_diagnosis": overall_diagnosis,
                "asset_insights": asset_insights,
                "note": "This is the most recent market analysis for your portfolio."
            }
        
        # Process vector search results
        report_data = results[0]
        overall_diagnosis = report_data.get("report", {}).get("overall_diagnosis", "No diagnosis available")
        
        # Format the return data
        return {
            "report_date": report_date,
            "portfolio_assets": portfolio_assets[:5],  # Show top 5 portfolio assets
            "overall_diagnosis": overall_diagnosis,
            "note": "This information is from relevant portfolio market analysis reports."
        }
        
    except Exception as e:
        rich.print(f"[bright_red]Error searching portfolio market reports: {str(e)}[/bright_red]")
        return {"error": f"An error occurred: {str(e)}"}


@tool
def market_news_reports_vector_search_tool(query: str, k: int = 1):
    """
    Perform a vector similarity search on market news reports for the CURRENT PORTFOLIO.
    
    IMPORTANT: This tool provides market news summary and insights ONLY for assets in the current portfolio allocation.
    It is important to note that this tool DOES NOT provide real-time data or live updates.
    If someone asks for real-time data or live updates regarding assets that are not in the current portfolio, use the Tavily Search tool.
    
    Use this tool when you need:
    - Recent news affecting portfolio assets
    - Sentiment analysis for portfolio holdings
    - News summaries for specific assets in the portfolio
    - Overall news impact on the current portfolio
    
    Args:
        query (str): The search query about news related to portfolio assets.
        k (int, optional): Number of top results to return. Defaults to 1.
        
    Returns:
        dict: Contains relevant news summaries from the most recent news report
             for the current portfolio.
    """
    try:
        rich.print(f"\n[Action] Searching portfolio news reports for: {query}")
        
        # Get the most recent document for context information only
        most_recent = news_collection.find_one(
            {}, 
            sort=[("timestamp", -1)]
        )
        
        if not most_recent:
            return {"results": "No news reports found for the current portfolio."}
        
        # Generate query embedding
        query_embedding = ve.get_embeddings(model_id=embedding_model_id, text=query)
        
        # Extract the date of the most recent report
        report_date = most_recent.get("date_string", "Unknown date")
        
        # Get portfolio assets list for context
        portfolio_assets = []
        try:
            for allocation in most_recent.get("portfolio_allocation", []):
                asset = allocation.get("asset", "Unknown")
                description = allocation.get("description", "")
                allocation_pct = allocation.get("allocation_percentage", "")
                portfolio_assets.append(f"{asset} ({description}): {allocation_pct}")
        except Exception as e:
            logger.error(f"Error extracting portfolio information: {e}")
        
        # Perform vector search across all documents
        pipeline = [
            {
                "$vectorSearch": {
                    "index": f"{news_collection_name}_report_vector_index",
                    "path": "report_embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 5,
                    "limit": k
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date_string": 1,
                    "report.asset_news_summary": 1,
                    "report.overall_news_diagnosis": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(news_collection.aggregate(pipeline))
        
        # If no results from vector search, just return the most recent document
        if not results:
            # Extract relevant information
            overall_diagnosis = most_recent.get("report", {}).get("overall_news_diagnosis", "No news diagnosis available")
            asset_news_summaries = most_recent.get("report", {}).get("asset_news_summary", [])
            
            # Format asset news summary information
            news_summaries = []
            for summary in asset_news_summaries[:3]:  # Limit to 3 assets for readability
                asset = summary.get("asset", "Unknown")
                summary_text = summary.get("summary", "No summary available")
                sentiment = summary.get("overall_sentiment_category", "Unknown")
                news_summaries.append(f"{asset} ({sentiment}): {summary_text}")
            
            return {
                "report_date": report_date,
                "portfolio_assets": portfolio_assets[:5],  # Show top 5 portfolio assets
                "overall_diagnosis": overall_diagnosis,
                "news_summaries": news_summaries,
                "note": "This is the most recent news report for your portfolio."
            }
        
        # Process vector search results
        report_data = results[0]
        report = report_data.get("report", {})
        overall_diagnosis = report.get("overall_news_diagnosis", "No news diagnosis available")
        asset_news_summaries = report.get("asset_news_summary", [])
        
        # Format news summaries
        news_summaries = []
        for summary in asset_news_summaries:
            asset = summary.get("asset", "Unknown")
            summary_text = summary.get("summary", "No summary available")
            sentiment = summary.get("overall_sentiment_category", "Unknown")
            news_summaries.append(f"{asset} ({sentiment}): {summary_text}")
        
        # Format the return data
        return {
            "report_date": report_date,
            "portfolio_assets": portfolio_assets[:5],  # Show top 5 portfolio assets
            "overall_diagnosis": overall_diagnosis,
            "news_summaries": news_summaries[:3],  # Limit to 3 for readability
            "note": "This information is from relevant portfolio news reports."
        }
        
    except Exception as e:
        rich.print(f"[bright_red]Error searching portfolio news reports: {str(e)}[/bright_red]")
        return {"error": f"An error occurred: {str(e)}"}


# Define a function to process chunks from the agent
def process_chunks(chunk):
    """
    Processes a chunk from the agent and displays information about tool calls or the agent's answer.

    Parameters:
        chunk (dict): A dictionary containing information about the agent's messages.

    Returns:
        None

    This function processes a chunk of data to check for agent messages.
    It iterates over the messages and checks for tool calls.
    If a tool call is found, it extracts the tool name and query, then prints a formatted message using the Rich library.
    If no tool call is found, it extracts and prints the agent's answer using the Rich library.
    """

    # Check if the chunk contains an agent's message
    if "agent" in chunk:
        # Iterate over the messages in the chunk
        for message in chunk["agent"]["messages"]:
            # Check if the message contains tool calls
            if "tool_calls" in message.additional_kwargs:
                # If the message contains tool calls, extract and display an informative message with tool call details

                # Extract all the tool calls
                tool_calls = message.additional_kwargs["tool_calls"]

                # Iterate over the tool calls
                for tool_call in tool_calls:
                    # Extract the tool name
                    tool_name = tool_call["function"]["name"]

                    # Extract the tool query
                    tool_arguments = eval(tool_call["function"]["arguments"])
                    tool_query = tool_arguments.get("query", "")

                    # Display an informative message with tool call details
                    rich.print(
                        f"\nThe agent is calling the tool [on deep_sky_blue1]{tool_name}[/on deep_sky_blue1] with the query [on deep_sky_blue1]{tool_query}[/on deep_sky_blue1]. Please wait for the agent's answer[deep_sky_blue1]...[/deep_sky_blue1]",
                        style="deep_sky_blue1",
                    )
            else:
                # If the message doesn't contain tool calls, extract and display the agent's answer

                # Extract the agent's answer
                agent_answer = message.content

                # Display the agent's answer
                rich.print(f"\nAgent:\n{agent_answer}", style="black on white")


# Define an async function to process checkpoints from the memory
async def process_checkpoints(checkpoints):
    """
    Asynchronously processes a list of checkpoints and displays relevant information.
    Each checkpoint consists of a tuple where the first element is the index and the second element is an object
    containing various details about the checkpoint. The function distinguishes between messages from the user
    and the agent, displaying them accordingly.

    Parameters:
        checkpoints (list): A list of checkpoint tuples to process.

    Returns:
        None

    This function processes a list of checkpoints asynchronously.
    It iterates over the checkpoints and displays the following information for each checkpoint:
    - Timestamp
    - Checkpoint ID
    - Messages associated with the checkpoint
    """

    rich.print("\n==========================================================\n")

    # Initialize an empty list to store the checkpoints
    checkpoints_list = []

    # Iterate over the checkpoints and add them to the list in an async way
    async for checkpoint_tuple in checkpoints:
        checkpoints_list.append(checkpoint_tuple)

    # Iterate over the list of checkpoints
    for idx, checkpoint_tuple in enumerate(checkpoints_list):
        # Extract key information about the checkpoint
        checkpoint = checkpoint_tuple.checkpoint
        messages = checkpoint["channel_values"].get("messages", [])

        # Display checkpoint information
        rich.print(f"[white]Checkpoint:[/white]")
        rich.print(f"[black]Timestamp: {checkpoint['ts']}[/black]")
        rich.print(f"[black]Checkpoint ID: {checkpoint['id']}[/black]")

        # Display checkpoint messages
        for message in messages:
            if isinstance(message, HumanMessage):
                rich.print(
                    f"[bright_magenta]User: {message.content}[/bright_magenta] [bright_cyan](Message ID: {message.id})[/bright_cyan]"
                )
            elif isinstance(message, AIMessage):
                rich.print(
                    f"[bright_magenta]Agent: {message.content}[/bright_magenta] [bright_cyan](Message ID: {message.id})[/bright_cyan]"
                )

        rich.print("")

    rich.print("==========================================================")


# Define an async function to chat with the agent
async def main():
    """
    Entry point of the application. Connects to a MongoDB database, initializes a persistent chat memory,
    creates a LangGraph agent, and handles user interaction in a loop until the user chooses to quit.

    Parameters:
        None

    Returns:
        None

    This function performs the following steps:
    1. Connects to the MongoDB database using the AsyncMongoClient.
    2. Initializes a persistent chat memory.
    3. Creates a LangGraph agent with the specified model and tools.
    4. Enters a loop to interact with the user:
       - Prompts the user for a question.
       - Checks if the user wants to quit.
       - Uses the LangGraph agent to get the agent's answer.
       - Processes the chunks from the agent.
       - Lists and processes all checkpoints that match a given configuration.
    """

    # Resource: https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/#using-the-async-mongodb-client
    # Load MONGODB_URI from environment variables
    MONGODB_URI = os.getenv("MONGODB_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    CHECKPOINTS_AIO_COLLECTION = os.getenv("CHECKPOINTS_AIO_COLLECTION", "checkpoints_aio")

    # Initialize the async MongoDB client
    async_mongodb_client = AsyncMongoClient(MONGODB_URI)
    
    # Initialize the async MongoDB collection for memory
    # NOTE: This collection is used for storing checkpoints and messages
    async_mongodb_memory_collection = async_mongodb_client[DATABASE_NAME][CHECKPOINTS_AIO_COLLECTION]

    # Initialize persistent chat memory
    memory = AsyncMongoDBSaver(client=async_mongodb_client, db_name=DATABASE_NAME)

    # Ask user if they want a new thread or to continue an existing one
    rich.print("\nWelcome to the Market Assistant!\n", style="bold green")
    rich.print("Would you like to start a new chat session or continue an existing one?")
    rich.print("1. Start a new chat session")
    rich.print("2. Continue an existing chat session")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    thread_id = None
    
    if choice == "2":
        # List available threads
        threads = await list_available_threads(async_mongodb_memory_collection)
        
        if not threads:
            rich.print("No existing chat sessions found. Starting a new one.", style="yellow")
            thread_id = generate_thread_id()
        else:
            # Display available threads
            rich.print("\nAvailable chat sessions:", style="bold")
            for i, thread in enumerate(threads, 1):
                # Try to extract the datetime from the thread_id for a more readable format
                try:
                    date_part = thread.split('_')[1]
                    time_part = thread.split('_')[2]
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
                    rich.print(f"{i}. Session from {formatted_date} (ID: {thread})")
                except:
                    rich.print(f"{i}. {thread}")
            
            # Let user select a thread
            selection = input("\nEnter the number of the session you want to continue (or 'n' for a new session): ")

            if selection.lower() == 'n':
                thread_id = generate_thread_id()
            else:
                # First check if selection is one of the actual thread_ids in the list
                if selection in threads:
                    thread_id = selection
                else:
                    try:
                        idx = int(selection) - 1
                        if 0 <= idx < len(threads):
                            thread_id = threads[idx]
                        else:
                            rich.print("Invalid selection. Starting a new session.", style="yellow")
                            thread_id = generate_thread_id()
                    except ValueError:
                        rich.print("Invalid input. Starting a new session.", style="yellow")
                        thread_id = generate_thread_id()
    else:
        # Generate a new thread_id
        thread_id = generate_thread_id()
    
    rich.print(f"\nChat session ID: {thread_id}", style="cyan")

    # Create a LangGraph agent with the new tools
    langgraph_agent = create_react_agent(
        model=llm, 
        tools=[
            tavily, 
            market_analysis_reports_vector_search_tool, 
            market_news_reports_vector_search_tool
        ], 
        checkpointer=memory
    )

    # Loop until the user chooses to quit the chat
    while True:
        # Get the user's question and display it in the terminal
        user_question = input("\nUser:\n")

        # Check if the user wants to quit the chat
        if user_question.lower() == "quit":
            rich.print(
                "\nAgent:\nHave a nice day! :wave:\n", style="black on white"
            )
            break

        # Use the async stream method of the LangGraph agent to get the agent's answer
        async for chunk in langgraph_agent.astream(
            {"messages": [HumanMessage(content=user_question)]},
            {"configurable": {"thread_id": thread_id}},  # Use the dynamic thread_id
        ):
            # Process the chunks from the agent
            process_chunks(chunk)

            # Use the async list method of the memory to list all checkpoints that match the current thread_id
            checkpoints = memory.alist({"configurable": {"thread_id": thread_id}})
            # Process the checkpoints from the memory in an async way
            await process_checkpoints(checkpoints)


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())