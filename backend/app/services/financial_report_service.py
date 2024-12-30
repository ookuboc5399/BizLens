from datetime import datetime
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from ..models.financial_report import FinancialReport, FinancialReportCreate
from typing import List, Optional
import uuid

class FinancialReportService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        self.client = bigquery.Client(credentials=credentials)
        self.dataset = os.getenv('BIGQUERY_DATASET')
        self.table = 'financial_reports'

    async def get_company_reports(self, ticker: str) -> List[FinancialReport]:
        query = f"""
        SELECT 
            fr.id,
            fr.company_id,
            fr.fiscal_year,
            fr.quarter,
            fr.report_type,
            fr.file_url,
            fr.source,
            fr.report_date,
            fr.created_at,
            fr.updated_at
        FROM `{self.dataset}.{self.table}` fr
        JOIN `{self.dataset}.companies` c ON fr.company_id = c.id
        WHERE c.ticker = @ticker
        ORDER BY fr.fiscal_year DESC, fr.quarter DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker)
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()

        reports = []
        for row in results:
            report = FinancialReport(
                id=row.id,
                company_id=row.company_id,
                fiscal_year=row.fiscal_year,
                quarter=row.quarter,
                report_type=row.report_type,
                file_url=row.file_url,
                source=row.source,
                report_date=row.report_date,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            reports.append(report)

        return reports

    async def create_report(self, report: FinancialReportCreate) -> FinancialReport:
        now = datetime.utcnow()
        report_id = str(uuid.uuid4())

        query = f"""
        INSERT INTO `{self.dataset}.{self.table}` (
            id, company_id, fiscal_year, quarter, report_type,
            file_url, source, report_date, created_at
        )
        VALUES (
            @id, @company_id, @fiscal_year, @quarter, @report_type,
            @file_url, @source, @report_date, @created_at
        )
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id", "STRING", report_id),
                bigquery.ScalarQueryParameter("company_id", "STRING", report.company_id),
                bigquery.ScalarQueryParameter("fiscal_year", "STRING", report.fiscal_year),
                bigquery.ScalarQueryParameter("quarter", "STRING", report.quarter),
                bigquery.ScalarQueryParameter("report_type", "STRING", report.report_type),
                bigquery.ScalarQueryParameter("file_url", "STRING", report.file_url),
                bigquery.ScalarQueryParameter("source", "STRING", report.source),
                bigquery.ScalarQueryParameter("report_date", "TIMESTAMP", report.report_date),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", now),
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        query_job.result()

        return FinancialReport(
            id=report_id,
            company_id=report.company_id,
            fiscal_year=report.fiscal_year,
            quarter=report.quarter,
            report_type=report.report_type,
            file_url=report.file_url,
            source=report.source,
            report_date=report.report_date,
            created_at=now
        )

    async def get_latest_report(self, ticker: str) -> Optional[FinancialReport]:
        query = f"""
        SELECT 
            fr.id,
            fr.company_id,
            fr.fiscal_year,
            fr.quarter,
            fr.report_type,
            fr.file_url,
            fr.source,
            fr.report_date,
            fr.created_at,
            fr.updated_at
        FROM `{self.dataset}.{self.table}` fr
        JOIN `{self.dataset}.companies` c ON fr.company_id = c.id
        WHERE c.ticker = @ticker
        ORDER BY fr.fiscal_year DESC, fr.quarter DESC
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker)
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        rows = list(results)

        if not rows:
            return None

        row = rows[0]
        return FinancialReport(
            id=row.id,
            company_id=row.company_id,
            fiscal_year=row.fiscal_year,
            quarter=row.quarter,
            report_type=row.report_type,
            file_url=row.file_url,
            source=row.source,
            report_date=row.report_date,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
