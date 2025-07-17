from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class CryptoPortfolioAllocation(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    asset_type: Optional[str] = Field(None, description="The asset type (e.g. Cryptocurrency, Stablecoin).")
    description: Optional[str] = Field(None, description="A description of the asset.")
    allocation_percentage: Optional[str] = Field(None, description="The allocation percentage of the asset.")

class SentimentScore(BaseModel):
    neutral: Optional[float] = Field(None, description="The neutral sentiment score.")
    negative: Optional[float] = Field(None, description="The negative sentiment score.")
    positive: Optional[float] = Field(None, description="The positive sentiment score.")


class AssetNews(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    headline: Optional[str] = Field(None, description="The headline of the news article.")
    description: Optional[str] = Field(None, description="A brief description of the news article.")
    source: Optional[str] = Field(None, description="The source of the news article.")
    posted: Optional[str] = Field(None, description="When the news article was posted.")
    link: Optional[str] = Field(None, description="The link to the news article.")
    sentiment_score: Optional[SentimentScore] = Field(None, description="The detailed sentiment scores of the article.")


class AssetNewsSentiment(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    final_sentiment_score: Optional[float] = Field(None, description="The final calculated sentiment score (0.0 to 1.0).")
    sentiment_category: Optional[str] = Field(None, description="The sentiment category (Positive, Negative, Neutral).")
    total_news: Optional[int] = Field(None, description="The total number of news articles related to the asset.")
    average_positive: Optional[float] = Field(None, description="The average positive sentiment score for the asset.")
    average_negative: Optional[float] = Field(None, description="The average negative sentiment score for the asset.")
    average_neutral: Optional[float] = Field(None, description="The average neutral sentiment score for the asset.")
    confidence_level: Optional[float] = Field(None, description="The confidence level of the sentiment analysis for the asset.")
    sentiment_summary: Optional[str] = Field(None, description="A summary of the sentiment analysis for the asset.")


class Report(BaseModel):
    asset_news: List[AssetNews] = Field(default_factory=list, description="A list of news articles related to the assets.")
    asset_news_sentiments: List[AssetNewsSentiment] = Field(default_factory=list, description="A summary of news articles related to the assets.")
    overall_news_diagnosis: Optional[str] = Field(None, description="The overall news diagnosis for the portfolio.")


class CryptoNewsAgentState(BaseModel):
    portfolio_allocation: List[CryptoPortfolioAllocation] = Field(default_factory=list, description="The portfolio allocation details.")
    report: Report = Field(default_factory=Report, description="The report containing analysis results.")
    next_step: Literal["__start__", "portfolio_allocation_node", "fetch_market_news_node", "news_sentiment_calc_node", "news_sentiment_summary_node", "__end__"] = Field(
        "__start__", description="The next step in the workflow."
    )
    updates: List[str] = Field(default_factory=list, description="A list of updates or messages for the workflow.")