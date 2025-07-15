import logging
from agents.tools.db.mdb import MongoDBConnector
from agents.tools.states.agent_market_news_state import MarketNewsAgentState, AssetNewsSentiment as MarketAssetNewsSentiment
from agents.tools.bedrock.anthropic_chat_completions import BedrockAnthropicChatCompletions
from agents.tools.agent_profiles import AgentProfiles
from agents.tools.risk_profiles import RiskProfiles
import os
from dotenv import load_dotenv
from typing import Optional, Dict, List, Union
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsSentimentSummaryTool(MongoDBConnector):
    def __init__(self, chat_completions_model_id: Optional[str] = os.getenv("CHAT_COMPLETIONS_MODEL_ID")):
        """
        NewsSentimentSummaryTool class to generate summaries and calculate sentiment metrics for financial news articles.
        This class uses the BedrockAnthropicChatCompletions model to generate concise summaries.
        Currently supports market news agent states, prepared for future crypto news agent states.
        
        Args:
            chat_completions_model_id (str): Model ID for chat completions. Default is os.getenv("CHAT_COMPLETIONS_MODEL_ID").
        """
        self.chat_completions_model_id = chat_completions_model_id
        logger.info("NewsSentimentSummaryTool initialized")
    
    def group_news_by_asset(self, state: MarketNewsAgentState) -> Dict[str, List]:
        """Group financial news articles by asset symbol."""
        asset_news_groups = defaultdict(list)
        
        for article in state.report.asset_news:
            if article.asset:
                asset_news_groups[article.asset].append(article)
        
        return asset_news_groups
    
    def get_asset_sentiment_by_asset(self, state: MarketNewsAgentState) -> Dict[str, MarketAssetNewsSentiment]:
        """Create a lookup dictionary for asset sentiments by asset symbol."""
        asset_sentiment_lookup = {}
        
        for sentiment in state.report.asset_news_sentiments:
            if sentiment.asset:
                asset_sentiment_lookup[sentiment.asset] = sentiment
        
        return asset_sentiment_lookup
    
    def truncate_text(self, text: str, max_length: int = 1500) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def generate_asset_summary(self, asset: str, description: str, news_articles: List, asset_sentiment: MarketAssetNewsSentiment, agent_profile: dict) -> str:
        """Generate a summary for an asset's financial news articles using LLM."""
        # Limit to first 3 articles with character limit
        limited_articles = news_articles[:3]
        
        # Prepare news articles content for the LLM
        news_content = []
        for i, article in enumerate(limited_articles, 1):
            news_content.append(f"Article {i}:")
            news_content.append(f"Headline: {self.truncate_text(article.headline or '', 200)}")
            news_content.append(f"Description: {self.truncate_text(article.description or '', 1500)}")
            news_content.append(f"Source: {article.source}")
            news_content.append(f"Posted: {article.posted}")
            if article.sentiment_score:
                news_content.append(f"Sentiment: Positive: {article.sentiment_score.positive}, Negative: {article.sentiment_score.negative}, Neutral: {article.sentiment_score.neutral}")
            news_content.append("")
        
        news_context = "\n".join(news_content)
        
        # Prepare sentiment analysis context
        sentiment_context = ""
        if asset_sentiment:
            sentiment_context = (
                f"Overall Sentiment Analysis for {asset}:\n"
                f"- Sentiment Category: {asset_sentiment.sentiment_category}\n"
                f"- Total News Articles: {asset_sentiment.total_news}\n"
                f"- Confidence Level: {asset_sentiment.confidence_level}\n"
                f"- Average Positive: {asset_sentiment.average_positive}\n"
                f"- Average Negative: {asset_sentiment.average_negative}\n\n"
            )
        
        # Generate the LLM prompt
        llm_prompt = (
            f"You are a {agent_profile['role']} "
            f"Your task is to provide a concise summary of recent financial news sentiment about {asset} ({description}).\n\n"
            f"Instructions: {agent_profile['instructions']}\n\n"
            f"Rules: {agent_profile['rules']}\n\n"
            f"{sentiment_context}"
            f"Recent Financial News Articles:\n{news_context}\n\n"
            f"Generate a concise summary of the financial news sentiment for {asset} ({description}). "
            f"Focus on key insights and implications for investors based on recent news coverage. Be objective and factual."
        )

        logger.info(f"LLM Prompt for {asset} financial news sentiment summary:")
        logger.info(llm_prompt)
        
        try:
            # Instantiate the chat completion model
            chat_completions = BedrockAnthropicChatCompletions(model_id=self.chat_completions_model_id)
            # Generate summary
            summary = chat_completions.predict(llm_prompt)
            
            # Truncate if necessary to ensure it's under 80 words
            words = summary.split()
            if len(words) > 80:
                summary = " ".join(words[:80]) + "..."
                
            return summary
        except Exception as e:
            logger.error(f"Error generating summary for {asset}: {e}")
            if asset_sentiment:
                return f"Recent financial news for {asset} indicates {asset_sentiment.sentiment_category.lower()} market perception with {asset_sentiment.confidence_level} confidence level based on {asset_sentiment.total_news} articles."
            else:
                return f"Recent financial news coverage about {asset} shows mixed market sentiment."
    
    def generate_news_sentiment_summary(self, state: MarketNewsAgentState) -> dict:
        """
        Generate summaries for financial news articles grouped by asset.
        
        Args:
            state (MarketNewsAgentState): The current state of the news agent.
            
        Returns:
            dict: Updated state with enhanced asset news sentiment summaries.
        """
        message = "[Tool] Generating financial news sentiment summaries."
        logger.info(message)

        # Determine agent ID based on state type (prepared for future crypto news agent)
        if hasattr(state, 'portfolio_allocation') and state.portfolio_allocation:
            # Check if this is crypto-related by looking for crypto-specific fields
            first_allocation = state.portfolio_allocation[0]
            if hasattr(first_allocation, 'asset_type') and first_allocation.asset_type:
                agent_id = "CRYPTO_NEWS_AGENT"
            else:
                agent_id = "MARKET_NEWS_AGENT"
        else:
            agent_id = "MARKET_NEWS_AGENT"  # Default to market news

        # Retrieve the active risk profile (fallback is handled internally in RiskProfiles)
        risk_profiles = RiskProfiles()
        active_risk_profile = risk_profiles.get_active_risk_profile()
        state.updates.append(
            f"[Action] Using risk profile: {active_risk_profile['risk_id']} - {active_risk_profile.get('short_description', 'No description')}"
        )
        
        # Retrieve the appropriate agent profile
        profiler = AgentProfiles()
        agent_profile = profiler.get_agent_profile(agent_id)
        if not agent_profile:
            logger.error(f"Agent profile not found for agent ID: {agent_id}")
            state.updates.append(f"Unable to generate news sentiment summaries due to missing agent profile: {agent_id}.")
            return {"updates": state.updates, "next_step": state.next_step}
        
        state.updates.append(f"[Action] Using agent profile: {agent_id} - {agent_profile['role']}")
        
        # Group news articles by asset
        asset_news_groups = self.group_news_by_asset(state)
        
        # Get asset sentiment lookup
        asset_sentiment_lookup = self.get_asset_sentiment_by_asset(state)
        
        # Create asset description lookup
        asset_descriptions = {allocation.asset: allocation.description for allocation in state.portfolio_allocation}
        
        # Process each existing asset sentiment and add summary directly to the object
        for asset_sentiment in state.report.asset_news_sentiments:
            asset = asset_sentiment.asset
            news_articles = asset_news_groups.get(asset, [])
            
            # Get asset description
            description = asset_descriptions.get(asset, "")
            
            # Generate summary using LLM if we have news articles
            if news_articles:
                summary_text = self.generate_asset_summary(asset, description, news_articles, asset_sentiment, agent_profile)
                # Set the sentiment_summary directly on the existing object
                asset_sentiment.sentiment_summary = summary_text
            else:
                # Provide a fallback summary if no news articles
                asset_sentiment.sentiment_summary = f"Limited financial news coverage for {asset}. Sentiment analysis based on available data shows {asset_sentiment.sentiment_category.lower()} indicators."
        
        # Generate comprehensive overall diagnosis using all asset summaries and risk profile
        if state.report.asset_news_sentiments:
            try:
                # Collect all asset summaries for context
                asset_summaries_context = []
                for sentiment in state.report.asset_news_sentiments:
                    asset_summaries_context.append(
                        f"- {sentiment.asset}: {sentiment.sentiment_category} sentiment (Score: {sentiment.final_sentiment_score:.2f}, "
                        f"Confidence: {sentiment.confidence_level:.2f}, Articles: {sentiment.total_news})\n"
                        f"  Summary: {sentiment.sentiment_summary or 'No summary available'}"
                    )
                
                # Determine market context based on agent type
                if agent_id == "CRYPTO_NEWS_AGENT":
                    market_context = "cryptocurrency portfolio"
                    market_type = "crypto assets"
                else:
                    market_context = "traditional market portfolio"
                    market_type = "traditional market assets"
                
                overall_prompt = (
                    f"===== INVESTOR RISK PROFILE =====\n"
                    f"Risk Profile ID      : {active_risk_profile['risk_id']}\n"
                    f"Description          : {active_risk_profile.get('short_description', 'No description')}\n"
                    f"================================\n\n"
                    f"You are a {agent_profile['role']}. "
                    f"Based on the following comprehensive financial news sentiment analysis for the entire {market_context}, "
                    f"provide a unified overall diagnosis that considers all {market_type} collectively.\n\n"
                    f"PORTFOLIO ASSET NEWS SENTIMENT ANALYSIS:\n"
                    f"{'='*50}\n"
                    f"{chr(10).join(asset_summaries_context)}\n"
                    f"{'='*50}\n\n"
                    f"Generate a comprehensive overall portfolio diagnosis (maximum 250 words) that:\n"
                    f"1. Synthesizes the news sentiment across all portfolio assets\n"
                    f"2. Provides actionable insights aligned with the investor's risk profile\n"
                    f"3. Considers portfolio-level implications and correlations\n"
                    f"4. Offers strategic recommendations based on the financial news landscape\n"
                    f"5. Addresses how the overall news sentiment aligns with the investor's objectives and risk tolerance\n"
                    f"6. If possible, include relevant highlights from the most recent financial news coverage that support the analysis."
                )
                
                chat_completions = BedrockAnthropicChatCompletions(model_id=self.chat_completions_model_id)
                enhanced_diagnosis = chat_completions.predict(overall_prompt)
                
                # Truncate if necessary
                words = enhanced_diagnosis.split()
                if len(words) > 250:
                    enhanced_diagnosis = " ".join(words[:250]) + "..."
                
                state.report.overall_news_diagnosis = enhanced_diagnosis
                
            except Exception as e:
                logger.error(f"Error generating enhanced overall diagnosis: {e}")
                # Create a fallback diagnosis based on sentiment categories
                sentiment_categories = [s.sentiment_category for s in state.report.asset_news_sentiments if s.sentiment_category]
                if sentiment_categories:
                    positive_count = sentiment_categories.count("Positive")
                    negative_count = sentiment_categories.count("Negative") 
                    neutral_count = sentiment_categories.count("Neutral")
                    
                    dominant_sentiment = "Mixed"
                    if positive_count > negative_count and positive_count > neutral_count:
                        dominant_sentiment = "Positive"
                    elif negative_count > positive_count and negative_count > neutral_count:
                        dominant_sentiment = "Negative"
                    elif neutral_count > positive_count and neutral_count > negative_count:
                        dominant_sentiment = "Neutral"
                    
                    # Create context-appropriate fallback message
                    if agent_id == "CRYPTO_NEWS_AGENT":
                        market_context = "cryptocurrency"
                    else:
                        market_context = "traditional market"
                    
                    state.report.overall_news_diagnosis = (
                        f"Portfolio financial news sentiment analysis shows {dominant_sentiment.lower()} overall trends "
                        f"for {market_context} assets. Based on {len(state.report.asset_news_sentiments)} assets analyzed, "
                        f"consider adjusting positions according to your {active_risk_profile['risk_id']} risk profile."
                    )
        
        # Update state with message
        state.updates.append(message)

        # Set the next step in the state
        state.next_step = "__end__"

        return {
            "asset_news_sentiments": state.report.asset_news_sentiments,
            "overall_news_diagnosis": state.report.overall_news_diagnosis,
            "updates": state.updates,
            "next_step": state.next_step
        }

