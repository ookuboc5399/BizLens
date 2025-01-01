from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FinancialReportCreate(BaseModel):
    """決算資料作成モデル"""
    company_id: str
    fiscal_year: str
    quarter: str
    report_type: str
    file_url: str
    source: str
    report_date: datetime

class FinancialReport(FinancialReportCreate):
    """決算資料モデル"""
    id: int
    gcs_path: str
    signed_url: Optional[str] = None
    original_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class FinancialReportResponse(BaseModel):
    """決算資料レスポンスモデル"""
    company_id: str
    fiscal_year: str
    quarter: str
    report_type: str
    source: str
    report_date: datetime
    signed_url: str
    created_at: datetime

    class Config:
        from_attributes = True
