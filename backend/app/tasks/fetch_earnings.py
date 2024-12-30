from datetime import datetime, date, timedelta
import calendar
import requests
from bs4 import BeautifulSoup
from ..db.earnings import insert_earnings_data
import time

def should_fetch_next_month_data() -> bool:
    """今日が月末かどうかをチェック"""
    today = date.today()
    _, last_day = calendar.monthrange(today.year, today.month)
    return today.day == last_day

def get_target_month() -> date:
    """2ヶ月後の月を取得"""
    today = date.today()
    if today.month + 2 > 12:
        # 年をまたぐ場合の処理
        new_year = today.year + ((today.month + 2) // 12)
        new_month = (today.month + 2) % 12
        if new_month == 0:
            new_month = 12
    else:
        new_year = today.year
        new_month = today.month + 2
    
    return date(new_year, new_month, 1)

def scrape_earnings_page(url: str) -> list:
    """決算カレンダーページから企業情報をスクレイピング"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    companies = []

    try:
        # Yahoo!ファイナンスの決算カレンダーのテーブルから情報を取得
        table = soup.find('table', {'class': '_13C_m5Hx'})  # クラス名は実際のものに変更が必要
        if table:
            rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    company = {
                        "code": cols[0].text.strip(),
                        "name": cols[1].text.strip(),
                        "market": cols[2].text.strip(),
                        "fiscal_year": cols[3].text.strip() if len(cols) > 3 else None,
                        "quarter": cols[4].text.strip() if len(cols) > 4 else None
                    }
                    companies.append(company)
    except Exception as e:
        print(f"Error scraping page {url}: {e}")

    return companies

def fetch_earnings_for_specific_month(year: int, month: int):
    """指定された年月の決算データを取得"""
    _, last_day = calendar.monthrange(year, month)
    
    for day in range(1, last_day + 1):
        target_date = date(year, month, day)
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            url = f"https://finance.yahoo.co.jp/calendar/{year}/{month}/{day}"
            companies = scrape_earnings_page(url)
            
            if companies:
                insert_earnings_data(date_str, companies)
                print(f"Successfully saved data for {date_str}")
            
            time.sleep(2)  # サーバー負荷対策
            
        except Exception as e:
            print(f"Error processing date {date_str}: {e}")

# データを即時取得するためのスクリプト
if __name__ == "__main__":
    # 2024年11月のデータを取得
    fetch_earnings_for_specific_month(2024, 11)
    # 2024年12月のデータを取得
    fetch_earnings_for_specific_month(2024, 12) 