# Initialize the NewsSentimentSummaryTool
news_sentiment_summary_obj = NewsSentimentSummaryTool()

# Define tools
def generate_news_sentiment_summary_tool(state: MarketNewsAgentState) -> dict:
    """Generate summaries for financial news articles grouped by asset."""
    return news_sentiment_summary_obj.generate_news_sentiment_summary(state=state)

# Example usage
if __name__ == "__main__":
    print("="*80)
    print("TESTING MARKET NEWS SENTIMENT SUMMARY")
    print("="*80)
    
    from agents.tools.states.agent_market_news_state import MarketNewsAgentState, PortfolioAllocation, AssetNews, AssetNewsSentiment, SentimentScore, Report
    
    # Create mock AssetNews data for testing
    mock_asset_news = [
        AssetNews(
            asset="SPY",
            headline="S&P 500 reaches record highs amid economic optimism",
            description="Strong earnings reports and economic data drive market gains as investors show confidence in corporate fundamentals",
            source="MarketWatch",
            posted="2 hours ago",
            link="https://example.com/spy-news-1",
            sentiment_score=SentimentScore(positive=0.8, negative=0.1, neutral=0.1)
        ),
        AssetNews(
            asset="SPY",
            headline="Concerns about market volatility emerge",
            description="Analysts warn of potential correction as valuations appear stretched across multiple sectors",
            source="Bloomberg",
            posted="4 hours ago",
            link="https://example.com/spy-news-2",
            sentiment_score=SentimentScore(positive=0.2, negative=0.7, neutral=0.1)
        ),
        AssetNews(
            asset="QQQ",
            headline="Tech stocks surge on AI innovation breakthrough",
            description="Nasdaq leads market rally as artificial intelligence sector shows unprecedented growth potential",
            source="CNBC",
            posted="1 hour ago",
            link="https://example.com/qqq-news-1",
            sentiment_score=SentimentScore(positive=0.9, negative=0.05, neutral=0.05)
        ),
        AssetNews(
            asset="GLD",
            headline="Gold prices stable amid market uncertainty",
            description="Safe haven demand supports precious metals as investors seek diversification strategies",
            source="Reuters",
            posted="3 hours ago",
            link="https://example.com/gld-news-1",
            sentiment_score=SentimentScore(positive=0.4, negative=0.3, neutral=0.3)
        )
    ]
    
    # Create mock AssetNewsSentiment data
    mock_asset_news_sentiments = [
        AssetNewsSentiment(
            asset="SPY",
            final_sentiment_score=0.65,
            sentiment_category="Positive",
            total_news=2,
            average_positive=0.5,
            average_negative=0.4,
            average_neutral=0.1,
            confidence_level=0.75
        ),
        AssetNewsSentiment(
            asset="QQQ",
            final_sentiment_score=0.85,
            sentiment_category="Positive",
            total_news=1,
            average_positive=0.9,
            average_negative=0.05,
            average_neutral=0.05,
            confidence_level=0.80
        ),
        AssetNewsSentiment(
            asset="GLD",
            final_sentiment_score=0.52,
            sentiment_category="Neutral",
            total_news=1,
            average_positive=0.4,
            average_negative=0.3,
            average_neutral=0.3,
            confidence_level=0.70
        )
    ]
    
    # Initialize the state with mock data
    state = MarketNewsAgentState(
        portfolio_allocation=[
            PortfolioAllocation(asset="SPY", description="S&P 500 ETF", allocation_percentage="25%"),
            PortfolioAllocation(asset="QQQ", description="Nasdaq ETF", allocation_percentage="20%"),
            PortfolioAllocation(asset="GLD", description="Gold ETF", allocation_percentage="8%")
        ],
        report=Report(
            asset_news=mock_asset_news,
            asset_news_sentiments=mock_asset_news_sentiments
        ),
        next_step="generate_news_sentiment_summary_node"
    )
    
    # Generate summaries
    result = generate_news_sentiment_summary_tool(state)
    
    # Print results
    print(f"Overall Diagnosis: {state.report.overall_news_diagnosis}")
    print(f"Next step: {state.next_step}")
    
    print("\nNews Sentiment Summary by Asset:")
    for asset_sentiment in state.report.asset_news_sentiments:
        print(f"\n🔸 {asset_sentiment.asset}")
        print(f"   Final Sentiment Score: {asset_sentiment.final_sentiment_score:.4f}")
        print(f"   Sentiment Category: {asset_sentiment.sentiment_category}")
        print(f"   Total News Articles: {asset_sentiment.total_news}")
        print(f"   Average Positive: {asset_sentiment.average_positive:.4f}")
        print(f"   Average Negative: {asset_sentiment.average_negative:.4f}")
        print(f"   Confidence Level: {asset_sentiment.confidence_level:.2f}")
        print(f"   Summary: {asset_sentiment.sentiment_summary[:100] if asset_sentiment.sentiment_summary else 'No summary'}...")
    
    print(f"\nTotal assets analyzed: {len(state.report.asset_news_sentiments)}")
    print(f"Total news articles processed: {len(state.report.asset_news)}")