from fastapi import APIRouter, HTTPException
import os
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

@router.post("/google/token")
async def get_google_token(code: str):
    """Google OAuth認証コードからトークンを取得"""
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Google OAuth設定が不完全です")

        # Google OAuthトークンエンドポイントにリクエスト
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:5173/auth/callback"
        }

        response = requests.post(token_url, data=data)
        
        if not response.ok:
            print(f"Google OAuth error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="トークン取得に失敗しました")

        token_data = response.json()
        return token_data

    except Exception as e:
        print(f"OAuth token error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/google/refresh")
async def refresh_google_token(refresh_token: str):
    """Google OAuthリフレッシュトークンを使用してトークンを更新"""
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Google OAuth設定が不完全です")

        # Google OAuthトークンエンドポイントにリクエスト
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        response = requests.post(token_url, data=data)
        
        if not response.ok:
            print(f"Google OAuth refresh error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="トークン更新に失敗しました")

        token_data = response.json()
        return token_data

    except Exception as e:
        print(f"OAuth refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
