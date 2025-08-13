from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Union
from service_asset_suggestions import AssetSuggestions
from service_crypto_suggestions import CryptoAssetSuggestions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the services
asset_suggestions_service = AssetSuggestions()
crypto_suggestions_service = CryptoAssetSuggestions()

# Create the router
router = APIRouter(prefix="/suggestions", tags=["Asset Suggestions"])

# Traditional Asset Models
class MacroIndicatorSuggestion(BaseModel):
    """Model for traditional asset indicator suggestions."""
    indicator: str
    action: str
    explanation: str
    sensitivity: Optional[str] = None
    note: Optional[str] = None

class AssetSuggestion(BaseModel):
    """Model for traditional asset suggestions."""
    asset: str
    asset_type: str
    description: str
    macro_indicators: List[MacroIndicatorSuggestion]

class MessageResponse(BaseModel):
    """Response model for traditional asset suggestions."""
    asset_suggestions: List[AssetSuggestion]

# Crypto-Specific Models
class CryptoMovingAverageIndicator(BaseModel):
    """Model for crypto moving average analysis."""
    indicator: str
    action: str
    explanation: str
    trend_direction: Optional[str] = None
    percentage_difference: Optional[str] = None
    suggestion: Optional[str] = None
    note: Optional[str] = None

class CryptoRSIIndicator(BaseModel):
    """Model for crypto RSI analysis."""
    indicator: str
    action: str
    explanation: str
    rsi_value: Optional[float] = None
    interpretation: Optional[str] = None
    diagnosis: Optional[str] = None
    suggestion: Optional[str] = None
    note: Optional[str] = None

class CryptoVolumeIndicator(BaseModel):
    """Model for crypto volume analysis."""
    indicator: str
    action: str
    explanation: str
    current_volume: Optional[float] = None
    avg_volume: Optional[float] = None
    volume_ratio: Optional[str] = None
    diagnosis: Optional[str] = None
    interpretation: Optional[str] = None
    suggestion: Optional[str] = None
    note: Optional[str] = None

class CryptoVWAPIndicator(BaseModel):
    """Model for crypto VWAP analysis."""
    indicator: str
    action: str
    explanation: str
    vwap_value: Optional[float] = None
    current_price: Optional[float] = None
    price_vs_vwap: Optional[str] = None
    diagnosis: Optional[str] = None
    interpretation: Optional[str] = None
    suggestion: Optional[str] = None
    note: Optional[str] = None

class CryptoOverallTrendIndicator(BaseModel):
    """Model for crypto overall trend analysis."""
    indicator: str
    action: str
    explanation: str
    price_data: Optional[dict] = None
    note: Optional[str] = None

# Union type for all crypto indicators
CryptoIndicator = Union[
    CryptoMovingAverageIndicator,
    CryptoRSIIndicator,
    CryptoVolumeIndicator,
    CryptoVWAPIndicator,
    CryptoOverallTrendIndicator
]

class CryptoAssetSuggestion(BaseModel):
    """Model for crypto asset suggestions."""
    asset: str
    asset_type: str
    description: str
    crypto_indicators: List[CryptoIndicator]

class CryptoMessageResponse(BaseModel):
    """Response model for crypto asset suggestions."""
    crypto_suggestions: List[CryptoAssetSuggestion]

### Asset Suggestions Endpoints ###

