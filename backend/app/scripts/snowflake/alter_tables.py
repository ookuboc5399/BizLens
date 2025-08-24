
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from app.services.snowflake_service import SnowflakeService

def add_tradingview_summary_column():
    """
    Adds the 'tradingview_summary' column to the 'companies' table.
    """
    snowflake_service = SnowflakeService()
    conn = snowflake_service.get_connection()

    if not conn:
        print("Could not connect to Snowflake. Aborting table alteration.")
        return

    try:
        cursor = conn.cursor()
        
        alter_table_sql = "ALTER TABLE companies ADD COLUMN IF NOT EXISTS tradingview_summary VARIANT;"
        
        print("Executing ALTER TABLE statement for 'companies'...")
        cursor.execute(alter_table_sql)
        print("'companies' table altered successfully. 'tradingview_summary' column added.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        snowflake_service.close_connection()

if __name__ == "__main__":
    add_tradingview_summary_column()
