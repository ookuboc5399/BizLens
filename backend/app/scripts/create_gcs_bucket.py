from google.cloud import storage
from google.oauth2 import service_account
import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

def create_gcs_bucket():
    # GCSクライアントの初期化
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    storage_client = storage.Client(credentials=credentials)
    
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("GCS_BUCKET_NAME environment variable is not set")
    
    try:
        # バケットが存在するか確認
        bucket = storage_client.bucket(bucket_name)
        if not bucket.exists():
            # バケットを作成
            bucket = storage_client.create_bucket(
                bucket_name,
                location="asia-northeast1"  # 東京リージョン
            )
            print(f"Bucket {bucket.name} created")
            
            # CORS設定を追加
            bucket.cors = [
                {
                    'origin': ['*'],  # 本番環境では適切なオリジンに制限することを推奨
                    'method': ['GET', 'HEAD'],
                    'responseHeader': ['Content-Type'],
                    'maxAgeSeconds': 3600
                }
            ]
            bucket.patch()
            
            print(f"Bucket {bucket.name} configured successfully")
        else:
            print(f"Bucket {bucket.name} already exists")
            
            # 既存のバケットのCORS設定を更新
            bucket.cors = [
                {
                    'origin': ['*'],
                    'method': ['GET', 'HEAD'],
                    'responseHeader': ['Content-Type'],
                    'maxAgeSeconds': 3600
                }
            ]
            bucket.patch()
            print(f"Updated CORS settings for bucket {bucket.name}")
            
    except Exception as e:
        print(f"Error creating/updating bucket: {str(e)}")

if __name__ == "__main__":
    create_gcs_bucket()
