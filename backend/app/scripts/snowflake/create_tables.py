
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def create_companies_table():
    """
    Creates the 'companies' table in Snowflake if it doesn't exist.
    """
    snowflake_service = SnowflakeService()
    conn = snowflake_service.get_connection()

    if not conn:
        print("Could not connect to Snowflake. Aborting table creation.")
        return

    try:
        cursor = conn.cursor()
        
        # It's good practice to specify the database and schema
        db = snowflake_service.conn.database
        schema = snowflake_service.conn.schema
        print(f"Using database '{db}' and schema '{schema}'")
        cursor.execute(f"USE DATABASE {db}")
        cursor.execute(f"USE SCHEMA {schema}")

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS companies (
            company_name VARCHAR,
            ticker VARCHAR,
            sector VARCHAR,
            industry VARCHAR,
            country VARCHAR,
            website VARCHAR,
            description VARCHAR,
            market_cap NUMBER,
            employees NUMBER,
            market VARCHAR,
            market_price FLOAT,
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
            -- Add a primary key, for example, on ticker
            PRIMARY KEY (ticker)
        );
        """
        
        print("Executing CREATE TABLE statement for 'companies'...")
        cursor.execute(create_table_sql)
        print("'companies' table created successfully (if it did not exist).")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    create_companies_table()
