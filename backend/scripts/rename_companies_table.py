#!/usr/bin/env python3
"""
SnowflakeのCOMPANIESテーブルをCOMPANIES_JPにリネームするスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def rename_companies_table():
    """COMPANIESテーブルをCOMPANIES_JPにリネーム"""
    
    snowflake_service = SnowflakeService()
    
    try:
        # 現在のテーブル構造を確認
        print("現在のテーブル構造を確認中...")
        check_table_query = """
        SHOW TABLES LIKE 'COMPANIES' IN SCHEMA PUBLIC;
        """
        
        cursor = snowflake_service.conn.cursor()
        cursor.execute(check_table_query)
        tables = cursor.fetchall()
        
        if not tables:
            print("COMPANIESテーブルが見つかりません。")
            return
        
        print(f"COMPANIESテーブルが見つかりました: {tables}")
        
        # 新しいテーブルCOMPANIES_JPを作成（既存のCOMPANIESテーブルと同じ構造）
        print("COMPANIES_JPテーブルを作成中...")
        create_table_query = """
        CREATE TABLE COMPANIES_JP AS SELECT * FROM COMPANIES;
        """
        
        cursor.execute(create_table_query)
        print("COMPANIES_JPテーブルが作成されました。")
        
        # 新しいテーブルの構造を確認
        print("新しいテーブルの構造を確認中...")
        describe_query = """
        DESCRIBE TABLE COMPANIES_JP;
        """
        
        cursor.execute(describe_query)
        structure = cursor.fetchall()
        print("COMPANIES_JPテーブルの構造:")
        for col in structure:
            print(f"  {col}")
        
        # データが正しく移行されたか確認
        print("データ移行の確認中...")
        count_query = """
        SELECT COUNT(*) FROM COMPANIES_JP;
        """
        
        cursor.execute(count_query)
        count = cursor.fetchone()[0]
        print(f"COMPANIES_JPテーブルのレコード数: {count}")
        
        # 元のテーブルのレコード数も確認
        cursor.execute("SELECT COUNT(*) FROM COMPANIES;")
        original_count = cursor.fetchone()[0]
        print(f"元のCOMPANIESテーブルのレコード数: {original_count}")
        
        if count == original_count:
            print("データ移行が正常に完了しました。")
            
            # 元のテーブルを削除（オプション）
            print("元のCOMPANIESテーブルを削除しますか？ (y/n): ", end="")
            response = input().strip().lower()
            
            if response == 'y':
                drop_query = """
                DROP TABLE COMPANIES;
                """
                cursor.execute(drop_query)
                print("元のCOMPANIESテーブルを削除しました。")
            else:
                print("元のCOMPANIESテーブルは保持されます。")
        else:
            print("警告: データ移行に問題があります。元のテーブルは削除されません。")
        
        snowflake_service.conn.commit()
        print("操作が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        snowflake_service.conn.rollback()
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    rename_companies_table()
