import asyncio
import os
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
import re
import json
import pandas as pd
import io

load_dotenv()

# BigQuery設定
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)
client = bigquery.Client(credentials=credentials, project=os.getenv('GOOGLE_CLOUD_PROJECT'))

# ブラウザのヘッダーを模倣
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}

def parse_nikkei_date(date_str: str) -> str:
    """日経の日付文字列をISO形式に変換"""
    # "YYYY/MM/DD" -> "YYYY-MM-DD"
    try:
        date_obj = datetime.strptime(date_str, '%Y/%m/%d')
        return date_obj.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def parse_fiscal_period(period_str: str, quarter_str: str) -> tuple:
    """決算期と四半期を解析"""
    # 例: period_str="2月期", quarter_str=" 第３ "
    try:
        month_match = re.match(r'(\d+)月期', period_str)
        quarter_match = re.search(r'第\s*(\d)\s*', quarter_str)
        
        if month_match and quarter_match:
            month = int(month_match.group(1))
            quarter = int(quarter_match.group(1))
            
            # 決算期から年度を計算
            now = datetime.now()
            if month < now.month:
                year = now.year + 1
            else:
                year = now.year
            
            return year, quarter
    except Exception as e:
        print(f"Error parsing fiscal period '{period_str}', '{quarter_str}': {e}")
    return None, None

def parse_company_code(code_str: str) -> str:
    """企業コードを抽出"""
    try:
        # 数字4桁のみを抽出
        code = re.sub(r'\D', '', code_str)[:4]
        if len(code) == 4:
            return code
    except Exception as e:
        print(f"Error parsing company code '{code_str}': {e}")
    return None

