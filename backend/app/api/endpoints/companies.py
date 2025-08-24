from fastapi import APIRouter, HTTPException, Query
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
from ...services.company_service import CompanyService
from ...services.bigquery_service import BigQueryService

router = APIRouter()
company_service = CompanyService()

def get_bigquery_client():
    load_dotenv()
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    return bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))

@router.get("/search")
async def search_companies(
    query: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sector: str = None,
    country: str = None
):
    try:
        client = get_bigquery_client()
        
        conditions = ["1=1"]
        parameters = []

        if query:
            conditions.append("""
                (LOWER(company_name) LIKE LOWER(@search_term)
                OR LOWER(ticker) LIKE LOWER(@search_term))
            """)
            parameters.append(
                bigquery.ScalarQueryParameter("search_term", "STRING", f"%{query}%")
            )

        if sector:
            conditions.append("LOWER(sector) = LOWER(@sector)")
            parameters.append(
                bigquery.ScalarQueryParameter("sector", "STRING", sector)
            )

        if country:
            conditions.append("LOWER(country) = LOWER(@country)")
            parameters.append(
                bigquery.ScalarQueryParameter("country", "STRING", country)
            )

        offset = (page - 1) * page_size

        bq_query = f"""
        SELECT
            ticker,
            company_name,
            market,
            sector,
            industry,
            country,
            website,
            business_description,
            market_cap,
            current_price,
            per,
            pbr,
            roe,
            roa,
            dividend_yield
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.companies`
        WHERE {" AND ".join(conditions)}
        ORDER BY market_cap DESC NULLS LAST
        LIMIT @page_size
        OFFSET @offset
        """

        parameters.extend([
            bigquery.ScalarQueryParameter("page_size", "INT64", page_size),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ])

        count_query = f"""
        SELECT COUNT(*) as total
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.companies`
        WHERE {" AND ".join(conditions)}
        """

        job_config = bigquery.QueryJobConfig(query_parameters=parameters)

        query_job = client.query(bq_query, job_config=job_config)
        results = query_job.result()

        count_job = client.query(count_query, job_config=job_config)
        total = next(count_job.result()).total

        companies = []
        for row in results:
            company = {
                "ticker": row.ticker,
                "company_name": row.company_name,
                "market": row.market,
                "sector": row.sector,
                "industry": row.industry,
                "country": row.country,
                "website": row.website,
                "business_description": row.business_description,
                "market_cap": row.market_cap,
                "current_price": row.current_price,
                "per": row.per,
                "pbr": row.pbr,
                "roe": row.roe,
                "roa": row.roa,
                "dividend_yield": row.dividend_yield
            }
            companies.append(company)

        return {
            "companies": companies,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"Error in search_companies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}")
async def get_company_detail(ticker: str):
    try:
        client = get_bigquery_client()
        
        query = f"""
        SELECT
            ticker,
            company_name,
            market,
            sector,
            industry,
            country,
            website,
            business_description,
            data_source,
            last_updated,
            current_price,
            market_cap,
            per,
            pbr,
            eps,
            bps,
            roe,
            roa,
            current_assets,
            total_assets,
            current_liabilities,
            total_liabilities,
            capital,
            minority_interests,
            shareholders_equity,
            debt_ratio,
            current_ratio,
            equity_ratio,
            operating_cash_flow,
            investing_cash_flow,
            financing_cash_flow,
            cash_and_equivalents,
            revenue,
            operating_income,
            net_income,
            operating_margin,
            net_margin,
            dividend_yield,
            dividend_per_share,
            payout_ratio,
            beta,
            shares_outstanding,
            market_type,
            currency,
            collected_at
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.companies`
        WHERE ticker = @ticker
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker)
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        rows = list(results)
        
        if not rows:
            raise HTTPException(status_code=404, detail="Company not found")
            
        row = rows[0]
        return dict(row)
        
    except Exception as e:
        print(f"Error in get_company_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/financial-history")
async def get_financial_history(ticker: str):
    try:
        client = get_bigquery_client()
        query = f"""
        SELECT
            collected_at as date,
            revenue,
            operating_income,
            net_income,
            operating_margin,
            net_margin,
            roe,
            roa,
            current_ratio,
            debt_ratio,
            equity_ratio
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.companies`
        WHERE ticker = @ticker
        ORDER BY collected_at DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker)
            ]
        )
        
        results = client.query(query, job_config=job_config).result()
        
        return {
            "data": [dict(row) for row in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
