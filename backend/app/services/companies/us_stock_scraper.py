"""
Yahoo Financeからアメリカ株の情報を取得するスクレイパー
"""
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import os

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ログディレクトリの作成
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'us_stock_scraping.log')

# ファイルハンドラーの設定
fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

# コンソールハンドラーの設定
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

class USStockScraper:
    def __init__(self):
        """初期化"""
        self.base_url = "https://finance.yahoo.com/quote"
        self.driver = None

    def setup_driver(self):
        """WebDriverの設定"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')  # ヘッドレスモードを有効化
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        logger.info("WebDriver initialized")

    def close_driver(self):
        """WebDriverを終了"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """要素の待機"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Error waiting for element {value}: {str(e)}")
            return None

    def get_key_statistics(self, ticker: str) -> Dict[str, Any]:
        """Key Statisticsの取得"""
        url = f"{self.base_url}/{ticker}/key-statistics"
        try:
            self.driver.get(url)
            time.sleep(5)  # ページの読み込みを待機

            # データの抽出
            statistics_data = {
                "ticker": ticker,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {}
            }

            # ページソースをログに出力（デバッグ用）
            logger.debug(f"Page source: {self.driver.page_source}")

            # ページ全体からテーブルを取得
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"Found {len(tables)} tables")

            # 各テーブルのデータを処理
            for table in tables:
                try:
                    # テーブルのセクション名を取得
                    try:
                        # テーブルの前にある最も近いh3要素を探す
                        section_header = table.find_element(By.XPATH, "preceding::h3[1]")
                        section_name = section_header.text.strip()
                    except:
                        # セクション名が見つからない場合はデフォルト値を使用
                        section_name = f"Statistics_{tables.index(table)}"
                    logger.info(f"Processing section: {section_name}")

                    # テーブル内の行を取得
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    section_data = {}

                    for row in rows:
                        try:
                            # 項目名と値を取得
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                key = cells[0].text.strip()
                                value = cells[1].text.strip()
                                
                                # 数値の変換
                                if value == 'N/A':
                                    value = None
                                elif value.endswith('%'):
                                    value = float(value.replace('%', '')) / 100
                                elif value.endswith('B'):
                                    value = float(value.replace('B', '')) * 1_000_000_000
                                elif value.endswith('M'):
                                    value = float(value.replace('M', '')) * 1_000_000
                                elif value.endswith('K'):
                                    value = float(value.replace('K', '')) * 1_000
                                elif value.endswith('T'):
                                    value = float(value.replace('T', '')) * 1_000_000_000_000
                                else:
                                    # カンマを削除して数値に変換を試みる
                                    cleaned_value = value.replace(',', '')
                                    try:
                                        value = float(cleaned_value)
                                    except ValueError:
                                        # 数値変換に失敗した場合は元の値を保持
                                        pass
                                
                                section_data[key] = value
                        except Exception as e:
                            logger.error(f"Error processing row: {str(e)}")
                            continue

                    statistics_data["data"][section_name] = section_data
                    logger.info(f"Successfully processed section {section_name}")
                except Exception as e:
                    logger.error(f"Error processing table: {str(e)}")
                    continue

            return statistics_data

        except Exception as e:
            logger.error(f"Error fetching key statistics for {ticker}: {str(e)}")
            return {"error": str(e)}

    def get_all_info(self, ticker: str) -> Dict[str, Any]:
        """全ての情報を取得"""
        try:
            self.setup_driver()
            return self.get_key_statistics(ticker)
        except Exception as e:
            logger.error(f"Error fetching all info for {ticker}: {str(e)}")
            return {"error": str(e)}
        finally:
            self.close_driver()

def save_to_json(data: Dict[str, Any], filename: str):
    """データをJSONファイルに保存"""
    filepath = os.path.join("data", "us_stocks", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved data to {filepath}")

def main():
    """メイン処理"""
    scraper = USStockScraper()
    ticker = "NVDA"  # テスト用のティッカー
    
    try:
        data = scraper.get_all_info(ticker)
        save_to_json(data, f"{ticker}_data.json")
        logger.info(f"Successfully collected data for {ticker}")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()
