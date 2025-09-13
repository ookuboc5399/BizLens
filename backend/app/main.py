from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# .envファイルを読み込み
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込み
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from app.routers import admin, chat
from app.api.endpoints import admin as admin_endpoints, companies as companies_endpoints, earnings_calendar, financial_reports, auth

app = FastAPI(title="BizLens API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なドメインを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# APIエンドポイント
app.include_router(admin_endpoints.router, prefix="/api/admin", tags=["admin"])
app.include_router(companies_endpoints.router, prefix="/api/companies", tags=["companies"])
app.include_router(earnings_calendar.router, prefix="/api/earnings", tags=["earnings"])
app.include_router(financial_reports.router, prefix="/api/financial-reports", tags=["financial-reports"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


# ヘルスチェック
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Vercel用のハンドラー
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
