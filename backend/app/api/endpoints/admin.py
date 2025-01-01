from fastapi import APIRouter, Depends, HTTPException
from typing import List
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging
from ...services.financial_data_collector import FinancialDataCollector
from ...models.admin import CompanyUpdate
from ...scripts.fetch_financial_reports import FinancialReportCollector

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/companies")
async def list_companies():
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
    company: CompanyUpdate
):
    try:
        collector = FinancialDataCollector()
        result = collector.save_to_bigquery(company.dict(), "companies")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/collect")
async def collect_data(
    symbols: List[str]
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
async def fetch_financial_reports():
    """決算資料の取得を開始"""
    async def event_generator():
        collector = None
        try:
            # 進捗状況の初期値を送信
            yield f"data: {json.dumps({'progress': 0, 'message': '処理を開始します'})}\n\n"
            
            try:
                # コレクターの初期化
                collector = FinancialReportCollector()
                await collector.initialize()
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
            except Exception as e:
                logger.error(f"Error fetching companies: {str(e)}")
                yield f"data: {json.dumps({'error': f'企業一覧の取得に失敗しました: {str(e)}'})}\n\n"
                return
            
            # 企業ごとに決算資料を取得
            for i, company in enumerate(companies, 1):
                try:
                    progress = round(10 + ((i / total) * 90), 1)  # 10%から100%まで
                    
                    # 進捗状況を送信
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'current': i,
                        'total': total,
                        'message': f'{company["company_name"]} ({company["ticker"]}) の決算資料を取得中...'
                    })}\n\n"
                    
                    # EDINETから取得
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'current': i,
                        'total': total,
                        'message': f'{company["company_name"]} - EDINETから取得中...'
                    })}\n\n"
                    await collector.fetch_edinet_reports(company['ticker'], company['ticker'])
                    await asyncio.sleep(1)  # APIレート制限を考慮
                    
                    # TDnetから取得
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'current': i,
                        'total': total,
                        'message': f'{company["company_name"]} - TDnetから取得中...'
                    })}\n\n"
                    await collector.fetch_tdnet_reports(company['ticker'], company['ticker'])
                    await asyncio.sleep(1)
                    
                    # 企業サイトから取得
                    if company.get('website'):
                        yield f"data: {json.dumps({
                            'progress': progress,
                            'current': i,
                            'total': total,
                            'message': f'{company["company_name"]} - 企業サイトから取得中...'
                        })}\n\n"
                        await collector.fetch_company_website_reports(
                            company['ticker'],
                            company['ticker'],
                            company['website']
                        )
                        await asyncio.sleep(1)
                    
                    # 企業の処理完了を通知
                    yield f"data: {json.dumps({
                        'progress': progress,
                        'current': i,
                        'total': total,
                        'message': f'{company["company_name"]} の処理が完了しました ({i}/{total}社)'
                    })}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error processing company {company['ticker']}: {str(e)}")
                    yield f"data: {json.dumps({
                        'error': f"{company['company_name']}の処理中にエラーが発生しました: {str(e)}"
                    })}\n\n"
            
            # 完了通知
            yield f"data: {json.dumps({
                'progress': 100,
                'message': f'全ての企業（{total}社）の決算資料取得が完了しました'
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
