import logging
from db.mdb import MongoDBConnector
from vogayeai.vogaye_ai_embeddings import VogayeAIEmbeddings
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, AssetSubreddits, SentimentScore, Comment
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

# Constants
LIMIT_N = 10

class SocialMediaRetrievalTool(MongoDBConnector):
    def __init__(self, uri=None, database_name: str = None, appname: str = None, collection_name: str = os.getenv("SUBREDDIT_SUBMISSIONS_COLLECTION")):
        """
        Service for performing vector search operations on subreddit submissions.

        Args:
            uri (str, optional): MongoDB URI. Defaults to None.
            database_name (str, optional): Database name. Defaults to None.
            appname (str, optional): Application name. Defaults to None.
            collection_name (str, optional): Collection name. Defaults to "subreddit_submissions".
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        self.collection = self.get_collection(collection_name)
        self.embedding_model_id = os.getenv("EMBEDDINGS_MODEL_ID", "voyage-finance-2")
        self.vector_index_name = os.getenv("SUBREDDIT_SUBMISSIONS_VECTOR_INDEX_NAME", "subreddit_submissions_VS_IDX")
        self.vector_field = os.getenv("SUBREDDIT_SUBMISSIONS_VECTOR_FIELD", "submission_embeddings")
        logger.info("SocialMediaRetrievalTool initialized")

    def vector_search_subreddit_submissions(self, query: str, n: int, asset_id: str = None) -> dict:
        """Performs a vector search on the MongoDB Atlas Vector Search index for subreddit submissions.
        
        Args:
            query (str): The search query to find relevant subreddit submissions.
            n (int): The number of results to return.
            asset_id (str, optional): The asset ID to filter results by. Defaults to None

        Returns:
            dict: A dictionary containing the search results, including subreddit submissions.        
        """
        message = "[Action] Performing MongoDB Atlas Vector Search for subreddit submissions."
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
                # Build filter conditions
                sentiment_filter = {
                    "$or": [
                        {"sentiment_score.positive": {"$gt": threshold}},
                        {"sentiment_score.negative": {"$gt": threshold}}
                    ]
                }
                
                # Add asset_id filter if provided
                if asset_id:
                    filter_obj = {
                        "$and": [
                            sentiment_filter,
                            {"asset_id": asset_id}
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
                            "asset": "$asset_id",
                            "subreddit": 1,
                            "url": 1,
                            "author": 1,
                            "author_fullname": 1,
                            "title": 1,
                            "description": "$selftext",
                            "create_at_utc": "$created_at_utc",
                            "score": 1,
                            "num_comments": 1,
                            "ups": 1,
                            "downs": 1,
                            "sentiment_score": 1,
                            "comments": {
                                "$slice": ["$comments", 3]
                            },
                            "vectorSearchScore": { "$meta": "vectorSearchScore" }
                        }
                    }
                ]
                
                current_results = list(self.collection.aggregate(pipeline))
                logger.info(f"Found {len(current_results)} results with threshold {threshold}")
                
                # Add unique results (avoid duplicates)
                existing_urls = {r.get('url') for r in results}
                for result in current_results:
                    if result.get('url') not in existing_urls:
                        results.append(result)
                        existing_urls.add(result.get('url'))
                        
            except Exception as e:
                logger.error(f"Error during vector search with threshold {threshold}: {e}")
                continue

        return {
            "subreddit_submissions": results[:n]  # Limit to requested number
        }

    def convert_to_asset_subreddits(self, raw_submission: dict) -> AssetSubreddits:
        """
        Convert a raw submission dictionary to an AssetSubreddits object.
        
        Args:
            raw_submission (dict): Raw submission data from MongoDB
            
        Returns:
            AssetSubreddits: Structured submission object
        """
        # Convert sentiment score
        sentiment_data = raw_submission.get('sentiment_score', {})
        sentiment_score = SentimentScore(
            neutral=sentiment_data.get('neutral'),
            negative=sentiment_data.get('negative'),
            positive=sentiment_data.get('positive')
        )
        
        # Convert comments
        comments = []
        for comment_data in raw_submission.get('comments', []):
            comment = Comment(
                id=comment_data.get('id'),
                author=comment_data.get('author'),
                body=comment_data.get('body'),
                score=comment_data.get('score'),
                create_at_utc=comment_data.get('created_at_utc').isoformat() if comment_data.get('created_at_utc') else None
            )
            comments.append(comment)
        
        # Convert main submission
        asset_subreddit = AssetSubreddits(
            asset=raw_submission.get('asset'),
            subreddit=raw_submission.get('subreddit'),
            url=raw_submission.get('url'),
            author=raw_submission.get('author'),
            author_fullname=raw_submission.get('author_fullname'),
            title=raw_submission.get('title'),
            description=raw_submission.get('description'),
            create_at_utc=raw_submission.get('create_at_utc').isoformat() if raw_submission.get('create_at_utc') else None,
            score=raw_submission.get('score'),
            num_comments=raw_submission.get('num_comments'),
            comments=comments,
            ups=raw_submission.get('ups'),
            downs=raw_submission.get('downs'),
            sentiment_score=sentiment_score
        )
        
        return asset_subreddit


# Initialize the SocialMediaRetrievalTool
social_media_retrieval_obj = SocialMediaRetrievalTool()


def fetch_social_media_submissions_tool(state: CryptoNewsAgentState) -> dict:
    """
    Fetch social media submissions for assets in the portfolio allocation.
    Performs vector search on subreddit submissions and converts to AssetSubreddits objects.
    
    Args:
        state (CryptoNewsAgentState): The agent state containing portfolio allocation
        
    Returns:
        dict: Updated state with AssetSubreddits objects
    """
    asset_subreddits = []
    
    # Process each asset in the portfolio allocation
    for allocation in state.portfolio_allocation:
        asset_id = allocation.asset
        asset_description = allocation.description
        
        if asset_id:
            logger.info(f"Fetching social media sentiment for asset: {asset_id} ({asset_description})")
            
            # Generate a search query for the asset
            query = f"sentiment analysis discussion about {asset_id} ({asset_description})"
            
            # Perform vector search for this specific asset
            search_results = social_media_retrieval_obj.vector_search_subreddit_submissions(
                query=query, 
                n=LIMIT_N, 
                asset_id=asset_id
            )
            
            # Convert raw results to AssetSubreddits objects
            if search_results and "subreddit_submissions" in search_results:
                for raw_submission in search_results["subreddit_submissions"]:
                    asset_subreddit = social_media_retrieval_obj.convert_to_asset_subreddits(raw_submission)
                    asset_subreddits.append(asset_subreddit)
    
    # Update the state with the fetched data
    updated_state = state.model_copy()
    updated_state.report.asset_subreddits = asset_subreddits
    updated_state.next_step = "social_media_sentiment_summary_node"
    
    return updated_state


# Example usage
if __name__ == "__main__":
    from states.agent_crypto_news_state import CryptoNewsAgentState, PortfolioAllocation

    # Initialize the state with traditional assets portfolio
    state = CryptoNewsAgentState(
        portfolio_allocation=[
            PortfolioAllocation(
                asset="SPY", 
                asset_type="ETF",
                description="S&P 500 ETF", 
                allocation_percentage="25%"
            ),
            PortfolioAllocation(
                asset="QQQ", 
                asset_type="ETF",
                description="Nasdaq ETF", 
                allocation_percentage="20%"
            ),
            PortfolioAllocation(
                asset="EEM", 
                asset_type="ETF",
                description="Emerging Markets ETF", 
                allocation_percentage="8%"
            ),
            PortfolioAllocation(
                asset="XLE", 
                asset_type="ETF",
                description="Energy Sector ETF", 
                allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="TLT", 
                asset_type="ETF",
                description="Long-Term Treasury Bonds", 
                allocation_percentage="10%"
            ),
            PortfolioAllocation(
                asset="LQD", 
                asset_type="ETF",
                description="Investment-Grade Bonds", 
                allocation_percentage="7%"
            ),
            PortfolioAllocation(
                asset="HYG", 
                asset_type="ETF",
                description="High-Yield Bonds", 
                allocation_percentage="5%"
            ),
            PortfolioAllocation(
                asset="VNQ", 
                asset_type="ETF",
                description="Real Estate ETF", 
                allocation_percentage="6%"
            ),
            PortfolioAllocation(
                asset="GLD", 
                asset_type="ETF",
                description="Gold ETF", 
                allocation_percentage="8%"
            ),
            PortfolioAllocation(
                asset="USO", 
                asset_type="ETF",
                description="Oil ETF", 
                allocation_percentage="6%"
            )
        ],
        next_step="social_media_sentiment_node",
    )

    # Use the tool to fetch social media submissions
    updated_state = fetch_social_media_submissions_tool(state)

    # Print summary
    print("\n" + "="*80)
    print("SOCIAL MEDIA RETRIEVAL SUMMARY")
    print("="*80)
    
    print(f"Total AssetSubreddits fetched: {len(updated_state.report.asset_subreddits)}")
    print(f"Next step: {updated_state.next_step}")
    
    # Group by asset for summary
    asset_counts = {}
    for asset_subreddit in updated_state.report.asset_subreddits:
        asset = asset_subreddit.asset
        if asset not in asset_counts:
            asset_counts[asset] = 0
        asset_counts[asset] += 1
    
    print("\nSubmissions per asset:")
    for asset, count in asset_counts.items():
        print(f"  {asset}: {count} submissions")
    
    print("\nFirst few submissions:")
    for i, asset_subreddit in enumerate(updated_state.report.asset_subreddits[:5]):
        print(f"  {i+1}. {asset_subreddit.asset}: {asset_subreddit.title}")
        print(f"     Sentiment: P:{asset_subreddit.sentiment_score.positive:.3f} N:{asset_subreddit.sentiment_score.negative:.3f}")
        print(f"     Date: {asset_subreddit.create_at_utc}")
