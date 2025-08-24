from google.cloud import bigquery
from google.oauth2 import service_account
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import glob
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

def convert_us_stock_data(data: dict) -> dict:
    """米国株のデータを変換"""
    try:
        stats = data.get("data", {})
        valuation = stats.get("Valuation Measures", {})
        income = stats.get("Income Statement", {})
        balance = stats.get("Balance Sheet", {})
        management = stats.get("Management Effectiveness", {})
        cash_flow = stats.get("Cash Flow Statement", {})
        profitability = stats.get("Profitability", {})
        dividends = stats.get("Dividends & Splits", {})
        stock_history = stats.get("Stock Price History", {})
        share_stats = stats.get("Share Statistics", {})

        return {
            "ticker": data.get("ticker"),
            "market": "US",
            "company_name": "",
            "industry": "",
            "business_description": "",
            "website": "",
            "data_source": "yahoo_finance",
            "last_updated": data.get("fetched_at"),
            "current_price": None,
            "market_cap": safe_float(valuation.get("Market Cap")),
            "per": safe_float(valuation.get("Trailing P/E")),
            "pbr": safe_float(valuation.get("Price/Book")),
            "eps": safe_float(income.get("Diluted EPS (ttm)")),
            "bps": safe_float(balance.get("Book Value Per Share (mrq)")),
            "roe": safe_float(management.get("Return on Equity (ttm)")),
            "roa": safe_float(management.get("Return on Assets (ttm)")),
            "current_assets": None,
            "total_assets": None,
            "current_liabilities": None,
            "total_liabilities": None,
            "capital": None,
            "minority_interests": None,
            "shareholders_equity": None,
            "debt_ratio": safe_float(balance.get("Total Debt/Equity (mrq)")),
            "current_ratio": safe_float(balance.get("Current Ratio (mrq)")),
            "equity_ratio": None,
            "operating_cash_flow": safe_float(cash_flow.get("Operating Cash Flow (ttm)")),
            "investing_cash_flow": None,
            "financing_cash_flow": None,
            "cash_and_equivalents": safe_float(balance.get("Total Cash (mrq)")),
            "revenue": safe_float(income.get("Revenue (ttm)")),
            "operating_income": safe_float(income.get("EBITDA")),
            "net_income": safe_float(income.get("Net Income Avi to Common (ttm)")),
            "operating_margin": safe_float(profitability.get("Operating Margin (ttm)")),
            "net_margin": safe_float(profitability.get("Profit Margin")),
            "dividend_yield": safe_float(dividends.get("Forward Annual Dividend Yield 4")),
            "dividend_per_share": safe_float(dividends.get("Forward Annual Dividend Rate 4")),
            "payout_ratio": safe_float(dividends.get("Payout Ratio 4")),
            "beta": safe_float(stock_history.get("Beta (5Y Monthly)")),
            "shares_outstanding": int(safe_float(share_stats.get("Shares Outstanding 5")) or 0),
            "market_type": "US",
            "sector": "",
            "country": "US",
            "currency": "USD",
            "collected_at": data.get("fetched_at")
        }
    except Exception as e:
        logger.error(f"Error converting US stock data for {data.get('ticker')}: {str(e)}")
        return None

def safe_float(value: Any) -> Optional[float]:
    """安全に浮動小数点数に変換"""
    if value is None or value == "" or value == "—" or value == "N/A" or value == "-":
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        # 通貨記号や単位を削除
        value_str = str(value)
        value_str = value_str.replace("$", "").replace("¥", "").replace("円", "")
        value_str = value_str.replace(",", "").replace(" ", "")
        # 百万/億単位の変換
        if "M" in value_str:
            value_str = value_str.replace("M", "")
            return float(value_str) * 1_000_000
        if "B" in value_str:
            value_str = value_str.replace("B", "")
            return float(value_str) * 1_000_000_000
        if "T" in value_str:
            value_str = value_str.replace("T", "")
            return float(value_str) * 1_000_000_000_000
        if "百万" in value_str:
            value_str = value_str.replace("百万", "")
            return float(value_str) * 1_000_000
        if "億" in value_str:
            value_str = value_str.replace("億", "")
            return float(value_str) * 100_000_000
        return float(value_str)
    except (ValueError, TypeError) as e:
        logger.debug(f"Failed to convert value '{value}' to float: {str(e)}")
        return None

