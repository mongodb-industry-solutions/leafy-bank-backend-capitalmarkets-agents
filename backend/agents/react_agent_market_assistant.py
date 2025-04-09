import os
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from agents.tools.bedrock.client import BedrockClient
from pymongo import AsyncMongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# Tools
from agents.react_agent_market_assistant_tools import tavily_search_tool, market_analysis_reports_vector_search_tool, market_news_reports_vector_search_tool

# Initialize dotenv to load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MarketAssistantReactAgent:
    """
    Service class for the Market Assistant React Agent.
    Provides methods for creating and managing chat sessions with the agent.
    """
    
    def __init__(self):
        """Initialize the Market Assistant React Agent service."""
        # Load MongoDB configuration from environment variables
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("DATABASE_NAME")
        self.checkpoints_collection = os.getenv("CHECKPOINTS_AIO_COLLECTION", "checkpoints_aio")
        self.checkpoint_writes_collection = os.getenv("CHECKPOINTS_WRITES_AIO_COLLECTION", "checkpoint_writes_aio")
        
        # Instantiate Bedrock client
        bedrock_client = BedrockClient()._get_bedrock_client()

        # Initialize LLM
        self.chat_completion_model_id = os.getenv("CHAT_COMPLETIONS_MODEL_ID")
        self.llm = ChatBedrock(model=self.chat_completion_model_id,
                client=bedrock_client,
                temperature=0)
        
        # Initialize async MongoDB client
        self.async_mongodb_client = AsyncMongoClient(self.mongodb_uri)
        self.async_mongodb_memory_collection = self.async_mongodb_client[self.database_name][self.checkpoints_collection]
        self.memory = AsyncMongoDBSaver(client=self.async_mongodb_client, db_name=self.database_name)
        
        # Create the agent with tools - done at initialization to avoid recreation
        self.langgraph_agent = create_react_agent(
            model=self.llm, 
            tools=[
                tavily_search_tool,
                market_analysis_reports_vector_search_tool,
                market_news_reports_vector_search_tool
            ],
            checkpointer=self.memory
        )
        
        logger.info("MarketAssistantReactAgent initialized with LangGraph agent and tools")
    
    def generate_thread_id(self):
        """Generate a unique thread_id based on current timestamp."""
        return f"thread_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    async def list_available_threads(self, limit=3):
        """
        List the most recent thread_ids from the MongoDB memory store.
        
        Args:
            limit (int): Maximum number of threads to return (default: 3)
            
        Returns:
            list: List of the most recent thread_ids
        """
        threads = []
        try:
            # First approach: try to get distinct thread_ids directly
            try:
                distinct_threads = await self.async_mongodb_memory_collection.distinct("thread_id")
                # Sort by extracting timestamp from thread_id format (thread_YYYYMMDD_HHMMSS)
                sorted_threads = sorted(
                    [t for t in distinct_threads if t and t != "null"],
                    key=lambda x: x.split('_')[1:] if len(x.split('_')) >= 3 else "",
                    reverse=True
                )
                return sorted_threads[:limit]
            except Exception as e1:
                logger.error(f"Error with distinct query: {str(e1)}")
            
            # Second approach: try using find() instead of aggregate
            try:
                cursor = self.async_mongodb_memory_collection.find(
                    {"thread_id": {"$ne": None}},
                    {"thread_id": 1, "_id": 0}
                ).sort("_id", -1).limit(limit * 10)  # Get more than needed to account for duplicates
                
                thread_set = set()
                async for doc in cursor:
                    thread_id = doc.get("thread_id")
                    if thread_id and thread_id != "null" and thread_id not in thread_set:
                        thread_set.add(thread_id)
                        threads.append(thread_id)
                        if len(threads) >= limit:
                            break
                
                return threads
            except Exception as e2:
                logger.error(f"Error with find query: {str(e2)}")
                
        except Exception as e:
            logger.error(f"Error retrieving thread IDs: {str(e)}")
        
        # If all methods fail, return an empty list
        return threads
    
    async def cleanup_old_threads(self, keep_threads=None):
        """
        Clean up old threads from the memory collections.
        
        Args:
            keep_threads (list): List of thread_ids to keep (if None, deletes all threads)
            
        Returns:
            int: Number of deleted documents
        """
        deleted_count = 0
        try:
            # Build the query to delete documents not in the keep_threads list
            query = {} if keep_threads is None else {"thread_id": {"$nin": keep_threads}}
            
            # Delete from the checkpoints collection
            result = await self.async_mongodb_client[self.database_name][self.checkpoints_collection].delete_many(query)
            deleted_count += result.deleted_count
            
            # Delete from the checkpoint writes collection
            result = await self.async_mongodb_client[self.database_name][self.checkpoint_writes_collection].delete_many(query)
            deleted_count += result.deleted_count
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up old threads: {str(e)}")
            return 0
    
    async def create_new_session(self):
        """
        Create a new chat session and clean up older threads.
        
        Returns:
            dict: Information about the new session
        """
        # Generate a new thread_id for a new chat session
        thread_id = self.generate_thread_id()
        
        # Clean up older threads, keeping only the 2 most recent ones (plus this new one)
        threads = await self.list_available_threads(limit=2)
        if threads:
            threads.append(thread_id)  # Also keep the new thread
            deleted_count = await self.cleanup_old_threads(keep_threads=threads)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} older memory records.")
        
        return {
            "status": "success",
            "thread_id": thread_id,
            "message": "New chat session created"
        }
    
    async def continue_session(self, thread_selection=None):
        """
        Continue an existing chat session or create a new one if none exists.
        
        Args:
            thread_selection: ID of thread to continue (if None, a list of threads will be returned)
            
        Returns:
            dict: Information about the selected session or available sessions
        """
        # Get only the 3 most recent threads
        threads = await self.list_available_threads(limit=3)
        
        # Clean up older threads
        if threads:
            deleted_count = await self.cleanup_old_threads(keep_threads=threads)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} older memory records.")
        
        if not threads:
            # No existing sessions, create a new one
            thread_id = self.generate_thread_id()
            return {
                "status": "success",
                "thread_id": thread_id,
                "message": "No existing chat sessions found. Created a new one."
            }
        
        # If no specific thread was selected, return the list of available threads
        if thread_selection is None:
            formatted_threads = []
            for i, thread in enumerate(threads, 1):
                # Try to extract the datetime from the thread_id for a more readable format
                try:
                    date_part = thread.split('_')[1]
                    time_part = thread.split('_')[2]
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
                    formatted_threads.append({
                        "id": thread,
                        "display": f"Session from {formatted_date}",
                        "timestamp": formatted_date
                    })
                except:
                    formatted_threads.append({
                        "id": thread,
                        "display": thread,
                        "timestamp": ""
                    })
            
            return {
                "status": "success",
                "available_threads": formatted_threads,
                "message": "Available chat sessions retrieved"
            }
        
        # Otherwise, use the selected thread
        if thread_selection.isdigit() and 0 < int(thread_selection) <= len(threads):
            # Selection is a number index
            thread_id = threads[int(thread_selection) - 1]
        elif thread_selection in threads:
            # Selection is one of the actual thread_ids in the list
            thread_id = thread_selection
        else:
            # Invalid selection, create a new session
            thread_id = self.generate_thread_id()
            return {
                "status": "success",
                "thread_id": thread_id,
                "message": "Invalid selection. Created a new session."
            }
        
        return {
            "status": "success",
            "thread_id": thread_id,
            "message": f"Continuing chat session {thread_id}"
        }
    
    async def clear_all_memory(self):
        """
        Clear all chat memory.
        
        Returns:
            dict: Information about the operation
        """
        deleted_count = await self.cleanup_old_threads()
        thread_id = self.generate_thread_id()
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "thread_id": thread_id,
            "message": f"Deleted {deleted_count} memory records. All chat history has been cleared."
        }
        
    async def get_checkpoint_data(self, thread_id):
        """
        Retrieve the conversation history and tool usage data from checkpoints.
        
        Args:
            thread_id (str): The thread ID to retrieve checkpoint data for
            
        Returns:
            dict: Checkpoint data including timestamp, ID, and messages
        """
        try:
            # Try multiple query formats to ensure we get the right checkpoint data
            checkpoints_list = []
            
            # First try with configurable.thread_id
            async for checkpoint_tuple in self.memory.alist({"configurable": {"thread_id": thread_id}}):
                checkpoints_list.append(checkpoint_tuple)
            
            # If no results, try with direct thread_id
            if not checkpoints_list:
                async for checkpoint_tuple in self.memory.alist({"thread_id": thread_id}):
                    checkpoints_list.append(checkpoint_tuple)
                    
            # If still no results, try looking in metadata.thread_id (binary format)
            if not checkpoints_list:
                try:
                    thread_id_binary = str(thread_id).encode('utf-8')
                    async for checkpoint_tuple in self.memory.alist({"metadata.thread_id": thread_id_binary}):
                        checkpoints_list.append(checkpoint_tuple)
                except Exception as e:
                    logger.error(f"Error querying binary thread_id: {str(e)}")
            
            if not checkpoints_list:
                logger.warning(f"No checkpoints found for thread_id: {thread_id}")
                return {"messages": []}
            
            # Log the number of checkpoints found
            logger.info(f"Found {len(checkpoints_list)} checkpoints for thread_id: {thread_id}")
            
            # Get the most recent checkpoint
            latest_checkpoint = checkpoints_list[-1].checkpoint
            
            # Log checkpoint structure for debugging
            logger.debug(f"Checkpoint structure: {latest_checkpoint.keys()}")
            logger.debug(f"Channel values: {latest_checkpoint.get('channel_values', {}).keys()}")
            
            # Extract messages from the checkpoint
            messages = []
            checkpoint_messages = latest_checkpoint["channel_values"].get("messages", [])
            logger.info(f"Number of messages in checkpoint: {len(checkpoint_messages)}")
            
            for message in checkpoint_messages:
                message_data = {
                    "content": message.content,
                    "message_id": message.id if hasattr(message, "id") else "",
                    "type": "human" if isinstance(message, HumanMessage) else "agent"
                }
                
                # Check for tool calls in agent messages - try multiple formats
                if isinstance(message, AIMessage):
                    # Standard format
                    if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
                        tool_calls = []
                        for tool_call in message.additional_kwargs["tool_calls"]:
                            tool_name = tool_call["function"]["name"]
                            try:
                                tool_arguments = eval(tool_call["function"]["arguments"])
                                tool_query = tool_arguments.get("query", "")
                            except:
                                # If eval fails, use the raw arguments string
                                tool_query = tool_call["function"]["arguments"]
                                
                            tool_calls.append({
                                "tool_name": tool_name,
                                "query": tool_query
                            })
                        message_data["tool_calls"] = tool_calls
                    
                    # Alternative format: tool_call_id
                    elif hasattr(message, "tool_call_id") and message.tool_call_id:
                        message_data["tool_call_id"] = message.tool_call_id
                    
                    # Alternative format: tool_inputs
                    elif hasattr(message, "tool_inputs") and message.tool_inputs:
                        message_data["tool_inputs"] = message.tool_inputs
                
                messages.append(message_data)
            
            return {
                "timestamp": latest_checkpoint.get("ts", ""),
                "checkpoint_id": latest_checkpoint.get("id", ""),
                "messages": messages
            }
                
        except Exception as e:
            logger.error(f"Error retrieving checkpoint data: {str(e)}")
            logger.exception("Full exception details:")
            return {"messages": []}
    
    async def process_user_message(self, thread_id, message_content):
        """
        Process a user message and get the agent's response.
        
        Args:
            thread_id (str): The ID of the thread for this conversation
            message_content (str): The content of the user's message
            
        Returns:
            dict: The agent's response and any tool calls made
        """
        # Check for special commands
        if message_content.lower() == "clear all memory":
            result = await self.clear_all_memory()
            return {
                "status": "success",
                "message_type": "system",
                "content": result["message"],
                "thread_id": result["thread_id"]
            }
        
        # Process the message with the agent
        response_chunks = []
        tool_calls = []
        thoughts = []
        final_answer = None
        
        try:
            # Log that we're about to invoke the agent with tools
            logger.info(f"Processing message with agent, thread_id: {thread_id}")
            
            # Use the async stream method of the LangGraph agent to get the agent's answer
            async for chunk in self.langgraph_agent.astream(
                {"messages": [HumanMessage(content=message_content)]},
                {"configurable": {"thread_id": thread_id}}
            ):
                # Log full chunk for debugging
                logger.debug(f"Chunk: {chunk}")
                
                # Check if this is the final answer
                if "agent" in chunk and chunk.get("agent", {}).get("is_final", False):
                    for message in chunk["agent"]["messages"]:
                        final_answer = message.content
                        logger.info(f"Final answer captured: {final_answer[:100]}...")
                
                # Process chunks to extract the response and any tool calls
                if "agent" in chunk:
                    for message in chunk["agent"]["messages"]:
                        # Check for tool calls using multiple possible formats
                        if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
                            tool_calls_data = message.additional_kwargs["tool_calls"]
                            for tool_call in tool_calls_data:
                                tool_name = tool_call["function"]["name"]
                                # Log tool calls for debugging
                                logger.info(f"Tool called: {tool_name}")
                                try:
                                    tool_arguments = eval(tool_call["function"]["arguments"])
                                    tool_query = tool_arguments.get("query", "")
                                except:
                                    tool_query = tool_call["function"]["arguments"]
                                    
                                tool_calls.append({
                                    "tool_name": tool_name,
                                    "query": tool_query
                                })
                                thoughts.append(f"I'll use {tool_name} to find information about {tool_query}")
                        else:
                            # Could be a thought or regular message content
                            content = message.content
                            if content.strip():  # Only add non-empty content
                                if "I need to" in content or "I should" in content or "Let me" in content:
                                    thoughts.append(content)
                                else:
                                    response_chunks.append(content)
                
                # Also check for ReAct thought process in other formats
                if "intermediate_steps" in chunk:
                    for step in chunk["intermediate_steps"]:
                        if hasattr(step, "thought") and step.thought:
                            thoughts.append(step.thought)
                        if hasattr(step, "action") and step.action:
                            tool_calls.append({
                                "tool_name": step.action.tool,
                                "query": str(step.action.tool_input)
                            })
            
            # Get checkpoint data for the conversation history
            checkpoint_data = await self.get_checkpoint_data(thread_id)
            
            # For the final response, prioritize the final answer if available
            final_response = final_answer if final_answer else " ".join(response_chunks)
            
            # Return the response with checkpoint data and thoughts
            return {
                "status": "success",
                "message_type": "agent",
                "content": final_response,
                "tool_calls": tool_calls,
                "thread_id": thread_id,
                "checkpoint_data": checkpoint_data,
                "thoughts": thoughts if thoughts else None
            }
                    
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.exception("Full stack trace:")
            return {
                "status": "error",
                "message": f"An error occurred processing your message: {str(e)}",
                "thread_id": thread_id
            }