#!/usr/bin/env python3
"""
EARNINGS_CALENDARテーブルをCOMPANIES_JPに統合し、COMPANIES_USテーブルを作成するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def merge_earnings_and_create_us_table():
    """EARNINGS_CALENDARをCOMPANIES_JPに統合し、COMPANIES_USを作成"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # 1. EARNINGS_CALENDARテーブルの構造を確認
        print("EARNINGS_CALENDARテーブルの構造を確認中...")
        cursor.execute("DESCRIBE TABLE EARNINGS_CALENDAR;")
        earnings_structure = cursor.fetchall()
        print("EARNINGS_CALENDARテーブルの構造:")
        for col in earnings_structure:
            print(f"  {col}")
        
        # 2. COMPANIES_JPテーブルにEARNINGS_CALENDARの列を追加
        print("\nCOMPANIES_JPテーブルにEARNINGS_CALENDARの列を追加中...")
        
        # EARNINGS_CALENDARから追加する列を定義（実際の列名に合わせて修正）
        earnings_columns = [
            "announcement_date",
            "fiscal_year",
            "fiscal_quarter"
        ]
        
        # 各列を追加
        for column in earnings_columns:
            try:
                # 列が存在するかチェック
                cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'COMPANIES_JP' AND COLUMN_NAME = '{column.upper()}'
                """)
                
                if cursor.fetchone()[0] == 0:
                    # 列が存在しない場合は追加
                    if column == "announcement_date":
                        cursor.execute(f"ALTER TABLE COMPANIES_JP ADD COLUMN {column.upper()} DATE;")
                    elif column in ["fiscal_year", "fiscal_quarter"]:
                        cursor.execute(f"ALTER TABLE COMPANIES_JP ADD COLUMN {column.upper()} NUMBER(38,0);")
                    else:
                        cursor.execute(f"ALTER TABLE COMPANIES_JP ADD COLUMN {column.upper()} VARCHAR(16777216);")
                    print(f"  列 {column.upper()} を追加しました")
                else:
                    print(f"  列 {column.upper()} は既に存在します")
                    
            except Exception as e:
                print(f"  列 {column.upper()} の追加でエラー: {e}")
        
        # 3. EARNINGS_CALENDARのデータをCOMPANIES_JPに統合
        print("\nEARNINGS_CALENDARのデータをCOMPANIES_JPに統合中...")
        
        merge_query = """
        UPDATE COMPANIES_JP c
        SET 
            ANNOUNCEMENT_DATE = ec.ANNOUNCEMENT_DATE,
            FISCAL_YEAR = ec.FISCAL_YEAR,
            FISCAL_QUARTER = ec.FISCAL_QUARTER
        FROM EARNINGS_CALENDAR ec
        WHERE c.TICKER = ec.TICKER
        """
        
        cursor.execute(merge_query)
        updated_rows = cursor.rowcount
        print(f"  {updated_rows} 件のレコードを更新しました")
        
        # 4. COMPANIES_USテーブルを作成
        print("\nCOMPANIES_USテーブルを作成中...")
        
        # COMPANIES_JPと同じ構造でCOMPANIES_USを作成
        create_us_table_query = """
        CREATE TABLE COMPANIES_US AS 
        SELECT * FROM COMPANIES_JP WHERE 1=0
        """
        
        cursor.execute(create_us_table_query)
        print("COMPANIES_USテーブルが作成されました")
        
        # 5. アメリカ企業のサンプルデータを挿入（例）
        print("\nCOMPANIES_USにサンプルデータを挿入中...")
        
        # 主要なアメリカ企業のサンプルデータ
        us_companies = [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'country': 'US',
                'market': 'NASDAQ',
                'market_cap': 3000000000000,
                'current_price': 150.0,
                'employees': 164000,
                'revenue': 394328000000,
                'operating_profit': 114301000000,
                'net_profit': 96995000000
            },
            {
                'ticker': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software',
                'country': 'US',
                'market': 'NASDAQ',
                'market_cap': 2800000000000,
                'current_price': 375.0,
                'employees': 221000,
                'revenue': 211915000000,
                'operating_profit': 88452000000,
                'net_profit': 72361000000
            },
            {
                'ticker': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'country': 'US',
                'market': 'NASDAQ',
                'market_cap': 1800000000000,
                'current_price': 140.0,
                'employees': 156500,
                'revenue': 307394000000,
                'operating_profit': 84294000000,
                'net_profit': 73737000000
            }
        ]
        
        # サンプルデータを挿入
        for company in us_companies:
            insert_query = """
            INSERT INTO COMPANIES_US (
                TICKER, COMPANY_NAME, SECTOR, INDUSTRY, COUNTRY, MARKET,
                MARKET_CAP, CURRENT_PRICE, EMPLOYEES, REVENUE, OPERATING_PROFIT, NET_PROFIT
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                company['ticker'],
                company['company_name'],
                company['sector'],
                company['industry'],
                company['country'],
                company['market'],
                company['market_cap'],
                company['current_price'],
                company['employees'],
                company['revenue'],
                company['operating_profit'],
                company['net_profit']
            ))
        
        print(f"  {len(us_companies)} 件のサンプルデータを挿入しました")
        
        # 6. 最終確認
        print("\n最終確認中...")
        
        # COMPANIES_JPのレコード数
        cursor.execute("SELECT COUNT(*) FROM COMPANIES_JP")
        jp_count = cursor.fetchone()[0]
        print(f"COMPANIES_JPのレコード数: {jp_count}")
        
        # COMPANIES_USのレコード数
        cursor.execute("SELECT COUNT(*) FROM COMPANIES_US")
        us_count = cursor.fetchone()[0]
        print(f"COMPANIES_USのレコード数: {us_count}")
        
        # EARNINGS_CALENDARのレコード数
        cursor.execute("SELECT COUNT(*) FROM EARNINGS_CALENDAR")
        earnings_count = cursor.fetchone()[0]
        print(f"EARNINGS_CALENDARのレコード数: {earnings_count}")
        
        snowflake_service.conn.commit()
        print("\n操作が完了しました。")
        
        # 7. EARNINGS_CALENDARテーブルの削除（オプション）
        print("\nEARNINGS_CALENDARテーブルを削除しますか？ (y/n): ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            cursor.execute("DROP TABLE EARNINGS_CALENDAR")
            print("EARNINGS_CALENDARテーブルを削除しました。")
            snowflake_service.conn.commit()
        else:
            print("EARNINGS_CALENDARテーブルは保持されます。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        snowflake_service.conn.rollback()
    finally:
        cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    merge_earnings_and_create_us_table()
