from datetime import datetime
import yfinance as yf
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv

class FinancialDataCollector:
    def __init__(self):
        load_dotenv()
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        self.bq_client = bigquery.Client(credentials=credentials)
    
    def collect_yahoo_finance_data(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            return {
                "symbol": symbol,
                "company_name": stock.info.get("longName"),
                "sector": stock.info.get("sector"),
                "industry": stock.info.get("industry"),
                "market_cap": stock.info.get("marketCap"),
                "price_data": stock.history(period="1y").to_dict('records'),
                "dividends": stock.dividends.to_dict() if not stock.dividends.empty else {},
                "splits": stock.splits.to_dict() if not stock.splits.empty else {},
                "source": "yahoo_finance",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def save_to_bigquery(self, data, table_id):
        try:
            table = self.bq_client.get_table(f'BuffetCodeClone.{table_id}')
            rows_to_insert = [data]
            errors = self.bq_client.insert_rows_json(table, rows_to_insert)
            if errors:
                return {"status": "error", "message": errors}
            return {"status": "success", "message": "Data saved successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)} 