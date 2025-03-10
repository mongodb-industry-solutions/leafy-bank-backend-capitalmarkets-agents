from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    return MongoDBChatMessageHistory(
        os.getenv("MONGODB_URI"), session_id, database_name=os.getenv("DATABASE_NAME"), collection_name=os.getenv("MACRO_INDICATORS_AGENT_CHAT_HISTORY_COLLECTION")
    )

temp_mem = get_session_history("macro_indicators_agent_id")
logging.info("Agent Macro Indicators Chat History initialized")