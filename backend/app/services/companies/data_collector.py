import yfinance as yf
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from datetime import datetime, timezone
import logging
from ..bigquery_service import BigQueryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyDataCollector:
    def __init__(self):
        self.bq_client = BigQueryService()
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
        """BigQueryからすべての企業情報を取得"""
        try:
            query = """
            SELECT DISTINCT
                ticker as company_id,
                company_name
            FROM `{}.{}.companies`
            ORDER BY ticker
            """.format(self.bq_client.project_id, self.bq_client.dataset)
            
            query_job = self.bq_client.client.query(query)
            results = query_job.result()
            
            companies = []
            for row in results:
                companies.append({
                    "company_id": row.company_id,
                    "company_name": row.company_name
                })
            
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            raise

    async def collect_company_data(self, ticker: str):
        """企業の基本情報と財務データを収集"""
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
                "market_price": info.get("currentPrice", 0),
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
                "collected_at": datetime.now(timezone.utc).isoformat()
            }

            # BigQueryに保存
            table_id = f"{self.bq_client.project_id}.{self.bq_client.dataset}.companies"
            errors = self.bq_client.client.insert_rows_json(table_id, [company_data])
            if errors:
                raise Exception(f"Failed to insert rows: {errors}")

            logger.info(f"Successfully collected data for {ticker}")
            return {"status": "success", "data": company_data}

        except Exception as e:
            logger.error(f"Error collecting data for {ticker}: {str(e)}")
            raise

        finally:
            await self.close()

    def save_to_bigquery(self, data: dict, table_name: str):
        """データをBigQueryに保存"""
        try:
            table_id = f"{self.bq_client.project_id}.{self.bq_client.dataset}.{table_name}"
            errors = self.bq_client.client.insert_rows_json(table_id, [data])
            if errors:
                return {"status": "error", "message": str(errors)}
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
