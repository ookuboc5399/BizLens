from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv

def test_bigquery_connection():
    # 環境変数の読み込み
    load_dotenv()
    
    try:
        # 認証情報の取得
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        client = bigquery.Client(credentials=credentials)

        # テストクエリ
        query = """
        SELECT *
        FROM `BuffetCodeClone.companies`
        LIMIT 5
        """

        query_job = client.query(query)
        results = query_job.result()
        
        print("BigQuery接続テスト結果:")
        print("-" * 50)
        for row in results:
            print(row)
        print("-" * 50)
        print("BigQuery接続成功！")
        
    except Exception as e:
        print(f"エラー: {str(e)}")

if __name__ == "__main__":
    test_bigquery_connection()