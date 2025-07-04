from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class PortfolioAllocation(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    asset_type: Optional[str] = Field(None, description="The asset type (e.g. Cryptocurrency, Stablecoin).")
    description: Optional[str] = Field(None, description="A description of the asset.")
    allocation_percentage: Optional[str] = Field(None, description="The allocation percentage of the asset.")


class CryptoAssetTrend(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    fluctuation_answer: Optional[str] = Field(None, description="A description of the asset's price movement and technical indicators.")
    diagnosis: Optional[str] = Field(None, description="A diagnosis or recommendation based on the crypto trend analysis.")


class MomentumIndicator(BaseModel):
    indicator_name: Optional[str] = Field(None, description="The momentum indicator name (e.g., RSI, Volume).")
    fluctuation_answer: Optional[str] = Field(None, description="A description of the momentum indicator's current state.")
    diagnosis: Optional[str] = Field(None, description="A diagnosis or recommendation based on the momentum indicator.")


class CryptoMomentumIndicator(BaseModel):
    asset: Optional[str] = Field(None, description="The digital asset symbol (e.g., BTC, ETH, FDUSD).")
    momentum_indicators: List[MomentumIndicator] = Field(default_factory=list, description="A list of momentum indicators (RSI, ATR, Volume) for this specific asset.")


class Report(BaseModel):
    crypto_trends: List[CryptoAssetTrend] = Field(default_factory=list, description="A list of digital asset trends using Moving Averages and price analysis.")
    crypto_momentum_indicators: List[CryptoMomentumIndicator] = Field(default_factory=list, description="A list of crypto-specific momentum indicators grouped by asset.")
    overall_diagnosis: Optional[str] = Field(None, description="A general diagnosis of the crypto portfolio with actionable recommendations.")


class CryptoAnalysisAgentState(BaseModel):
    portfolio_allocation: List[PortfolioAllocation] = Field(default_factory=list, description="The crypto portfolio allocation details.")
    report: Report = Field(default_factory=Report, description="The report containing crypto analysis results.")
    next_step: Literal["__start__", "portfolio_allocation_node", "crypto_trends_node", "crypto_momentum_indicators_node", "crypto_portfolio_overall_diagnosis_node", "__end__"] = Field(None, description="The next step in the crypto analysis workflow.")
    updates: List[str] = Field(default_factory=list, description="A list of updates or messages for the workflow.")