import logging
from agents.tools.states.agent_market_news_state import MarketNewsAgentState, AssetNews as MarketAssetNews, AssetNewsSentiment as MarketAssetNewsSentiment
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, AssetNews as CryptoAssetNews, AssetNewsSentiment as CryptoAssetNewsSentiment
from typing import List, Union
from dotenv import load_dotenv
import statistics

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsSentimentCalcTool:
    def __init__(self):
        """
        Tool for calculating aggregated sentiment scores from AssetNews objects.
        """
        self.sentiment_categories = ["Positive", "Negative", "Neutral"]
        logger.info("NewsSentimentCalcTool initialized")

    def calculate_aggregated_sentiment(self, asset_news_list: List[Union[MarketAssetNews, CryptoAssetNews]]) -> dict:
        """
        Calculate aggregated sentiment scores for each asset based on AssetNews objects.
        
        Args:
            asset_news_list (List[Union[MarketAssetNews, CryptoAssetNews]]): List of AssetNews objects
            
        Returns:
            dict: Aggregated sentiment data by asset
        """
        # Group news articles by asset
        asset_news_groups = {}
        
        for asset_news in asset_news_list:
            asset = asset_news.asset
            if not asset:
                continue
                
            if asset not in asset_news_groups:
                asset_news_groups[asset] = []
            asset_news_groups[asset].append(asset_news)
        
        # Calculate aggregated sentiment for each asset
        asset_sentiment_summary = {}
        
        for asset, news_articles in asset_news_groups.items():
            # Extract sentiment scores and other metrics
            sentiment_scores = []
            positive_scores = []
            negative_scores = []
            neutral_scores = []
            
            for article in news_articles:
                if article.sentiment_score:
                    sentiment = article.sentiment_score
                    positive = sentiment.positive if sentiment.positive is not None else 0
                    negative = sentiment.negative if sentiment.negative is not None else 0
                    neutral = sentiment.neutral if sentiment.neutral is not None else 0
                    
                    # More nuanced sentiment calculation with positive bias
                    if positive > negative * 1.5:  # Positive dominates
                        normalized_sentiment = 0.5 + (positive * 0.5)  # Scale to 0.5-1.0
                    elif negative > positive * 1.5:  # Negative dominates
                        normalized_sentiment = 0.5 - (negative * 0.5)  # Scale to 0.0-0.5
                    else:  # Balanced or neutral
                        # Use traditional weighted approach but with positive bias
                        weighted_sentiment = positive - negative
                        normalized_sentiment = (weighted_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
                    
                    # Apply positive bias: boost scores that are in the 0.5-0.6 range
                    if 0.5 <= normalized_sentiment < 0.6:
                        # Apply a small boost to push marginally positive scores into the Positive category
                        positive_bias = min(0.08, (positive - negative) * 0.12)  # Max boost of 0.08
                        normalized_sentiment += positive_bias
                    
                    # Ensure bounds
                    normalized_sentiment = max(0.0, min(1.0, normalized_sentiment))
                    
                    sentiment_scores.append(normalized_sentiment)
                    positive_scores.append(positive)
                    negative_scores.append(negative)
                    neutral_scores.append(neutral)
                else:
                    # If no sentiment score, treat as neutral
                    sentiment_scores.append(0.5)
                    positive_scores.append(0.33)
                    negative_scores.append(0.33)
                    neutral_scores.append(0.33)
            
            # Calculate final aggregated sentiment score
            if sentiment_scores:
                # Calculate final sentiment score with equal weighting for news articles
                final_sentiment = statistics.mean(sentiment_scores)
                
                # Apply final positive bias if score is close to threshold
                if 0.54 <= final_sentiment < 0.6:
                    # Calculate how much positive sentiment exceeds negative overall
                    overall_positive = statistics.mean(positive_scores) if positive_scores else 0
                    overall_negative = statistics.mean(negative_scores) if negative_scores else 0
                    
                    if overall_positive > overall_negative:
                        # Apply a gentle boost to push it into Positive territory
                        bias_boost = min(0.08, (overall_positive - overall_negative) * 0.12)
                        final_sentiment += bias_boost
                
                # Confidence adjustment based on number of articles
                confidence_adjustment = min(len(sentiment_scores) / 3, 1.0)  # Max confidence at 3+ articles
                confidence_adjustment = max(confidence_adjustment, 0.6)  # Minimum 0.6 confidence
                
                final_sentiment = final_sentiment * confidence_adjustment
                
                # Ensure score is between 0 and 1
                final_sentiment = max(0.0, min(1.0, final_sentiment))
                
            else:
                final_sentiment = 0.5  # Neutral if no data
                confidence_adjustment = 0.5
            
            # Create summary
            asset_sentiment_summary[asset] = {
                'asset': asset,
                'final_sentiment_score': round(final_sentiment, 4),
                'sentiment_category': self.get_sentiment_category(final_sentiment),
                'total_news': len(news_articles),
                'average_positive': round(statistics.mean(positive_scores) if positive_scores else 0, 4),
                'average_negative': round(statistics.mean(negative_scores) if negative_scores else 0, 4),
                'average_neutral': round(statistics.mean(neutral_scores) if neutral_scores else 0, 4),
                'confidence_level': round(confidence_adjustment, 2),
                'most_recent_article': news_articles[0] if news_articles else None
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
        if score >= 0.6:
            return "Positive"
        elif score >= 0.4:
            return "Neutral"
        else:
            return "Negative"


# Initialize the NewsSentimentCalcTool
news_sentiment_calc_obj = NewsSentimentCalcTool()

def calculate_news_sentiment_tool(state: Union[MarketNewsAgentState, CryptoNewsAgentState]) -> dict:
    """
    Calculate aggregated sentiment scores from AssetNews data in the state.
    
    Args:
        state (Union[MarketNewsAgentState, CryptoNewsAgentState]): The agent state containing AssetNews objects
        
    Returns:
        dict: Updated state with sentiment analysis results
    """
    # Determine state type for proper object creation and messaging
    state_type = 'crypto' if isinstance(state, CryptoNewsAgentState) else 'market'
    
    if state_type == 'crypto':
        message = "[Tool] Calculating crypto news sentiment analysis."
        AssetNewsSentimentClass = CryptoAssetNewsSentiment
        market_name = "Crypto market"
        optimistic_phrase = "bullish sentiment"
        concern_phrase = "bearish sentiment"
    else:
        message = "[Tool] Calculating news sentiment analysis."
        AssetNewsSentimentClass = MarketAssetNewsSentiment
        market_name = "Market"
        optimistic_phrase = "optimistic outlook"
        concern_phrase = "concerning outlook"
    
    logger.info(message)
    
    # Calculate aggregated sentiment scores
    sentiment_summary = news_sentiment_calc_obj.calculate_aggregated_sentiment(state.report.asset_news)
    
    # Convert sentiment_summary dict to AssetNewsSentiment objects
    asset_news_sentiments = []
    for asset, summary in sentiment_summary.items():
        asset_sentiment = AssetNewsSentimentClass(
            asset=summary['asset'],
            final_sentiment_score=summary['final_sentiment_score'],
            sentiment_category=summary['sentiment_category'],
            total_news=summary['total_news'],
            average_positive=summary['average_positive'],
            average_negative=summary['average_negative'],
            average_neutral=summary['average_neutral'],
            confidence_level=summary['confidence_level']
        )
        asset_news_sentiments.append(asset_sentiment)
    
    # Create overall diagnosis based on sentiment results
    positive_count = sum(1 for sentiment in asset_news_sentiments if sentiment.sentiment_category == 'Positive')
    negative_count = sum(1 for sentiment in asset_news_sentiments if sentiment.sentiment_category == 'Negative')
    neutral_count = sum(1 for sentiment in asset_news_sentiments if sentiment.sentiment_category == 'Neutral')
    
    total_assets = len(asset_news_sentiments)
    
    # Create market-appropriate diagnosis
    if positive_count > negative_count and positive_count > neutral_count:
        overall_diagnosis = f"Overall POSITIVE news sentiment across {positive_count}/{total_assets} assets. {market_name} shows {optimistic_phrase}."
    elif negative_count > positive_count and negative_count > neutral_count:
        overall_diagnosis = f"Overall NEGATIVE news sentiment across {negative_count}/{total_assets} assets. {market_name} shows {concern_phrase}."
    else:
        overall_diagnosis = f"MIXED news sentiment with {positive_count} positive, {negative_count} negative, {neutral_count} neutral assets. {market_name} sentiment is uncertain."
    
    # Update the state
    updated_state = state.model_copy()
    updated_state.report.asset_news_sentiments = asset_news_sentiments
    updated_state.report.overall_news_diagnosis = overall_diagnosis
    updated_state.updates.append(message)
    updated_state.next_step = "news_sentiment_summary_node"
    
    return updated_state


# Example usage
if __name__ == "__main__":
    # Test with Market News State
    print("="*80)
    print("TESTING MARKET NEWS SENTIMENT CALCULATION")
    print("="*80)
    
    from agents.tools.states.agent_market_news_state import MarketNewsAgentState, PortfolioAllocation as MarketPortfolioAllocation, AssetNews as MarketAssetNews, SentimentScore as MarketSentimentScore, Report as MarketReport
    
    # Create mock AssetNews data for testing market
    mock_market_asset_news = [
        MarketAssetNews(
            asset="SPY",
            headline="S&P 500 reaches record highs amid economic optimism",
            description="Strong earnings reports drive market gains",
            source="MarketWatch",
            posted="2 hours ago",
            link="https://example.com/spy-news-1",
            sentiment_score=MarketSentimentScore(positive=0.8, negative=0.1, neutral=0.1)
        ),
        MarketAssetNews(
            asset="SPY",
            headline="Concerns about market volatility emerge",
            description="Analysts warn of potential correction",
            source="Bloomberg",
            posted="4 hours ago",
            link="https://example.com/spy-news-2",
            sentiment_score=MarketSentimentScore(positive=0.2, negative=0.7, neutral=0.1)
        ),
        MarketAssetNews(
            asset="QQQ",
            headline="Tech stocks surge on AI innovation",
            description="Nasdaq leads market rally",
            source="CNBC",
            posted="1 hour ago",
            link="https://example.com/qqq-news-1",
            sentiment_score=MarketSentimentScore(positive=0.9, negative=0.05, neutral=0.05)
        ),
        MarketAssetNews(
            asset="GLD",
            headline="Gold prices stable amid market uncertainty",
            description="Safe haven demand supports precious metals",
            source="Reuters",
            posted="3 hours ago",
            link="https://example.com/gld-news-1",
            sentiment_score=MarketSentimentScore(positive=0.4, negative=0.3, neutral=0.3)
        )
    ]
    
    # Initialize the market state with mock data
    market_state = MarketNewsAgentState(
        portfolio_allocation=[
            MarketPortfolioAllocation(asset="SPY", description="S&P 500 ETF"),
            MarketPortfolioAllocation(asset="QQQ", description="Nasdaq ETF"),
            MarketPortfolioAllocation(asset="GLD", description="Gold ETF")
        ],
        report=MarketReport(asset_news=mock_market_asset_news),
        next_step="news_sentiment_summary_node"
    )
    
    # Calculate sentiment for market
    market_result = calculate_news_sentiment_tool(market_state)
    
    # Print market results
    print(f"Overall Diagnosis: {market_result.report.overall_news_diagnosis}")
    print(f"Next step: {market_result.next_step}")
    
    print("\nMarket News Sentiment Summary by Asset:")
    for asset_sentiment in market_result.report.asset_news_sentiments:
        print(f"\n🔸 {asset_sentiment.asset}")
        print(f"   Final Sentiment Score: {asset_sentiment.final_sentiment_score:.4f}")
        print(f"   Sentiment Category: {asset_sentiment.sentiment_category}")
        print(f"   Total News Articles: {asset_sentiment.total_news}")
        print(f"   Average Positive: {asset_sentiment.average_positive:.4f}")
        print(f"   Average Negative: {asset_sentiment.average_negative:.4f}")
        print(f"   Average Neutral: {asset_sentiment.average_neutral:.4f}")
        print(f"   Confidence Level: {asset_sentiment.confidence_level:.2f}")
    
    print(f"\nTotal market assets analyzed: {len(market_result.report.asset_news_sentiments)}")
    print(f"Total market news articles processed: {len(market_result.report.asset_news)}")

    # Test with Crypto News State
    print("\n" + "="*80)
    print("TESTING CRYPTO NEWS SENTIMENT CALCULATION")
    print("="*80)
    
    from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, PortfolioAllocation as CryptoPortfolioAllocation, AssetNews as CryptoAssetNews, SentimentScore as CryptoSentimentScore, Report as CryptoReport
    
    # Create mock AssetNews data for testing crypto
    mock_crypto_asset_news = [
        CryptoAssetNews(
            asset="BTC",
            headline="Bitcoin reaches new all-time high amid institutional adoption",
            description="Major corporations announce Bitcoin treasury holdings",
            source="CoinDesk",
            posted="2 hours ago",
            link="https://example.com/btc-news-1",
            sentiment_score=CryptoSentimentScore(positive=0.85, negative=0.08, neutral=0.07)
        ),
        CryptoAssetNews(
            asset="BTC",
            headline="Regulatory concerns weigh on Bitcoin price",
            description="Government announces stricter crypto regulations",
            source="CryptoNews",
            posted="4 hours ago",
            link="https://example.com/btc-news-2",
            sentiment_score=CryptoSentimentScore(positive=0.15, negative=0.75, neutral=0.1)
        ),
        CryptoAssetNews(
            asset="ETH",
            headline="Ethereum upgrade shows promising scalability improvements",
            description="Network congestion reduces significantly after latest update",
            source="CoinTelegraph",
            posted="1 hour ago",
            link="https://example.com/eth-news-1",
            sentiment_score=CryptoSentimentScore(positive=0.92, negative=0.03, neutral=0.05)
        ),
        CryptoAssetNews(
            asset="FDUSD",
            headline="Stablecoin market remains stable amid volatility",
            description="FDUSD maintains peg during market turbulence",
            source="CryptoDaily",
            posted="3 hours ago",
            link="https://example.com/fdusd-news-1",
            sentiment_score=CryptoSentimentScore(positive=0.45, negative=0.25, neutral=0.3)
        )
    ]
    
    # Initialize the crypto state with mock data
    crypto_state = CryptoNewsAgentState(
        portfolio_allocation=[
            CryptoPortfolioAllocation(asset="BTC", description="Bitcoin"),
            CryptoPortfolioAllocation(asset="ETH", description="Ethereum"),
            CryptoPortfolioAllocation(asset="FDUSD", description="First Digital USD")
        ],
        report=CryptoReport(asset_news=mock_crypto_asset_news),
        next_step="news_sentiment_summary_node"
    )
    
    # Calculate sentiment for crypto
    crypto_result = calculate_news_sentiment_tool(crypto_state)
    
    # Print crypto results
    print(f"Overall Diagnosis: {crypto_result.report.overall_news_diagnosis}")
    print(f"Next step: {crypto_result.next_step}")
    
    print("\nCrypto News Sentiment Summary by Asset:")
    for asset_sentiment in crypto_result.report.asset_news_sentiments:
        print(f"\n🔸 {asset_sentiment.asset}")
        print(f"   Final Sentiment Score: {asset_sentiment.final_sentiment_score:.4f}")
        print(f"   Sentiment Category: {asset_sentiment.sentiment_category}")
        print(f"   Total News Articles: {asset_sentiment.total_news}")
        print(f"   Average Positive: {asset_sentiment.average_positive:.4f}")
        print(f"   Average Negative: {asset_sentiment.average_negative:.4f}")
        print(f"   Average Neutral: {asset_sentiment.average_neutral:.4f}")
        print(f"   Confidence Level: {asset_sentiment.confidence_level:.2f}")
    
    print(f"\nTotal crypto assets analyzed: {len(crypto_result.report.asset_news_sentiments)}")
    print(f"Total crypto news articles processed: {len(crypto_result.report.asset_news)}")