import logging
from agents.tools.db.mdb import MongoDBConnector
from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, AssetSentiment
from agents.tools.bedrock.anthropic_chat_completions import BedrockAnthropicChatCompletions
from agents.tools.agent_profiles import AgentProfiles
import os
from dotenv import load_dotenv
from typing import Optional, Dict, List
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SocialMediaSentimentSummaryTool(MongoDBConnector):
    def __init__(self, chat_completions_model_id: Optional[str] = os.getenv("CHAT_COMPLETIONS_MODEL_ID"), agent_id: Optional[str] = "CRYPTO_NEWS_AGENT"):
        """
        SocialMediaSentimentSummaryTool class to generate summaries and calculate sentiment metrics for social media submissions.
        This class uses the BedrockAnthropicChatCompletions model to generate concise summaries.
        
        Args:
            chat_completions_model_id (str): Model ID for chat completions. Default is os.getenv("CHAT_COMPLETIONS_MODEL_ID").
            agent_id (str): Agent ID. Default is "CRYPTO_NEWS_AGENT".
        """
        self.chat_completions_model_id = chat_completions_model_id
        self.agent_id = agent_id
        logger.info("SocialMediaSentimentSummaryTool initialized")
    
    def group_submissions_by_asset(self, state: CryptoNewsAgentState) -> Dict[str, List]:
        """Group social media submissions by asset symbol."""
        asset_submissions_groups = defaultdict(list)
        
        for submission in state.report.asset_subreddits:
            if submission.asset:
                asset_submissions_groups[submission.asset].append(submission)
        
        return asset_submissions_groups
    
    def get_asset_sentiment_by_asset(self, state: CryptoNewsAgentState) -> Dict[str, AssetSentiment]:
        """Create a lookup dictionary for asset sentiments by asset symbol."""
        asset_sentiment_lookup = {}
        
        for sentiment in state.report.asset_sentiments:
            if sentiment.asset:
                asset_sentiment_lookup[sentiment.asset] = sentiment
        
        return asset_sentiment_lookup
    
    def truncate_text(self, text: str, max_length: int = 1500) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def generate_asset_summary(self, asset: str, description: str, submissions_group: List, asset_sentiment: AssetSentiment, agent_profile: dict) -> str:
        """Generate a summary for an asset's social media submissions using LLM."""
        # Limit to first 3 submissions with character limit
        limited_submissions = submissions_group[:3]
        
        # Prepare submissions content for the LLM
        submissions_content = []
        for i, submission in enumerate(limited_submissions, 1):
            submissions_content.append(f"Submission {i}:")
            submissions_content.append(f"Title: {self.truncate_text(submission.title or '', 200)}")
            submissions_content.append(f"Description: {self.truncate_text(submission.description or '', 1500)}")
            submissions_content.append(f"Score: {submission.score}, Comments: {submission.num_comments}, Upvotes: {submission.ups}")
            if submission.sentiment_score:
                submissions_content.append(f"Sentiment: Positive: {submission.sentiment_score.positive}, Negative: {submission.sentiment_score.negative}, Neutral: {submission.sentiment_score.neutral}")
            submissions_content.append("")
        
        submissions_context = "\n".join(submissions_content)
        
        # Prepare sentiment analysis context
        sentiment_context = ""
        if asset_sentiment:
            sentiment_context = (
                f"Overall Sentiment Analysis for {asset}:\n"
                f"- Final Sentiment Score: {asset_sentiment.final_sentiment_score}\n"
                f"- Sentiment Category: {asset_sentiment.sentiment_category}\n"
                f"- Total Submissions: {asset_sentiment.total_submissions}\n"
                f"- Confidence Level: {asset_sentiment.confidence_level}\n"
                f"- Total Engagement: {asset_sentiment.total_engagement_score}\n\n"
            )
        
        # Generate the LLM prompt
        llm_prompt = (
            f"You are an AI assistant for a crypto news agent. "
            f"Your task is to provide a concise summary of recent social media sentiment about {asset} ({description}).\n\n"
            f"Role: {agent_profile['role']}\n"
            f"Instructions: {agent_profile['instructions']}\n\n"
            f"{sentiment_context}"
            f"Recent Social Media Submissions:\n{submissions_context}\n\n"
            f"Generate a concise summary (maximum 80 words) of the social media sentiment for {asset} ({description}). "
            f"Focus on key insights and implications for crypto investors based on community sentiment. Be objective and factual."
        )

        logger.info(f"LLM Prompt for {asset} social media sentiment summary:")
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
                return f"Recent social media sentiment for {asset} indicates {asset_sentiment.sentiment_category.lower()} community perception with {asset_sentiment.confidence_level} confidence level."
            else:
                return f"Recent social media discussions about {asset} show mixed community sentiment."
    
    def generate_social_media_sentiment_summary(self, state: CryptoNewsAgentState) -> dict:
        """
        Generate summaries for social media submissions grouped by asset.
        
        Args:
            state (CryptoNewsAgentState): The current state of the crypto news agent.
            
        Returns:
            dict: Updated state with enhanced asset sentiment summaries.
        """
        message = "[Tool] Generating social media sentiment summaries."
        logger.info(message)
        
        # Retrieve the CRYPTO_NEWS_AGENT profile
        profiler = AgentProfiles()
        agent_profile = profiler.get_agent_profile(self.agent_id)
        if not agent_profile:
            logger.error(f"Agent profile not found for agent ID: {self.agent_id}")
            state.updates.append("Unable to generate sentiment summaries due to missing agent profile.")
            return {"updates": state.updates, "next_step": state.next_step}
        
        state.updates.append(f"[Action] Using agent profile: {self.agent_id} - {agent_profile['role']}")
        
        # Group submissions by asset
        asset_submissions_groups = self.group_submissions_by_asset(state)
        
        # Get asset sentiment lookup
        asset_sentiment_lookup = self.get_asset_sentiment_by_asset(state)
        
        # Create asset description lookup
        asset_descriptions = {allocation.asset: allocation.description for allocation in state.portfolio_allocation}
        
        # Process each asset group and enhance existing asset sentiments with summaries
        enhanced_asset_sentiments = []
        for asset_sentiment in state.report.asset_sentiments:
            asset = asset_sentiment.asset
            submissions_group = asset_submissions_groups.get(asset, [])
            
            # Get asset description
            description = asset_descriptions.get(asset, "")
            
            # Generate summary using LLM if we have submissions
            summary_text = ""
            if submissions_group:
                summary_text = self.generate_asset_summary(asset, description, submissions_group, asset_sentiment, agent_profile)
            
            # Create enhanced AssetSentiment object with summary
            enhanced_sentiment = AssetSentiment(
                asset=asset_sentiment.asset,
                final_sentiment_score=asset_sentiment.final_sentiment_score,
                sentiment_category=asset_sentiment.sentiment_category,
                total_submissions=asset_sentiment.total_submissions,
                recent_submissions=asset_sentiment.recent_submissions,
                average_positive=asset_sentiment.average_positive,
                average_negative=asset_sentiment.average_negative,
                average_neutral=asset_sentiment.average_neutral,
                total_engagement_score=asset_sentiment.total_engagement_score,
                total_comments=asset_sentiment.total_comments,
                total_ups=asset_sentiment.total_ups,
                confidence_level=asset_sentiment.confidence_level
            )
            
            # Add summary as a field if needed (you might want to add this to the AssetSentiment model)
            # For now, we'll store it in the updates
            if summary_text:
                state.updates.append(f"[Summary] {asset}: {summary_text}")
            
            enhanced_asset_sentiments.append(enhanced_sentiment)
        
        # Update the state with enhanced sentiments
        state.report.asset_sentiments = enhanced_asset_sentiments
        
        # Enhance overall news diagnosis with LLM-generated insights
        if state.report.overall_news_diagnosis:
            try:
                # Generate enhanced overall diagnosis
                overall_prompt = (
                    f"You are an AI assistant for a crypto news agent. "
                    f"Based on the following social media sentiment analysis, provide a comprehensive overall diagnosis.\n\n"
                    f"Role: {agent_profile['role']}\n"
                    f"Instructions: {agent_profile['instructions']}\n\n"
                    f"Current Diagnosis: {state.report.overall_news_diagnosis}\n\n"
                    f"Asset Sentiments:\n"
                )
                
                for sentiment in enhanced_asset_sentiments:
                    overall_prompt += f"- {sentiment.asset}: {sentiment.sentiment_category} sentiment (Score: {sentiment.final_sentiment_score}, Confidence: {sentiment.confidence_level})\n"
                
                overall_prompt += (
                    f"\nGenerate an enhanced overall diagnosis (maximum 150 words) that provides actionable insights "
                    f"for crypto portfolio optimization based on the social media sentiment analysis."
                )
                
                chat_completions = BedrockAnthropicChatCompletions(model_id=self.chat_completions_model_id)
                enhanced_diagnosis = chat_completions.predict(overall_prompt)
                
                # Truncate if necessary
                words = enhanced_diagnosis.split()
                if len(words) > 150:
                    enhanced_diagnosis = " ".join(words[:150]) + "..."
                
                state.report.overall_news_diagnosis = enhanced_diagnosis
                
            except Exception as e:
                logger.error(f"Error generating enhanced overall diagnosis: {e}")
                # Keep the original diagnosis if enhancement fails
        
        # Update state with message
        state.updates.append(message)

        # Set the next step in the state
        state.next_step = "__end__"

        return {
            "asset_sentiments": state.report.asset_sentiments,
            "overall_news_diagnosis": state.report.overall_news_diagnosis,
            "updates": state.updates,
            "next_step": state.next_step
        }

