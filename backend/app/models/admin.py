from pydantic import BaseModel
from typing import Optional

class CompanyUpdate(BaseModel):
    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    website: Optional[str] = None
    description: Optional[str] = None 