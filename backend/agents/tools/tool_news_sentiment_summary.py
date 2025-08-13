import logging
from agents.tools.db.mdb import MongoDBConnector
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, AssetNewsSentiment as CryptoAssetNewsSentiment
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
        NewsSentimentSummaryTool class to generate summaries and calculate sentiment metrics for news articles.
        This class uses the BedrockAnthropicChatCompletions model to generate concise summaries.
        Supports both crypto and market news agent states.
        
        Args:
            chat_completions_model_id (str): Model ID for chat completions. Default is os.getenv("CHAT_COMPLETIONS_MODEL_ID").
        """
        self.chat_completions_model_id = chat_completions_model_id
        logger.info("NewsSentimentSummaryTool initialized")
    
    def group_news_by_asset(self, state: Union[CryptoNewsAgentState, MarketNewsAgentState]) -> Dict[str, List]:
        """Group news articles by asset symbol."""
        asset_news_groups = defaultdict(list)
        
        for news in state.report.asset_news:
            if news.asset:
                asset_news_groups[news.asset].append(news)
        
        return asset_news_groups
    
    def get_asset_sentiment_by_asset(self, state: Union[CryptoNewsAgentState, MarketNewsAgentState]) -> Dict[str, Union[CryptoAssetNewsSentiment, MarketAssetNewsSentiment]]:
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
    
    def generate_asset_summary(self, asset: str, description: str, news_group: List, asset_sentiment: Union[CryptoAssetNewsSentiment, MarketAssetNewsSentiment], agent_profile: dict) -> str:
        """Generate a summary for an asset's news articles using LLM."""
        # Limit to first 3 news articles with character limit
        limited_news = news_group[:3]
        
        # Prepare news content for the LLM
        news_content = []
        for i, news in enumerate(limited_news, 1):
            news_content.append(f"Article {i}:")
            news_content.append(f"Headline: {self.truncate_text(news.headline or '', 200)}")
            news_content.append(f"Description: {self.truncate_text(news.description or '', 1500)}")
            news_content.append(f"Source: {news.source}, Posted: {news.posted}")
            if news.sentiment_score:
                news_content.append(f"Sentiment: Positive: {news.sentiment_score.positive}, Negative: {news.sentiment_score.negative}, Neutral: {news.sentiment_score.neutral}")
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
                f"- Average Negative: {asset_sentiment.average_negative}\n"
                f"- Average Neutral: {asset_sentiment.average_neutral}\n\n"
            )
        
        # Generate the LLM prompt
        llm_prompt = (
            f"You are a {agent_profile['role']} "
            f"Your task is to provide a concise summary of recent news sentiment about {asset} ({description}).\n\n"
            f"Instructions: {agent_profile['instructions']}\n\n"
            f"Rules: {agent_profile['rules']}\n\n"
            f"{sentiment_context}"
            f"Recent News Articles:\n{news_context}\n\n"
            f"Generate a concise summary of the news sentiment for {asset} ({description}). "
            f"Focus on key insights and implications for investors based on recent news coverage. Be objective and factual."
        )

        logger.info(f"LLM Prompt for {asset} news sentiment summary:")
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
                return f"Recent news sentiment for {asset} indicates {asset_sentiment.sentiment_category.lower()} market perception with {asset_sentiment.confidence_level} confidence level."
            else:
                return f"Recent news coverage about {asset} shows mixed market sentiment."
    
    def generate_news_sentiment_summary(self, state: Union[CryptoNewsAgentState, MarketNewsAgentState]) -> dict:
        """
        Generate summaries for news articles grouped by asset.
        
        Args:
            state (Union[CryptoNewsAgentState, MarketNewsAgentState]): The current state of the news agent.
            
        Returns:
            dict: Updated state with enhanced asset sentiment summaries.
        """
        message = "[Tool] Generating news sentiment summaries."
        logger.info(message)

        # Determine agent ID based on state type
        if isinstance(state, CryptoNewsAgentState):
            agent_id = "CRYPTO_NEWS_AGENT"
        else:  # MarketNewsAgentState
            agent_id = "MARKET_NEWS_AGENT"

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
            state.updates.append(f"Unable to generate sentiment summaries due to missing agent profile: {agent_id}.")
            return {"updates": state.updates, "next_step": state.next_step}
        
        state.updates.append(f"[Action] Using agent profile: {agent_id} - {agent_profile['role']}")
        
        # Group news by asset
        asset_news_groups = self.group_news_by_asset(state)
        
        # Get asset sentiment lookup
        asset_sentiment_lookup = self.get_asset_sentiment_by_asset(state)
        
        # Create asset description lookup
        asset_descriptions = {allocation.asset: allocation.description for allocation in state.portfolio_allocation}
        
        # Process each existing asset sentiment and add summary directly to the object
        for asset_sentiment in state.report.asset_news_sentiments:
            asset = asset_sentiment.asset
            news_group = asset_news_groups.get(asset, [])
            
            # Get asset description
            description = asset_descriptions.get(asset, "")
            
            # Generate summary using LLM if we have news articles
            if news_group:
                summary_text = self.generate_asset_summary(asset, description, news_group, asset_sentiment, agent_profile)
                # Set the sentiment_summary directly on the existing object
                asset_sentiment.sentiment_summary = summary_text
            else:
                # Provide a fallback summary if no news articles
                asset_sentiment.sentiment_summary = f"Limited news coverage for {asset}. Sentiment analysis based on available data shows {asset_sentiment.sentiment_category.lower()} indicators."
        
        # Generate comprehensive overall diagnosis using all asset summaries and risk profile
        if state.report.asset_news_sentiments:
            try:
                # Collect all asset summaries for context
                asset_summaries_context = []
                for sentiment in state.report.asset_news_sentiments:
                    asset_summaries_context.append(
                        f"- {sentiment.asset}: {sentiment.sentiment_category} sentiment (Score: {sentiment.final_sentiment_score:.2f}, "
                        f"Confidence: {sentiment.confidence_level:.2f})\n"
                        f"  Summary: {sentiment.sentiment_summary or 'No summary available'}"
                    )
                
                # Determine market context based on state type
                if isinstance(state, CryptoNewsAgentState):
                    market_context = "cryptocurrency portfolio"
                    market_type = "crypto assets"
                else:
                    market_context = "market portfolio"
                    market_type = "market assets"
                
                overall_prompt = (
                    f"===== INVESTOR RISK PROFILE =====\n"
                    f"Risk Profile ID      : {active_risk_profile['risk_id']}\n"
                    f"Description          : {active_risk_profile.get('short_description', 'No description')}\n"
                    f"================================\n\n"
                    f"You are a {agent_profile['role']}. "
                    f"Based on the following comprehensive news sentiment analysis for the entire {market_context}, "
                    f"provide a unified overall diagnosis that considers all {market_type} collectively.\n\n"
                    f"PORTFOLIO ASSET SENTIMENT ANALYSIS:\n"
                    f"{'='*50}\n"
                    f"{chr(10).join(asset_summaries_context)}\n"
                    f"{'='*50}\n\n"
                    f"Generate a comprehensive overall portfolio diagnosis (maximum 250 words) that:\n"
                    f"1. Synthesizes the sentiment across all portfolio assets\n"
                    f"2. Provides actionable insights aligned with the investor's risk profile\n"
                    f"3. Considers portfolio-level implications and correlations\n"
                    f"4. Offers strategic recommendations based on the news sentiment landscape\n"
                    f"5. Addresses how the overall sentiment aligns with the investor's objectives and risk tolerance\n"
                    f"6. If possible, include relevant highlights from the most recent news coverage that support the analysis."
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
                    if isinstance(state, CryptoNewsAgentState):
                        market_context = "cryptocurrency"
                    else:
                        market_context = "market"
                    
                    state.report.overall_news_diagnosis = (
                        f"Portfolio news sentiment analysis shows {dominant_sentiment.lower()} overall trends "
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
def generate_news_sentiment_summary_tool(state: Union[CryptoNewsAgentState, MarketNewsAgentState]) -> dict:
    """Generate summaries for news articles grouped by asset."""
    return news_sentiment_summary_obj.generate_news_sentiment_summary(state=state)

# Example usage
if __name__ == "__main__":
    # Test with Market News State
    print("="*80)
    print("TESTING MARKET NEWS STATE")
    print("="*80)
    
    from agents.tools.states.agent_market_news_state import MarketNewsAgentState, PortfolioAllocation as MarketPortfolioAllocation, AssetNews as MarketAssetNews, AssetNewsSentiment as MarketAssetNewsSentiment, Report as MarketReport, SentimentScore as MarketSentimentScore
    
    # Initialize the market state with sample data
    market_state = MarketNewsAgentState(
        portfolio_allocation=[
            MarketPortfolioAllocation(
                asset="SPY", description="S&P 500 ETF", allocation_percentage="25%"
            ),
            MarketPortfolioAllocation(
                asset="QQQ", description="Nasdaq ETF", allocation_percentage="20%"
            )
        ],
        report=MarketReport(
            asset_news=[
                MarketAssetNews(
                    asset="SPY",
                    headline="S&P 500 reaches new highs",
                    description="Strong earnings drive market gains",
                    source="MarketWatch",
                    posted="2 hours ago",
                    sentiment_score=MarketSentimentScore(positive=0.8, negative=0.1, neutral=0.1)
                )
            ],
            asset_news_sentiments=[
                MarketAssetNewsSentiment(
                    asset="SPY",
                    final_sentiment_score=0.75,
                    sentiment_category="Positive",
                    total_news=5,
                    confidence_level=0.85,
                    average_positive=0.8,
                    average_negative=0.1,
                    average_neutral=0.1
                )
            ]
        ),
        next_step="news_sentiment_summary_node",
    )
    
    # Generate summaries
    market_result = generate_news_sentiment_summary_tool(market_state)

    # Print the updated market state
    print("\nUpdated Market State:")
    print(f"Overall Diagnosis: {market_state.report.overall_news_diagnosis}")
    print(f"Next Step: {market_state.next_step}")
    print(f"Asset Sentiments with summaries: {len(market_state.report.asset_news_sentiments)}")
    for sentiment in market_state.report.asset_news_sentiments:
        print(f"  - {sentiment.asset}: {sentiment.sentiment_summary[:100]}...")

    # Test with Crypto News State
    print("\n" + "="*80)
    print("TESTING CRYPTO NEWS STATE")
    print("="*80)
    
    from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, PortfolioAllocation as CryptoPortfolioAllocation, AssetNews as CryptoAssetNews, AssetNewsSentiment as CryptoAssetNewsSentiment, Report as CryptoReport, SentimentScore as CryptoSentimentScore
    
    # Initialize the crypto state with sample data
    crypto_state = CryptoNewsAgentState(
        portfolio_allocation=[
            CryptoPortfolioAllocation(
                asset="BTC", description="Bitcoin", allocation_percentage="40%"
            ),
            CryptoPortfolioAllocation(
                asset="ETH", description="Ethereum", allocation_percentage="30%"
            )
        ],
        report=CryptoReport(
            asset_news=[
                CryptoAssetNews(
                    asset="BTC",
                    headline="Bitcoin reaches new all-time high",
                    description="Institutional adoption drives price surge",
                    source="CoinDesk",
                    posted="1 hour ago",
                    sentiment_score=CryptoSentimentScore(positive=0.9, negative=0.05, neutral=0.05)
                )
            ],
            asset_news_sentiments=[
                CryptoAssetNewsSentiment(
                    asset="BTC",
                    final_sentiment_score=0.85,
                    sentiment_category="Positive",
                    total_news=8,
                    confidence_level=0.90,
                    average_positive=0.85,
                    average_negative=0.08,
                    average_neutral=0.07
                )
            ]
        ),
        next_step="news_sentiment_summary_node",
    )
    
    # Generate summaries
    crypto_result = generate_news_sentiment_summary_tool(crypto_state)

    # Print the updated crypto state
    print("\nUpdated Crypto State:")
    print(f"Overall Diagnosis: {crypto_state.report.overall_news_diagnosis}")
    print(f"Next Step: {crypto_state.next_step}")
    print(f"Asset Sentiments with summaries: {len(crypto_state.report.asset_news_sentiments)}")
    for sentiment in crypto_state.report.asset_news_sentiments:
        print(f"  - {sentiment.asset}: {sentiment.sentiment_summary[:100]}...")