# Initialize the SocialMediaSentimentSummaryTool
social_media_sentiment_summary_obj = SocialMediaSentimentSummaryTool()

# Define tools
def generate_social_media_sentiment_summary_tool(state: CryptoNewsAgentState) -> dict:
    """Generate summaries for social media submissions grouped by asset."""
    return social_media_sentiment_summary_obj.generate_social_media_sentiment_summary(state=state)

# Example usage
if __name__ == "__main__":
    from agents.tools.states.agent_crypto_news_state import CryptoNewsAgentState, PortfolioAllocation, AssetSubreddits, AssetSentiment, Report, SentimentScore
    
    # Initialize the state with sample data
    state = CryptoNewsAgentState(
        portfolio_allocation=[
            PortfolioAllocation(
                asset="BTC", asset_type="Cryptocurrency", description="Bitcoin", allocation_percentage="40%"
            ),
            PortfolioAllocation(
                asset="ETH", asset_type="Cryptocurrency", description="Ethereum", allocation_percentage="30%"
            )
        ],
        report=Report(
            asset_subreddits=[
                AssetSubreddits(
                    asset="BTC",
                    title="Bitcoin price analysis",
                    description="Technical analysis shows bullish momentum",
                    score=100,
                    num_comments=25,
                    ups=95,
                    sentiment_score=SentimentScore(positive=0.8, negative=0.1, neutral=0.1)
                )
            ],
            asset_sentiments=[
                AssetSentiment(
                    asset="BTC",
                    final_sentiment_score=0.75,
                    sentiment_category="Positive",
                    total_submissions=10,
                    confidence_level=0.85
                )
            ]
        ),
        next_step="social_media_sentiment_summary_node",
    )
    
    # Generate summaries
    result = generate_social_media_sentiment_summary_tool(state)

    # Print the updated state
    print("\nUpdated State:")
    print(state.model_dump_json(indent=4))