from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

def update_earnings_calendar_table():
    """earnings_calendarテーブルのスキーマを更新"""
    
    # BigQuery クライアントの初期化
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    client = bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    
    # データセットとテーブルの参照を作成
    dataset_id = os.getenv('BIGQUERY_DATASET')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    table_id = f"{project_id}.{dataset_id}.earnings_calendar"
    
    # スキーマの定義
    schema = [
        bigquery.SchemaField("ticker", "STRING", mode="REQUIRED"),  # codeをtickerに変更
        bigquery.SchemaField("company_name", "STRING"),
        bigquery.SchemaField("announcement_date", "DATE"),
        bigquery.SchemaField("fiscal_year", "INTEGER"),
        bigquery.SchemaField("fiscal_quarter", "INTEGER"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("updated_at", "TIMESTAMP")
    ]
    
    try:
        # 既存のデータをバックアップ
        backup_query = f"""
        CREATE OR REPLACE TABLE `{project_id}.{dataset_id}.earnings_calendar_backup` AS
        SELECT * FROM `{table_id}`
        """
        logger.info("Creating backup table...")
        backup_job = client.query(backup_query)
        backup_job.result()
        
        # 既存のテーブルを削除
        logger.info("Dropping existing table...")
        client.delete_table(table_id, not_found_ok=True)
        
        # 新しいテーブルを作成
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        logger.info(f"Created table {table_id} with new schema")
        
        # データを移行
        migration_query = f"""
        INSERT INTO `{table_id}` (
            ticker,
            company_name,
            announcement_date,
            fiscal_year,
            fiscal_quarter,
            created_at,
            updated_at
        )
        SELECT
            code as ticker,  # codeからtickerへの変換
            company_name,
            announcement_date,
            fiscal_year,
            fiscal_quarter,
            created_at,
            updated_at
        FROM `{project_id}.{dataset_id}.earnings_calendar_backup`
        """
        logger.info("Migrating data to new table...")
        migration_job = client.query(migration_query)
        migration_job.result()
        
        logger.info("Schema update completed successfully")
        
    except Exception as e:
        logger.error(f"Error updating schema: {str(e)}")
        raise

if __name__ == "__main__":
    update_earnings_calendar_table()
