from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ...services.financial_report_service import FinancialReportService
from ...models.financial_report import FinancialReport, FinancialReportCreate
from fastapi_limiter.depends import RateLimiter

router = APIRouter()
financial_report_service = FinancialReportService()

@router.get("/{ticker}", response_model=List[FinancialReport])
async def get_company_reports(
    ticker: str,
    rate_limiter: None = Depends(RateLimiter(times=10, seconds=60))
):
    """企業の決算資料一覧を取得"""
    try:
        reports = await financial_report_service.get_company_reports(ticker)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/latest", response_model=FinancialReport)
async def get_latest_report(
    ticker: str,
    rate_limiter: None = Depends(RateLimiter(times=10, seconds=60))
):
    """企業の最新の決算資料を取得"""
    try:
        report = await financial_report_service.get_latest_report(ticker)
        if not report:
            raise HTTPException(status_code=404, detail="決算資料が見つかりません")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=FinancialReport)
async def create_report(
    report: FinancialReportCreate,
    rate_limiter: None = Depends(RateLimiter(times=10, seconds=60))
):
    """新しい決算資料を登録"""
    try:
        created_report = await financial_report_service.create_report(report)
        return created_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
