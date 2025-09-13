#!/usr/bin/env python3
"""
両方のテーブルの構造を比較するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def check_table_structure():
    """両方のテーブルの構造を比較"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # COMPANIES_JPテーブルの構造を確認
        print("COMPANIES_JPテーブルの構造:")
        cursor.execute("DESCRIBE TABLE COMPANIES_JP;")
        jp_structure = cursor.fetchall()
        jp_columns = [col[0] for col in jp_structure]
        for col in jp_structure:
            print(f"  {col[0]} - {col[1]}")
        
        print(f"\nCOMPANIES_JPの列数: {len(jp_columns)}")
        
        # COMPANIES_USテーブルの構造を確認
        print("\nCOMPANIES_USテーブルの構造:")
        cursor.execute("DESCRIBE TABLE COMPANIES_US;")
        us_structure = cursor.fetchall()
        us_columns = [col[0] for col in us_structure]
        for col in us_structure:
            print(f"  {col[0]} - {col[1]}")
        
        print(f"\nCOMPANIES_USの列数: {len(us_columns)}")
        
        # 列の違いを確認
        print("\n列の違い:")
        jp_set = set(jp_columns)
        us_set = set(us_columns)
        
        only_in_jp = jp_set - us_set
        only_in_us = us_set - jp_set
        
        if only_in_jp:
            print(f"COMPANIES_JPにのみ存在: {list(only_in_jp)}")
        if only_in_us:
            print(f"COMPANIES_USにのみ存在: {list(only_in_us)}")
        if not only_in_jp and not only_in_us:
            print("両テーブルの列は一致しています")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    check_table_structure()