def convert_china_stock_data(data: dict) -> dict:
    """中国株のデータを変換"""
    try:
        indicators = data.get("financial_info", {}).get("data", {}).get("indicators", {})
        company_info = data.get("company_info", {}).get("data", {})
        stock_price = data.get("stock_price", {}).get("data", {})
        price_history = stock_price.get("price_history", [{}])[0] if stock_price.get("price_history") else {}
        
        return {
            "ticker": data.get("ticker"),
            "market": company_info.get("market_info", {}).get("market"),
            "company_name": company_info.get("basic_info", {}).get("正式社名"),
            "industry": company_info.get("market_info", {}).get("industry"),
            "business_description": company_info.get("business_description"),
            "website": company_info.get("basic_info", {}).get("URL"),
            "data_source": "nikkei",
            "last_updated": data.get("fetched_at"),
            "current_price": safe_float(stock_price.get("current_price", {}).get("取引値")),
            "market_cap": safe_float(price_history.get("basic_info", {}).get("時価総額")),
            "per": safe_float(price_history.get("market_info", {}).get("per")),
            "pbr": None,
            "eps": None,
            "bps": safe_float(indicators.get("BPS")),
            "roe": safe_float(indicators.get("ROE")),
            "roa": safe_float(indicators.get("ROA")),
            "current_assets": safe_float(indicators.get("流動資産")),
            "total_assets": safe_float(indicators.get("総資産")),
            "current_liabilities": safe_float(indicators.get("流動負債")),
            "total_liabilities": safe_float(indicators.get("総負債")),
            "capital": safe_float(indicators.get("資本金")),
            "minority_interests": safe_float(indicators.get("少数株主権益")),
            "shareholders_equity": safe_float(indicators.get("株主資本")),
            "debt_ratio": safe_float(indicators.get("負債比率")),
            "current_ratio": safe_float(indicators.get("流動比率")),
            "equity_ratio": safe_float(indicators.get("株主資本比率")),
            "operating_cash_flow": safe_float(indicators.get("営業活動キャッシュフロー")),
            "investing_cash_flow": safe_float(indicators.get("投資活動キャッシュフロー")),
            "financing_cash_flow": safe_float(indicators.get("財務活動キャッシュフロー")),
            "cash_and_equivalents": safe_float(indicators.get("現金および現金同等物")),
            "revenue": safe_float(indicators.get("売上高")),
            "operating_income": safe_float(indicators.get("営業利益")),
            "net_income": safe_float(indicators.get("当期純利益")),
            "operating_margin": safe_float(indicators.get("営業利益率")),
            "net_margin": safe_float(indicators.get("純利益率")),
            "dividend_yield": safe_float(indicators.get("配当利回り")),
            "dividend_per_share": safe_float(indicators.get("1株配当金")),
            "payout_ratio": safe_float(indicators.get("配当性向")),
            "beta": None,
            "shares_outstanding": int(safe_float(indicators.get("発行済株式数")) or 0),
            "market_type": "China",
            "sector": company_info.get("market_info", {}).get("sector"),
            "country": "China",
            "currency": "CNY",
            "collected_at": data.get("fetched_at")
        }
    except Exception as e:
        logger.error(f"Error converting China stock data for {data.get('ticker')}: {str(e)}")
        return None

