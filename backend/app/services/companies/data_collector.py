import yfinance as yf
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from datetime import datetime, timezone
import logging
# from ..bigquery_service import BigQueryService # BigQueryServiceを削除
from ..snowflake_service import SnowflakeService # SnowflakeServiceを追加

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyDataCollector:
    def __init__(self):
        # self.bq_client = BigQueryService() # BigQueryServiceを削除
        self.sf_client = SnowflakeService() # SnowflakeServiceを追加
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    async def initialize(self):
        """HTTPセッションの初期化"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """セッションのクローズ"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_all_companies(self):
        """Snowflakeからすべての企業情報を取得"""
        try:
            query = """
            SELECT DISTINCT
                ticker,
                company_name
            FROM companies -- Snowflakeのテーブル名
            ORDER BY ticker
            """
            
            # SnowflakeServiceのqueryメソッドを使用
            results = self.sf_client.query(query)
            
            companies = []
            for row in results:
                companies.append({
                    "company_id": row["TICKER"],
                    "company_name": row["COMPANY_NAME"]
                })
            
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching companies from Snowflake: {str(e)}")
            raise

    async def collect_company_data(self, ticker: str):
        """企業の基本情報と財務データを収集し、Snowflakeに保存"""
        try:
            await self.initialize()

            # Yahoo Financeから基本情報を取得
            stock = yf.Ticker(f"{ticker}.T")
            info = stock.info

            # 基本情報を抽出
            company_data = {
                "ticker": ticker,
                "company_name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market": "東証",
                "current_price": info.get("currentPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "per": info.get("forwardPE", 0),
                "pbr": info.get("priceToBook", 0),
                "eps": info.get("trailingEPS", 0),
                "bps": info.get("bookValue", 0),
                "roe": info.get("returnOnEquity", 0),
                "roa": info.get("returnOnAssets", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "dividend_per_share": info.get("lastDividendValue", 0),
                "beta": info.get("beta", 0),
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "country": info.get("country", ""),
                "website": info.get("website", ""),
                "business_description": info.get("longBusinessSummary", ""),
                "shares_outstanding": info.get("sharesOutstanding", 0),
                "volume": info.get("volume", 0),
                "revenue": info.get("totalRevenue", 0),
                "operating_profit": info.get("operatingProfits", 0),
                "net_profit": info.get("netIncomeToCommon", 0),
                "total_assets": info.get("totalAssets", 0),
                "equity": info.get("totalStockholderEquity", 0),
                "operating_margin": info.get("operatingMargins", 0),
                "net_margin": info.get("netMargins", 0),
                "tradingview_summary": None # TradingViewのデータは別途取得する場合
            }

            # Snowflakeに保存 (upsert_companiesメソッドを使用)
            self.sf_client.upsert_companies([company_data])

            logger.info(f"Successfully collected and saved data for {ticker} to Snowflake")
            return {"status": "success", "data": company_data}

        except Exception as e:
            logger.error(f"Error collecting data for {ticker}: {str(e)}")
            raise

        finally:
            await self.close()

    # save_to_bigqueryメソッドは削除 (collect_company_data内でupsert_companiesを使うため)
    # def save_to_bigquery(self, data: dict, table_name: str):
    #     """データをBigQueryに保存"""
    #     try:
    #         table_id = f"{self.bq_client.project_id}.{self.bq_client.dataset}.{table_name}"
    #         errors = self.bq_client.client.insert_rows_json(table_id, [data])
    #         if errors:
    #             return {"status": "error", "message": str(errors)}
    #         return {"status": "success"}
    #     except Exception as e:
    #         return {"status": "error", "message": str(e)}