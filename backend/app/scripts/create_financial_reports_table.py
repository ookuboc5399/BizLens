import os
import sys
from google.cloud import bigquery

# backendディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.bigquery_service import BigQueryService

def create_financial_reports_table():
    """financial_reportsテーブルを作成"""
    bigquery_service = BigQueryService()
    client = bigquery_service.client
    
    # テーブルのスキーマを定義
    schema = [
        bigquery.SchemaField("company_id", "STRING", mode="REQUIRED", description="証券コード"),
        bigquery.SchemaField("company_name", "STRING", mode="REQUIRED", description="会社名"),
        bigquery.SchemaField("fiscal_year", "STRING", mode="REQUIRED", description="会計年度"),
        bigquery.SchemaField("quarter", "STRING", mode="REQUIRED", description="四半期（1-4）"),
        bigquery.SchemaField("report_type", "STRING", mode="REQUIRED", description="レポートの種類"),
        bigquery.SchemaField("file_url", "STRING", mode="REQUIRED", description="PDFファイルのURL"),
        bigquery.SchemaField("source", "STRING", mode="REQUIRED", description="データソース（TDnet/EDINET/企業ウェブサイト）"),
        bigquery.SchemaField("report_date", "TIMESTAMP", mode="REQUIRED", description="レポートの日付"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="レコード作成日時"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", description="レコード更新日時")
    ]
    
    # テーブル参照を作成
    dataset_ref = client.dataset(bigquery_service.dataset)
    table_ref = dataset_ref.table("financial_reports")
    table = bigquery.Table(table_ref, schema=schema)
    
    try:
        # 既存のテーブルを削除
        client.delete_table(table_ref, not_found_ok=True)
        print("Deleted existing table")
        
        # 新しいテーブルを作成
        client.create_table(table)
        print("Created financial_reports table")
        
    except Exception as e:
        print(f"Error creating table: {str(e)}")
        raise

if __name__ == "__main__":
    create_financial_reports_table()
