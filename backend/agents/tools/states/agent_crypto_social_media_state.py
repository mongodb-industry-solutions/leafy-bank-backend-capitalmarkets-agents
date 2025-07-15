from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class PortfolioAllocation(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    asset_type: Optional[str] = Field(None, description="The asset type (e.g. Cryptocurrency, Stablecoin).")
    description: Optional[str] = Field(None, description="A description of the asset.")
    allocation_percentage: Optional[str] = Field(None, description="The allocation percentage of the asset.")


class SentimentScore(BaseModel):
    neutral: Optional[float] = Field(None, description="The neutral sentiment score.")
    negative: Optional[float] = Field(None, description="The negative sentiment score.")
    positive: Optional[float] = Field(None, description="The positive sentiment score.")


class Comment(BaseModel):
    id: Optional[str] = Field(None, description="The unique identifier of the comment.")
    author: Optional[str] = Field(None, description="The username of the author of the comment.")
    body: Optional[str] = Field(None, description="The content of the comment.")
    score: Optional[int] = Field(None, description="The score of the comment.")
    create_at_utc: Optional[str] = Field(None, description="When the comment was created in UTC format.")


class AssetSubreddits(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    subreddit: Optional[str] = Field(None, description="The name of the subreddit related to the asset.")
    url: Optional[str] = Field(None, description="The link to the subreddit.")
    author: Optional[str] = Field(None, description="The username of the author of the subreddit post.")
    author_fullname: Optional[str] = Field(None, description="The full name of the author of the subreddit post.")
    title: Optional[str] = Field(None, description="A brief title of the subreddit post.")
    description: Optional[str] = Field(None, description="A brief description of the subreddit post.")
    create_at_utc: Optional[str] = Field(None, description="When the subreddit post was created in UTC format.")
    score: Optional[int] = Field(None, description="The score of the subreddit post.")
    num_comments: Optional[int] = Field(None, description="The number of comments on the subreddit post.")
    comments: List[Comment] = Field(default_factory=list, description="A list of comments on the subreddit post.")
    ups: Optional[int] = Field(None, description="The number of upvotes the subreddit post received.")
    downs: Optional[int] = Field(None, description="The number of downvotes the subreddit post received.")
    sentiment_score: Optional[SentimentScore] = Field(None, description="The sentiment score of the news article.")


class AssetSocialMediaSentiment(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    final_sentiment_score: Optional[float] = Field(None, description="The final calculated sentiment score (0.0 to 1.0).")
    sentiment_category: Optional[str] = Field(None, description="The sentiment category (Positive, Negative, Neutral).")
    total_submissions: Optional[int] = Field(None, description="The total number of submissions related to the asset.")
    recent_submissions: Optional[int] = Field(None, description="The number of recent submissions (last 10 days) related to the asset.")
    average_positive: Optional[float] = Field(None, description="The average positive sentiment score for the asset.")
    average_negative: Optional[float] = Field(None, description="The average negative sentiment score for the asset.")
    average_neutral: Optional[float] = Field(None, description="The average neutral sentiment score for the asset.")
    total_engagement_score: Optional[int] = Field(None, description="The total engagement score (sum of all scores).")
    total_comments: Optional[int] = Field(None, description="The total number of comments across all submissions.")
    total_ups: Optional[int] = Field(None, description="The total number of upvotes across all submissions.")
    confidence_level: Optional[float] = Field(None, description="The confidence level of the sentiment analysis for the asset.")
    sentiment_summary: Optional[str] = Field(None, description="A summary of the sentiment analysis for the asset.")


class Report(BaseModel):
    asset_subreddits: List[AssetSubreddits] = Field(default_factory=list, description="A list of asset subreddits related to the portfolio.")
    asset_sm_sentiments: List[AssetSocialMediaSentiment] = Field(default_factory=list, description="A list of asset sentiments related to the portfolio.")
    overall_news_diagnosis: Optional[str] = Field(None, description="The overall news diagnosis for the portfolio.")


class CryptoSocialMediaAgentState(BaseModel):
    portfolio_allocation: List[PortfolioAllocation] = Field(default_factory=list, description="The portfolio allocation details.")
    report: Report = Field(default_factory=Report, description="The report containing news results.")
    next_step: Literal["__start__", "portfolio_allocation_node", "social_media_sentiment_node", "social_media_sentiment_calc_node", "social_media_sentiment_summary_node", "__end__"] = Field(None, description="The next step in the workflow (e.g., 'portfolio_allocation_node').")
    updates: List[str] = Field(default_factory=list, description="A list of updates or messages for the workflow.")
