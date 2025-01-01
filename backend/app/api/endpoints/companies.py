from fastapi import APIRouter, HTTPException, Query
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
from ...services.company_service import CompanyService
from ...services.bigquery_service import BigQueryService

router = APIRouter()
company_service = CompanyService()

# BigQueryクライアント取得関数を修正
def get_bigquery_client():
    load_dotenv()  # 環境変数の読み込み
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
        
        # 検索条件の構築
        conditions = ["1=1"]  # デフォルトの条件
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

        # ページネーション用のオフセット計算
        offset = (page - 1) * page_size

        # クエリの構築
        bq_query = f"""
        SELECT *
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}`
        WHERE {" AND ".join(conditions)}
        ORDER BY market_cap DESC
        LIMIT @page_size
        OFFSET @offset
        """

        parameters.extend([
            bigquery.ScalarQueryParameter("page_size", "INT64", page_size),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ])

        # 総件数を取得するクエリ
        count_query = f"""
        SELECT COUNT(*) as total
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}`
        WHERE {" AND ".join(conditions)}
        """

        job_config = bigquery.QueryJobConfig(query_parameters=parameters)

        # メインクエリの実行
        query_job = client.query(bq_query, job_config=job_config)
        results = query_job.result()

        # 総件数の取得
        count_job = client.query(count_query, job_config=job_config)
        total = next(count_job.result()).total

        # 結果の整形
        companies = []
        for row in results:
            company = {
                "company_name": row.company_name,
                "ticker": row.ticker,
                "sector": row.sector,
                "industry": row.industry,
                "country": row.country,
                "website": row.website,
                "description": row.description,
                "market_cap": row.market_cap,
                "employees": row.employees
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
        print(f"Getting company details for ticker: {ticker}")
        client = get_bigquery_client()
        print("BigQuery client initialized")
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset = os.getenv('BIGQUERY_DATASET')
        table = os.getenv('BIGQUERY_TABLE')
        
        print(f"Executing query for ticker: {ticker}")
        query = f"""
        SELECT
            ticker,
            company_name,
            market_price,
            market_cap,
            per,
            roe,
            dividend_yield,
            market,
            sector,
            pbr,
            roa,
            net_margin,
            dividend_per_share,
            payout_ratio,
            beta,
            description
        FROM `{project_id}.{dataset}.{table}`
        WHERE ticker = @ticker
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ticker", "STRING", ticker)
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        print(f"Query job created: {query_job.job_id}")
        results = query_job.result()
        print("Query completed")
        
        rows = list(results)
        print(f"Found {len(rows)} rows")
        
        if not rows:
            raise HTTPException(status_code=404, detail="Company not found")
            
        for row in rows:
            return {
                "ticker": row.ticker,
                "company_name": row.company_name,
                "market_price": row.market_price,
                "market_cap": row.market_cap,
                "per": row.per,
                "roe": row.roe,
                "dividend_yield": row.dividend_yield,
                "market": row.market,
                "sector": row.sector,
                "pbr": row.pbr,
                "roa": row.roa,
                "net_margin": row.net_margin,
                "dividend_per_share": row.dividend_per_share,
                "payout_ratio": row.payout_ratio,
                "beta": row.beta,
                "description": row.description
            }
            
        raise HTTPException(status_code=404, detail="Company not found")
        
    except Exception as e:
        print(f"Error in get_company_detail: {str(e)}")
        print(f"Project ID: {project_id}")
        print(f"Dataset: {dataset}")
        print(f"Table: {table}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/financial-history")
async def get_financial_history(ticker: str):
    try:
        client = get_bigquery_client()
        query = f"""
        SELECT
            2023 as year,  # 現在は単年度データのみ
            revenue,
            operating_income as operating_profit,
            net_income,
            gross_margin as gross_profit_margin,
            operating_margin,
            net_margin as net_profit_margin,
            roe
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}`
        WHERE ticker = @ticker
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
