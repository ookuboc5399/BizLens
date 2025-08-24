import os
import asyncio
from datetime import datetime, timezone
import logging
from ..bigquery_service import BigQueryService
# from .financial_report_service_selenium import TDNetScraper  # 一時的にコメントアウト

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ログファイルのパスを設定
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'tdnet_scraping.log')

# ファイルハンドラーの追加
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# コンソールハンドラーの追加
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

class FinancialReportService:
    def __init__(self):
        self.bigquery_service = BigQueryService()
        # self.tdnet_scraper = TDNetScraper()  # 一時的にコメントアウト
        logger.info("FinancialReportService initialized")

    async def close(self):
        """サービスのクローズ"""
        # self.tdnet_scraper.close()  # 一時的にコメントアウト
        logger.info("FinancialReportService closed")

    async def search_reports(self, company_id=None, company_name=None, fiscal_year=None, quarter=None, sector=None, industry=None):
        """決算資料を検索"""
        try:
            conditions = []
            params = {}

            # 検索条件の構築
            if company_id:
                conditions.append("code = @company_id")
                params["company_id"] = company_id
            if company_name:
                conditions.append("LOWER(company) LIKE CONCAT('%', LOWER(@company_name), '%')")
                params["company_name"] = company_name
            if fiscal_year:
                conditions.append("earnings_fiscal_year = @fiscal_year")
                params["fiscal_year"] = fiscal_year
            if quarter:
                conditions.append("earnings_quarter = @quarter")
                params["quarter"] = quarter
            if sector:
                conditions.append("sector = @sector")
                params["sector"] = sector
            if industry:
                conditions.append("industry = @industry")
                params["industry"] = industry

            # クエリの構築
            query = f"""
            SELECT 
                date,
                time,
                code,
                company,
                title,
                pdf_url,
                exchange,
                sector,
                industry,
                market,
                description,
                earnings_date,
                earnings_fiscal_year,
                earnings_quarter,
                created_at,
                updated_at
            FROM `{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.company_financial_data`
            """

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date DESC, time DESC"

            # クエリの実行
            results = self.bigquery_service.query(query)
            
            # 結果の整形
            reports = []
            for row in results:
                report = {
                    "date": row["date"].strftime("%Y/%m/%d"),
                    "time": row["time"],
                    "code": row["code"],
                    "company": row["company"],
                    "title": row["title"],
                    "pdf_url": row["pdf_url"],
                    "exchange": row["exchange"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "market": row["market"],
                    "description": row["description"],
                    "earnings_date": row["earnings_date"].strftime("%Y/%m/%d") if row["earnings_date"] else None,
                    "earnings_fiscal_year": row["earnings_fiscal_year"],
                    "earnings_quarter": row["earnings_quarter"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                }
                reports.append(report)

            return reports

        except Exception as e:
            logger.error(f"Error searching reports: {str(e)}")
            raise

    async def get_company_reports(self, company_id: str):
        """企業の決算資料一覧を取得"""
        try:
            query = f"""
            SELECT 
                date,
                time,
                code,
                company,
                title,
                pdf_url,
                exchange,
                sector,
                industry,
                market,
                description,
                earnings_date,
                earnings_fiscal_year,
                earnings_quarter,
                created_at,
                updated_at
            FROM `{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.company_financial_data`
            WHERE code = @company_id
            ORDER BY date DESC, time DESC
            """

            results = self.bigquery_service.query(query, {"company_id": company_id})
            
            reports = []
            for row in results:
                report = {
                    "date": row["date"].strftime("%Y/%m/%d"),
                    "time": row["time"],
                    "code": row["code"],
                    "company": row["company"],
                    "title": row["title"],
                    "pdf_url": row["pdf_url"],
                    "exchange": row["exchange"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "market": row["market"],
                    "description": row["description"],
                    "earnings_date": row["earnings_date"].strftime("%Y/%m/%d") if row["earnings_date"] else None,
                    "earnings_fiscal_year": row["earnings_fiscal_year"],
                    "earnings_quarter": row["earnings_quarter"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                }
                reports.append(report)

            return reports

        except Exception as e:
            logger.error(f"Error getting company reports: {str(e)}")
            raise

    async def fetch_tdnet_reports(self, start_date=None, end_date=None, progress_callback=None):
        """TDnetから決算資料を取得してBigQueryに保存"""
        try:
            # TDnetから決算資料を取得（一時的に無効化）
            # result = await self.tdnet_scraper.fetch_reports(start_date, end_date)
            
            # 一時的にダミーレスポンスを返す
            logger.warning("TDnet scraping is temporarily disabled")
            return {"status": "error", "message": "TDnet scraping is temporarily disabled"}
            
            # if result["status"] != "success":
            #     return result
            
            # reports = result["reports"]
            # total_reports = len(reports)
            # saved_reports = 0
            
            # # 取得した決算資料をBigQueryに保存
            # for i, report in enumerate(reports, 1):
            #     try:
            #         await self._save_report(report)
            #         saved_reports += 1

            #         # 進捗状況の更新
            #         if progress_callback:
            #             progress = int(20 + (i / total_reports * 80))  # 20%から100%まで
            #             await progress_callback(progress, f"決算資料を保存中... ({saved_reports}/{total_reports})")

            #     except Exception as e:
            #         logger.error("Error saving report: %s", str(e), exc_info=True)
            #         continue
            
            # logger.info("Successfully saved %d reports", saved_reports)
            # return {"status": "success", "message": f"Processed {saved_reports} reports"}
            
        except Exception as e:
            logger.error("Error in fetch_tdnet_reports: %s", str(e), exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _save_report(self, report):
        """決算資料をBigQueryに保存"""
        try:
            # 企業情報を取得
            company_query = f"""
            SELECT 
                sector,
                industry,
                market,
                description
            FROM `{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.companies`
            WHERE code = @code
            """
            company_results = self.bigquery_service.query(company_query, {"code": report["code"]})
            company_data = next(company_results, {})

            # 決算予定情報を取得
            earnings_query = f"""
            SELECT 
                earnings_date,
                fiscal_year,
                quarter
            FROM `{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.earnings_calendar`
            WHERE code = @code
            ORDER BY earnings_date DESC
            LIMIT 1
            """
            earnings_results = self.bigquery_service.query(earnings_query, {"code": report["code"]})
            earnings_data = next(earnings_results, {})

            # データの統合
            report_data = {
                "date": report["date"],
                "time": report["time"],
                "code": report["code"],
                "company": report["company"],
                "title": report["title"],
                "pdf_url": report["pdf_url"] if "pdf_url" in report else None,
                "exchange": report["exchange"],
                "sector": company_data.get("sector"),
                "industry": company_data.get("industry"),
                "market": company_data.get("market"),
                "description": company_data.get("description"),
                "earnings_date": earnings_data.get("earnings_date"),
                "earnings_fiscal_year": earnings_data.get("fiscal_year"),
                "earnings_quarter": earnings_data.get("quarter"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug("Saving report data: %s", report_data)
            
            table_id = f"{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.company_financial_data"
            errors = self.bigquery_service.client.insert_rows_json(table_id, [report_data])
            if errors:
                logger.error("Error inserting rows: %s", errors)
                raise Exception(f"Failed to insert rows: {errors}")
            logger.info("Created report for %s (%s)", report_data["company"], report_data["code"])
            
        except Exception as e:
            logger.error("Error saving report: %s", str(e), exc_info=True)
            raise
