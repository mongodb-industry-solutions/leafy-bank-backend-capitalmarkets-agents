import logging
from pymongo.errors import OperationFailure

from mdb import MongoDBConnector

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

class VectorSearchIndexCreator(MongoDBConnector):
    def __init__(self, collection_name: str, uri=None, database_name: str = None, appname: str = None):
        """ VectorSearchIndexCreator class to create a vector search index in MongoDB. If it already exists, it will not be created again."""
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        self.collection = self.get_collection(self.collection_name)
        logger.info("VectorSearchIndexCreator initialized")

    def create_index(self, index_name: str, vector_field: str, dimensions: int = 1024, similarity_metric: str = "cosine", include_filters: bool = True) -> dict:
        """
        Creates a vector search index on the MongoDB collection.

        Args:
            index_name (str): Index name.
            vector_field (str): Vector field name.
            dimensions (int, optional): Number of dimensions. Default is 1024.
            similarity_metric (str, optional): Similarity metric. Default is "cosine".
            include_filters (bool, optional): Whether to include filter fields. Default is True.

        Returns:
            dict: Index creation result
        """
        logger.info(f"Creating vector search index...")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Vector Field: {vector_field}")
        logger.info(f"Dimensions: {dimensions}")
        logger.info(f"Similarity Metric: {similarity_metric}")
        logger.info(f"Include Filters: {include_filters}")

        # Define the vector search index configuration
        fields = [
            {
                "path": vector_field,
                "type": "vector",
                "numDimensions": dimensions,
                "similarity": similarity_metric
            }
        ]

        # Add filter fields if requested
        if include_filters:
            filter_fields = [
                {
                    "path": "asset_id",
                    "type": "filter"
                },
                {
                    "path": "sentiment_score.positive",
                    "type": "filter"
                },
                {
                    "path": "sentiment_score.negative",
                    "type": "filter"
                },
                {
                    "path": "sentiment_score.neutral",
                    "type": "filter"
                },
                {
                    "path": "subreddit",
                    "type": "filter"
                },
                {
                    "path": "score",
                    "type": "filter"
                },
                {
                    "path": "ups",
                    "type": "filter"
                },
                {
                    "path": "downs",
                    "type": "filter"
                }
            ]
            fields.extend(filter_fields)
            logger.info(f"Added {len(filter_fields)} filter fields to index")

        index_config = {
            "name": index_name,
            "type": "vectorSearch",
            "definition": {
                "fields": fields
            }
        }

        try:
            # Create the index
            self.collection.create_search_index(index_config)
            logger.info(f"Vector search index '{index_name}' created successfully.")
            return {"status": "success", "message": f"Vector search index '{index_name}' created successfully."}
        except OperationFailure as e:
            if e.code == 68:  # IndexAlreadyExists error code
                logger.warning(f"Vector search index '{index_name}' already exists.")
                return {"status": "warning", "message": f"Vector search index '{index_name}' already exists."}
            else:
                logger.error(f"Error creating vector search index: {e}")
                return {"status": "error", "message": f"Error creating vector search index: {e}"}
        except Exception as e:
            logger.error(f"Error creating vector search index: {e}")
            return {"status": "error", "message": f"Error creating vector search index: {e}"}

    def create_index_with_custom_filters(self, index_name: str, vector_field: str, filter_fields: list, dimensions: int = 1024, similarity_metric: str = "cosine") -> dict:
        """
        Creates a vector search index with custom filter fields.

        Args:
            index_name (str): Index name.
            vector_field (str): Vector field name.
            filter_fields (list): List of filter field paths.
            dimensions (int, optional): Number of dimensions. Default is 1024.
            similarity_metric (str, optional): Similarity metric. Default is "cosine".

        Returns:
            dict: Index creation result
        """
        logger.info(f"Creating vector search index with custom filters...")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Vector Field: {vector_field}")
        logger.info(f"Filter Fields: {filter_fields}")

        # Define the vector search index configuration
        fields = [
            {
                "path": vector_field,
                "type": "vector",
                "numDimensions": dimensions,
                "similarity": similarity_metric
            }
        ]

        # Add custom filter fields
        for field_path in filter_fields:
            fields.append({
                "path": field_path,
                "type": "filter"
            })

        index_config = {
            "name": index_name,
            "type": "vectorSearch",
            "definition": {
                "fields": fields
            }
        }

        try:
            # Create the index
            self.collection.create_search_index(index_config)
            logger.info(f"Vector search index '{index_name}' created successfully.")
            return {"status": "success", "message": f"Vector search index '{index_name}' created successfully."}
        except OperationFailure as e:
            if e.code == 68:  # IndexAlreadyExists error code
                logger.warning(f"Vector search index '{index_name}' already exists.")
                return {"status": "warning", "message": f"Vector search index '{index_name}' already exists."}
            else:
                logger.error(f"Error creating vector search index: {e}")
                return {"status": "error", "message": f"Error creating vector search index: {e}"}
        except Exception as e:
            logger.error(f"Error creating vector search index: {e}")
            return {"status": "error", "message": f"Error creating vector search index: {e}"}


# Example usage
if __name__ == "__main__":
    subreddit_submissions_collection_name = os.getenv("SUBREDDIT_SUBMISSIONS_COLLECTION", "subredditSubmissions")
    subreddit_submissions_vector_index_name = os.getenv("SUBREDDIT_SUBMISSIONS_VECTOR_INDEX_NAME", "subreddit_submissions_VS_IDX")
    subreddit_submissions_vector_field = os.getenv("SUBREDDIT_SUBMISSIONS_VECTOR_FIELD", "submission_embeddings")

    # Create vector search index for market analysis
    vs_idx = VectorSearchIndexCreator(collection_name=subreddit_submissions_collection_name)
    result = vs_idx.create_index(
        index_name=subreddit_submissions_vector_index_name,
        vector_field=subreddit_submissions_vector_field
    )
    logger.info(result)