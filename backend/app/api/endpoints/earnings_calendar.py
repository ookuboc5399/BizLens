from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv

router = APIRouter()

def get_bigquery_client():
    load_dotenv()
    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        return bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    except Exception as e:
        print(f"Error initializing BigQuery client: {str(e)}")
        raise HTTPException(status_code=500, detail="データベース接続エラー")

@router.get("/monthly/{year}/{month}")
async def get_monthly_earnings(year: int, month: int):
    try:
        client = get_bigquery_client()
        
        query = f"""
        SELECT 
            DATE(announcement_date) as date,
            COUNT(*) as company_count
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.earnings_calendar`
        WHERE EXTRACT(YEAR FROM announcement_date) = {year}
        AND EXTRACT(MONTH FROM announcement_date) = {month}
        GROUP BY date
        ORDER BY date
        """
        
        print(f"Executing monthly query for {year}-{month}")
        query_job = client.query(query)
        results = query_job.result()
        
        calendar_data = {}
        for row in results:
            calendar_data[row.date.strftime('%Y-%m-%d')] = {
                "date": row.date.strftime('%Y-%m-%d'),
                "count": row.company_count
            }
        
        return calendar_data
    except Exception as e:
        print(f"Error in get_monthly_earnings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{date}")
async def get_daily_earnings(date: str):
    try:
        print(f"Getting daily earnings for date: {date}")
        client = get_bigquery_client()
        
        # 環境変数の確認
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset = os.getenv('BIGQUERY_DATASET')
        print(f"Project ID: {project_id}, Dataset: {dataset}")
        
        # テーブルの存在確認
        try:
            table = client.get_table(f"{project_id}.{dataset}.earnings_calendar")
            print(f"Table exists with schema: {[field.name for field in table.schema]}")
        except Exception as e:
            print(f"Error checking table: {str(e)}")
            raise HTTPException(status_code=500, detail="テーブル確認エラー")

        # 企業の詳細情報を含むクエリ
        query = f"""
        WITH latest_earnings AS (
            SELECT 
                ticker,
                company_name,
                announcement_date,
                fiscal_year,
                fiscal_quarter,
                ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY created_at DESC) as rn
            FROM `{project_id}.{dataset}.earnings_calendar`
            WHERE DATE(announcement_date) = '{date}'
        )
        SELECT 
            e.ticker as company_code,
            COALESCE(c.company_name, e.company_name) as company_name,
            c.market as market,
            e.fiscal_year,
            e.fiscal_quarter as quarter,
            c.description,
            c.sector,
            c.industry,
            c.market_cap,
            c.per,
            c.pbr,
            c.dividend_yield
        FROM latest_earnings e
        LEFT JOIN `{project_id}.{dataset}.companies` c
        ON e.ticker = c.ticker
        WHERE e.rn = 1
        ORDER BY e.ticker
        """
        
        print(f"Executing query for date {date}: {query}")
        query_job = client.query(query)
        
        print("Waiting for query results...")
        results = query_job.result()
        
        companies = []
        print("Processing results...")
        row_count = 0
        for row in results:
            row_count += 1
            print(f"Processing row {row_count}: {row.company_code}")
            company_data = {
                "code": row.company_code,
                "name": row.company_name,
                "market": row.market,
                "fiscal_year": row.fiscal_year,
                "quarter": f"Q{row.quarter}",
                "description": row.description,
                "sector": row.sector,
                "industry": row.industry,
                "market_cap": row.market_cap,
                "per": row.per,
                "pbr": row.pbr,
                "dividend_yield": row.dividend_yield
            }
            companies.append(company_data)
        
        print(f"Found {len(companies)} companies")
        return companies
    except Exception as e:
        error_message = f"Error in get_daily_earnings: {str(e)}"
        print(error_message)
        print(f"Project ID: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        print(f"Dataset: {os.getenv('BIGQUERY_DATASET')}")
        raise HTTPException(status_code=500, detail=error_message)