async def fetch_nikkei_data(session, year: int, month: int):
    """日経から決算予定データを取得"""
    url = f"https://www.nikkei.com/markets/kigyo/money-schedule/kessan/?ResultFlag=4&KessanMonth={month:02d}"
    print(f"Fetching Nikkei data from: {url}")
    
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                earnings_data = []
                # デバッグ用にHTMLを保存
                with open(f'debug_nikkei_{year}_{month}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # 決算発表スケジュールのテーブルを探す
                article = soup.find('div', class_='m-artcle')
                if not article:
                    print("Article div not found")
                    return []
                
                table = article.find('table', class_='cmn-table_style2')
                
                if not table:
                    print("Table not found in Nikkei")
                    return []
                
                for row in table.find_all('tr', class_='tr2'):  # データ行を取得
                    cols = row.find_all(['td', 'th'])  # thタグも含める
                    if len(cols) >= 8:  # 必要なカラム数があることを確認
                        # 列の順序:
                        # 0: 決算発表日
                        # 1: 証券コード
                        # 2: 会社名
                        # 3: 関連情報
                        # 4: 決算期
                        # 5: 決算種別
                        # 6: 業種
                        # 7: 上場市場
                        date_str = cols[0].text.strip()
                        # 証券コードはaタグ内にある
                        code_link = cols[1].find('a')
                        code_str = code_link.text.strip() if code_link else cols[1].text.strip()
                        # 会社名もaタグ内にある
                        name_link = cols[2].find('a')
                        company_name = name_link.text.strip() if name_link else cols[2].text.strip()
                        period_str = cols[4].text.strip()  # 決算期
                        quarter_str = cols[5].text.strip()  # 決算種別
                        
                        print(f"Raw data: date='{date_str}', code='{code_str}', name='{company_name}', period='{period_str}', quarter='{quarter_str}'")
                        
                        announcement_date = parse_nikkei_date(date_str)
                        code = parse_company_code(code_str)
                        fiscal_year, quarter = parse_fiscal_period(period_str, quarter_str)
                        
                        print(f"Parsed data: date='{announcement_date}', code='{code}', fiscal_year='{fiscal_year}', quarter='{quarter}'")
                        
                        if all([announcement_date, code, fiscal_year, quarter]):
                            earnings_data.append({
                                "code": code,
                                "company_name": company_name,
                                "date": announcement_date,
                                "fiscal_year": fiscal_year,
                                "quarter": quarter,
                            })
                        else:
                            print(f"Skipping row due to missing data")
                
                print(f"Found {len(earnings_data)} companies from Nikkei for {year}/{month}")
                return earnings_data
            else:
                print(f"Failed to fetch Nikkei data: {response.status}")
                return []
    except Exception as e:
        print(f"Error fetching Nikkei data: {str(e)}")
        return []

async def fetch_jpx_data(session, year: int, month: int):
    """JPXから決算予定データを取得"""
    # 最新のExcelファイルのURLを取得
    index_url = "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/index.html"
    
    try:
        async with session.get(index_url, headers=HEADERS) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Excelファイルへのリンクを探す
                excel_link = None
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    if 'kessan.xlsx' in href:
                        excel_link = href
                        break
                
                if not excel_link:
                    print("Excel file link not found")
                    return []
                
                # 相対URLを絶対URLに変換
                if not excel_link.startswith('http'):
                    excel_link = f"https://www.jpx.co.jp{excel_link}"
                
                print(f"Downloading Excel file from: {excel_link}")
                
                # Excelファイルをダウンロード
                async with session.get(excel_link, headers=HEADERS) as excel_response:
                    if excel_response.status == 200:
                        content = await excel_response.read()
                        df = pd.read_excel(io.BytesIO(content))
                        
                        earnings_data = []
                        print(f"Excel columns: {df.columns.tolist()}")
                        print(f"First few rows: {df.head()}")
                        
                        # データを解析して必要な情報を抽出
                        for _, row in df.iterrows():
                            try:
                                date_str = row['日付'].strftime('%Y-%m-%d')
                                code = str(row['コード']).zfill(4)
                                company_name = row['会社名']
                                fiscal_year = int(row['決算期'].split('年')[0])
                                if fiscal_year < 100:
                                    fiscal_year += 2000
                                quarter = int(row['四半期'])
                                
                                # 指定された年月のデータのみを抽出
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                if date_obj.year == year and date_obj.month == month:
                                    earnings_data.append({
                                        "code": code,
                                        "company_name": company_name,
                                        "date": date_str,
                                        "fiscal_year": fiscal_year,
                                        "quarter": quarter,
                                            })
                            except Exception as e:
                                print(f"Error processing row: {e}")
                                continue
                        
                        print(f"Found {len(earnings_data)} companies from JPX for {year}/{month}")
                        return earnings_data
                    else:
                        print(f"Failed to download Excel file: {excel_response.status}")
                        return []
            else:
                print(f"Failed to fetch JPX index page: {response.status}")
                return []
    except Exception as e:
        print(f"Error fetching JPX data: {str(e)}")
        return []

async def save_to_bigquery(earnings_data):
    """決算予定データをBigQueryに保存"""
    table_id = f"{os.getenv('BIGQUERY_DATASET')}.earnings_calendar"
    
    # データを整形
    rows_to_insert = []
    for data in earnings_data:
        row = {
            "ticker": data["code"],
            "company_name": data["company_name"],
            "announcement_date": data["date"],
            "fiscal_year": data["fiscal_year"],
            "fiscal_quarter": data["quarter"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        rows_to_insert.append(row)
    
    # BigQueryに保存
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Failed to insert rows: {errors}")
    else:
        print(f"Successfully inserted {len(rows_to_insert)} rows")

async def fetch_earnings_data(session, year: int, month: int):
    """両方のソースから決算予定データを取得"""
    nikkei_data = await fetch_nikkei_data(session, year, month)
    jpx_data = await fetch_jpx_data(session, year, month)
    
    # データをマージ（同じ企業の場合は両方のソースからの情報を保持）
    merged_data = {}
    for data in nikkei_data + jpx_data:
        key = f"{data['code']}_{data['date']}"
        if key not in merged_data:
            merged_data[key] = data
        else:
            # 既存のデータがある場合は上書き（最新のデータを優先）
            merged_data[key] = data
    
    return list(merged_data.values())

async def main():
    # 取得対象の期間を設定
    target_dates = [
        # 2024年2月と8月のデータを取得
        (2024, 2),
        (2024, 8),
        # 優先度の高い期間
        (2024, 12),
        (2025, 1),
    ]
    
    async with aiohttp.ClientSession() as session:
        for year, month in target_dates:
            print(f"Fetching data for {year}/{month}")
            earnings_data = await fetch_earnings_data(session, year, month)
            if earnings_data:
                await save_to_bigquery(earnings_data)
            # レート制限を考慮して待機
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
