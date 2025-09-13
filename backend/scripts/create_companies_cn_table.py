#!/usr/bin/env python3
"""
中国企業用のCOMPANIES_CNテーブルを作成するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def create_companies_cn_table():
    """中国企業用のCOMPANIES_CNテーブルを作成"""
    
    snowflake_service = SnowflakeService()
    
    try:
        cursor = snowflake_service.conn.cursor()
        
        # データベースとスキーマを設定
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        
        print(f"データベース: {db_name}")
        print(f"スキーマ: {schema_name}")
        
        # COMPANIES_CNテーブルを作成
        print("\nCOMPANIES_CNテーブルを作成中...")
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {db_name}.{schema_name}.COMPANIES_CN (
            TICKER VARCHAR(50),
            COMPANY_NAME VARCHAR(500),
            SECTOR VARCHAR(200),
            INDUSTRY VARCHAR(200),
            COUNTRY VARCHAR(10) DEFAULT 'CN',
            MARKET VARCHAR(20) DEFAULT 'CN',
            WEBSITE VARCHAR(500),
            BUSINESS_DESCRIPTION VARCHAR(2000),
            DESCRIPTION VARCHAR(3000),
            MARKET_CAP NUMBER(38,0),
            EMPLOYEES NUMBER(38,0),
            CURRENT_PRICE NUMBER(38,2),
            SHARES_OUTSTANDING NUMBER(38,0),
            VOLUME NUMBER(38,0),
            PER NUMBER(38,2),
            PBR NUMBER(38,2),
            EPS NUMBER(38,2),
            BPS NUMBER(38,2),
            ROE NUMBER(38,2),
            ROA NUMBER(38,2),
            REVENUE NUMBER(38,0),
            OPERATING_PROFIT NUMBER(38,0),
            NET_PROFIT NUMBER(38,0),
            TOTAL_ASSETS NUMBER(38,0),
            EQUITY NUMBER(38,0),
            OPERATING_MARGIN NUMBER(38,2),
            NET_MARGIN NUMBER(38,2),
            DIVIDEND_YIELD NUMBER(38,2),
            COMPANY_TYPE VARCHAR(50),
            CEO VARCHAR(200),
            FOUNDED_YEAR NUMBER(38,0),
            FUNDING_SERIES VARCHAR(100),
            TOTAL_FUNDING NUMBER(38,0),
            LATEST_FUNDING NUMBER(38,0),
            INVESTORS VARCHAR(1000),
            BUSINESS_MODEL VARCHAR(200),
            TARGET_MARKET VARCHAR(500),
            COMPETITIVE_ADVANTAGE VARCHAR(500),
            GROWTH_STAGE VARCHAR(100),
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
        
        cursor.execute(create_table_sql)
        print("COMPANIES_CNテーブルが作成されました")
        
        # テーブル構造を確認
        print("\nCOMPANIES_CNテーブルの構造を確認中...")
        cursor.execute(f"DESCRIBE TABLE {db_name}.{schema_name}.COMPANIES_CN")
        columns = cursor.fetchall()
        
        print("COMPANIES_CNテーブルの列:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # 中国企業のサンプルデータを挿入
        print("\nCOMPANIES_CNにサンプルデータを挿入中...")
        
        sample_companies = [
            {
                'ticker': 'BABA',
                'company_name': '阿里巴巴集团控股有限公司',
                'sector': 'テクノロジー',
                'industry': 'EC・インターネット',
                'country': 'CN',
                'market': 'CN',
                'website': 'https://www.alibaba.com/',
                'business_description': '中国最大のECプラットフォーム企業',
                'description': '阿里巴巴集团控股有限公司は、中国最大のECプラットフォーム企業で、B2B、B2C、C2Cの各分野で事業を展開しています。',
                'company_type': 'LISTED',
                'ceo': '張勇',
                'founded_year': 1999,
                'business_model': 'B2B2C',
                'target_market': '中国・東南アジア',
                'growth_stage': '成熟'
            },
            {
                'ticker': 'TCEHY',
                'company_name': '腾讯控股有限公司',
                'sector': 'テクノロジー',
                'industry': 'インターネット・ゲーム',
                'country': 'CN',
                'market': 'CN',
                'website': 'https://www.tencent.com/',
                'business_description': '中国最大のインターネット企業の一つ',
                'description': '腾讯控股有限公司は、中国最大のインターネット企業の一つで、ゲーム、SNS、決済、クラウドサービスなどを提供しています。',
                'company_type': 'LISTED',
                'ceo': '馬化騰',
                'founded_year': 1998,
                'business_model': 'B2C',
                'target_market': '中国・東南アジア',
                'growth_stage': '成熟'
            },
            {
                'ticker': 'JD',
                'company_name': '京东集团股份有限公司',
                'sector': 'テクノロジー',
                'industry': 'EC・物流',
                'country': 'CN',
                'market': 'CN',
                'website': 'https://www.jd.com/',
                'business_description': '中国の大手EC企業',
                'description': '京东集团股份有限公司は、中国の大手EC企業で、自社物流網を活用した高速配送サービスを特徴としています。',
                'company_type': 'LISTED',
                'ceo': '劉強東',
                'founded_year': 1998,
                'business_model': 'B2C',
                'target_market': '中国',
                'growth_stage': '成熟'
            }
        ]
        
        for company in sample_companies:
            insert_sql = f"""
            INSERT INTO {db_name}.{schema_name}.COMPANIES_CN (
                TICKER, COMPANY_NAME, SECTOR, INDUSTRY, COUNTRY, MARKET, WEBSITE,
                BUSINESS_DESCRIPTION, DESCRIPTION, COMPANY_TYPE, CEO, FOUNDED_YEAR,
                BUSINESS_MODEL, TARGET_MARKET, GROWTH_STAGE
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            values = (
                company['ticker'], company['company_name'], company['sector'],
                company['industry'], company['country'], company['market'],
                company['website'], company['business_description'], company['description'],
                company['company_type'], company['ceo'], company['founded_year'],
                company['business_model'], company['target_market'], company['growth_stage']
            )
            
            cursor.execute(insert_sql, values)
            print(f"  {company['company_name']} を挿入しました")
        
        # コミット
        snowflake_service.conn.commit()
        print(f"\n{len(sample_companies)}件のサンプルデータを挿入しました")
        
        # データ件数を確認
        cursor.execute(f"SELECT COUNT(*) FROM {db_name}.{schema_name}.COMPANIES_CN")
        count = cursor.fetchone()[0]
        print(f"COMPANIES_CNテーブルの総レコード数: {count}")
        
        print("\nCOMPANIES_CNテーブルの作成が完了しました！")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    create_companies_cn_table()
