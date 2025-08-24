
import asyncio
import sys
import json
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from app.services.company_service import CompanyService

async def test_collection():
    """
    Tests the collect_all_data method for a specific ticker.
    """
    service = CompanyService()
    # Toyota Motor Corporation ticker on Yahoo Finance
    ticker = "7203.T" 
    print(f"--- Testing data collection for {ticker} ---")
    data = await service.collect_all_data(ticker)
    print("--- Collected Data ---")
    # Use json.dumps for pretty printing the dictionary
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("----------------------")
    # Close the snowflake connection if it was opened
    if service.snowflake:
        service.snowflake.close_connection()

if __name__ == "__main__":
    asyncio.run(test_collection())
