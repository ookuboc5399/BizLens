#!/usr/bin/env python3
"""
環境変数の設定を確認するスクリプト
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def check_environment_variables():
    """環境変数の設定を確認"""
    
    print("=== 環境変数チェック ===")
    
    # OpenAI関連
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    print(f"OPENAI_API_KEY: {'設定済み' if openai_api_key else '未設定'}")
    print(f"OPENAI_MODEL: {openai_model}")
    
    if openai_api_key:
        print(f"API Key (最初の10文字): {openai_api_key[:10]}...")
    else:
        print("⚠️  OPENAI_API_KEYが設定されていません")
    
    # Snowflake関連
    snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")
    snowflake_user = os.getenv("SNOWFLAKE_USER")
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
    snowflake_database = os.getenv("SNOWFLAKE_DATABASE")
    snowflake_schema = os.getenv("SNOWFLAKE_SCHEMA")
    
    print(f"\n=== Snowflake設定 ===")
    print(f"SNOWFLAKE_ACCOUNT: {'設定済み' if snowflake_account else '未設定'}")
    print(f"SNOWFLAKE_USER: {'設定済み' if snowflake_user else '未設定'}")
    print(f"SNOWFLAKE_PASSWORD: {'設定済み' if snowflake_password else '未設定'}")
    print(f"SNOWFLAKE_DATABASE: {'設定済み' if snowflake_database else '未設定'}")
    print(f"SNOWFLAKE_SCHEMA: {'設定済み' if snowflake_schema else '未設定'}")
    
    # その他の設定
    print(f"\n=== その他の設定 ===")
    print(f"PORT: {os.getenv('PORT', '8000')}")
    
    # 推奨設定
    print(f"\n=== 推奨設定 ===")
    if not openai_api_key:
        print("1. OPENAI_API_KEYを設定してください")
        print("   export OPENAI_API_KEY='your-api-key-here'")
    
    if not openai_model or openai_model == "gpt-4":
        print("2. OPENAI_MODELを設定してください（例：gpt-4o-mini）")
        print("   export OPENAI_MODEL='gpt-4o-mini'")
    
    if not all([snowflake_account, snowflake_user, snowflake_password, snowflake_database, snowflake_schema]):
        print("3. Snowflake関連の環境変数を設定してください")

if __name__ == "__main__":
    check_environment_variables()
