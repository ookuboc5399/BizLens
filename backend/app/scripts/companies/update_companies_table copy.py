"""
既存のcompaniesテーブルをバックアップし、株式情報を追加するスクリプト
"""
import os
import json
from datetime import datetime
from google.cloud import bigquery
from typing import Dict, Any, List, Optional
import time

# 企業リスト
COMPANIES = {
    "china": [
        "00001",  # 長江和記実業 (CK Hutchison Holdings)
        "00005",  # HSBCホールディングス (HSBC Holdings)
        "00700",  # テンセント (Tencent Holdings)
        "00941",  # 中国移動通信 (China Mobile)
        "01299",  # AIAグループ (AIA Group)
        "02318",  # 中国平安保険 (Ping An Insurance)
        "02388",  # 中銀香港 (BOC Hong Kong)
        "03988",  # 中国銀行 (Bank of China)
        "03968",  # 招商銀行 (China Merchants Bank)
        "02333",  # 長城汽車 (Great Wall Motor)
        "01988",  # 中国民生銀行 (China Minsheng Banking)
        "01398",  # 中国工商銀行 (Industrial and Commercial Bank of China)
        "00939",  # 中国建設銀行 (China Construction Bank)
        "01113",  # 長江実業地産 (CK Asset Holdings)
        "00016",  # 新鴻基地産 (Sun Hung Kai Properties)
        "00003",  # 香港電灯 (Hong Kong and China Gas)
        "00006",  # 電能実業 (Power Assets Holdings)
        "00012",  # 恒基地産 (Henderson Land Development)
        "00017",  # 新世界発展 (New World Development)
        "00019",  # 太古A (Swire Pacific 'A')
        "00066",  # 港鉄 (MTR Corporation)
        "00101",  # 恒隆地産 (Hang Lung Properties)
        "00175",  # 吉利汽車 (Geely Automobile)
        "00267",  # 中信資源 (CITIC Resources)
        "00386",  # 中国石油化工 (Sinopec Corp)
        "00388",  # 香港取引所 (Hong Kong Exchanges and Clearing)
        "00688",  # 中国海外発展 (China Overseas Land & Investment)
        "00762",  # 中国聯通 (China Unicom)
        "00823",  # 領展房地産基金 (Link Real Estate Investment Trust)
        "00857",  # 中国石油天然気 (PetroChina)
        "00883",  # 中国海洋石油 (CNOOC)
        "00902",  # 華能国際電力 (Huaneng Power International)
        "00914",  # 安徽海螺水泥 (Anhui Conch Cement)
        "01038",  # 長江基建 (CK Infrastructure Holdings)
        "01044",  # 恒安国際 (Hengan International)
        "01088",  # 中国神華能源 (China Shenhua Energy)
        "01109",  # 華潤置地 (China Resources Land)
        "01177",  # 中国生物製薬 (Sino Biopharmaceutical)
        "01288",  # 中国農業銀行 (Agricultural Bank of China)
        "01313",  # 華潤燃気 (China Resources Gas)
        "01810",  # 小米集団 (Xiaomi Corporation)
        "01928",  # サンズチャイナ (Sands China)
        "02007",  # 碧桂園 (Country Garden Holdings)
        "02202",  # 万科企業 (China Vanke)
        "02313",  # 申洲国際 (Shenzhou International)
        "02319",  # 蒙牛乳業 (China Mengniu Dairy)
        "02628",  # 中国人寿保険 (China Life Insurance)
        "02688",  # 新奥能源 (ENN Energy Holdings)
        "03328",  # 交通銀行 (Bank of Communications)
        "06030",  # 中信証券 (CITIC Securities)
        "06837",  # 海通証券 (Haitong Securities)
        "06886",  # 中国飛鶴 (China Feihe)
        "09988",  # アリババグループ (Alibaba Group Holding)
        "03690",  # 美団 (Meituan)
        "09888",  # 百度 (Baidu)
        "09618",  # 京東集団 (JD.com)
        "09999",  # ネットイース (NetEase)
        "02382",  # 舜宇光学科技 (Sunny Optical Technology)
        "02269",  # 藍月亮集団 (Blue Moon Group)
        "06618",  # 京東健康 (JD Health International)
        "09633",  # クアラテック (Kuaishou Technology)
        "09868",  # 快手科技 (Kuaishou Technology)
        "09922",  # 泡泡瑪特 (Pop Mart International)
        "09923",  # 再鼎医薬 (Zai Lab)
        "09961",  # 中通快遞 (ZTO Express)
        "09962",  # 亜盛医薬 (Ascentage Pharma)
        "09966",  # 康希諾生物 (CanSino Biologics)
    ],
    "us": [
        "NVDA",  # NVIDIA Corporation
        "TSLA",  # Tesla, Inc.
        "AAPL",  # Apple Inc.
        "MSFT",  # Microsoft Corporation
        "GOOGL", # Alphabet Inc.
        "AMZN",  # Amazon.com, Inc.
        "META",  # Meta Platforms, Inc.
        "BRK-B", # Berkshire Hathaway Inc.
        "JPM",   # JPMorgan Chase & Co.
        "V",     # Visa Inc.
        "JNJ",   # Johnson & Johnson
        "WMT",   # Walmart Inc.
        "MA",    # Mastercard Incorporated
        "PG",    # The Procter & Gamble Company
        "HD",    # The Home Depot, Inc.
        "BAC",   # Bank of America Corporation
        "AVGO",  # Broadcom Inc.
        "XOM",   # Exxon Mobil Corporation
        "COST",  # Costco Wholesale Corporation
        "ABBV",  # AbbVie Inc.
        "MRK",   # Merck & Co., Inc.
        "CSCO",  # Cisco Systems, Inc.
        "PEP",   # PepsiCo, Inc.
        "TMO",   # Thermo Fisher Scientific Inc.
        "ACN",   # Accenture plc
        "MCD",   # McDonald's Corporation
        "ABT",   # Abbott Laboratories
        "DHR",   # Danaher Corporation
        "ADBE",  # Adobe Inc.
        "LLY"    # Eli Lilly and Company
    ]
}