def create_companies_table():
    """BigQueryにcompaniesテーブルを作成してデータを挿入"""
    
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
            
            # バックアップデータの行数を確認
            count_query = f"""
            SELECT COUNT(*) as count
            FROM `{backup_table_id}`
            """
            query_job = client.query(count_query)
            results = query_job.result()
            row = next(results)
            backup_count = row.count
            logger.info(f"Backup table contains {backup_count} rows")

            # 既存のテーブルを削除
            client.delete_table(table_id)
            logger.info(f"Deleted existing table: {table_id}")
            
            # 新しいテーブルを作成
            table = bigquery.Table(table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="collected_at"
            )
            table = client.create_table(table)
            logger.info(f"Created new table {table_id}")

            # バックアップからデータを復元
            if backup_count > 0:
                restore_query = f"""
                INSERT INTO `{table_id}`
                SELECT * FROM `{backup_table_id}`
                """
                query_job = client.query(restore_query)
                query_job.result()
                logger.info(f"Restored {backup_count} rows from backup")
            
        except Exception as e:
            logger.info(f"Table does not exist or error occurred: {str(e)}")
            # 新しいテーブルを作成
            table = bigquery.Table(table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="collected_at"
            )
            table = client.create_table(table)
            logger.info(f"Created new table {table_id}")
        
        # データの収集と変換
        companies_data = []
        
        # プロジェクトルートからの相対パスを設定
        root_dir = Path(__file__).parent.parent.parent.parent
        
        # US株のデータを収集
        us_stocks_dir = root_dir / "data" / "stocks" / "us"
        if us_stocks_dir.exists():
            for file_path in us_stocks_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        converted_data = convert_us_stock_data(data)
                        if converted_data:
                            companies_data.append(converted_data)
                            logger.info(f"Converted US stock data for {data['ticker']}")
                except Exception as e:
                    logger.error(f"Error processing US stock file {file_path}: {str(e)}")
        
        # 中国株のデータを収集
        china_stocks_dir = root_dir / "data" / "stocks" / "china"
        if china_stocks_dir.exists():
            for file_path in china_stocks_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        converted_data = convert_china_stock_data(data)
                        if converted_data:
                            companies_data.append(converted_data)
                            logger.info(f"Converted China stock data for {data['ticker']}")
                except Exception as e:
                    logger.error(f"Error processing China stock file {file_path}: {str(e)}")
        
        # データの挿入（バッチ処理）
        if companies_data:
            batch_size = 1000  # 一度に挿入する行数
            total_rows = len(companies_data)
            successful_inserts = 0
            failed_rows = []

            for i in range(0, total_rows, batch_size):
                batch = companies_data[i:i + batch_size]
                try:
                    errors = client.insert_rows_json(table, batch)
                    if errors:
                        logger.error(f"Errors occurred while inserting batch {i//batch_size + 1}:")
                        for error in errors:
                            error_index = error.get('index', 0) + i
                            error_row = batch[error.get('index', 0)]
                            logger.error(f"Row {error_index} (ticker: {error_row.get('ticker')}): {error.get('errors')}")
                            failed_rows.append({
                                'index': error_index,
                                'ticker': error_row.get('ticker'),
                                'errors': error.get('errors')
                            })
                    else:
                        successful_inserts += len(batch)
                        logger.info(f"Successfully inserted batch {i//batch_size + 1} ({len(batch)} rows)")
                except Exception as e:
                    logger.error(f"Error inserting batch {i//batch_size + 1}: {str(e)}")
                    failed_rows.extend([{
                        'index': j + i,
                        'ticker': row.get('ticker'),
                        'errors': [{'message': str(e)}]
                    } for j, row in enumerate(batch)])

            logger.info(f"Insertion complete: {successful_inserts}/{total_rows} rows inserted successfully")
            
            if failed_rows:
                logger.warning(f"Failed to insert {len(failed_rows)} rows")
                # エラー詳細をファイルに保存
                error_file = root_dir / "logs" / f"insert_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                error_file.parent.mkdir(parents=True, exist_ok=True)
                with open(error_file, 'w') as f:
                    json.dump(failed_rows, f, indent=2)
                logger.info(f"Error details saved to {error_file}")
        else:
            logger.warning("No data to insert")

        # 最終確認
        try:
            final_count_query = f"""
            SELECT COUNT(*) as count
            FROM `{table_id}`
            """
            query_job = client.query(final_count_query)
            results = query_job.result()
            row = next(results)
            final_count = row.count
            logger.info(f"Final table contains {final_count} rows")
        except Exception as e:
            logger.error(f"Error checking final row count: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error creating/updating table: {str(e)}")
        raise

if __name__ == "__main__":
    create_companies_table()
