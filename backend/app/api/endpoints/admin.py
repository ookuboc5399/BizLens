from fastapi import APIRouter, Depends, HTTPException
from typing import List
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging
from ...services.financial_data_collector import FinancialDataCollector
from ...models.admin import CompanyUpdate
from ...auth.dependencies import get_current_admin_user
from ...scripts.fetch_financial_reports import FinancialReportCollector

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/companies")
async def list_companies(
    current_user: dict = Depends(get_current_admin_user)
):
    try:
        collector = FinancialDataCollector()
        companies = collector.bq_client.query("""
            SELECT DISTINCT symbol, company_name, sector, industry
            FROM `BuffetCodeClone.companies`
            ORDER BY company_name
        """).result()
        return {"companies": [dict(row) for row in companies]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/companies/update")
async def update_company(
    company: CompanyUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    try:
        collector = FinancialDataCollector()
        result = collector.save_to_bigquery(company.dict(), "companies")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/collect")
async def collect_data(
    symbols: List[str],
    current_user: dict = Depends(get_current_admin_user)
):
    collector = FinancialDataCollector()
    results = []
    for symbol in symbols:
        data = collector.collect_yahoo_finance_data(symbol)
        if "error" not in data:
            save_result = collector.save_to_bigquery(data, "financial_data")
            results.append({
                "symbol": symbol,
                "status": save_result["status"],
                "message": save_result.get("message", "")
            })
        else:
            results.append({
                "symbol": symbol,
                "status": "error",
                "message": data["error"]
            })
    return results

@router.post("/financial-reports/fetch")
async def fetch_financial_reports(
    current_user: dict = Depends(get_current_admin_user)
):
    """決算資料の取得を開始"""
    async def event_generator():
        collector = None
        try:
            # 進捗状況の初期値を送信
            yield f"data: {json.dumps({'progress': 0, 'message': '処理を開始します'})}\n\n"
            
            # 企業一覧を取得
            financial_data_collector = FinancialDataCollector()
            companies_query = """
                SELECT DISTINCT symbol as ticker, company_name, sector, website
                FROM `BuffetCodeClone.companies`
                ORDER BY company_name
            """
            companies_result = financial_data_collector.bq_client.query(companies_query).result()
            companies = [dict(row) for row in companies_result]
            total = len(companies)
            
            # コレクターの初期化
            collector = FinancialReportCollector()
            await collector.initialize()
            
            # 企業ごとに決算資料を取得
            for i, company in enumerate(companies):
                try:
                    current = i + 1
                    progress = round((current / total) * 100, 1)
                    
                    # 進捗状況を送信
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'current': current,
                        'total': total,
                        'message': f'{company['company_name']}の決算資料を取得中...'
                    })}\n\n"
                    
                    # 各ソースから決算資料を取得
                    await collector.fetch_edinet_reports(company['ticker'], company['ticker'])
                    await asyncio.sleep(1)  # APIレート制限を考慮
                    
                    await collector.fetch_tdnet_reports(company['ticker'], company['ticker'])
                    await asyncio.sleep(1)
                    
                    if company.get('website'):
                        await collector.fetch_company_website_reports(
                            company['ticker'],
                            company['ticker'],
                            company['website']
                        )
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing company {company['ticker']}: {str(e)}")
                    yield f"data: {json.dumps({
                        'error': f"{company['company_name']}の処理中にエラーが発生しました: {str(e)}"
                    })}\n\n"
            
            # 完了通知
            yield f"data: {json.dumps({
                'progress': 100,
                'message': '全ての企業の決算資料取得が完了しました'
            })}\n\n"
            
        except Exception as e:
            logger.error(f"Error in fetch_financial_reports: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        finally:
            if collector:
                await collector.close()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
