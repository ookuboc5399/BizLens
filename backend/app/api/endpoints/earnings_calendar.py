from fastapi import APIRouter, HTTPException
import os
from dotenv import load_dotenv
from ...services.snowflake_service import SnowflakeService

router = APIRouter()
snowflake_service = SnowflakeService()

@router.get("/monthly/{year}/{month}")
async def get_monthly_earnings(year: int, month: int):
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        query = f"""
        SELECT 
            TO_DATE(announcement_date) as date,
            COUNT(*) as company_count
        FROM {db_name}.{schema_name}.earnings_calendar
        WHERE EXTRACT(YEAR FROM announcement_date) = {year}
        AND EXTRACT(MONTH FROM announcement_date) = {month}
        GROUP BY date
        ORDER BY date
        """
        
        print(f"Executing monthly query for {year}-{month}")
        results = snowflake_service.query(query)
        
        calendar_data = {}
        for row in results:
            calendar_data[row['DATE'].strftime('%Y-%m-%d')] = {
                "date": row['DATE'].strftime('%Y-%m-%d'),
                "count": row['COMPANY_COUNT']
            }
        
        return calendar_data
    except Exception as e:
        print(f"Error in get_monthly_earnings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{date}")
async def get_daily_earnings(date: str):
    try:
        print(f"Getting daily earnings for date: {date}")
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        # テーブルの存在確認はSnowflakeServiceのinitialize_databaseで行うため、ここでは不要

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
            FROM {db_name}.{schema_name}.earnings_calendar
            WHERE TO_DATE(announcement_date) = '{date}'
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
        LEFT JOIN {db_name}.{schema_name}.companies c
        ON e.ticker = c.ticker
        WHERE e.rn = 1
        ORDER BY e.ticker
        """
        
        print(f"Executing query for date {date}: {query}")
        results = snowflake_service.query(query)
        
        companies = []
        print("Processing results...")
        row_count = 0
        for row in results:
            row_count += 1
            print(f"Processing row {row_count}: {row['COMPANY_CODE']}")
            company_data = {
                "code": row['COMPANY_CODE'],
                "name": row['COMPANY_NAME'],
                "market": row['MARKET'],
                "fiscal_year": row['FISCAL_YEAR'],
                "quarter": f"Q{row['QUARTER']}",
                "description": row['DESCRIPTION'],
                "sector": row['SECTOR'],
                "industry": row['INDUSTRY'],
                "market_cap": row['MARKET_CAP'],
                "per": row['PER'],
                "pbr": row['PBR'],
                "dividend_yield": row['DIVIDEND_YIELD']
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
