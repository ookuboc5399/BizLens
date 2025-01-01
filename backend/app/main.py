from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import companies, earnings, financial_reports, admin

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # フロントエンドのオリジン
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 開発環境用の認証スキップ
@app.middleware("http")
async def add_dev_user(request: Request, call_next):
    # 開発環境では常に管理者権限を持つように
    request.state.user = {
        "id": "1",
        "email": "admin@example.com",
        "role": "admin"
    }
    response = await call_next(request)
    return response

# ルーターの追加
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(earnings.router, prefix="/api/earnings", tags=["earnings"])
app.include_router(financial_reports.router, prefix="/api/financial-reports", tags=["financial-reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Welcome to BuffetCode API"}
