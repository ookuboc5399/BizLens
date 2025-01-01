from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_admin_user(request: Request, token: str = Depends(oauth2_scheme)):
    # 開発環境では認証をスキップ
    if os.getenv("ENV") == "development":
        return request.state.user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        if not is_admin(username):
            raise HTTPException(status_code=403, detail="Not an admin user")
        return {"username": username}
    except JWTError:
        raise credentials_exception

def is_admin(username: str) -> bool:
    # 実際の実装ではデータベースでの確認が必要
    return username in os.getenv("ADMIN_USERS", "").split(",")