@router.get("/fetch-asset-suggestions-macro-indicators-based", response_model=MessageResponse)
async def fetch_asset_suggestions_macro_indicators_based():
    """
    Fetch asset suggestions based on the current portfolio and market conditions.
    
    Each asset receives individual recommendations per macroeconomic indicator:
    
    Macro indicators analyzed:
    - GDP: Economic growth indicator
    - Effective Interest Rate: Cost of capital indicator  
    - Unemployment Rate: Labor market health indicator
    
    For each indicator, assets receive a recommendation (KEEP or REDUCE) with explanation
    based on the following rules:
    
    - GDP:
        - Up → Keep Equity assets, Reduce Bond assets, Keep Commodity assets
        - Down → Reduce Equity assets, Keep Bond assets, Reduce Commodity assets
    - Effective Interest Rate:
        - Up → Keep Bond assets, Reduce Real Estate assets, Reduce Commodity assets
        - Down → Reduce Bond assets, Keep Real Estate assets, Keep Commodity assets
    - Unemployment Rate:
        - Up → Reduce Equity assets, Reduce Commodity assets
        - Down → Keep Equity assets, Keep Commodity assets

    Returns:
        MessageResponse: An object containing asset suggestions with per-indicator actions,
                         explanations, and notes about conflicting signals.
    """
    try:
        suggestions = asset_suggestions_service.fetch_asset_suggestions_macro_indicators_based()
        if not suggestions:
            logger.warning("No asset suggestions generated")
            return MessageResponse(asset_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} asset suggestions")
        return MessageResponse(asset_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching asset suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-asset-suggestions-market-volatility-based", response_model=MessageResponse)
async def fetch_asset_suggestions_market_volatility_based():
    """
    Fetch asset suggestions based on the current portfolio and market volatility (VIX).
    
    Each asset receives a recommendation based on its VIX sensitivity:
    
    VIX ranges:
    - Above 20: Generally indicates high volatility/market fear
    - 12-20: Normal volatility range
    - Below 12: Low volatility/market complacency
    
    Asset VIX sensitivity levels:
    - High: QQQ, EEM, HYG - Most affected by volatility spikes
    - Neutral: SPY, XLE, VNQ, USO - Moderately affected by volatility
    - Low: TLT, LQD, GLD - Less affected or may benefit from volatility
    
    Recommendation rules:
    - High VIX (>20):
      - High sensitivity assets → REDUCE
      - Neutral sensitivity assets → REDUCE (less urgently)
      - Low sensitivity assets → KEEP
    - Low VIX (<12):
      - High sensitivity assets → KEEP (increase exposure)
      - Other assets → KEEP
    - Normal VIX (12-20):
      - All assets → KEEP

    Returns:
        MessageResponse: An object containing asset suggestions with VIX-based actions,
                         explanations, and notes about asset sensitivity levels.
    """
    try:
        suggestions = asset_suggestions_service.fetch_asset_suggestions_market_volatility_based()
        if not suggestions:
            logger.warning("No asset suggestions generated")
            return MessageResponse(asset_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} asset suggestions based on market volatility")
        return MessageResponse(asset_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching market volatility-based asset suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

### Crypto Asset Suggestions Endpoints ###

@router.get("/fetch-crypto-suggestions-trend-based", response_model=CryptoMessageResponse)
async def fetch_crypto_suggestions_trend_based():
    """
    Fetch crypto asset suggestions based on detailed moving average trend analysis.
    
    Returns detailed MA analysis including:
    - MA9, MA21, MA50 analysis with exact values
    - Percentage differences and trend directions
    - Overall trend assessment
    """
    try:
        suggestions = crypto_suggestions_service.fetch_crypto_suggestions_trend_based()
        if not suggestions:
            logger.warning("No crypto trend-based suggestions generated")
            return CryptoMessageResponse(crypto_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} crypto suggestions based on trend analysis")
        return CryptoMessageResponse(crypto_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching crypto trend-based suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-crypto-suggestions-momentum-based", response_model=CryptoMessageResponse)
async def fetch_crypto_suggestions_momentum_based():
    """
    Fetch crypto asset suggestions based on detailed momentum indicators analysis.
    
    Returns detailed momentum analysis including:
    - RSI values with interpretations
    - Volume ratios vs averages
    - VWAP positioning with percentages
    """
    try:
        suggestions = crypto_suggestions_service.fetch_crypto_suggestions_momentum_based()
        if not suggestions:
            logger.warning("No crypto momentum-based suggestions generated")
            return CryptoMessageResponse(crypto_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} crypto suggestions based on momentum analysis")
        return CryptoMessageResponse(crypto_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching crypto momentum-based suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch-crypto-suggestions-comprehensive", response_model=CryptoMessageResponse)
async def fetch_crypto_suggestions_comprehensive():
    """
    Fetch comprehensive crypto asset suggestions with all indicator details combined.
    
    Returns complete analysis with all indicators:
    - Moving averages (MA9, MA21, MA50)
    - Momentum indicators (RSI, Volume, VWAP)
    - Detailed values and interpretations
    """
    try:
        suggestions = crypto_suggestions_service.fetch_crypto_suggestions_comprehensive()
        if not suggestions:
            logger.warning("No comprehensive crypto suggestions generated")
            return CryptoMessageResponse(crypto_suggestions=[])
            
        logger.info(f"Successfully fetched {len(suggestions)} comprehensive crypto suggestions")
        return CryptoMessageResponse(crypto_suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error fetching comprehensive crypto suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))