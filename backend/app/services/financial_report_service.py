import logging
from datetime import datetime
from google.cloud import storage
from ..models.financial_report import FinancialReportCreate
from ..services.bigquery_service import BigQueryService
import aiohttp
import os
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)

class FinancialReportService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "financial_report_bucket")
        self.bucket = self.storage_client.bucket(self.bucket_name)
        self.bigquery_service = BigQueryService()

    async def create_report(self, report: FinancialReportCreate):
        """決算資料を保存"""
        try:
            # PDFファイルをダウンロード
            file_content = await self._download_pdf(report.file_url)
            if not file_content:
                logger.error(f"Failed to download PDF from {report.file_url}")
                return None

            # GCSにPDFを保存
            file_path = self._generate_file_path(report)
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(file_content, content_type='application/pdf')

            # 署名付きURLを生成（1時間有効）
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=3600,
                method="GET"
            )

            # BigQueryにメタデータを保存
            metadata = {
                "company_id": report.company_id,
                "fiscal_year": report.fiscal_year,
                "quarter": report.quarter,
                "report_type": report.report_type,
                "source": report.source,
                "original_url": report.file_url,
                "gcs_path": file_path,
                "report_date": report.report_date.isoformat(),
                "created_at": datetime.now().isoformat()
            }

            self.bigquery_service.insert_rows("financial_reports", [metadata])
            logger.info(f"Saved report for company {report.company_id}: {file_path}")

            return {
                "file_path": file_path,
                "signed_url": signed_url
            }

        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            raise

    async def _download_pdf(self, url: str) -> bytes:
        """PDFファイルをダウンロード"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download PDF. Status: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            return None

    def _generate_file_path(self, report: FinancialReportCreate) -> str:
        """GCSのファイルパスを生成"""
        # URLからファイル名を抽出
        url_path = urlparse(report.file_url).path
        original_filename = os.path.basename(unquote(url_path))
        
        # 拡張子を保持
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.pdf'
        
        # ファイル名を生成
        filename = f"{report.company_id}_{report.fiscal_year}Q{report.quarter}_{report.report_type}_{report.source}{ext}"
        
        # パスを生成
        return f"{report.company_id}/{report.fiscal_year}/{filename}"

    async def get_company_reports(self, company_id: str):
        """企業の決算資料一覧を取得"""
        try:
            query = f"""
            SELECT *
            FROM `BuffetCodeClone.financial_reports`
            WHERE company_id = '{company_id}'
            ORDER BY report_date DESC
            """
            
            results = self.bigquery_service.query(query)
            reports = []
            
            for row in results:
                # GCSの署名付きURLを生成
                blob = self.bucket.blob(row['gcs_path'])
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=3600,
                    method="GET"
                )
                
                report = dict(row)
                report['signed_url'] = signed_url
                reports.append(report)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error getting company reports: {str(e)}")
            raise

    async def search_reports(self, company_id: str = None, fiscal_year: str = None, 
                           quarter: str = None, report_type: str = None, source: str = None):
        """決算資料を検索"""
        try:
            conditions = []
            
            if company_id:
                conditions.append(f"company_id = '{company_id}'")
            if fiscal_year:
                conditions.append(f"fiscal_year = '{fiscal_year}'")
            if quarter:
                conditions.append(f"quarter = '{quarter}'")
            if report_type:
                conditions.append(f"report_type = '{report_type}'")
            if source:
                conditions.append(f"source = '{source}'")
            
            where_clause = " AND ".join(conditions) if conditions else "1 = 1"
            
            query = f"""
            SELECT *
            FROM `BuffetCodeClone.financial_reports`
            WHERE {where_clause}
            ORDER BY report_date DESC
            """
            
            results = self.bigquery_service.query(query)
            reports = []
            
            for row in results:
                # GCSの署名付きURLを生成
                blob = self.bucket.blob(row['gcs_path'])
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=3600,
                    method="GET"
                )
                
                report = dict(row)
                report['signed_url'] = signed_url
                reports.append(report)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error searching reports: {str(e)}")
            raise