def convert_to_float(value: str) -> float:
    """文字列を浮動小数点数に変換"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if value == "—" or value == "" or value == "N/A":
            return None
        return float(value.replace(",", ""))
    except (ValueError, AttributeError):
        return None

def convert_china_stock_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """中国株のデータを変換"""
    try:
        indicators = data["financial_info"]["data"]["indicators"]
        
        return {
            # 基本情報
            "ticker": data["ticker"],
            "market": data["company_info"]["data"]["market_info"]["market"],
            "company_name": data["company_info"]["data"]["basic_info"].get("正式社名", ""),
            "industry": data["company_info"]["data"]["market_info"]["industry"],
            "business_description": data["company_info"]["data"]["business_description"],
            "website": data["company_info"]["data"]["basic_info"].get("URL", ""),
            "data_source": "nikkei",
            "last_updated": data["fetched_at"],
            
            # 株価情報
            "current_price": convert_to_float(data["stock_price"]["data"]["current_price"].get("取引値")),
            "market_cap": convert_to_float(data["stock_price"]["data"]["price_history"][0]["basic_info"].get("時価総額")),
            "per": convert_to_float(data["stock_price"]["data"]["price_history"][0]["market_info"].get("per")),
            "bps": convert_to_float(indicators.get("BPS")),
            
            # 財務指標
            "current_assets": convert_to_float(indicators.get("流動資産")),
            "total_assets": convert_to_float(indicators.get("総資産")),
            "current_liabilities": convert_to_float(indicators.get("流動負債")),
            "total_liabilities": convert_to_float(indicators.get("総負債")),
            "capital": convert_to_float(indicators.get("資本金")),
            "minority_interests": convert_to_float(indicators.get("少数株主権益")),
            "shareholders_equity": convert_to_float(indicators.get("株主資本")),
            "debt_ratio": convert_to_float(indicators.get("負債比率")),
            "current_ratio": convert_to_float(indicators.get("流動比率")),
            "equity_ratio": convert_to_float(indicators.get("株主資本比率")),
            
            # キャッシュフロー
            "operating_cash_flow": convert_to_float(indicators.get("営業活動キャッシュフロー")),
            "investing_cash_flow": convert_to_float(indicators.get("投資活動キャッシュフロー")),
            "financing_cash_flow": convert_to_float(indicators.get("財務活動キャッシュフロー")),
            "cash_and_equivalents": convert_to_float(indicators.get("現金および現金同等物"))
        }
    except Exception as e:
        print(f"Error converting China stock data: {str(e)}")
        return None

def convert_us_stock_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """アメリカ株のデータを変換"""
    try:
        stats = data["data"]
        valuation = stats.get("Valuation Measures", {})
        balance = stats.get("Balance Sheet", {})
        income = stats.get("Income Statement", {})
        cash_flow = stats.get("Cash Flow Statement", {})
        profitability = stats.get("Profitability", {})
        shares = stats.get("Share Statistics", {})
        
        return {
            # 基本情報
            "ticker": data["ticker"],
            "market": "NYSE/NASDAQ",
            "company_name": "",  # Yahoo Financeからは取得できない
            "industry": "",      # Yahoo Financeからは取得できない
            "business_description": "",  # Yahoo Financeからは取得できない
            "website": "",       # Yahoo Financeからは取得できない
            "data_source": "yahoo_finance",
            "last_updated": data["fetched_at"],
            
            # 株価情報
            "current_price": valuation.get("Current Price", None),
            "market_cap": valuation.get("Market Cap (intraday)", None),
            "per": valuation.get("Forward P/E", None),
            "pbr": valuation.get("Price/Book", None),
            "eps": income.get("EPS (TTM)", None),
            "bps": balance.get("Book Value Per Share", None),
            "roe": profitability.get("Return on Equity", None),
            "roa": profitability.get("Return on Assets", None),
            
            # 財務指標
            "current_assets": balance.get("Total Current Assets", None),
            "total_assets": balance.get("Total Assets", None),
            "current_liabilities": balance.get("Total Current Liabilities", None),
            "total_liabilities": balance.get("Total Liabilities", None),
            "capital": balance.get("Common Stock", None),
            "minority_interests": balance.get("Minority Interest", None),
            "shareholders_equity": balance.get("Total Stockholder Equity", None),
            "debt_ratio": balance.get("Total Debt/Equity", None),
            "current_ratio": None,  # 計算が必要
            "equity_ratio": None,  # 計算が必要
            
            # キャッシュフロー
            "operating_cash_flow": cash_flow.get("Operating Cash Flow", None),
            "investing_cash_flow": cash_flow.get("Investing Cash Flow", None),
            "financing_cash_flow": cash_flow.get("Financing Cash Flow", None),
            "cash_and_equivalents": balance.get("Cash And Cash Equivalents", None),
            
            # 収益性指標
            "revenue": income.get("Total Revenue", None),
            "operating_income": income.get("Operating Income", None),
            "net_income": income.get("Net Income", None),
            "operating_margin": profitability.get("Operating Margin", None),
            "net_margin": profitability.get("Profit Margin", None),
            
            # 配当関連
            "dividend_yield": valuation.get("Forward Annual Dividend Yield", None),
            "dividend_per_share": valuation.get("Forward Annual Dividend Rate", None),
            "payout_ratio": valuation.get("Payout Ratio", None),
            
            # その他
            "beta": valuation.get("Beta (5Y Monthly)", None),
            "shares_outstanding": shares.get("Shares Outstanding", None),
            "market_type": "US",
            "sector": "",  # Yahoo Financeからは取得できない
            "country": "US",
            "currency": "USD",
            "collected_at": data["fetched_at"]
        }
    except Exception as e:
        print(f"Error converting US stock data: {str(e)}")
        return None

def get_required_schema() -> List[bigquery.SchemaField]:
    """必要なスキーマを定義"""
    return [
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
        bigquery.SchemaField("collected_at", "TIMESTAMP")
    ]

def update_table_schema(client: bigquery.Client, table_ref: str, required_schema: List[bigquery.SchemaField]) -> None:
    """テーブルのスキーマを更新（既存のフィールドを維持）"""
    table = client.get_table(table_ref)
    existing_fields = {field.name: field for field in table.schema}
    
    # 新しいスキーマを作成（既存のフィールドを維持）
    new_schema = list(table.schema)
    
    # 必要なフィールドを追加（既存のフィールドは保持）
    for required_field in required_schema:
        if required_field.name not in existing_fields:
            print(f"Adding new column: {required_field.name}")
            # ALTER TABLEを使用して列を追加
            query = f"""
            ALTER TABLE `{table_ref}`
            ADD COLUMN IF NOT EXISTS {required_field.name} {required_field.field_type}
            """
            query_job = client.query(query)
            query_job.result()  # クエリの完了を待機
            
            # スキーマリストにも追加
            new_schema.append(required_field)
    
    # テーブルのスキーマを更新
    if len(new_schema) > len(table.schema):
        table = client.get_table(table_ref)  # 最新のテーブル情報を取得
        table.schema = new_schema
        client.update_table(table, ["schema"])
        print("Schema updated successfully")
        
        # 更新されたスキーマをログに出力
        updated_table = client.get_table(table_ref)
        print("Updated schema:")
        for field in updated_table.schema:
            print(f"- {field.name}: {field.field_type}")

def update_companies_table(client: bigquery.Client, project_id: str, dataset_id: str, companies_data: List[Dict[str, Any]]) -> None:
    """companiesテーブルを更新"""
    table_id = f"{project_id}.{dataset_id}.companies"
    
    # 必要なスキーマを取得
    required_schema = get_required_schema()
    
    try:
        # テーブルが存在するか確認
        client.get_table(table_id)
    except Exception:
        # テーブルが存在しない場合は作成
        table = bigquery.Table(table_id, schema=required_schema)
        client.create_table(table)
        print(f"Created new table: {table_id}")
    
    # スキーマの更新
    update_table_schema(client, table_id, required_schema)
    
    # 一時テーブルの作成（必要なスキーマを使用）
    temp_table_id = f"{project_id}.{dataset_id}.companies_temp"
    temp_table = bigquery.Table(temp_table_id, schema=required_schema)
    temp_table = client.create_table(temp_table, exists_ok=True)
    
    # 一時テーブルにデータを挿入（スキーマが完全な状態で）
    errors = client.insert_rows_json(temp_table, companies_data)
    if errors:
        print("Errors occurred while inserting rows to temp table:", errors)
        return

    # 既存のデータと新しいデータをマージ
    merge_query = f"""
    MERGE `{table_id}` T
    USING `{temp_table_id}` S
    ON T.ticker = S.ticker
    WHEN MATCHED THEN
        UPDATE SET
            market = S.market,
            company_name = S.company_name,
            industry = S.industry,
            business_description = S.business_description,
            website = S.website,
            data_source = S.data_source,
            last_updated = S.last_updated,
            current_price = S.current_price,
            market_cap = S.market_cap,
            per = S.per,
            pbr = S.pbr,
            eps = S.eps,
            bps = S.bps,
            roe = S.roe,
            roa = S.roa,
            current_assets = S.current_assets,
            total_assets = S.total_assets,
            current_liabilities = S.current_liabilities,
            total_liabilities = S.total_liabilities,
            capital = S.capital,
            minority_interests = S.minority_interests,
            shareholders_equity = S.shareholders_equity,
            debt_ratio = S.debt_ratio,
            current_ratio = S.current_ratio,
            equity_ratio = S.equity_ratio,
            operating_cash_flow = S.operating_cash_flow,
            investing_cash_flow = S.investing_cash_flow,
            financing_cash_flow = S.financing_cash_flow,
            cash_and_equivalents = S.cash_and_equivalents,
            revenue = S.revenue,
            operating_income = S.operating_income,
            net_income = S.net_income,
            operating_margin = S.operating_margin,
            net_margin = S.net_margin,
            dividend_yield = S.dividend_yield,
            dividend_per_share = S.dividend_per_share,
            payout_ratio = S.payout_ratio,
            beta = S.beta,
            shares_outstanding = S.shares_outstanding,
            market_type = S.market_type,
            sector = S.sector,
            country = S.country,
            currency = S.currency,
            collected_at = S.collected_at
    WHEN NOT MATCHED THEN
        INSERT (ticker, market, company_name, industry, business_description, 
                website, data_source, last_updated, current_price, market_cap,
                per, pbr, eps, bps, roe, roa, current_assets, total_assets,
                current_liabilities, total_liabilities, capital, minority_interests,
                shareholders_equity, debt_ratio, current_ratio, equity_ratio,
                operating_cash_flow, investing_cash_flow, financing_cash_flow,
                cash_and_equivalents, revenue, operating_income, net_income,
                operating_margin, net_margin, dividend_yield, dividend_per_share,
                payout_ratio, beta, shares_outstanding, market_type, sector,
                country, currency, collected_at)
        VALUES (S.ticker, S.market, S.company_name, S.industry, S.business_description,
                S.website, S.data_source, S.last_updated, S.current_price, S.market_cap,
                S.per, S.pbr, S.eps, S.bps, S.roe, S.roa, S.current_assets, S.total_assets,
                S.current_liabilities, S.total_liabilities, S.capital, S.minority_interests,
                S.shareholders_equity, S.debt_ratio, S.current_ratio, S.equity_ratio,
                S.operating_cash_flow, S.investing_cash_flow, S.financing_cash_flow,
                S.cash_and_equivalents, S.revenue, S.operating_income, S.net_income,
                S.operating_margin, S.net_margin, S.dividend_yield, S.dividend_per_share,
                S.payout_ratio, S.beta, S.shares_outstanding, S.market_type, S.sector,
                S.country, S.currency, S.collected_at)
    """
    
    # マージクエリの実行
    merge_job = client.query(merge_query)
    merge_job.result()
    
    # 一時テーブルの削除
    client.delete_table(temp_table_id)
    if errors:
        print("Errors occurred while inserting rows:", errors)
    else:
        print(f"Successfully inserted {len(companies_data)} rows")

def collect_china_stocks() -> List[Dict[str, Any]]:
    """中国株のデータを収集"""
    from app.services.companies.china_stock_scraper import ChinaStockScraper
    
    companies_data = []
    china_scraper = ChinaStockScraper()
    
    for ticker in COMPANIES["china"]:
        try:
            print(f"Collecting data for China stock: {ticker}")
            data = china_scraper.get_all_info(ticker)
            
            # JSONファイルに保存
            save_path = os.path.join("data", "stocks", "china", f"{ticker}_data.json")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved data for {ticker}")
            
            # データを変換して追加
            company_data = convert_china_stock_data(data)
            if company_data:
                companies_data.append(company_data)
            
            # API制限を考慮して待機
            time.sleep(2)
            
        except Exception as e:
            print(f"Error collecting data for {ticker}: {str(e)}")
            continue
    
    return companies_data

def collect_us_stocks() -> List[Dict[str, Any]]:
    """アメリカ株のデータを収集"""
    from app.services.companies.us_stock_scraper import USStockScraper
    
    companies_data = []
    us_scraper = USStockScraper()
    
    for ticker in COMPANIES["us"]:
        try:
            print(f"Collecting data for US stock: {ticker}")
            data = us_scraper.get_all_info(ticker)
            
            # JSONファイルに保存
            save_path = os.path.join("data", "stocks", "us", f"{ticker}_data.json")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved data for {ticker}")
            
            # データを変換して追加
            company_data = convert_us_stock_data(data)
            if company_data:
                companies_data.append(company_data)
            
            # API制限を考慮して待機
            time.sleep(2)
            
        except Exception as e:
            print(f"Error collecting data for {ticker}: {str(e)}")
            continue
    
    return companies_data

def main():
    """メイン処理"""
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='株式情報を収集してBigQueryに保存')
    parser.add_argument('--market', choices=['china', 'us', 'all'], default='all',
                      help='取得する市場を指定 (china: 中国株, us: アメリカ株, all: 両方)')
    args = parser.parse_args()
    
    # BigQueryクライアントの初期化
    from app.services.bigquery_service import BigQueryService
    bq_service = BigQueryService()
    client = bq_service.client
    project_id = bq_service.project_id
    dataset_id = bq_service.dataset
    
    try:
        companies_data = []
        
        # 指定された市場のデータを取得
        if args.market in ['china', 'all']:
            print("Collecting China stocks data...")
            china_data = collect_china_stocks()
            companies_data.extend(china_data)
            print(f"Collected {len(china_data)} China stocks")
        
        if args.market in ['us', 'all']:
            print("Collecting US stocks data...")
            us_data = collect_us_stocks()
            companies_data.extend(us_data)
            print(f"Collected {len(us_data)} US stocks")
        
        # テーブルの更新
        if companies_data:
            update_companies_table(client, project_id, dataset_id, companies_data)
            print(f"Successfully updated companies table with {len(companies_data)} stocks")
        else:
            print("No data to update")
        
    except Exception as e:
        print(f"Error updating companies table: {str(e)}")

if __name__ == "__main__":
    main()
