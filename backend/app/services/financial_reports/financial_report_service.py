import os
import asyncio
from datetime import datetime, timezone
import logging
# from ..bigquery_service import BigQueryService  # BigQueryServiceを削除
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
        # self.bigquery_service = BigQueryService()  # BigQueryServiceを削除
        # self.tdnet_scraper = TDNetScraper()  # 一時的にコメントアウト
        logger.info("FinancialReportService initialized")

    async def close(self):
        """サービスのクローズ"""
        # self.tdnet_scraper.close()  # 一時的にコメントアウト
        logger.info("FinancialReportService closed")

    async def search_reports(self, company_id=None, company_name=None, fiscal_year=None, quarter=None, sector=None, industry=None):
        """決算資料を検索（BigQuery使用部分をコメントアウト）"""
        try:
            # BigQueryを使用している部分をコメントアウト
            logger.info("search_reports method called (BigQuery functionality disabled)")
            return []

        except Exception as e:
            logger.error(f"Error searching reports: {str(e)}")
            raise

    async def get_company_reports(self, company_id: str):
        """企業の決算資料一覧を取得（BigQuery使用部分をコメントアウト）"""
        try:
            # BigQueryを使用している部分をコメントアウト
            logger.info(f"get_company_reports method called for company_id: {company_id} (BigQuery functionality disabled)")
            return []

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
        """決算資料をBigQueryに保存（BigQuery使用部分をコメントアウト）"""
        try:
            # BigQueryを使用している部分をコメントアウト
            logger.info(f"_save_report method called (BigQuery functionality disabled)")
            return
            if errors:
                logger.error("Error inserting rows: %s", errors)
                raise Exception(f"Failed to insert rows: {errors}")
            logger.info("Created report for %s (%s)", report_data["company"], report_data["code"])
            
        except Exception as e:
            logger.error("Error saving report: %s", str(e), exc_info=True)
            raise
