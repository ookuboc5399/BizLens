from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import companies, earnings, financial_reports
import logging
from .services.bigquery_service import BigQueryService
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# 環境変数を読み込む
load_dotenv()

app = FastAPI()

# CORSの設定を更新
app.add_middleware(
    CORSMiddleware,
    # 許可するオリジンのリストを更新
    allow_origins=[
        "http://localhost:5173",  # Viteのデフォルトポート
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",  # React開発サーバー
        "http://localhost:4173",  # Vite本番ビルド
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
    expose_headers=["*"]
)

# ルーターの登録
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(earnings.router, prefix="/api/earnings", tags=["earnings"])
app.include_router(financial_reports.router, prefix="/api/financial-reports", tags=["financial-reports"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error handler: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.on_event("startup")
async def startup_event():
    # 環境変数の確認
    print("Environment variables:")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    print(f"BIGQUERY_DATASET: {os.getenv('BIGQUERY_DATASET')}")
    print(f"BIGQUERY_TABLE: {os.getenv('BIGQUERY_TABLE')}")

    bigquery_service = BigQueryService()
    await bigquery_service.initialize_database()
    # scheduler.start()  # コメントアウト
