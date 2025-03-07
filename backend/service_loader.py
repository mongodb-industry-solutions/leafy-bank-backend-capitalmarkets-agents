import time
import logging
from datetime import datetime, timedelta, timezone

from loaders.yfinance_tickers_extract import YFinanceTickersExtract
from loaders.yfinance_tickers_transform import YFinanceTickersTransform
from loaders.yfinance_tickers_load import YFinanceTickersLoad
from loaders.yfinance_tickers_cleaner import YFinanceTickersCleaner

from loaders.financial_news_scraper import FinancialNewsScraper

from loaders.pyfredapi_macroindicators_extract import PyFredAPIExtract
from loaders.pyfredapi_macroindicators_transform import PyFredAPITransform
from loaders.pyfredapi_macroindicators_load import PyFredAPILoad

from loaders.config.config_loader import ConfigLoader

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class LoaderService:
    def __init__(self):
        """
        Service for loading Yahoo Finance market data, PyFredAPI macroeconomic data, and Financial News data.
        """
        self.config_loader = ConfigLoader()
        self.utc = timezone.utc
        logger.info("LoaderService initialized")

    def load_yfinance_market_data(self, date_str: str):
        """
        Loads Yahoo Finance market data for the given date.

        :param date_str: Date in "%Y%m%d" format.
        """
        logger.info("Starting Yahoo Finance market data loading process")

        # Validate the date is not current date or future date
        current_date = datetime.now(self.utc).strftime("%Y%m%d")
        if date_str >= current_date:
            raise ValueError("date_str cannot be the current date or a future date")

        # Date string for end date
        start_date_str = date_str

        # Define date range for extraction
        start_date = datetime.strptime(start_date_str, "%Y%m%d").replace(tzinfo=self.utc)
        end_date = start_date + timedelta(days=1)
        end_date_str = end_date.strftime("%Y%m%d")

        logger.info(f"Extracting data for {start_date_str}")

        # Extract Market Data
        extractor = YFinanceTickersExtract(start_date=start_date_str, end_date=end_date_str)
        extracted_data = extractor.extract()

        # Transform Market Data
        transformer = YFinanceTickersTransform()
        transformed_data = {}
        for asset_type, data in extracted_data.items():
            logger.info(f"Transforming data for asset type: {asset_type}")
            for symbol, df in data.items():
                transformed_data[symbol] = transformer.transform(symbol=symbol, df=df)

        # Load Market Data
        loader = YFinanceTickersLoad()
        loader.load(transformed_data, start_date=start_date_str)

        # Clean up Market Data older than 60 days
        cleaner = YFinanceTickersCleaner()
        cleaner.run()

        logger.info("Yahoo Finance market data loading process completed")

    def load_pyfredapi_macroeconomic_data(self, date_str: str):
        """
        Loads PyFredAPI macroeconomic data for the given date.

        :param date_str: Date in "%Y%m%d" format.
        """
        logger.info("Starting PyFredAPI macroeconomic data loading process")

        # Validate the date is not current date or future date
        current_date = datetime.now(self.utc).strftime("%Y%m%d")
        if date_str >= current_date:
            raise ValueError("date_str cannot be the current date or a future date")

        # Date string for end date
        end_date_str = date_str

        # Define date range for extraction
        end_date = datetime.strptime(end_date_str, "%Y%m%d").replace(tzinfo=self.utc)
        start_date = end_date - timedelta(days=7)
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # Extract Macroeconomic Data
        extractor = PyFredAPIExtract(start_date=start_date_str, end_date=end_date_str)
        extracted_data = extractor.extract()

        # Transform Macroeconomic Data
        transformer = PyFredAPITransform()
        transformed_data = {}
        for series_id, df in extracted_data.items():
            transformed_data[series_id] = transformer.transform(series_id, df)

        # Load Macroeconomic Data
        loader = PyFredAPILoad()
        loader.load(transformed_data)

        logger.info("PyFredAPI macroeconomic data loading process completed")

    def load_recent_financial_news(self):
        """
        Loads recent financial news data.
        """
        logger.info("Starting financial news processing")

        # Scraper
        news_scraper = FinancialNewsScraper(
            collection_name=os.getenv("NEWS_COLLECTION", "financial_news"),
            scrape_num_articles=int(os.getenv("SCRAPE_NUM_ARTICLES", 1))
        )
        news_scraper.run()

        logger.info("Financial News processing completed!")

# Example usage:
# if __name__ == "__main__":
    # service = LoaderService()
    # Example usage:
    # service.load_yfinance_market_data("20250306")
    # service.load_pyfredapi_macroeconomic_data("20250306")
    # service.load_recent_financial_news()