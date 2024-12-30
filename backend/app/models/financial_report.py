from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FinancialReport(BaseModel):
    id: str
    company_id: str
    fiscal_year: str
    quarter: str
    report_type: str
    file_url: str
    source: str
    report_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

class FinancialReportCreate(BaseModel):
    company_id: str
    fiscal_year: str
    quarter: str
    report_type: str
    file_url: str
    source: str
    report_date: datetime
