from fastapi import APIRouter, Depends, HTTPException
from typing import List, AsyncGenerator
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging
from ...services.companies.data_collector import CompanyDataCollector
from ...services.financial_reports.financial_report_service import FinancialReportService
from ...models.admin import CompanyUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/companies")
async def list_companies():
    try:
        collector = CompanyDataCollector()
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
    company: CompanyUpdate
):
    try:
        collector = CompanyDataCollector()
        result = collector.save_to_bigquery(company.dict(), "companies")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/collect")
async def collect_company_data():
    """企業データの収集を開始"""
    async def event_generator():
        collector = None
        try:
            yield f"data: {json.dumps({'progress': 0, 'message': '企業データの収集を開始します'})}\n\n"
            
            try:
                collector = CompanyDataCollector()
                yield f"data: {json.dumps({'progress': 5, 'message': 'コレクターの初期化が完了しました'})}\n\n"
            except Exception as e:
                logger.error(f"Error initializing collector: {str(e)}")
                yield f"data: {json.dumps({'error': f'初期化エラー: {str(e)}'})}\n\n"
                return

            try:
                # 企業一覧を取得
                companies = await collector.fetch_all_companies()
                total = len(companies)
                if total == 0:
                    yield f"data: {json.dumps({'error': '企業データが見つかりません'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'progress': 10, 'message': f'企業一覧の取得が完了しました（{total}社）'})}\n\n"

                # 企業データを収集
                for i, company in enumerate(companies, 1):
                    progress = int(10 + (i / total * 90))
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'message': f'{company["company_name"]}の企業データを収集中... ({i}/{total})'
                    })}\n\n"

                    try:
                        await collector.collect_company_data(company["company_id"])
                    except Exception as e:
                        logger.error(f"Error collecting data for {company['company_id']}: {str(e)}")
                        yield f"data: {json.dumps({'error': f'{company["company_name"]}のデータ収集に失敗: {str(e)}'})}\n\n"

                yield f"data: {json.dumps({
                    'progress': 100,
                    'message': f'企業データの収集が完了しました（{total}社）'
                })}\n\n"

            except Exception as e:
                logger.error(f"Error in data collection: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        except Exception as e:
            logger.error(f"Error in collect_company_data: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.post("/financial-reports/fetch")
async def fetch_financial_reports():
    """決算資料の取得を開始"""
    async def event_generator():
        service = None
        try:
            yield f"data: {json.dumps({'progress': 0, 'message': '決算資料の収集を開始します'})}\n\n"
            
            try:
                service = FinancialReportService()
                yield f"data: {json.dumps({'progress': 5, 'message': 'サービスの初期化が完了しました'})}\n\n"
            except Exception as e:
                logger.error(f"Error initializing service: {str(e)}")
                yield f"data: {json.dumps({'error': f'初期化エラー: {str(e)}'})}\n\n"
                return
            
            try:
                # TDnetから決算資料を取得
                yield f"data: {json.dumps({
                    'progress': 20,
                    'message': 'TDnetから決算資料を取得中...'
                })}\n\n"
                
                result = await service.fetch_tdnet_reports()
                if result["status"] != "success":
                    yield f"data: {json.dumps({'error': result['message']})}\n\n"
                    return
                
                yield f"data: {json.dumps({
                    'progress': 100,
                    'message': result['message']
                })}\n\n"
                
            except Exception as e:
                logger.error(f"Error fetching TDnet reports: {str(e)}")
                yield f"data: {json.dumps({'error': f'決算資料の取得に失敗しました: {str(e)}'})}\n\n"
                return
            
        except Exception as e:
            logger.error(f"Error in fetch_financial_reports: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        finally:
            if service:
                await service.close()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
