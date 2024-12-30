from typing import Optional, List, Dict
from .bigquery_service import BigQueryService
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import yfinance as yf  # Yahoo Financeのデータ取得用

class CompanyService:
    def __init__(self):
        self.bigquery = BigQueryService()

    async def collect_all_data(self, ticker: str) -> Dict:
        """個別企業のデータを収集"""
        try:
            print(f"Collecting data for {ticker}")
            
            # Yahoo Financeからデータを取得
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 基本情報を収集
            company_data = {
                "ticker": ticker,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market": "TSE",  # 東証を想定
                
                # 株価データ
                "market_price": info.get("currentPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "volume": info.get("volume", 0),
                
                # 財務指標
                "per": info.get("forwardPE", 0),
                "pbr": info.get("priceToBook", 0),
                "roe": info.get("returnOnEquity", 0),
                "revenue": info.get("totalRevenue", 0),
                "operating_profit": info.get("operatingMargins", 0) * info.get("totalRevenue", 0),
                "net_profit": info.get("netIncomeToCommon", 0),
                
                # 配当データ
                "dividend_yield": info.get("dividendYield", 0),
                "dividend_per_share": info.get("dividendRate", 0),
            }
            
            # BigQueryにデータを保存
            await self.bigquery.upsert_company_data([company_data])
            
            return company_data
            
        except Exception as e:
            print(f"Error collecting data for {ticker}: {str(e)}")
            raise

    async def collect_company_data(self):
        try:
            collected_data = []
            failed_companies = []
            
            companies = await self.get_company_list()
            total_companies = len(companies)
            
            # バッチ処理（10社ごとに処理して、その後30秒待機）
            batch_size = 10  # 必要に応じて変更可能
            for i in range(0, len(companies), batch_size):
                batch = companies[i:i + batch_size]
                
                for company in batch:
                    try:
                        data = await self.collect_all_data(company['ticker'])
                        collected_data.append(data)
                    except Exception as e:
                        failed_companies.append({
                            'ticker': company['ticker'],
                            'error': str(e)
                        })
                
                # 進捗状況を計算
                progress = {
                    "current": len(collected_data) + len(failed_companies),
                    "total": total_companies,
                    "percentage": round((len(collected_data) + len(failed_companies)) / total_companies * 100, 1)
                }
                print(f"Progress: {progress['percentage']}% ({progress['current']}/{progress['total']})")
                
                # バッチ処理後の待機
                if i + batch_size < len(companies):
                    print(f"Waiting 30 seconds before next batch...")
                    await asyncio.sleep(30)
        
            return {
                "total": len(collected_data),
                "updated": len(collected_data),
                "failed": failed_companies,
                "progress": 100
            }
                    
        except Exception as e:
            print(f"Error in collect_company_data: {str(e)}")
            raise

    async def get_company_details(self, company_id: str):
        company_data = await self.bigquery.get_company_data(company_id)
        if not company_data:
            return None

        metrics = await self.bigquery.get_company_metrics(company_data.get('ticker'))
        financials = await self.bigquery.get_financial_history(company_data.get('ticker'))

        return {
            "company": company_data,
            "metrics": metrics,
            "financials": financials
        }

    async def search_companies(self, query: str) -> List[dict]:
        return await self.bigquery.search_companies(query)

    async def get_company(self, company_id: str):
        return await self.bigquery.get_company_data(company_id)

    async def get_financial_metrics(self, company_id: str):
        return await self.bigquery.get_financial_metrics(company_id)

    async def get_peer_companies(self, company_id: str):
        return await self.bigquery.get_peer_companies(company_id)

    async def store_company_data(self, data):
        # BigQueryにデータを保存
        await self.bigquery.insert_companies(data)

    async def get_company_list(self) -> List[Dict]:
        """全企業のリストを取得"""
        try:
            query = f"""
            SELECT DISTINCT
                ticker,
                company_name as name
            FROM `{self.bigquery.project_id}.{self.bigquery.dataset}.{self.bigquery.table}`
            """
            
            query_job = self.bigquery.client.query(query)
            results = query_job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Error getting company list: {str(e)}")
            raise
