from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ...services.financial_report_service import FinancialReportService
from ...models.financial_report import FinancialReportResponse
from ...auth.dependencies import get_current_admin_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{company_id}", response_model=List[FinancialReportResponse])
async def get_company_reports(
    company_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """企業の決算資料一覧を取得"""
    try:
        service = FinancialReportService()
        reports = await service.get_company_reports(company_id)
        return reports
    except Exception as e:
        logger.error(f"Error getting reports for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"決算資料の取得に失敗しました: {str(e)}"
        )

@router.get("/latest/{company_id}")
async def get_latest_report(
    company_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """企業の最新の決算資料を取得"""
    try:
        service = FinancialReportService()
        reports = await service.get_company_reports(company_id)
        if not reports:
            raise HTTPException(
                status_code=404,
                detail=f"決算資料が見つかりません: {company_id}"
            )
        return reports[0]  # 最新のレポートを返す
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest report for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"決算資料の取得に失敗しました: {str(e)}"
        )

@router.get("/download/{company_id}/{fiscal_year}/{quarter}")
async def get_report_download_url(
    company_id: str,
    fiscal_year: str,
    quarter: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """決算資料のダウンロードURLを取得"""
    try:
        service = FinancialReportService()
        reports = await service.get_company_reports(company_id)
        
        # 指定された年度・四半期のレポートを検索
        for report in reports:
            if (report["fiscal_year"] == fiscal_year and 
                report["quarter"] == quarter):
                return {"download_url": report["signed_url"]}
        
        raise HTTPException(
            status_code=404,
            detail=f"指定された決算資料が見つかりません: {company_id} {fiscal_year}Q{quarter}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download URL for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ダウンロードURLの取得に失敗しました: {str(e)}"
        )

@router.get("/search")
async def search_reports(
    company_id: str = None,
    fiscal_year: str = None,
    quarter: str = None,
    report_type: str = None,
    source: str = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """決算資料を検索"""
    try:
        service = FinancialReportService()
        reports = await service.search_reports(
            company_id=company_id,
            fiscal_year=fiscal_year,
            quarter=quarter,
            report_type=report_type,
            source=source
        )
        return reports
    except Exception as e:
        logger.error(f"Error searching reports: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"決算資料の検索に失敗しました: {str(e)}"
        )
