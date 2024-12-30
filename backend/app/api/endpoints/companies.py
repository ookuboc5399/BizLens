from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import json
import asyncio
from ...services.company_service import CompanyService
from ...services.bigquery_service import BigQueryService

router = APIRouter()
company_service = CompanyService()

# Redis接続の設定
@router.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://localhost", encoding="utf8")
    await FastAPILimiter.init(redis_client)
    FastAPICache.init(redis_client)

# BigQueryクライアント取得関数を修正
def get_bigquery_client():
    load_dotenv()  # 環境変数の読み込み
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    return bigquery.Client(credentials=credentials)

@router.get("/search")
@cache(expire=60)  # 60秒間キャッシュ
async def search_companies(
    rate_limiter: None = Depends(RateLimiter(times=10, seconds=60)),
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
        FROM `{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}`
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
        FROM `{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}`
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
            beta
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
                "beta": row.beta
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
            fiscal_year as year,
            revenue,
            operating_profit,
            net_income,
            gross_profit_margin,
            operating_margin,
            net_profit_margin,
            roe
        FROM `{os.getenv('BIGQUERY_DATASET')}.financial_history`
        WHERE ticker = @ticker
        ORDER BY fiscal_year ASC
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

@router.post("/collect-data", status_code=200)
async def collect_company_data():
    async def event_generator():
        try:
            print("Starting data collection process...")
            
            # データ収集の開始
            collected_data = []
            failed_companies = []
            
            companies = await company_service.get_company_list()
            total = len(companies)
            print(f"Found {total} companies to process")
            
            # 進捗状況の初期値を送信
            initial_data = {'progress': 0, 'current': 0, 'total': total}
            print(f"Sending initial progress: {initial_data}")
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # バッチ処理（10社ごと）
            batch_size = 10
            for i in range(0, total, batch_size):
                batch = companies[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(total+batch_size-1)//batch_size}")
                
                for company in batch:
                    try:
                        print(f"Collecting data for {company['ticker']}")
                        data = await company_service.collect_all_data(company['ticker'])
                        collected_data.append(data)
                    except Exception as e:
                        print(f"Error collecting data for {company['ticker']}: {str(e)}")
                        failed_companies.append({
                            'ticker': company['ticker'],
                            'error': str(e)
                        })
                    
                    current = len(collected_data) + len(failed_companies)
                    progress = round((current / total) * 100, 1)
                    progress_data = {'progress': progress, 'current': current, 'total': total}
                    print(f"Sending progress update: {progress_data}")
                    yield f"data: {json.dumps(progress_data)}\n\n"
                
                if i + batch_size < total:
                    print(f"Waiting 30 seconds before next batch...")
                    await asyncio.sleep(30)
            
            final_data = {
                'progress': 100,
                'total': len(collected_data),
                'updated': len(collected_data),
                'failed': failed_companies
            }
            print(f"Data collection completed. Final status: {final_data}")
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            print(f"Error in event_generator: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    ) 

@router.get("/earnings/monthly/{year}/{month}")
async def get_monthly_earnings(year: int, month: int):
    try:
        print(f"Getting monthly earnings for {year}-{month}")
        # 月の最初の日と最後の日を計算
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        print(f"Date range: {start_date} to {end_date}")
        bigquery_service = BigQueryService()
        calendar = await bigquery_service.get_earnings_calendar(start_date, end_date)
        print(f"Retrieved {len(calendar)} entries from BigQuery")
        
        # 日付ごとにグループ化
        monthly_data = {}
        for entry in calendar:
            date = entry["announcement_date"]
            if date not in monthly_data:
                monthly_data[date] = {
                    "date": date,
                    "count": 0
                }
            monthly_data[date]["count"] += 1

        return monthly_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/earnings/daily/{date}")
async def get_daily_earnings(date: str):
    try:
        print(f"Getting daily earnings for {date}")
        bigquery_service = BigQueryService()
        calendar = await bigquery_service.get_earnings_calendar(date, date)
        print(f"Retrieved {len(calendar)} companies for {date}")
        
        # 企業情報を整形
        companies = []
        for entry in calendar:
            companies.append({
                "code": entry["code"],
                "name": entry["company_name"],
                "market": entry.get("market", ""),
                "fiscal_year": str(entry["fiscal_year"]),
                "quarter": f"Q{entry['fiscal_quarter']}"
            })

        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
