
import os
import json
import snowflake.connector
from dotenv import load_dotenv
from typing import List, Dict, Optional

class SnowflakeService:
    def __init__(self):
        load_dotenv()
        try:
            self.conn = snowflake.connector.connect(
                user=os.getenv("SNOWFLAKE_USER"),
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
                database=os.getenv("SNOWFLAKE_DATABASE"),
                schema=os.getenv("SNOWFLAKE_SCHEMA"),
            )
            print("Successfully connected to Snowflake.")
        except Exception as e:
            print(f"Error connecting to Snowflake: {e}")
            self.conn = None

    def get_connection(self):
        return self.conn

    def upsert_companies(self, companies_data: List[Dict]):
        if not self.conn:
            print("No connection to Snowflake. Aborting upsert.")
            return

        cursor = self.conn.cursor()
        
        # The order of columns must match the table schema
        # and the order of values in the params tuple.
        columns = [
            'company_name', 'ticker', 'sector', 'industry', 'country', 'website',
            'description', 'business_description', 'market_cap', 'employees', 'market', 'current_price',
            'shares_outstanding', 'volume', 'per', 'pbr', 'eps', 'bps', 'roe',
            'roa', 'revenue', 'operating_profit', 'net_profit', 'total_assets',
            'equity', 'operating_margin', 'net_margin', 'dividend_yield', 'company_type', 'ceo'
        ]
        
        try:
            for company in companies_data:
                # 国に基づいてテーブル名を決定
                country = company.get('country', 'JP')
                if country == 'JP':
                    table_name = 'companies_jp'
                elif country == 'CN':
                    table_name = 'companies_cn'
                else:
                    table_name = 'companies_us'
                
                db_name = os.getenv("SNOWFLAKE_DATABASE")
                schema_name = os.getenv("SNOWFLAKE_SCHEMA")
                full_table_name = f"{db_name}.{schema_name}.{table_name}"
                
                merge_sql = f"""
                MERGE INTO {full_table_name} AS target
                USING (SELECT %s AS ticker) AS source
                ON target.ticker = source.ticker
                WHEN NOT MATCHED THEN
                    INSERT ({', '.join(columns)})
                    VALUES ({', '.join(['%s'] * len(columns))});
                """

                # Ensure all columns are present in the dictionary, with None as default
                # Also, ensure the order of values matches the `columns` list.
                params = [company.get(col) for col in columns]
                # The ticker is used twice in the MERGE statement
                final_params = [company.get('ticker')] + params
                
                cursor.execute(merge_sql, tuple(final_params))
                print(f"Successfully merged data for ticker: {company.get('ticker')} to {table_name}")
            
            self.conn.commit()
            print("Upsert operation committed.")

        except Exception as e:
            print(f"An error occurred during upsert: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def close_connection(self):
        if self.conn and not self.conn.is_closed():
            self.conn.close()
            print("Snowflake connection closed.")

    def query(self, query_string: str, params: Optional[Dict] = None) -> List[Dict]:
        """汎用クエリ実行メソッド"""
        if not self.conn:
            print("No connection to Snowflake. Aborting query.")
            return []

        cursor = self.conn.cursor()
        try:
            if params:
                # Snowflake connector uses qmark style for parameters
                # Convert params dict to a tuple in the correct order if needed
                # For now, assuming query_string already contains placeholders like ?
                # and params are passed as a tuple or list in execute
                # This part might need refinement based on actual query structure
                cursor.execute(query_string, params)
            else:
                cursor.execute(query_string)
            
            columns = [col[0] for col in cursor.description]
            results = []
            for row in cursor:
                results.append({col.lower(): val for col, val in zip(columns, row)})
            return results
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise
        finally:
            cursor.close()

    async def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict]:
        """指定期間の決算予定を取得"""
        print(f"Querying earnings calendar from {start_date} to {end_date}")
        query = f"""
        SELECT 
            e.ticker,
            e.company_name,
            e.announcement_date,
            e.fiscal_year,
            e.fiscal_quarter,
            c.sector,
            c.market_cap,
            c.current_price AS market_price, -- Snowflakeではcurrent_priceを使用
            c.per,
            c.roe
        FROM CORPORATE_INF.PUBLIC.earnings_calendar e -- データベース名.スキーマ名.テーブル名
        LEFT JOIN CORPORATE_INF.PUBLIC.companies c -- データベース名.スキーマ名.テーブル名
        ON e.ticker = c.ticker
        WHERE e.announcement_date BETWEEN %s AND %s -- Snowflakeのプレースホルダー
        ORDER BY e.announcement_date
        """
        
        try:
            # Snowflakeのプレースホルダーは%s
            results = self.query(query, (start_date, end_date))
            print(f"Found {len(results)} earnings announcements")
            return results
        except Exception as e:
            print(f"Error querying Snowflake for earnings calendar: {str(e)}")
            raise

    def create_companies_table(self):
        """companiesテーブルの作成"""
        if not self.conn:
            print("No connection to Snowflake. Aborting table creation.")
            return

        cursor = self.conn.cursor()
        try:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {os.getenv("SNOWFLAKE_DATABASE")}.{os.getenv("SNOWFLAKE_SCHEMA")}.companies (
                company_name VARCHAR,
                ticker VARCHAR,
                sector VARCHAR,
                industry VARCHAR,
                country VARCHAR,
                website VARCHAR,
                business_description VARCHAR,
                description VARCHAR,
                market_cap NUMBER,
                employees NUMBER,
                market VARCHAR,
                current_price FLOAT,
                shares_outstanding NUMBER,
                volume NUMBER,
                per FLOAT,
                pbr FLOAT,
                eps FLOAT,
                bps FLOAT,
                roe FLOAT,
                roa FLOAT,
                revenue FLOAT,
                operating_profit FLOAT,
                net_profit FLOAT,
                total_assets FLOAT,
                equity FLOAT,
                operating_margin FLOAT,
                net_margin FLOAT,
                tradingview_summary VARIANT,
                dividend_yield FLOAT
            );
            """
            cursor.execute(create_table_sql)
            print("companies table created or already exists.")
        except Exception as e:
            print(f"Error creating companies table: {str(e)}")
            raise
        finally:
            cursor.close()

    def create_earnings_calendar_table(self):
        """決算予定カレンダーテーブルの作成"""
        if not self.conn:
            print("No connection to Snowflake. Aborting table creation.")
            return

        cursor = self.conn.cursor()
        try:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {os.getenv("SNOWFLAKE_DATABASE")}.{os.getenv("SNOWFLAKE_SCHEMA")}.earnings_calendar (
                ticker VARCHAR,
                company_name VARCHAR,
                announcement_date DATE,
                fiscal_year NUMBER,
                fiscal_quarter NUMBER,
                created_at TIMESTAMP_NTZ,
                updated_at TIMESTAMP_NTZ
            );
            """
            cursor.execute(create_table_sql)
            print("earnings_calendar table created or already exists.")
        except Exception as e:
            print(f"Error creating earnings_calendar table: {str(e)}")
            raise
        finally:
            cursor.close()

    def initialize_database(self):
        """データベースの初期化とテーブル存在確認"""
        if not self.conn:
            print("No connection to Snowflake. Aborting database initialization.")
            return

        try:
            # データベースとスキーマの存在確認は接続時に行われるため、ここではテーブルの存在確認と作成のみ
            self.create_companies_table()
            self.create_earnings_calendar_table()
            print("Snowflake database initialized successfully.")
            return True
        except Exception as e:
            print(f"Failed to initialize Snowflake database: {str(e)}")
            raise

    def upsert_earnings_calendar(self, earnings_data: List[Dict]):
        """決算予定の更新または挿入"""
        if not self.conn:
            print("No connection to Snowflake. Aborting upsert.")
            return

        cursor = self.conn.cursor()
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        table_id = f"{db_name}.{schema_name}.earnings_calendar"

        try:
            for data in earnings_data:
                merge_sql = f"""
                MERGE INTO {table_id} AS target
                USING (SELECT
                        %s AS ticker,
                        %s AS company_name,
                        %s AS announcement_date,
                        %s AS fiscal_year,
                        %s AS fiscal_quarter
                       ) AS source
                ON target.ticker = source.TICKER
                   AND target.fiscal_year = source.FISCAL_YEAR
                   AND target.fiscal_quarter = source.FISCAL_QUARTER
                WHEN MATCHED THEN
                    UPDATE SET
                        announcement_date = source.ANNOUNCEMENT_DATE,
                        updated_at = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                    INSERT (ticker, company_name, announcement_date, fiscal_year, fiscal_quarter, created_at, updated_at)
                    VALUES (source.TICKER, source.COMPANY_NAME, source.ANNOUNCEMENT_DATE, source.FISCAL_YEAR, source.FISCAL_QUARTER, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
                """
                
                ticker_value = data["ticker"].replace(".T", "")

                params = (
                    ticker_value,
                    data["company_name"],
                    data["announcement_date"],
                    data["fiscal_year"],
                    data["fiscal_quarter"]
                )
                
                cursor.execute(merge_sql, params)
                print(f"Successfully merged data for earnings: {ticker_value} - {data['fiscal_year']}Q{data['fiscal_quarter']}")
            
            self.conn.commit()
            print("Upsert operation committed.")

        except Exception as e:
            print(f"An error occurred during upsert_earnings_calendar: {e}")
            self.conn.rollback()
            raise
        finally:
            cursor.close()

# Example of how to use it
if __name__ == '__main__':
    snowflake_service = SnowflakeService()
    if snowflake_service.get_connection():
        # Do something with the connection
        cursor = snowflake_service.get_connection().cursor()
        try:
            cursor.execute("SELECT CURRENT_VERSION()")
            one_row = cursor.fetchone()
            print(f"Snowflake version: {one_row[0]}")
        finally:
            cursor.close()
        snowflake_service.close_connection()
