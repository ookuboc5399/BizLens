"""
companiesテーブルのバックアップを作成するスクリプト
"""
from datetime import datetime
from google.cloud import bigquery
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_companies_table():
    """companiesテーブルのバックアップを作成"""
    
    # BigQueryクライアントの初期化
    from app.services.bigquery_service import BigQueryService
    bq_service = BigQueryService()
    client = bq_service.client
    project_id = bq_service.project_id
    dataset_id = bq_service.dataset
    
    # テーブルIDの設定
    source_table_id = f"{project_id}.{dataset_id}.companies"
    backup_table_id = f"{project_id}.{dataset_id}.companies_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # バックアップテーブルの作成
        query = f"""
        CREATE OR REPLACE TABLE `{backup_table_id}`
        AS SELECT *
        FROM `{source_table_id}`
        """
        
        # クエリの実行
        query_job = client.query(query)
        query_job.result()  # クエリの完了を待機
        
        # バックアップテーブルの行数を確認
        backup_table = client.get_table(backup_table_id)
        rows = client.get_table(backup_table_id).num_rows
        
        logger.info(f"Successfully created backup table: {backup_table_id}")
        logger.info(f"Backed up {rows} rows")
        
        return {
            "backup_table_id": backup_table_id,
            "rows_backed_up": rows,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise

def main():
    """メイン処理"""
    try:
        result = backup_companies_table()
        print(f"Backup completed successfully:")
        print(f"- Backup table: {result['backup_table_id']}")
        print(f"- Rows backed up: {result['rows_backed_up']}")
        print(f"- Created at: {result['created_at']}")
        
    except Exception as e:
        print(f"Error in backup process: {str(e)}")

if __name__ == "__main__":
    main()
