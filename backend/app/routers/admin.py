from fastapi import APIRouter, HTTPException, Depends
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from datetime import datetime, timedelta
from pydantic import BaseModel
# import os

# from ..config import settings

router = APIRouter()

# ログインリクエストボディのPydanticモデルを定義 (フロントエンドがSupabase認証になったため、このモデルは不要になるが、一旦残す)
class AdminLoginRequest(BaseModel):
    email: str
    password: str

# 環境変数から取得する管理者認証情報 (不要になったためコメントアウト)
# ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
# ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
# SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# JWTトークン生成のための関数 (不要になったため削除)
# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=30)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
#     return encoded_jwt

# 管理者認証のための依存性 (不要になったため削除)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

# async def get_current_admin(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=401,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         email: str = payload.get("sub")
#         role: str = payload.get("role")
#         if email is None or role != "admin":
#             raise credentials_exception
#         return {"email": email, "role": role}
#     except JWTError:
#         raise credentials_exception


# ログインエンドポイント (不要になったためコメントアウト)
# @router.post("/login")
# async def admin_login(request: AdminLoginRequest):
#     if request.email != ADMIN_EMAIL or request.password != ADMIN_PASSWORD:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     access_token_expires = timedelta(days=1)
#     token = create_access_token(
#         data={"sub": request.email, "role": "admin"}, expires_delta=access_token_expires
#     )
#     return {"access_token": token, "user": {"email": request.email, "role": "admin"}}


# 保護されたエンドポイントの例 (認証はフロントエンドで管理)

@router.post("/companies/collect-data")
async def collect_company_data():
    # データ収集ロジック
    return {"message": "Data collection completed"}
