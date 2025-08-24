
import os
import json
import snowflake.connector
from dotenv import load_dotenv
from typing import List, Dict

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
            'description', 'market_cap', 'employees', 'market', 'market_price',
            'shares_outstanding', 'volume', 'per', 'pbr', 'eps', 'bps', 'roe',
            'roa', 'revenue', 'operating_profit', 'net_profit', 'total_assets',
            'equity', 'operating_margin', 'net_margin', 'tradingview_summary'
        ]
        
        merge_sql = f"""
        MERGE INTO companies AS target
        USING (SELECT %s AS ticker) AS source
        ON target.ticker = source.ticker
        WHEN NOT MATCHED THEN
            INSERT ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))});
        """

        try:
            for company in companies_data:
                # Ensure all columns are present in the dictionary, with None as default
                # Also, ensure the order of values matches the `columns` list.
                params = [company.get(col) for col in columns]
                # The ticker is used twice in the MERGE statement
                final_params = [company.get('ticker')] + params
                
                # Convert tradingview_summary dict to JSON string for VARIANT type
                summary_index = columns.index('tradingview_summary')
                if final_params[summary_index + 1] is not None:
                    final_params[summary_index + 1] = json.dumps(final_params[summary_index + 1])

                cursor.execute(merge_sql, tuple(final_params))
                print(f"Successfully merged data for ticker: {company.get('ticker')}")
            
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
