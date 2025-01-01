from google.cloud import bigquery
from google.oauth2 import service_account
import os
from typing import List, Optional, Dict
import datetime
from pathlib import Path
from dotenv import load_dotenv

class BigQueryService:
    def __init__(self):
        try:
            load_dotenv()
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            print(f"Initializing BigQueryService with credentials from: {credentials_path}")
            
            if not credentials_path:
                raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
            
            if not os.path.exists(credentials_path):
                raise Exception(f"Credentials file not found at: {credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            self.dataset = os.getenv('BIGQUERY_DATASET')
            self.table = os.getenv('BIGQUERY_TABLE')
            
            print(f"BigQuery configuration:")
            print(f"Project ID: {self.project_id}")
            print(f"Dataset: {self.dataset}")
            print(f"Table: {self.table}")
            
            self.client = bigquery.Client(credentials=credentials, project=self.project_id)
            print("BigQuery client initialized successfully")
            
        except Exception as e:
            print(f"Error initializing BigQueryService: {str(e)}")
            raise

    async def create_companies_table(self):
        """companiesテーブルの作成"""
        table_id = f"{self.project_id}.{self.dataset}.{self.table}"
        
        schema = [
            # 基本情報
            bigquery.SchemaField("company_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ticker", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("sector", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("industry", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("website", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("market_cap", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("employees", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("market", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("market_price", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("shares_outstanding", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("volume", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("per", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("pbr", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("eps", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("bps", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("roe", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("roa", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("revenue", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("operating_profit", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("net_profit", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("total_assets", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("equity", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("operating_margin", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("net_margin", "FLOAT", mode="NULLABLE")
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.clustering_fields = ["ticker"]
        self.client.create_table(table, exists_ok=True)

    async def create_earnings_calendar_table(self):
        """決算予定カレンダーテーブルの作成"""
        table_id = f"{self.project_id}.{self.dataset}.earnings_calendar"
        
        schema = [
            # 基本情報
            bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("company_name", "STRING", mode="REQUIRED"),
            # 決算情報
            bigquery.SchemaField("announcement_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("fiscal_year", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("fiscal_quarter", "INTEGER", mode="REQUIRED"),
            # メタデータ
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.clustering_fields = ["announcement_date", "code"]
        self.client.create_table(table, exists_ok=True)

    async def upsert_earnings_calendar(self, earnings_data: List[Dict]):
        """決算予定の更新または挿入"""
        try:
            table_id = f"{self.project_id}.{self.dataset}.earnings_calendar"
            
            for data in earnings_data:
                # 既存データの確認
                query = f"""
                SELECT code
                FROM `{table_id}`
                WHERE code = '{data["code"]}'
                AND fiscal_year = {data["fiscal_year"]}
                AND fiscal_quarter = {data["fiscal_quarter"]}
                """
                
                results = list(self.client.query(query).result())
                
                if results:
                    # UPDATE
                    update_query = f"""
                    UPDATE `{table_id}`
                    SET 
                        announcement_date = '{data["announcement_date"]}',
                        updated_at = CURRENT_TIMESTAMP()
                    WHERE code = '{data["code"]}'
                    AND fiscal_year = {data["fiscal_year"]}
                    AND fiscal_quarter = {data["fiscal_quarter"]}
                    """
                    self.client.query(update_query).result()
                else:
                    # INSERT
                    rows_to_insert = [{
                        "code": data["code"],
                        "company_name": data["company_name"],
                        "announcement_date": data["announcement_date"],
                        "fiscal_year": data["fiscal_year"],
                        "fiscal_quarter": data["fiscal_quarter"],
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat()
                    }]
                    
                    errors = self.client.insert_rows_json(table_id, rows_to_insert)
                    if errors:
                        raise Exception(f"Failed to insert rows: {errors}")
            
        except Exception as e:
            print(f"Error in upsert_earnings_calendar: {str(e)}")
            raise

    async def initialize_database(self):
        """データベースの初期化とテーブル存在確認"""
        try:
            # データセットの存在確認
            dataset_ref = self.client.dataset(self.dataset)
            try:
                dataset = self.client.get_dataset(dataset_ref)
                print(f"Dataset {self.dataset} exists in location {dataset.location}")
            except Exception as e:
                print(f"Dataset {self.dataset} does not exist: {str(e)}")
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "asia-northeast1"
                dataset = self.client.create_dataset(dataset)
                print(f"Created dataset {self.dataset}")

            # companiesテーブルの存在確認と作成
            companies_ref = dataset_ref.table(self.table)
            try:
                companies_table = self.client.get_table(companies_ref)
                print(f"Table {self.table} exists with {companies_table.num_rows} rows")
            except Exception as e:
                print(f"Table {self.table} does not exist: {str(e)}")
                # テーブルが存在しない場合は新規作成
                await self.create_companies_table()

            # earnings_calendarテーブルの存在確認と作成
            earnings_ref = dataset_ref.table('earnings_calendar')
            try:
                earnings_table = self.client.get_table(earnings_ref)
                print(f"Table earnings_calendar exists with {earnings_table.num_rows} rows")
            except Exception as e:
                print(f"Table earnings_calendar does not exist: {str(e)}")
                # テーブルが存在しない場合は新規作成
                await self.create_earnings_calendar_table()

            return True
        except Exception as e:
            print(f"Failed to initialize database: {str(e)}")
            raise

    def query(self, query_string: str) -> List[Dict]:
        """汎用クエリ実行メソッド"""
        try:
            results = self.client.query(query_string).result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise

    async def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict]:
        """指定期間の決算予定を取得"""
        print(f"Querying earnings calendar from {start_date} to {end_date}")
        query = f"""
        SELECT 
            e.code,
            e.company_name,
            e.announcement_date,
            e.fiscal_year,
            e.fiscal_quarter,
            c.sector,
            c.market_cap,
            c.market_price,
            c.per,
            c.roe
        FROM `{self.project_id}.{self.dataset}.earnings_calendar` e
        LEFT JOIN `{self.project_id}.{self.dataset}.{self.table}` c
        ON e.code = c.ticker
        WHERE e.announcement_date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY e.announcement_date
        """
        
        try:
            results = self.client.query(query).result()
            data = [dict(row) for row in results]
            print(f"Found {len(data)} earnings announcements")
            return data
        except Exception as e:
            print(f"Error querying BigQuery: {str(e)}")
            raise
