from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from .data_collector import DataCollector
from .bigquery_service import BigQueryService

class DataUpdateScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collector = DataCollector()
        self.bigquery = BigQueryService()

    async def update_daily_data(self):
        # 毎日の株価データ更新
        companies = await self.bigquery.get_all_companies()
        for company in companies:
            data = await self.collector.collect_stock_data(company['ticker'])
            await self.bigquery.update_stock_data(company['ticker'], data)

    async def update_quarterly_data(self):
        # 四半期財務データ更新
        companies = await self.bigquery.get_all_companies()
        for company in companies:
            data = await self.collector.collect_financial_data(company['ticker'])
            await self.bigquery.update_financial_data(company['ticker'], data)

    def start(self):
        # 毎日の株価データ更新（日本時間15:30）
        self.scheduler.add_job(
            self.update_daily_data,
            'cron',
            hour=15,
            minute=30,
            timezone='Asia/Tokyo'
        )
        
        # 四半期財務データ更新（毎週月曜日）
        self.scheduler.add_job(
            self.update_quarterly_data,
            'cron',
            day_of_week='mon'
        )
        
        self.scheduler.start() 