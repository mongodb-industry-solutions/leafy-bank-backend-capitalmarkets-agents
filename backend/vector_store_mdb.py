from langchain_mongodb import MongoDBAtlasVectorSearch
from loaders.embeddings.bedrock.getters import get_embedding_model
from db.mdb import MongoDBConnector
from dotenv import load_dotenv

import os
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class VectorStoreMongoDB(MongoDBConnector):
    def __init__(self, uri=None, database_name=None, collection_name=None, text_key=None, embedding_key=None, index_name=None, model_id=os.getenv("EMBEDDING_MODEL_ID")):
        """
        Initializes the VectorStoreMongoDB.
        """
        super().__init__(uri, database_name)
        self.collection_name = collection_name or os.getenv("NEWS_COLLECTION")
        self.text_key = text_key or "article_string"
        self.embedding_key = embedding_key or "article_embedding"
        self.index_name = index_name or os.getenv("VECTOR_INDEX_NAME")
        self.embedding_model = get_embedding_model(model_id=model_id)
        self.vector_store = self.create_vector_store()
        logger.info("VectorStoreMongoDB initialized")

    def create_vector_store(self):
        """
        Creates a vector store using MongoDB Atlas.
        """
        if self.vector_store is not None:
            logger.info("Vector store already created")
            return self.vector_store

        if self.index_name is None:
            self.index_name = f"{self.collection_name}_VS_IDX"

        logger.info(f"Creating vector store...")

        # Vector Store Creation
        self.vector_store = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string=self.uri,
            namespace=self.database_name + "." + self.collection_name,
            embedding=self.embedding_model,
            embedding_key=self.embedding_key,
            index_name=self.index_name,
            text_key=self.text_key
        )

        logger.info("Vector store created successfully")
        return self.vector_store

    def lookup_articles(self, query: str, n=10) -> str:
        """
        Looks up articles in the vector store based on the query.

        :param query: The search query.
        :param n: The number of articles to return.
        :return: A string representation of the search results.
        """
        result = self.vector_store.similarity_search_with_score(query=query, k=n)
        return str(result)

# Example usage
if __name__ == "__main__":
    vector_store = VectorStoreMongoDB()

    query = "Financial articles related to SPY (S&P 500 ETF)"

    result = vector_store.lookup_articles(query=query, n=5)
    print(result)