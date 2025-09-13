#!/usr/bin/env python3
"""
代表者（CEO/代表取締役）の列を追加するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def add_ceo_column():
    """代表者の列を追加"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # COMPANIES_JPテーブルに代表者列を追加
        print("COMPANIES_JPテーブルに代表者列を追加中...")
        try:
            cursor.execute("ALTER TABLE COMPANIES_JP ADD COLUMN CEO VARCHAR(100);")
            print("COMPANIES_JPにCEO列を追加しました")
        except Exception as e:
            print(f"COMPANIES_JPの列追加でエラー（既に存在する可能性）: {e}")
        
        # COMPANIES_USテーブルに代表者列を追加
        print("COMPANIES_USテーブルに代表者列を追加中...")
        try:
            cursor.execute("ALTER TABLE COMPANIES_US ADD COLUMN CEO VARCHAR(100);")
            print("COMPANIES_USにCEO列を追加しました")
        except Exception as e:
            print(f"COMPANIES_USの列追加でエラー（既に存在する可能性）: {e}")
        
        # 既存データの代表者情報を更新（サンプルデータ）
        print("既存データの代表者情報を更新中...")
        
        # 日本の主要企業の代表者情報
        jp_ceo_updates = [
            ("7203", "佐藤恒治"),  # トヨタ
            ("6758", "平井一夫"),  # ソニー
            ("9984", "田部井昌純"),  # ソフトバンク
            ("6861", "藤森義明"),  # キーエンス
            ("6954", "森田隆"),  # ファナック
            ("7974", "西田明男"),  # 任天堂
            ("8306", "三毛兼承"),  # 三菱UFJフィナンシャル・グループ
            ("9433", "宮内謙"),  # KDDI
            ("9432", "西室泰三"),  # NTT
            ("7269", "鈴木善久"),  # スズキ
        ]
        
        for ticker, ceo in jp_ceo_updates:
            try:
                cursor.execute("UPDATE COMPANIES_JP SET CEO = %s WHERE TICKER = %s", (ceo, ticker))
                if cursor.rowcount > 0:
                    print(f"COMPANIES_JP: {ticker} -> {ceo}")
            except Exception as e:
                print(f"更新エラー {ticker}: {e}")
        
        # アメリカの主要企業の代表者情報
        us_ceo_updates = [
            ("AAPL", "Tim Cook"),  # Apple
            ("MSFT", "Satya Nadella"),  # Microsoft
            ("GOOGL", "Sundar Pichai"),  # Alphabet
        ]
        
        for ticker, ceo in us_ceo_updates:
            try:
                cursor.execute("UPDATE COMPANIES_US SET CEO = %s WHERE TICKER = %s", (ceo, ticker))
                if cursor.rowcount > 0:
                    print(f"COMPANIES_US: {ticker} -> {ceo}")
            except Exception as e:
                print(f"更新エラー {ticker}: {e}")
        
        # 結果確認
        print("\n代表者情報の確認:")
        
        cursor.execute("SELECT TICKER, COMPANY_NAME, CEO FROM COMPANIES_JP WHERE CEO IS NOT NULL LIMIT 10")
        jp_ceos = cursor.fetchall()
        print("COMPANIES_JP（代表者情報あり）:")
        for ticker, company_name, ceo in jp_ceos:
            print(f"  {ticker}: {company_name} -> {ceo}")
        
        cursor.execute("SELECT TICKER, COMPANY_NAME, CEO FROM COMPANIES_US WHERE CEO IS NOT NULL LIMIT 10")
        us_ceos = cursor.fetchall()
        print("COMPANIES_US（代表者情報あり）:")
        for ticker, company_name, ceo in us_ceos:
            print(f"  {ticker}: {company_name} -> {ceo}")
        
        snowflake_service.conn.commit()
        print("\n代表者列の追加が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        snowflake_service.conn.rollback()
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    add_ceo_column()
