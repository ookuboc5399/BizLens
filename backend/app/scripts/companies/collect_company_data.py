import asyncio
import logging
from backend.app.services.companies.data_collector import DataCollector
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# BigQuery設定
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)
client = bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))

# 主要100社のティッカーリスト
COMPANIES = [
    # 日経225の主要企業
    '7203',  # トヨタ自動車
    '9432',  # NTT
    '9984',  # ソフトバンクグループ
    '6758',  # ソニーグループ
    '8306',  # 三菱UFJフィナンシャル・グループ
    '9433',  # KDDI
    '6861',  # キーエンス
    '6367',  # ダイキン工業
    '4502',  # 武田薬品工業
    '7974',  # 任天堂
    '6954',  # ファナック
    '6981',  # 村田製作所
    '8316',  # 三井住友フィナンシャルグループ
    '4063',  # 信越化学工業
    '9983',  # ファーストリテイリング
    '7267',  # ホンダ
    '8035',  # 東京エレクトロン
    '6501',  # 日立製作所
    '8766',  # 東京海上ホールディングス
    '7751',  # キヤノン
    '3382',  # セブン＆アイ・ホールディングス
    '9434',  # ソフトバンク
    '4755',  # 楽天グループ
    '2914',  # JT
    '6902',  # デンソー
    '7011',  # 三菱重工業
    '8031',  # 三井物産
    '8058',  # 三菱商事
    '6503',  # 三菱電機
    '6702',  # 富士通
]

async def save_to_bigquery(data_list):
    """データをBigQueryに保存"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = os.getenv('BIGQUERY_DATASET')
        table_id = f"{project_id}.{dataset_id}.companies"
        logger.info(f"Saving data to BigQuery table: {table_id}")
        
        # データを整形
        rows_to_insert = []
        for data in data_list:
            try:
                row = {
                    "ticker": data["ticker"],
                    "company_name": data["company_name"],
                    "sector": data["sector"],
                    "industry": data["industry"],
                    "country": data["country"],
                    "website": data["website"],
                    "description": data["description"],
                    "market": data["market"],
                    "market_price": float(data["market_price"]),
                    "market_cap": float(data["market_cap"]),
                    "shares_outstanding": int(data["shares_outstanding"]),
                    "volume": int(data["volume"]),
                    "per": float(data["per"]),
                    "pbr": float(data["pbr"]),
                    "eps": float(data["eps"]),
                    "bps": float(data["bps"]),
                    "roe": float(data["roe"]),
                    "roa": float(data["roa"]),
                    "revenue": float(data["revenue"]),
                    "operating_profit": float(data["operating_profit"]),
                    "net_profit": float(data["net_profit"]),
                    "total_assets": float(data["total_assets"]),
                    "equity": float(data["equity"]),
                    "operating_margin": float(data["operating_margin"]),
                    "net_margin": float(data["net_margin"]),
                    "dividend_yield": float(data["dividend_yield"]),
                    "dividend_per_share": float(data["dividend_per_share"]),
                    "payout_ratio": float(data["payout_ratio"]),
                    "employees": int(data.get("employees", 0)),
                    "collected_at": datetime.now(timezone.utc).isoformat()
                }
                rows_to_insert.append(row)
                logger.info(f"Prepared row for {data['ticker']}: {row}")
            except Exception as e:
                logger.error(f"Error preparing row for {data.get('ticker', 'unknown')}: {str(e)}")
                continue
        
        if not rows_to_insert:
            logger.warning("No valid rows to insert")
            return
        
        # BigQueryに保存
        logger.info(f"Attempting to insert {len(rows_to_insert)} rows")
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logger.error(f"Failed to insert rows: {errors}")
            for error in errors:
                logger.error(f"Error details: {error}")
        else:
            logger.info(f"Successfully inserted {len(rows_to_insert)} rows")
            
    except Exception as e:
        logger.error(f"Error in save_to_bigquery: {str(e)}")
        raise

async def main():
    collector = DataCollector()
    try:
        all_data = []
        for ticker in COMPANIES:
            try:
                logger.info(f"Collecting data for {ticker}")
                data = await collector.collect_all_data(ticker)
                all_data.append(data)
                logger.info(f"Successfully collected data for {ticker}")
                
                # 一定間隔で保存
                if len(all_data) >= 5:
                    await save_to_bigquery(all_data)
                    all_data = []
                
                # API制限を考慮して待機
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting data for {ticker}: {str(e)}")
                continue
        
        # 残りのデータを保存
        if all_data:
            await save_to_bigquery(all_data)
            
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
