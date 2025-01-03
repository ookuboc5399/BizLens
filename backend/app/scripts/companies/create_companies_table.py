from google.cloud import bigquery
from google.oauth2 import service_account
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

def create_companies_table():
    """BigQueryにcompaniesテーブルを作成"""
    
    # BigQuery クライアントの初期化
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    client = bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    
    # データセットとテーブルの参照を作成
    dataset_id = os.getenv('BIGQUERY_DATASET')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    table_id = f"{project_id}.{dataset_id}.companies"
    
    # スキーマの定義
    schema = [
        # 基本情報
        bigquery.SchemaField("ticker", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("market", "STRING"),
        bigquery.SchemaField("company_name", "STRING"),
        bigquery.SchemaField("industry", "STRING"),
        bigquery.SchemaField("business_description", "STRING"),
        bigquery.SchemaField("website", "STRING"),
        bigquery.SchemaField("data_source", "STRING"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
        
        # 株価情報
        bigquery.SchemaField("current_price", "FLOAT64"),
        bigquery.SchemaField("market_cap", "FLOAT64"),
        bigquery.SchemaField("per", "FLOAT64"),
        bigquery.SchemaField("pbr", "FLOAT64"),
        bigquery.SchemaField("eps", "FLOAT64"),
        bigquery.SchemaField("bps", "FLOAT64"),
        bigquery.SchemaField("roe", "FLOAT64"),
        bigquery.SchemaField("roa", "FLOAT64"),
        
        # 財務指標
        bigquery.SchemaField("current_assets", "FLOAT64"),
        bigquery.SchemaField("total_assets", "FLOAT64"),
        bigquery.SchemaField("current_liabilities", "FLOAT64"),
        bigquery.SchemaField("total_liabilities", "FLOAT64"),
        bigquery.SchemaField("capital", "FLOAT64"),
        bigquery.SchemaField("minority_interests", "FLOAT64"),
        bigquery.SchemaField("shareholders_equity", "FLOAT64"),
        bigquery.SchemaField("debt_ratio", "FLOAT64"),
        bigquery.SchemaField("current_ratio", "FLOAT64"),
        bigquery.SchemaField("equity_ratio", "FLOAT64"),
        
        # キャッシュフロー
        bigquery.SchemaField("operating_cash_flow", "FLOAT64"),
        bigquery.SchemaField("investing_cash_flow", "FLOAT64"),
        bigquery.SchemaField("financing_cash_flow", "FLOAT64"),
        bigquery.SchemaField("cash_and_equivalents", "FLOAT64"),
        
        # 収益性指標
        bigquery.SchemaField("revenue", "FLOAT64"),
        bigquery.SchemaField("operating_income", "FLOAT64"),
        bigquery.SchemaField("net_income", "FLOAT64"),
        bigquery.SchemaField("operating_margin", "FLOAT64"),
        bigquery.SchemaField("net_margin", "FLOAT64"),
        
        # 配当関連
        bigquery.SchemaField("dividend_yield", "FLOAT64"),
        bigquery.SchemaField("dividend_per_share", "FLOAT64"),
        bigquery.SchemaField("payout_ratio", "FLOAT64"),
        
        # その他
        bigquery.SchemaField("beta", "FLOAT64"),
        bigquery.SchemaField("shares_outstanding", "INTEGER"),
        bigquery.SchemaField("market_type", "STRING"),
        bigquery.SchemaField("sector", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("currency", "STRING"),
        bigquery.SchemaField("collected_at", "TIMESTAMP"),
    ]
    
    # テーブル設定
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="collected_at"
    )
    
    try:
        # 既存のテーブルが存在するか確認
        try:
            existing_table = client.get_table(table_id)
            logger.info(f"Found existing table: {table_id}")
            
            # 既存のデータをバックアップ
            backup_table_id = f"{table_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            query = f"""
            CREATE OR REPLACE TABLE `{backup_table_id}`
            AS SELECT * FROM `{table_id}`
            """
            query_job = client.query(query)
            query_job.result()
            logger.info(f"Created backup table: {backup_table_id}")
            
            # 既存のテーブルを削除
            client.delete_table(table_id)
            logger.info(f"Deleted existing table: {table_id}")
            
        except Exception as e:
            logger.info(f"Table does not exist: {table_id}")
        
        # 新しいテーブルを作成
        table = client.create_table(table)
        logger.info(f"Created new table {table_id}")
        
        # バックアップからデータを復元
        try:
            # バックアップテーブルのデータを確認
            query = f"""
            SELECT COUNT(*) as count
            FROM `{backup_table_id}`
            """
            query_job = client.query(query)
            results = query_job.result()
            row = next(results)
            backup_count = row.count
            
            if backup_count > 0:
                # データが存在する場合は復元
                query = f"""
                INSERT INTO `{table_id}`
                SELECT * FROM `{backup_table_id}`
                """
                query_job = client.query(query)
                query_job.result()
                logger.info(f"Restored {backup_count} rows from backup")
            else:
                logger.warning("Backup table exists but contains no data")
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error creating/updating table: {str(e)}")
        raise

if __name__ == "__main__":
    create_companies_table()
