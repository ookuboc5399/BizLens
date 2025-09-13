#!/usr/bin/env python3
"""
企業タイプ（上場企業/スタートアップ）の列を追加するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def add_company_type_column():
    """企業タイプの列を追加"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # COMPANIES_JPテーブルに企業タイプ列を追加
        print("COMPANIES_JPテーブルに企業タイプ列を追加中...")
        try:
            cursor.execute("ALTER TABLE COMPANIES_JP ADD COLUMN COMPANY_TYPE VARCHAR(50);")
            print("COMPANIES_JPにCOMPANY_TYPE列を追加しました")
        except Exception as e:
            print(f"COMPANIES_JPの列追加でエラー（既に存在する可能性）: {e}")
        
        # COMPANIES_USテーブルに企業タイプ列を追加
        print("COMPANIES_USテーブルに企業タイプ列を追加中...")
        try:
            cursor.execute("ALTER TABLE COMPANIES_US ADD COLUMN COMPANY_TYPE VARCHAR(50);")
            print("COMPANIES_USにCOMPANY_TYPE列を追加しました")
        except Exception as e:
            print(f"COMPANIES_USの列追加でエラー（既に存在する可能性）: {e}")
        
        # 既存データの企業タイプを更新（簡易的な判別）
        print("既存データの企業タイプを更新中...")
        
        # 上場企業の特徴（証券コードが4桁の数字、時価総額が大きいなど）
        update_jp_query = """
        UPDATE COMPANIES_JP 
        SET COMPANY_TYPE = CASE 
            WHEN TICKER REGEXP '^[0-9]{4}$' AND MARKET_CAP > 10000000000 THEN 'LISTED'
            WHEN TICKER REGEXP '^[0-9]{4}$' THEN 'LISTED'
            WHEN MARKET_CAP > 10000000000 THEN 'LISTED'
            ELSE 'STARTUP'
        END
        WHERE COMPANY_TYPE IS NULL
        """
        
        update_us_query = """
        UPDATE COMPANIES_US 
        SET COMPANY_TYPE = CASE 
            WHEN TICKER REGEXP '^[A-Z]{1,5}$' AND MARKET_CAP > 1000000000 THEN 'LISTED'
            WHEN TICKER REGEXP '^[A-Z]{1,5}$' THEN 'LISTED'
            WHEN MARKET_CAP > 1000000000 THEN 'LISTED'
            ELSE 'STARTUP'
        END
        WHERE COMPANY_TYPE IS NULL
        """
        
        cursor.execute(update_jp_query)
        jp_updated = cursor.rowcount
        print(f"COMPANIES_JP: {jp_updated}件を更新")
        
        cursor.execute(update_us_query)
        us_updated = cursor.rowcount
        print(f"COMPANIES_US: {us_updated}件を更新")
        
        # 結果確認
        print("\n企業タイプの分布:")
        
        cursor.execute("SELECT COMPANY_TYPE, COUNT(*) FROM COMPANIES_JP GROUP BY COMPANY_TYPE")
        jp_distribution = cursor.fetchall()
        print("COMPANIES_JP:")
        for company_type, count in jp_distribution:
            print(f"  {company_type}: {count}件")
        
        cursor.execute("SELECT COMPANY_TYPE, COUNT(*) FROM COMPANIES_US GROUP BY COMPANY_TYPE")
        us_distribution = cursor.fetchall()
        print("COMPANIES_US:")
        for company_type, count in us_distribution:
            print(f"  {company_type}: {count}件")
        
        snowflake_service.conn.commit()
        print("\n企業タイプ列の追加が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        snowflake_service.conn.rollback()
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    add_company_type_column()
