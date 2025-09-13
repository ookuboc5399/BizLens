#!/usr/bin/env python3
"""
異常なTICKERを削除するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def cleanup_abnormal_tickers():
    """異常なTICKERを削除"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # 異常なTICKERのパターンを定義
        abnormal_patterns = [
            # 20桁以上の数字
            "LENGTH(ticker) > 20",
            # 数字以外の文字が含まれている（日本の証券コードは4桁の数字）
            "ticker REGEXP '[^0-9]' AND country = 'JP'",
            # アメリカの証券コードは1-5文字のアルファベット
            "ticker REGEXP '[^A-Z]' AND country = 'US'",
            # 特定の異常なTICKER
            "ticker = '26570242392015430942'"
        ]
        
        print("異常なTICKERを検索中...")
        
        for pattern in abnormal_patterns:
            # COMPANIES_JPから検索
            jp_query = f"""
            SELECT TICKER, COMPANY_NAME, COUNTRY
            FROM COMPANIES_JP
            WHERE {pattern}
            """
            
            cursor.execute(jp_query)
            jp_results = cursor.fetchall()
            
            if jp_results:
                print(f"COMPANIES_JP - {pattern}:")
                for ticker, company_name, country in jp_results:
                    print(f"  {ticker}: {company_name} ({country})")
            
            # COMPANIES_USから検索
            us_query = f"""
            SELECT TICKER, COMPANY_NAME, COUNTRY
            FROM COMPANIES_US
            WHERE {pattern}
            """
            
            cursor.execute(us_query)
            us_results = cursor.fetchall()
            
            if us_results:
                print(f"COMPANIES_US - {pattern}:")
                for ticker, company_name, country in us_results:
                    print(f"  {ticker}: {company_name} ({country})")
        
        # 削除の確認
        print("\n異常なTICKERを削除しますか？ (y/N): ", end="")
        confirm = input().strip().lower()
        
        if confirm == 'y':
            # 異常なTICKERを削除
            for pattern in abnormal_patterns:
                # COMPANIES_JPから削除
                jp_delete_query = f"""
                DELETE FROM COMPANIES_JP
                WHERE {pattern}
                """
                
                cursor.execute(jp_delete_query)
                jp_deleted = cursor.rowcount
                if jp_deleted > 0:
                    print(f"COMPANIES_JP: {jp_deleted}件を削除")
                
                # COMPANIES_USから削除
                us_delete_query = f"""
                DELETE FROM COMPANIES_US
                WHERE {pattern}
                """
                
                cursor.execute(us_delete_query)
                us_deleted = cursor.rowcount
                if us_deleted > 0:
                    print(f"COMPANIES_US: {us_deleted}件を削除")
            
            snowflake_service.conn.commit()
            print("異常なTICKERの削除が完了しました。")
        else:
            print("削除をキャンセルしました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        snowflake_service.conn.rollback()
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    cleanup_abnormal_tickers()
