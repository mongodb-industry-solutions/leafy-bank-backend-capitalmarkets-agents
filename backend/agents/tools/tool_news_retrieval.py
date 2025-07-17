import logging
from agents.tools.db.mdb import MongoDBConnector
from agents.tools.vogayeai.vogaye_ai_embeddings import VogayeAIEmbeddings
from agents.tools.states.agent_market_news_state import MarketNewsAgentState, AssetNews as MarketAssetNews, SentimentScore as MarketSentimentScore
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, AssetNews as CryptoAssetNews, SentimentScore as CryptoSentimentScore
import os
from dotenv import load_dotenv
from typing import Union

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
NUMBER_OF_ARTICLES = 5

class NewsRetrievalTool(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("NEWS_COLLECTION")):
        """
        Service for performing vector search operations on Financial News data.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "financial_news".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        self.collection = self.get_collection(collection_name)
        self.embedding_model_id = os.getenv("EMBEDDINGS_MODEL_ID", "voyage-finance-2")
        self.vector_index_name = os.getenv("NEWS_VECTOR_INDEX_NAME", "finance_news_VS_IDX")
        self.vector_field = os.getenv("NEWS_COLLECTION_VECTOR_FIELD", "article_embedding")
        logger.info("NewsRetrievalTool initialized")

    def vector_search_news_articles(self, query: str, n: int, asset_symbol: str = None) -> dict:
        """
        Performs a vector search on the MongoDB Atlas Vector Search index for financial news articles.
        Uses sentiment-based filtering and proper projection to avoid field deletion.
        
        Args:
            query (str): The search query to find relevant news articles.
            n (int): The number of results to return.
            asset_symbol (str, optional): The asset symbol to filter results by. Defaults to None.

        Returns:
            dict: A dictionary containing the search results, including news articles.        
        """
        message = "[Action] Performing MongoDB Atlas Vector Search for financial news articles."
        print("\n" + message)

        logger.info(f"Query: {query}")
        ve = VogayeAIEmbeddings(api_key=os.getenv("VOYAGE_API_KEY"))
        query_vector = ve.get_embeddings(model_id=self.embedding_model_id, text=query)

        results = []
        
        # Try different sentiment thresholds to get enough results
        thresholds = [0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]  # Progressive fallback
        
        for threshold in thresholds:
            if len(results) >= n:
                break
                
            try:
                # Build filter conditions based on sentiment scores
                sentiment_filter = {
                    "$or": [
                        {"sentiment_score.positive": {"$gt": threshold}},
                        {"sentiment_score.negative": {"$gt": threshold}},
                        {"sentiment_score.neutral": {"$gt": threshold}}
                    ]
                }
                
                # Add asset_symbol filter if provided
                if asset_symbol:
                    filter_obj = {
                        "$and": [
                            sentiment_filter,
                            {"ticker": asset_symbol}
                        ]
                    }
                else:
                    filter_obj = sentiment_filter

                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": self.vector_index_name,
                            "path": self.vector_field,
                            "filter": filter_obj,
                            "queryVector": query_vector,
                            "numCandidates": max(n * 5, 20),
                            "limit": n
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "asset": "$ticker",
                            "headline": 1,
                            "description": 1,
                            "source": 1,
                            "posted": 1,
                            "link": 1,
                            "sentiment_score": 1,
                            "vectorSearchScore": { "$meta": "vectorSearchScore" }
                        }
                    }
                ]
                
                current_results = list(self.collection.aggregate(pipeline))
                logger.info(f"Found {len(current_results)} results with threshold {threshold}")
                
                # Add unique results (avoid duplicates based on link)
                existing_links = {r.get('link') for r in results}
                for result in current_results:
                    if result.get('link') not in existing_links:
                        results.append(result)
                        existing_links.add(result.get('link'))
                        
            except Exception as e:
                logger.error(f"Error during vector search with threshold {threshold}: {e}")
                continue

        return {
            "articles": results[:n]  # Limit to requested number
        }

    def convert_to_asset_news(self, raw_article: dict, state_type: str) -> Union[MarketAssetNews, CryptoAssetNews]:
        """
        Convert a raw article dictionary to an AssetNews object.
        
        Args:
            raw_article (dict): Raw article data from MongoDB
            state_type (str): Either 'market' or 'crypto' to determine which class to use
            
        Returns:
            Union[MarketAssetNews, CryptoAssetNews]: Structured article object
        """
        sentiment_score_dict = raw_article.get('sentiment_score', {})
        
        # Create the appropriate SentimentScore object based on state type
        if state_type == 'crypto':
            sentiment_score = CryptoSentimentScore(
                neutral=sentiment_score_dict.get('neutral'),
                negative=sentiment_score_dict.get('negative'),
                positive=sentiment_score_dict.get('positive')
            )
            
            # Create CryptoAssetNews object
            asset_news = CryptoAssetNews(
                asset=raw_article.get('asset'),
                headline=raw_article.get('headline'),
                description=raw_article.get('description'),
                source=raw_article.get('source'),
                posted=raw_article.get('posted'),
                link=raw_article.get('link'),
                sentiment_score=sentiment_score
            )
        else:
            sentiment_score = MarketSentimentScore(
                neutral=sentiment_score_dict.get('neutral'),
                negative=sentiment_score_dict.get('negative'),
                positive=sentiment_score_dict.get('positive')
            )
            
            # Create MarketAssetNews object
            asset_news = MarketAssetNews(
                asset=raw_article.get('asset'),
                headline=raw_article.get('headline'),
                description=raw_article.get('description'),
                source=raw_article.get('source'),
                posted=raw_article.get('posted'),
                link=raw_article.get('link'),
                sentiment_score=sentiment_score
            )
        
        return asset_news

    def fetch_market_news(self, state: Union[MarketNewsAgentState, CryptoNewsAgentState]) -> dict:
        """
        Fetches financial news articles related to the assets in the portfolio allocation.
        Performs vector search on news articles and converts to AssetNews objects.
        
        Args:
            state (Union[MarketNewsAgentState, CryptoNewsAgentState]): The agent state containing portfolio allocation
            
        Returns:
            dict: Updated state with AssetNews objects
        """
        # Determine state type
        if isinstance(state, CryptoNewsAgentState):
            state_type = 'crypto'
            message = "[Tool] Fetching crypto news articles."
        else:
            state_type = 'market'
            message = "[Tool] Fetching market news articles."
            
        logger.info(message)

        asset_news_list = []
        
        # Process each asset in the portfolio allocation
        for allocation in state.portfolio_allocation:
            asset_symbol = allocation.asset
            asset_description = allocation.description
            
            if asset_symbol:
                logger.info(f"Fetching news articles for asset: {asset_symbol} ({asset_description})")
                
                # Generate a search query for the asset
                query = f"financial news analysis about {asset_symbol} ({asset_description})"
                
                # Perform vector search for this specific asset
                search_results = self.vector_search_news_articles(
                    query=query, 
                    n=NUMBER_OF_ARTICLES, 
                    asset_symbol=asset_symbol
                )
                
                # Convert raw results to AssetNews objects with the correct type
                if search_results and "articles" in search_results:
                    for raw_article in search_results["articles"]:
                        asset_news = self.convert_to_asset_news(raw_article, state_type)
                        asset_news_list.append(asset_news)
        
        # Update the state with the fetched data
        updated_state = state.model_copy()
        updated_state.report.asset_news = asset_news_list
        updated_state.updates.append(message)
        updated_state.next_step = "news_sentiment_calc_node"
        
        return updated_state


# Initialize the NewsRetrievalTool
news_retrieval_obj = NewsRetrievalTool()

# Define tools
def fetch_market_news_tool(state: Union[MarketNewsAgentState, CryptoNewsAgentState]) -> dict:
    """
    Fetch market news articles for assets in the portfolio allocation.
    Performs vector search on news articles and converts to AssetNews objects.
    """
    return news_retrieval_obj.fetch_market_news(state=state)