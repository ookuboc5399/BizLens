from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from datetime import datetime, date

router = APIRouter()

@router.get("/monthly/{year}/{month}")
async def get_monthly_earnings(year: int, month: int):
    client = bigquery.Client()
    
    query = f"""
    SELECT 
        DATE(date) as date,
        company_count
    FROM `BuffetCodeClone.earnings_calendar`
    WHERE EXTRACT(YEAR FROM date) = {year}
    AND EXTRACT(MONTH FROM date) = {month}
    ORDER BY date
    """
    
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{date}")
async def get_daily_earnings(date: str):
    client = bigquery.Client()
    
    query = f"""
    SELECT 
        company_code,
        company_name,
        market,
        fiscal_year,
        quarter
    FROM `BuffetCodeClone.earnings_companies`
    WHERE date = '{date}'
    ORDER BY company_code
    """
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        companies = []
        for row in results:
            companies.append({
                "code": row.company_code,
                "name": row.company_name,
                "market": row.market,
                "fiscal_year": row.fiscal_year,
                "quarter": row.quarter
            })
        
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 