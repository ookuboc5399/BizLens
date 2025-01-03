"""
PDFファイルをGCSに格納するスクリプト
"""
import os
import json
import logging
import sys
import requests
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
from urllib.parse import urljoin, urlparse
import tempfile
from dotenv import load_dotenv

# プロジェクトルートをPYTHONPATHに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.append(project_root)

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

def download_pdf(url, temp_dir):
    """PDFファイルをダウンロード"""
    try:
        # URLが相対パスの場合、ベースURLを追加
        if url.startswith('/'):
            base_url = "https://www.release.tdnet.info"
            url = urljoin(base_url, url)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        # URLからファイル名を抽出
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(temp_dir, filename)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"Downloaded PDF: {filename}")
        return filepath, filename

    except Exception as e:
        logger.error(f"Error downloading PDF from {url}: {str(e)}")
        return None, None

def upload_to_gcs(bucket_name, source_file, destination_blob_name):
    """GCSにファイルをアップロード"""
    try:
        # 認証情報の設定
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
        
        if not os.path.exists(credentials_path):
            raise Exception(f"Credentials file not found at: {credentials_path}")
        
        # GCSクライアントの初期化
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        storage_client = storage.Client(credentials=credentials)
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file)
        logger.info(f"Uploaded {source_file} to gs://{bucket_name}/{destination_blob_name}")
        
        # 公開URLを生成
        blob.make_public()
        return blob.public_url

    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        return None

def organize_pdf_path(code, date_str, filename):
    """PDFの保存パスを生成"""
    # 日付文字列からYYYY/MMのパスを生成
    date_parts = date_str.split('/')
    year_month = f"{date_parts[0]}/{date_parts[1]}"
    
    # 企業コード/YYYY/MM/ファイル名 の形式でパスを生成
    return f"{code}/{year_month}/{filename}"

def process_financial_reports(records, bucket_name):
    """財務レポートの処理"""
    processed_records = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for record in records:
            try:
                if not record['pdf_links']:
                    continue

                pdf_url = record['pdf_links'][0]['url']
                
                # PDFをダウンロード
                local_path, filename = download_pdf(pdf_url, temp_dir)
                if not local_path:
                    continue

                # GCSのパスを生成
                gcs_path = organize_pdf_path(record['code'], record['date'], filename)
                
                # GCSにアップロード
                public_url = upload_to_gcs(bucket_name, local_path, gcs_path)
                if public_url:
                    record['gcs_url'] = public_url
                    processed_records.append(record)

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                logger.error(f"Record: {record}")
                continue

    return processed_records

def main():
    """メイン処理"""
    try:
        # 環境変数の読み込み
        load_dotenv()
        
        # バケット名の取得
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        if not bucket_name:
            raise Exception("GCS_BUCKET_NAME environment variable is not set")
        
        # JSONファイルのパス
        json_path = os.path.join(project_root, "data", "financial_reports.json")
        
        # データの読み込み
        records = load_json_data(json_path)
        
        # PDFファイルの処理とGCSへのアップロード
        processed_records = process_financial_reports(records, bucket_name)
        
        logger.info(f"Successfully processed {len(processed_records)} records")
        
        # 処理結果をJSONファイルに保存
        output_path = os.path.join(project_root, "data", "financial_reports_with_gcs.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_records, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved processed records to {output_path}")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
