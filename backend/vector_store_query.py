from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_aws import BedrockEmbeddings
from loaders.embeddings.bedrock.getters import get_embedding_model

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

def create_vector_store(
    cluster_uri: str,
    database_name: str,
    collection_name: str,
    text_key: str,
    embedding_key: str,
    index_name: str,
    embedding_model: BedrockEmbeddings,
) -> MongoDBAtlasVectorSearch:
    """
    Creates a vector store using MongoDB Atlas.

    :param cluster_uri: MongoDB connection URI.
    :param database_name: Name of the database.
    :param collection_name: Name of the collection.
    :param text_key: The field containing text data.
    :param embedding_key: Field that will contain the embedding for each document
    :param index_name: Name of the Atlas Vector Search index
    :param embedding_model: The embedding model to use.
    """

    if index_name is None:
        index_name = f"{collection_name}_VS_IDX"

    logging.info(f"Creating vector store...")

    # Vector Store Creation
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=cluster_uri,
        namespace=database_name + "." + collection_name,
        embedding=embedding_model,
        embedding_key=embedding_key,
        index_name=index_name,
        text_key=text_key
    )

    return vector_store

def lookup_articles(vector_store: MongoDBAtlasVectorSearch, query: str, n=10) -> str:
    """
    Looks up articles in the vector store based on the query.

    :param vector_store: The vector store instance.
    :param query: The search query.
    :param n: The number of articles to return.
    :return: A string representation of the search results.
    """
    result = vector_store.similarity_search_with_score(query=query, k=n)
    return str(result)

# Example usage
if __name__ == "__main__":

    embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")

    vector_store = create_vector_store(
        cluster_uri=os.getenv("MONGODB_URI"),
        database_name=os.getenv("DATABASE_NAME"),
        collection_name=os.getenv("NEWS_COLLECTION"),
        text_key="article_string",
        embedding_key="article_embedding",
        index_name=os.getenv("VECTOR_INDEX_NAME"),
        embedding_model=embedding_model
    )

    query = "Financial articles related to SPY (S&P 500 ETF)"

    result = lookup_articles(vector_store, query=query)
    print(result)