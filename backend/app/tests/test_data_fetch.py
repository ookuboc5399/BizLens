from app.tasks.fetch_earnings import fetch_earnings_for_specific_month
import asyncio

async def test_fetch():
    print("Starting data fetch test...")
    
    # 2024年11月と12月のデータを取得
    await fetch_earnings_for_specific_month(2024, 11)
    await fetch_earnings_for_specific_month(2024, 12)
    
    print("Data fetch test completed")

if __name__ == "__main__":
    asyncio.run(test_fetch()) 