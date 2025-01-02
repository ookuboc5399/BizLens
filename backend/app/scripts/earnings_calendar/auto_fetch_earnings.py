import asyncio
import os
from datetime import datetime, timedelta
from backend.app.scripts.earnings_calendar.fetch_earnings_data import fetch_earnings_data, save_to_bigquery
import aiohttp
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('earnings_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def auto_fetch():
    """翌々月の決算予定データを自動取得"""
    try:
        # 現在の日付から翌々月を計算
        today = datetime.now()
        target_month = today.replace(day=1) + timedelta(days=32)  # 翌月
        target_month = target_month.replace(day=1) + timedelta(days=32)  # 翌々月
        target_month = target_month.replace(day=1)  # 月初に設定
        
        year = target_month.year
        month = target_month.month
        
        logger.info(f"Starting auto fetch for {year}/{month}")
        
        async with aiohttp.ClientSession() as session:
            earnings_data = await fetch_earnings_data(session, year, month)
            if earnings_data:
                await save_to_bigquery(earnings_data)
                logger.info(f"Successfully fetched and saved {len(earnings_data)} records for {year}/{month}")
            else:
                logger.warning(f"No data found for {year}/{month}")
    
    except Exception as e:
        logger.error(f"Error in auto fetch: {str(e)}", exc_info=True)
        raise

def main():
    """メイン実行関数"""
    try:
        asyncio.run(auto_fetch())
    except Exception as e:
        logger.error(f"Failed to execute auto fetch: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
