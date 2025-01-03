"""
統合ビューを作成するスクリプト
"""
import os
import sys
from google.cloud import bigquery

# backendディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.bigquery_service import BigQueryService

def create_materialized_view():
    """統合ビューを作成"""
    bigquery_service = BigQueryService()
    client = bigquery_service.client
    
    # 既存のビューを削除
    drop_query = f"""
    DROP MATERIALIZED VIEW IF EXISTS `{bigquery_service.project_id}.{bigquery_service.dataset}.company_financial_data`
    """
    try:
        query_job = client.query(drop_query)
        query_job.result()
        print("Dropped existing materialized view")
    except Exception as e:
        print(f"Warning: {str(e)}")

    # テーブルを作成
    create_query = f"""
    CREATE OR REPLACE TABLE `{bigquery_service.project_id}.{bigquery_service.dataset}.company_financial_data`
    AS
    SELECT 
        fr.date,
        fr.time,
        fr.code,
        fr.company,
        fr.title,
        fr.pdf_url,
        fr.exchange,
        c.sector,
        c.industry,
        c.market,
        c.description,
        ec.announcement_date as earnings_date,
        CAST(ec.fiscal_year AS STRING) as earnings_fiscal_year,
        CAST(ec.fiscal_quarter AS STRING) as earnings_quarter,
        fr.created_at,
        fr.updated_at
    FROM 
        `{bigquery_service.project_id}.{bigquery_service.dataset}.financial_reports` fr
    LEFT JOIN 
        `{bigquery_service.project_id}.{bigquery_service.dataset}.companies` c
        ON fr.code = c.ticker
    LEFT JOIN 
        `{bigquery_service.project_id}.{bigquery_service.dataset}.earnings_calendar` ec
        ON fr.code = ec.ticker
    """
    
    try:
        # テーブルを作成
        query_job = client.query(create_query)
        query_job.result()
        print("Created materialized view: company_financial_data")
        
        # インデックスの作成
        index_query = f"""
        CREATE SEARCH INDEX IF NOT EXISTS company_financial_data_search
        ON `{bigquery_service.project_id}.{bigquery_service.dataset}.company_financial_data` (
            company,
            title,
            code,
            sector,
            industry
        )
        """
        query_job = client.query(index_query)
        query_job.result()
        print("Created search index")
        
    except Exception as e:
        print(f"Error creating materialized view: {str(e)}")
        raise

if __name__ == "__main__":
    create_materialized_view()
