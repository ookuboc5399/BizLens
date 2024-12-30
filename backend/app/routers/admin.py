from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings

router = APIRouter()

# 環境変数から取得する管理者認証情報
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

@router.post("/login")
async def admin_login(email: str, password: str):
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # JWTトークンの生成
    token = create_access_token({"sub": email, "role": "admin"})
    return {"token": token}

# 保護されたエンドポイントの例
@router.post("/companies/collect-data")
async def collect_company_data(current_admin = Depends(get_current_admin)):
    # データ収集ロジック
    return {"message": "Data collection completed"} 