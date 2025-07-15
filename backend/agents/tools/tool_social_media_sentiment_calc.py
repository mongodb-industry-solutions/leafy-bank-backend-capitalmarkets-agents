import logging
from agents.tools.states.agent_crypto_social_media_state import CryptoSocialMediaAgentState, AssetSubreddits as CryptoAssetSubreddits
from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState, AssetSubreddits as MarketAssetSubreddits
from typing import Union
from dotenv import load_dotenv
from datetime import datetime, timezone
import statistics

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SocialMediaSentimentCalcTool:
    def __init__(self):
        """
        Tool for calculating aggregated sentiment scores from AssetSubreddits objects.
        """
        self.sentiment_categories = ["Positive", "Negative", "Neutral"]
        logger.info("SocialMediaSentimentCalcTool initialized")

    def calculate_aggregated_sentiment(self, asset_subreddits: list) -> dict:
        """
        Calculate aggregated sentiment scores for each asset based on AssetSubreddits objects.
        
        Args:
            asset_subreddits (list): List of AssetSubreddits objects
            
        Returns:
            dict: Aggregated sentiment data by asset
        """
        # Group submissions by asset
        asset_submissions = {}
        
        for asset_subreddit in asset_subreddits:
            asset = asset_subreddit.asset
            if not asset:
                continue
                
            if asset not in asset_submissions:
                asset_submissions[asset] = []
            asset_submissions[asset].append(asset_subreddit)
        
        # Calculate aggregated sentiment for each asset
        asset_sentiment_summary = {}
        
        for asset, subs in asset_submissions.items():
            # Sort submissions by create_at_utc (most recent first)
            sorted_subs = sorted(subs, key=lambda x: datetime.fromisoformat(x.create_at_utc) if x.create_at_utc else datetime.min, reverse=True)
            
            # Extract sentiment scores and other metrics
            sentiment_scores = []
            positive_scores = []
            negative_scores = []
            neutral_scores = []
            
            total_score = 0
            total_comments = 0
            total_ups = 0
            recent_submissions = 0
            
            # Calculate cutoff for "recent" submissions (last 10 days)
            now = datetime.now(timezone.utc)
            recent_cutoff = now.timestamp() - (10 * 24 * 60 * 60)  # 10 days ago
            
            for sub in sorted_subs:
                sentiment = sub.sentiment_score
                positive = sentiment.positive if sentiment.positive is not None else 0
                negative = sentiment.negative if sentiment.negative is not None else 0
                neutral = sentiment.neutral if sentiment.neutral is not None else 0
                
                # More nuanced sentiment calculation
                # If positive is significantly higher than negative, treat as positive
                # If negative is significantly higher than positive, treat as negative
                # Otherwise, use the weighted approach
                
                if positive > negative * 1.5:  # Positive dominates
                    normalized_sentiment = 0.5 + (positive * 0.5)  # Scale to 0.5-1.0
                elif negative > positive * 1.5:  # Negative dominates
                    normalized_sentiment = 0.5 - (negative * 0.5)  # Scale to 0.0-0.5
                else:  # Balanced or neutral
                    # Use traditional weighted approach but with less penalty
                    weighted_sentiment = positive - negative
                    normalized_sentiment = (weighted_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
                
                # Ensure bounds
                normalized_sentiment = max(0.0, min(1.0, normalized_sentiment))
                
                sentiment_scores.append(normalized_sentiment)
                positive_scores.append(positive)
                negative_scores.append(negative)
                neutral_scores.append(neutral)
                
                # Engagement metrics (reduced weight)
                score = sub.score if sub.score is not None else 0
                comments = sub.num_comments if sub.num_comments is not None else 0
                ups = sub.ups if sub.ups is not None else 0
                
                total_score += score
                total_comments += comments
                total_ups += ups
                
                # Check if submission is recent
                if sub.create_at_utc:
                    sub_timestamp = datetime.fromisoformat(sub.create_at_utc)
                    if sub_timestamp.timestamp() > recent_cutoff:
                        recent_submissions += 1
                
            # Calculate final aggregated sentiment score
            if sentiment_scores:
                # Simplified weighting with minimal engagement impact
                weighted_scores = []
                for i, score in enumerate(sentiment_scores):
                    # Minimal time weight (recent submissions get slight boost)
                    time_weight = 1.1 if i < 3 else 1.0
                    
                    # Minimal engagement weight (very small impact)
                    engagement = (sorted_subs[i].score or 0) * 0.3 + (sorted_subs[i].num_comments or 0) * 0.2 + (sorted_subs[i].ups or 0) * 0.1
                    engagement_weight = min(engagement / 1000, 0.1) + 1.0  # Very small boost, max 1.1
                    
                    weighted_score = score * time_weight * engagement_weight
                    weighted_scores.append(weighted_score)
                
                # Calculate final sentiment score
                final_sentiment = statistics.mean(weighted_scores)
                
                # Reduced confidence penalty (less harsh)
                confidence_adjustment = min(len(sentiment_scores) / 5, 1.0)  # Max confidence at 5+ samples
                confidence_adjustment = max(confidence_adjustment, 0.7)  # Minimum 0.7 confidence
                
                final_sentiment = final_sentiment * confidence_adjustment
                
                # Ensure score is between 0 and 1
                final_sentiment = max(0.0, min(1.0, final_sentiment))
                
            else:
                final_sentiment = 0.5  # Neutral if no data
            
            # Create summary
            asset_sentiment_summary[asset] = {
                'asset': asset,
                'final_sentiment_score': round(final_sentiment, 4),
                'sentiment_category': self.get_sentiment_category(final_sentiment),
                'total_submissions': len(sorted_subs),
                'recent_submissions': recent_submissions,
                'average_positive': round(statistics.mean(positive_scores) if positive_scores else 0, 4),
                'average_negative': round(statistics.mean(negative_scores) if negative_scores else 0, 4),
                'average_neutral': round(statistics.mean(neutral_scores) if neutral_scores else 0, 4),
                'total_engagement_score': total_score,
                'total_comments': total_comments,
                'total_ups': total_ups,
                'most_recent_submission': sorted_subs[0] if sorted_subs else None,
                'confidence_level': round(confidence_adjustment, 2)
            }
        
        return asset_sentiment_summary

    def get_sentiment_category(self, score: float) -> str:
        """
        Categorize sentiment score into 3 categories: Positive, Neutral, Negative.
        
        Args:
            score (float): Sentiment score from 0.0 to 1.0
            
        Returns:
            str: Sentiment category
        """
        if score >= 0.55:  # Lowered threshold for positive
            return "Positive"
        elif score >= 0.45:  # Narrowed neutral range
            return "Neutral"
        else:
            return "Negative"


# Initialize the SocialMediaSentimentCalcTool
social_media_sentiment_calc_obj = SocialMediaSentimentCalcTool()

def calculate_social_media_sentiment_tool(state: Union[CryptoSocialMediaAgentState, MarketSocialMediaAgentState]) -> dict:
    """
    Calculate aggregated sentiment scores from AssetSubreddits data in the state.
    
    Args:
        state (Union[CryptoSocialMediaAgentState, MarketSocialMediaAgentState]): The agent state containing AssetSubreddits objects
        
    Returns:
        dict: Updated state with sentiment analysis results
    """
    # Calculate aggregated sentiment scores
    sentiment_summary = social_media_sentiment_calc_obj.calculate_aggregated_sentiment(state.report.asset_subreddits)
    
    # Import the appropriate AssetSocialMediaSentiment class based on state type
    if isinstance(state, CryptoSocialMediaAgentState):
        from agents.tools.states.agent_crypto_social_media_state import AssetSocialMediaSentiment
        asset_type = "crypto"
    else:  # MarketSocialMediaAgentState
        from agents.tools.states.agent_market_social_media_state import AssetSocialMediaSentiment
        asset_type = "market"
    
    # Convert sentiment_summary dict to AssetSocialMediaSentiment objects
    asset_sm_sentiments = []
    for asset, summary in sentiment_summary.items():
        asset_sentiment = AssetSocialMediaSentiment(
            asset=summary['asset'],
            final_sentiment_score=summary['final_sentiment_score'],
            sentiment_category=summary['sentiment_category'],
            total_submissions=summary['total_submissions'],
            recent_submissions=summary['recent_submissions'],
            average_positive=summary['average_positive'],
            average_negative=summary['average_negative'],
            average_neutral=summary['average_neutral'],
            total_engagement_score=summary['total_engagement_score'],
            total_comments=summary['total_comments'],
            total_ups=summary['total_ups'],
            confidence_level=summary['confidence_level']
        )
        asset_sm_sentiments.append(asset_sentiment)
    
    # Create overall diagnosis based on sentiment results
    positive_count = sum(1 for sentiment in asset_sm_sentiments if sentiment.sentiment_category == 'Positive')
    negative_count = sum(1 for sentiment in asset_sm_sentiments if sentiment.sentiment_category == 'Negative')
    neutral_count = sum(1 for sentiment in asset_sm_sentiments if sentiment.sentiment_category == 'Neutral')
    
    total_assets = len(asset_sm_sentiments)
    
    # Create market-appropriate diagnosis based on asset type
    if asset_type == "crypto":
        market_name = "Crypto market"
        optimistic_phrase = "bullish sentiment"
        concern_phrase = "bearish sentiment"
    else:
        market_name = "market"
        optimistic_phrase = "positive outlook"
        concern_phrase = "negative outlook"
    
    if positive_count > negative_count and positive_count > neutral_count:
        overall_diagnosis = f"Overall POSITIVE sentiment across {positive_count}/{total_assets} assets. {market_name} shows {optimistic_phrase}."
    elif negative_count > positive_count and negative_count > neutral_count:
        overall_diagnosis = f"Overall NEGATIVE sentiment across {negative_count}/{total_assets} assets. {market_name} shows {concern_phrase}."
    else:
        overall_diagnosis = f"MIXED sentiment with {positive_count} positive, {negative_count} negative, {neutral_count} neutral assets. {market_name} sentiment is uncertain."
    
    # Update the state
    updated_state = state.model_copy()
    updated_state.report.asset_sm_sentiments = asset_sm_sentiments
    updated_state.report.overall_news_diagnosis = overall_diagnosis
    updated_state.next_step = "social_media_sentiment_summary_node"
    
    return updated_state


# Example usage
if __name__ == "__main__":
    # Test with Crypto Social Media State
    print("="*80)
    print("TESTING CRYPTO SOCIAL MEDIA STATE")
    print("="*80)
    
    from agents.tools.states.agent_crypto_social_media_state import CryptoSocialMediaAgentState, PortfolioAllocation as CryptoPortfolioAllocation, Report as CryptoReport, AssetSubreddits as CryptoAssetSubreddits, SentimentScore as CryptoSentimentScore

    # Create mock AssetSubreddits data for testing crypto
    mock_crypto_asset_subreddits = [
        CryptoAssetSubreddits(
            asset="BTC",
            title="Bitcoin hits new highs",
            sentiment_score=CryptoSentimentScore(positive=0.8, negative=0.1, neutral=0.1),
            score=100,
            num_comments=50,
            ups=90,
            create_at_utc=datetime.now().isoformat()
        ),
        CryptoAssetSubreddits(
            asset="BTC", 
            title="Bitcoin volatility concerns",
            sentiment_score=CryptoSentimentScore(positive=0.2, negative=0.7, neutral=0.1),
            score=80,
            num_comments=30,
            ups=70,
            create_at_utc=datetime.now().isoformat()
        ),
        CryptoAssetSubreddits(
            asset="ETH",
            title="Ethereum rally continues",
            sentiment_score=CryptoSentimentScore(positive=0.9, negative=0.05, neutral=0.05),
            score=150,
            num_comments=75,
            ups=140,
            create_at_utc=datetime.now().isoformat()
        )
    ]

    # Initialize the crypto state with mock data
    crypto_state = CryptoSocialMediaAgentState(
        portfolio_allocation=[
            CryptoPortfolioAllocation(asset="BTC", asset_type="Cryptocurrency", description="Bitcoin"),
            CryptoPortfolioAllocation(asset="ETH", asset_type="Cryptocurrency", description="Ethereum")
        ],
        report=CryptoReport(asset_subreddits=mock_crypto_asset_subreddits),
        next_step="social_media_sentiment_calc_node"
    )

    # Calculate sentiment for crypto
    crypto_result = calculate_social_media_sentiment_tool(crypto_state)

    # Print crypto results
    print(f"Overall Diagnosis: {crypto_result.report.overall_news_diagnosis}")
    print(f"Next step: {crypto_result.next_step}")
    
    print("\nCrypto Sentiment Summary by Asset:")
    for asset_sentiment in crypto_result.report.asset_sm_sentiments:
        print(f"\n🔸 {asset_sentiment.asset}")
        print(f"   Final Sentiment Score: {asset_sentiment.final_sentiment_score:.4f}")
        print(f"   Sentiment Category: {asset_sentiment.sentiment_category}")
        print(f"   Total Submissions: {asset_sentiment.total_submissions}")
        print(f"   Recent Submissions (10 days): {asset_sentiment.recent_submissions}")
        print(f"   Average Positive: {asset_sentiment.average_positive:.4f}")
        print(f"   Average Negative: {asset_sentiment.average_negative:.4f}")
        print(f"   Confidence Level: {asset_sentiment.confidence_level:.2f}")

    # Test with Market Social Media State
    print("\n" + "="*80)
    print("TESTING MARKET SOCIAL MEDIA STATE")
    print("="*80)
    
    from agents.tools.states.agent_market_social_media_state import MarketSocialMediaAgentState, PortfolioAllocation as MarketPortfolioAllocation, Report as MarketReport, AssetSubreddits as MarketAssetSubreddits, SentimentScore as MarketSentimentScore

    # Create mock AssetSubreddits data for testing market
    mock_market_asset_subreddits = [
        MarketAssetSubreddits(
            asset="SPY",
            title="S&P 500 hits new highs",
            sentiment_score=MarketSentimentScore(positive=0.8, negative=0.1, neutral=0.1),
            score=100,
            num_comments=50,
            ups=90,
            create_at_utc=datetime.now().isoformat()
        ),
        MarketAssetSubreddits(
            asset="SPY", 
            title="Market volatility concerns",
            sentiment_score=MarketSentimentScore(positive=0.2, negative=0.7, neutral=0.1),
            score=80,
            num_comments=30,
            ups=70,
            create_at_utc=datetime.now().isoformat()
        ),
        MarketAssetSubreddits(
            asset="QQQ",
            title="Tech stocks rally continues",
            sentiment_score=MarketSentimentScore(positive=0.9, negative=0.05, neutral=0.05),
            score=150,
            num_comments=75,
            ups=140,
            create_at_utc=datetime.now().isoformat()
        )
    ]

    # Initialize the market state with mock data
    market_state = MarketSocialMediaAgentState(
        portfolio_allocation=[
            MarketPortfolioAllocation(asset="SPY", description="S&P 500 ETF"),
            MarketPortfolioAllocation(asset="QQQ", description="Nasdaq ETF")
        ],
        report=MarketReport(asset_subreddits=mock_market_asset_subreddits),
        next_step="social_media_sentiment_calc_node"
    )

    # Calculate sentiment for market
    market_result = calculate_social_media_sentiment_tool(market_state)

    # Print market results
    print(f"Overall Diagnosis: {market_result.report.overall_news_diagnosis}")
    print(f"Next step: {market_result.next_step}")
    
    print("\nMarket Sentiment Summary by Asset:")
    for asset_sentiment in market_result.report.asset_sm_sentiments:
        print(f"\n🔸 {asset_sentiment.asset}")
        print(f"   Final Sentiment Score: {asset_sentiment.final_sentiment_score:.4f}")
        print(f"   Sentiment Category: {asset_sentiment.sentiment_category}")
        print(f"   Total Submissions: {asset_sentiment.total_submissions}")
        print(f"   Recent Submissions (10 days): {asset_sentiment.recent_submissions}")
        print(f"   Average Positive: {asset_sentiment.average_positive:.4f}")
        print(f"   Average Negative: {asset_sentiment.average_negative:.4f}")
        print(f"   Confidence Level: {asset_sentiment.confidence_level:.2f}")