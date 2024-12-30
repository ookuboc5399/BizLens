import os
import time
from dotenv import load_dotenv
from google.cloud import bigquery
from datetime import datetime, date
from app.models.earnings_calendar import earnings_calendar_schema
from app.models.earnings_companies import earnings_companies_schema

# .envファイルを読み込む
load_dotenv()

def insert_sample_data(client, project_id, dataset):
    # 現在時刻をISO形式の文字列に変換
    current_time = datetime.now().isoformat()

    # earnings_companiesテーブルにサンプルデータを挿入
    companies_data = [
        {
            "code": "7203",
            "company_name": "トヨタ自動車",
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "code": "9984",
            "company_name": "ソフトバンクグループ",
            "created_at": current_time,
            "updated_at": current_time
        }
    ]

    # earnings_calendarテーブルにサンプルデータを挿入
    calendar_data = [
        {
            "code": "7203",
            "company_name": "トヨタ自動車",
            "fiscal_year": 2024,
            "fiscal_quarter": 3,
            "announcement_date": date(2024, 2, 15).isoformat(),  # dateオブジェクトも文字列に変換
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "code": "9984",
            "company_name": "ソフトバンクグループ",
            "fiscal_year": 2024,
            "fiscal_quarter": 3,
            "announcement_date": date(2024, 2, 8).isoformat(),   # dateオブジェクトも文字列に変換
            "created_at": current_time,
            "updated_at": current_time
        }
    ]

    # データの挿入
    try:
        table_ref = f"{project_id}.{dataset}.earnings_companies"
        errors = client.insert_rows_json(table_ref, companies_data)
        if errors == []:
            print("Successfully inserted rows into earnings_companies")
        else:
            print("Errors occurred while inserting into earnings_companies:", errors)

        table_ref = f"{project_id}.{dataset}.earnings_calendar"
        errors = client.insert_rows_json(table_ref, calendar_data)
        if errors == []:
            print("Successfully inserted rows into earnings_calendar")
        else:
            print("Errors occurred while inserting into earnings_calendar:", errors)

    except Exception as e:
        print(f"Error inserting data: {str(e)}")

def init_db():
    client = bigquery.Client()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset = "BuffetCodeClone"
    
    try:
        # データセットの存在確認、なければ作成
        dataset_ref = f"{project_id}.{dataset}"
        try:
            client.get_dataset(dataset_ref)
            print(f"Dataset {dataset_ref} already exists")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset)
            print(f"Created dataset {dataset_ref}")

        # 既存のテーブルを削除
        try:
            client.delete_table(f"{project_id}.{dataset}.earnings_calendar")
            print("Deleted existing earnings_calendar table")
        except Exception:
            print("earnings_calendar table does not exist")

        try:
            client.delete_table(f"{project_id}.{dataset}.earnings_companies")
            print("Deleted existing earnings_companies table")
        except Exception:
            print("earnings_companies table does not exist")

        # テーブルの作成（earnings_calendar）
        earnings_calendar_table = bigquery.Table(
            f"{project_id}.{dataset}.earnings_calendar",
            schema=earnings_calendar_schema
        )
        earnings_calendar_table = client.create_table(earnings_calendar_table)
        print(f"Created earnings_calendar table {earnings_calendar_table.table_id}")

        # テーブルの作成（earnings_companies）
        earnings_companies_table = bigquery.Table(
            f"{project_id}.{dataset}.earnings_companies",
            schema=earnings_companies_schema
        )
        earnings_companies_table = client.create_table(earnings_companies_table)
        print(f"Created earnings_companies table {earnings_companies_table.table_id}")

        # テーブルが利用可能になるまで少し待つ
        print("Waiting for tables to be ready...")
        time.sleep(5)  # 5秒待機

        # サンプルデータの挿入
        insert_sample_data(client, project_id, dataset)

        # データ確認のためのクエリ実行
        for table_name in ["earnings_calendar", "earnings_companies"]:
            query = f"""
            SELECT COUNT(*) as count
            FROM `{project_id}.{dataset}.{table_name}`
            """
            query_job = client.query(query)
            results = query_job.result()
            for row in results:
                print(f"Number of rows in {table_name}: {row.count}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    init_db() 