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
        client = get_bigquery_client()
        
        query = f"""
        SELECT 
            code as company_code,
            company_name,
            market,
            fiscal_year,
            fiscal_quarter as quarter
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.earnings_calendar`
        WHERE DATE(announcement_date) = '{date}'
        ORDER BY company_code
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        companies = []
        for row in results:
            companies.append({
                "code": row.company_code,
                "name": row.company_name,
                "market": row.market,
                "fiscal_year": row.fiscal_year,
                "quarter": f"Q{row.quarter}"
            })
        
        return companies
    except Exception as e:
        print(f"Error in get_daily_earnings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
