from typing import Optional, List, Dict
# from .bigquery_service import BigQueryService
from .snowflake_service import SnowflakeService
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import yfinance as yf  # Yahoo Financeのデータ取得用
from tradingview_ta import TA_Handler, Interval, Exchange # TradingViewのデータ取得用

class CompanyService:
    def __init__(self):
        # self.bigquery = BigQueryService()
        self.snowflake = SnowflakeService()

    async def collect_all_data(self, ticker: str) -> Dict:
        """個別企業のデータを収集"""
        company_data = {}
        # Yahoo Financeからデータを取得
        try:
            print(f"Collecting data for {ticker} from yfinance...")
            stock = yf.Ticker(ticker)
            info = stock.info
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
        except Exception as e:
            print(f"Error collecting data from yfinance for {ticker}: {str(e)}")
            # yfinanceが失敗しても処理を続ける
            company_data = {"ticker": ticker, "name": ""} 

        # TradingViewから分析サマリーを取得
        try:
            print(f"Collecting summary for {ticker} from TradingView...")
            tv_ticker = ticker.split('.')[0]
            handler = TA_Handler(
                symbol=tv_ticker,
                screener="japan",
                exchange="TSE",
                interval=Interval.INTERVAL_1_DAY
            )
            summary = handler.get_analysis().summary
            company_data['tradingview_summary'] = summary
        except Exception as e:
            print(f"Could not get TradingView summary for {ticker}: {e}")
            company_data['tradingview_summary'] = None

        # Save the collected data to Snowflake
        if self.snowflake.get_connection():
            print(f"Saving data for {ticker} to Snowflake...")
            self.snowflake.upsert_companies([company_data])
        
        return company_data

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

    async def get_company_details(self, ticker: str) -> Optional[Dict]:
        """企業の詳細情報を取得"""
        query = f"""
        SELECT * FROM companies WHERE ticker = %s
        """
        try:
            result = self.snowflake.query(query, (ticker,))
            if not result:
                print(f"No company data found for ticker: {ticker} in Snowflake.") # 追加
                return None
            
            company_data = result[0]
            print(f"Found company data for {ticker}: {company_data}") # 追加

            # TODO: financial_reportsテーブルから時系列データを取得する
            # とりあえずダミーデータを返す
            financials = {
                "revenue": [{"year": 2022, "value": 1000}, {"year": 2023, "value": 1200}],
                "netIncome": [{"year": 2022, "value": 100}, {"year": 2023, "value": 150}],
                "roe": [{"year": 2022, "value": 0.1}, {"year": 2023, "value": 0.12}],
                "per": [{"year": 2022, "value": 15}, {"year": 2023, "value": 18}],
                "assets": [{"type": "Current", "value": 500}, {"type": "Fixed", "value": 1000}],
                "liabilities": [{"type": "Current", "value": 300}, {"type": "Long-term", "value": 400}],
                "equity": 800
            }

            return_data = {
                "company": company_data,
                "financials": financials
            }
            print(f"Returning data for {ticker}: {return_data}") # 追加
            return return_data

        except Exception as e:
            print(f"Error getting company details for {ticker}: {e}")
            return None

    async def search_companies(self, query: str, page: int = 1, page_size: int = 10) -> Dict:
        """
        企業名またはティッカーで企業を検索し、ページネーションを適用します。
        """
        offset = (page - 1) * page_size
        
        # 検索クエリ
        search_sql = f"""
        SELECT 
            ticker,
            company_name,
            market,
            sector,
            industry,
            country,
            market_cap,
            current_price
        FROM companies
        WHERE company_name ILIKE %s OR ticker ILIKE %s
        ORDER BY market_cap DESC
        LIMIT %s OFFSET %s
        """
        
        # 総件数を取得するクエリ
        count_sql = f"""
        SELECT COUNT(*) as total
        FROM companies
        WHERE company_name ILIKE %s OR ticker ILIKE %s
        """
        
        like_query = f"%{query}%"
        
        try:
            # 企業リストの取得
            companies = self.snowflake.query(search_sql, (like_query, like_query, page_size, offset))
            
            # 総件数の取得
            total_result = self.snowflake.query(count_sql, (like_query, like_query))
            total = total_result[0]['total'] if total_result and len(total_result) > 0 and 'total' in total_result[0] else 0
            
            return {
                "companies": companies,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            print(f"Error searching companies in Snowflake: {e}")
            # エラーが発生した場合は空の結果を返すか、例外を再発生させる
            return {
                "companies": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }

    async def get_company(self, company_id: str):
        # return await self.bigquery.get_company_data(company_id)
        # TODO: Implement get_company_data for Snowflake
        return {}

    async def get_financial_metrics(self, company_id: str):
        # return await self.bigquery.get_financial_metrics(company_id)
        # TODO: Implement get_financial_metrics for Snowflake
        return {}

    async def get_peer_companies(self, company_id: str):
        # return await self.bigquery.get_peer_companies(company_id)
        # TODO: Implement get_peer_companies for Snowflake
        return []

    async def store_company_data(self, data):
        # BigQueryにデータを保存
        # await self.bigquery.insert_companies(data)
        # TODO: Implement insert_companies for Snowflake
        pass

    async def get_company_list(self) -> List[Dict]:
        """全企業のリストを取得"""
        # try:
        #     query = f"""
        #     SELECT DISTINCT
        #         ticker,
        #         company_name as name
        #     FROM `{self.bigquery.project_id}.{self.bigquery.dataset}.{self.bigquery.table}`
        #     """
        #     
        #     query_job = self.bigquery.client.query(query)
        #     results = query_job.result()
        #     
        #     return [dict(row) for row in results]
        #     
        # except Exception as e:
        #     print(f"Error getting company list: {str(e)}")
        #     raise
        # TODO: Implement get_company_list for Snowflake
        return []
