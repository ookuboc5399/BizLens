#!/usr/bin/env python3
"""
データベースのCOUNTRYデータを確認するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def check_countries_data():
    """データベースのCOUNTRYデータを確認"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # COMPANIES_JPテーブルのCOUNTRYデータを確認
        print("COMPANIES_JPテーブルのCOUNTRYデータを確認中...")
        cursor.execute("SELECT DISTINCT country FROM COMPANIES_JP WHERE country IS NOT NULL AND country != '' ORDER BY country;")
        jp_countries = cursor.fetchall()
        print("COMPANIES_JPの国一覧:")
        for country in jp_countries:
            print(f"  {country[0]}")
        
        # COMPANIES_USテーブルのCOUNTRYデータを確認
        print("\nCOMPANIES_USテーブルのCOUNTRYデータを確認中...")
        cursor.execute("SELECT DISTINCT country FROM COMPANIES_US WHERE country IS NOT NULL AND country != '' ORDER BY country;")
        us_countries = cursor.fetchall()
        print("COMPANIES_USの国一覧:")
        for country in us_countries:
            print(f"  {country[0]}")
        
        # 全テーブルのCOUNTRYデータを確認
        print("\n全テーブルのCOUNTRYデータを確認中...")
        cursor.execute("""
        SELECT DISTINCT country FROM COMPANIES_JP 
        WHERE country IS NOT NULL AND country != ''
        UNION
        SELECT DISTINCT country FROM COMPANIES_US 
        WHERE country IS NOT NULL AND country != ''
        ORDER BY country;
        """)
        all_countries = cursor.fetchall()
        print("全テーブルの国一覧:")
        for country in all_countries:
            print(f"  {country[0]}")
        
        # 各テーブルのレコード数も確認
        print("\n各テーブルのレコード数:")
        cursor.execute("SELECT COUNT(*) FROM COMPANIES_JP")
        jp_count = cursor.fetchone()[0]
        print(f"COMPANIES_JP: {jp_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM COMPANIES_US")
        us_count = cursor.fetchone()[0]
        print(f"COMPANIES_US: {us_count}件")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    check_countries_data()
