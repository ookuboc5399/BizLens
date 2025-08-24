from fastapi import APIRouter, HTTPException, Query
import os
from dotenv import load_dotenv
from ...services.company_service import CompanyService
from ...services.snowflake_service import SnowflakeService

router = APIRouter()
company_service = CompanyService()
snowflake_service = SnowflakeService()

@router.get("/search")
async def search_companies(
    query: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sector: str = None,
    country: str = None
):
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        conditions = ["1=1"]
        query_params = []

        if query:
            conditions.append("""
                (LOWER(company_name) LIKE LOWER(%s)
                OR LOWER(ticker) LIKE LOWER(%s))
            """)
            query_params.append(f"%{query}%")
            query_params.append(f"%{query}%")

        if sector:
            conditions.append("LOWER(sector) = LOWER(%s)")
            query_params.append(sector)

        if country:
            conditions.append("LOWER(country) = LOWER(%s)")
            query_params.append(country)

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
        FROM {db_name}.{schema_name}.companies
        WHERE {" AND ".join(conditions)}
        ORDER BY market_cap DESC NULLS LAST
        LIMIT %s
        OFFSET %s
        """

        # LIMITとOFFSETのパラメータも追加
        query_params.append(page_size)
        query_params.append(offset)

        results = snowflake_service.query(bq_query, tuple(query_params))

        count_query = f"""
        SELECT COUNT(*) as total
        FROM {db_name}.{schema_name}.companies
        WHERE {" AND ".join(conditions)}
        """
        # COUNTクエリのパラメータは検索クエリと同じ（LIMIT/OFFSETを除く）
        count_results = snowflake_service.query(count_query, tuple(query_params[:-2]))
        total = count_results[0]['TOTAL']

        companies = []
        for row in results:
            company = {
                "ticker": row['TICKER'],
                "company_name": row['COMPANY_NAME'],
                "market": row['MARKET'],
                "sector": row['SECTOR'],
                "industry": row['INDUSTRY'],
                "country": row['COUNTRY'],
                "website": row['WEBSITE'],
                "business_description": row['BUSINESS_DESCRIPTION'],
                "market_cap": row['MARKET_CAP'],
                "current_price": row['CURRENT_PRICE'],
                "per": row['PER'],
                "pbr": row['PBR'],
                "roe": row['ROE'],
                "roa": row['ROA'],
                "dividend_yield": row['DIVIDEND_YIELD']
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
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

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
        FROM {db_name}.{schema_name}.companies
        WHERE ticker = %s
        """
        
        results = snowflake_service.query(query, (ticker,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Company not found")
            
        row = results[0]
        # Snowflakeの列名は大文字になるため、辞書のキーを修正
        return {
            "ticker": row['TICKER'],
            "company_name": row['COMPANY_NAME'],
            "market": row['MARKET'],
            "sector": row['SECTOR'],
            "industry": row['INDUSTRY'],
            "country": row['COUNTRY'],
            "website": row['WEBSITE'],
            "business_description": row['BUSINESS_DESCRIPTION'],
            "last_updated": row['LAST_UPDATED'].isoformat() if row['LAST_UPDATED'] else None,
            "current_price": row['CURRENT_PRICE'],
            "market_cap": row['MARKET_CAP'],
            "per": row['PER'],
            "pbr": row['PBR'],
            "eps": row['EPS'],
            "bps": row['BPS'],
            "roe": row['ROE'],
            "roa": row['ROA'],
            "current_assets": row['CURRENT_ASSETS'],
            "total_assets": row['TOTAL_ASSETS'],
            "current_liabilities": row['CURRENT_LIABILITIES'],
            "total_liabilities": row['TOTAL_LIABILITIES'],
            "capital": row['CAPITAL'],
            "minority_interests": row['MINORIT_INTERESTS'],
            "shareholders_equity": row['SHAREHOLDERS_EQUITY'],
            "debt_ratio": row['DEBT_RATIO'],
            "current_ratio": row['CURRENT_RATIO'],
            "equity_ratio": row['EQUITY_RATIO'],
            "operating_cash_flow": row['OPERATING_CASH_FLOW'],
            "investing_cash_flow": row['INVESTING_CASH_FLOW'],
            "financing_cash_flow": row['FINANCING_CASH_FLOW'],
            "cash_and_equivalents": row['CASH_AND_EQUIVALENTS'],
            "revenue": row['REVENUE'],
            "operating_income": row['OPERATING_INCOME'],
            "net_income": row['NET_INCOME'],
            "operating_margin": row['OPERATING_MARGIN'],
            "net_margin": row['NET_MARGIN'],
            "dividend_yield": row['DIVIDEND_YIELD'],
            "dividend_per_share": row['DIVIDEND_PER_SHARE'],
            "payout_ratio": row['PAYOUT_RATIO'],
            "beta": row['BETA'],
            "shares_outstanding": row['SHARES_OUTSTANDING'],
            "market_type": row['MARKET_TYPE'],
            "currency": row['CURRENCY'],
            "collected_at": row['COLLECTED_AT'].isoformat() if row['COLLECTED_AT'] else None
        }
        
    except Exception as e:
        print(f"Error in get_company_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/financial-history")
async def get_financial_history(ticker: str):
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

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
        FROM {db_name}.{schema_name}.companies
        WHERE ticker = %s
        ORDER BY collected_at DESC
        """
        
        results = snowflake_service.query(query, (ticker,))
        
        return {
            "data": [{
                "date": row['DATE'].isoformat() if row['DATE'] else None,
                "revenue": row['REVENUE'],
                "operating_income": row['OPERATING_INCOME'],
                "net_income": row['NET_INCOME'],
                "operating_margin": row['OPERATING_MARGIN'],
                "net_margin": row['NET_MARGIN'],
                "roe": row['ROE'],
                "roa": row['ROA'],
                "current_ratio": row['CURRENT_RATIO'],
                "debt_ratio": row['DEBT_RATIO'],
                "equity_ratio": row['EQUITY_RATIO']
            } for row in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
