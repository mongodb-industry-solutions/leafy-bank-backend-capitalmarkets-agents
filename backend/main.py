import logging
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Add market assistant API router
from api_scheduled_agents import router as schuduled_agents_router
# Add market data API router
from api_market_data import router as market_data_router
# Add crypto data API router
from api_crypto_data import router as crypto_data_router
# Add portfolio data API router
from api_portfolio_data import router as portfolio_data_router
# Add stablecoins market cap API router
from api_stablecoins_market_cap import router as stablecoins_market_cap_router
# Add macro indicators data API router
from api_macro_indicators_data import router as macro_indicators_router
# Add report data API router
from api_report_data import router as report_data_router
# Add asset suggestions API router
from api_asset_suggestions import router as asset_suggestions_router
# Add chart mappings API router
from api_charts import router as charts_router
# Add risk profiles API router
from api_risk_profiles import router as risk_profiles_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@app.get("/")
async def read_root(request: Request):
    return {"message": "Server is running"}

# Add routers to the FastAPI app
app.include_router(schuduled_agents_router)
app.include_router(market_data_router)
app.include_router(crypto_data_router)
app.include_router(portfolio_data_router)
app.include_router(stablecoins_market_cap_router)
app.include_router(macro_indicators_router)
app.include_router(report_data_router)
app.include_router(asset_suggestions_router)
app.include_router(charts_router)
app.include_router(risk_profiles_router)