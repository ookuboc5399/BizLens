import os
import asyncio
from datetime import datetime, timezone
import logging
from ..bigquery_service import BigQueryService
from .financial_report_service_selenium import TDNetScraper

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
        self.tdnet_scraper = TDNetScraper()
        logger.info("FinancialReportService initialized")

    async def close(self):
        """サービスのクローズ"""
        self.tdnet_scraper.close()
        logger.info("FinancialReportService closed")

    async def fetch_tdnet_reports(self, start_date=None, end_date=None, progress_callback=None):
        """TDnetから決算資料を取得してBigQueryに保存"""
        try:
            # TDnetから決算資料を取得
            result = await self.tdnet_scraper.fetch_reports(start_date, end_date)
            
            if result["status"] != "success":
                return result
            
            reports = result["reports"]
            total_reports = len(reports)
            saved_reports = 0
            
            # 取得した決算資料をBigQueryに保存
            for i, report in enumerate(reports, 1):
                try:
                    await self._save_report(
                        company_id=report["company_id"],
                        company_name=report["company_name"],
                        fiscal_year=report["fiscal_year"],
                        quarter=report["quarter"],
                        report_type=report["report_type"],
                        file_url=report["file_url"],
                        source=report["source"],
                        report_date=report["report_date"]
                    )
                    saved_reports += 1

                    # 進捗状況の更新
                    if progress_callback:
                        progress = int(20 + (i / total_reports * 80))  # 20%から100%まで
                        await progress_callback(progress, f"決算資料を保存中... ({saved_reports}/{total_reports})")

                except Exception as e:
                    logger.error("Error saving report: %s", str(e), exc_info=True)
                    continue
            
            logger.info("Successfully saved %d reports", saved_reports)
            return {"status": "success", "message": f"Processed {saved_reports} reports"}
            
        except Exception as e:
            logger.error("Error in fetch_tdnet_reports: %s", str(e), exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _save_report(self, company_id: str, company_name: str, fiscal_year: str, quarter: str,
                          report_type: str, file_url: str, source: str, report_date: datetime):
        """決算資料をBigQueryに保存"""
        try:
            report_data = {
                "company_id": company_id,
                "company_name": company_name,
                "fiscal_year": fiscal_year,
                "quarter": quarter,
                "report_type": report_type,
                "file_url": file_url,
                "source": source,
                "report_date": report_date.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug("Saving report data: %s", report_data)
            
            table_id = f"{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.financial_reports"
            errors = self.bigquery_service.client.insert_rows_json(table_id, [report_data])
            if errors:
                logger.error("Error inserting rows: %s", errors)
                raise Exception(f"Failed to insert rows: {errors}")
            logger.info("Created report for %s (%s): %sQ%s", company_name, company_id, fiscal_year, quarter)
            
        except Exception as e:
            logger.error("Error saving report: %s", str(e), exc_info=True)
            raise
