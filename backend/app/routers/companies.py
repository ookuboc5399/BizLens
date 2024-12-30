from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.company_service import CompanyService
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter(tags=["companies"])
company_service = CompanyService()

@router.get("/search")
async def search_companies(
    q: str = Query(..., description="Company name or stock code to search for"),
):
    companies = await company_service.search_companies(q)
    return companies

@router.get("/{company_id}")
async def get_company(company_id: str):
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/{company_id}/details")
async def get_company_details(company_id: str):
    details = await company_service.get_company_details(company_id)
    if not details:
        raise HTTPException(status_code=404, detail="Company not found")
    return details

@router.get("/{company_id}/metrics")
async def get_company_metrics(company_id: str):
    metrics = await company_service.get_financial_metrics(company_id)
    return metrics

@router.get("/{company_id}/comparison")
async def get_company_comparison(company_id: str):
    comparison = await company_service.get_peer_companies(company_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Company not found")
    return comparison

@router.post("/collect-data", status_code=200)
async def collect_company_data():
    async def event_generator():
        try:
            print("Starting data collection process...")  # デバッグログ
            
            # データ収集の開始
            collected_data = []
            failed_companies = []
            
            companies = await company_service.get_company_list()
            total = len(companies)
            print(f"Found {total} companies to process")  # デバッグログ
            
            # 進捗状況の初期値を送信
            initial_data = {'progress': 0, 'current': 0, 'total': total}
            print(f"Sending initial progress: {initial_data}")  # デバッグログ
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # バッチ処理（10社ごと）
            batch_size = 10
            for i in range(0, total, batch_size):
                batch = companies[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(total+batch_size-1)//batch_size}")  # デバッグログ
                
                for company in batch:
                    try:
                        print(f"Collecting data for {company['ticker']}")  # デバッグログ
                        data = await company_service.collect_all_data(company['ticker'])
                        collected_data.append(data)
                    except Exception as e:
                        print(f"Error collecting data for {company['ticker']}: {str(e)}")  # デバッグログ
                        failed_companies.append({
                            'ticker': company['ticker'],
                            'error': str(e)
                        })
                    
                    # 進捗状況を送信
                    current = len(collected_data) + len(failed_companies)
                    progress = round((current / total) * 100, 1)
                    progress_data = {'progress': progress, 'current': current, 'total': total}
                    print(f"Sending progress update: {progress_data}")  # デバッグログ
                    yield f"data: {json.dumps(progress_data)}\n\n"
                
                if i + batch_size < total:
                    print(f"Waiting 30 seconds before next batch...")  # バッグログ
                    await asyncio.sleep(30)
            
            # 完了状態を送信
            final_data = {
                'progress': 100,
                'total': len(collected_data),
                'updated': len(collected_data),
                'failed': failed_companies
            }
            print(f"Data collection completed. Final status: {final_data}")  # デバッグログ
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            print(f"Error in event_generator: {str(e)}")  # デバッグログ
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
