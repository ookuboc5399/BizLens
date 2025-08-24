"""
JSONファイルからBigQueryにデータを格納するスクリプト
"""
import os
import json
import logging
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.append(project_root)

from app.services.bigquery_service import BigQueryService
from google.cloud import bigquery
from datetime import datetime

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_data(file_path):
    """JSONファイルからデータを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} records from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        raise

def get_bigquery_schema():
    """BigQueryのテーブルスキーマを定義"""
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("time", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pdf_url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("pdf_text", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("exchange", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED")
    ]

def transform_data(records):
    """データをBigQuery形式に変換"""
    transformed = []
    for record in records:
        try:
            # 日付文字列をDATE型に変換
            date_str = record['date'].replace('/', '-')
            
            # PDFリンク情報を取得
            pdf_url = None
            pdf_text = None
            if record['pdf_links'] and len(record['pdf_links']) > 0:
                pdf_url = record['pdf_links'][0]['url']
                pdf_text = record['pdf_links'][0]['text']
            
            row = {
                'date': date_str,
                'time': record['time'],
                'code': record['code'],
                'company': record['company'],
                'title': record['title'],
                'pdf_url': pdf_url,
                'pdf_text': pdf_text,
                'exchange': record['exchange'],
                'created_at': record['created_at'],
                'updated_at': record['updated_at']
            }
            transformed.append(row)
        except Exception as e:
            logger.error(f"Error transforming record: {str(e)}")
            logger.error(f"Record: {record}")
            continue
    
    logger.info(f"Transformed {len(transformed)} records")
    return transformed

def upload_to_bigquery(records):
    """BigQueryにデータをアップロード"""
    try:
        bq_service = BigQueryService()
        dataset_id = f"{bq_service.project_id}.{bq_service.dataset}"
        table_id = f"{dataset_id}.financial_reports"

        # データセットの存在確認と作成
        try:
            bq_service.client.get_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} already exists.")
        except Exception as e:
            if "Not found" in str(e):
                logger.info(f"Dataset {dataset_id} not found. Creating it...")
                dataset = bigquery.Dataset(dataset_id)
                dataset.location = "asia-northeast1"
                bq_service.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"Dataset {dataset_id} created.")
            else:
                logger.error(f"Error checking for dataset {dataset_id}: {str(e)}")
                raise

        # テーブルが存在する場合は削除
        try:
            bq_service.client.delete_table(table_id, not_found_ok=True)
            logger.info(f"Checked for existing table {table_id} and ensured it is removed if it existed.")
        except Exception as e:
            logger.warning(f"Could not delete table {table_id}, proceeding. Error: {str(e)}")

        # テーブルを新規作成
        schema = get_bigquery_schema()
        table = bigquery.Table(table_id, schema=schema)
        
        # クラスタリングの設定
        table.clustering_fields = ["date", "code"]
        
        # パーティショニングの設定（日付フィールドでパーティション）
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date"
        )
        
        table = bq_service.client.create_table(table)
        logger.info(f"Created new table {table_id}")
        
        # データの挿入
        errors = bq_service.client.insert_rows_json(table_id, records)
        if errors:
            logger.error("Errors occurred while inserting rows:")
            for error in errors:
                logger.error(error)
            raise Exception("Failed to insert rows")
        
        logger.info(f"Successfully uploaded {len(records)} records to {table_id}")
        
    except Exception as e:
        logger.error(f"Error uploading to BigQuery: {str(e)}")
        raise

def main():
    """メイン処理"""
    try:
        # プロジェクトルートからの相対パスを計算
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        json_path = os.path.join(project_root, "data", "financial_reports.json")
        
        # データの読み込み
        records = load_json_data(json_path)
        
        # データの変換
        transformed_records = transform_data(records)
        
        # BigQueryへのアップロード
        upload_to_bigquery(transformed_records)
        
        logger.info("Data upload completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
