"""
中国株の情報を取得するスクレーパー
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
log_file = os.path.join(log_dir, 'china_stock_scraping.log')

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

class ChinaStockScraper:
    def __init__(self):
        """初期化"""
        self.base_url = "https://www.nikihou.jp/company/company.html"
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

    def get_financial_info(self, ticker: str) -> Dict[str, Any]:
        """財務情報の取得"""
        url = f"{self.base_url}?code={ticker}&market=HKM&type=finance"
        try:
            self.driver.get(url)
            time.sleep(2)  # ページの読み込みを待機

            # 財務情報の抽出
            financial_data = {
                "ticker": ticker,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {}
            }

            # 財務諸表の取得
            # 財務諸表のテーブルを取得
            logger.info("Searching for financial statement tables...")
            tables = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'contentPart')]//table[contains(@class, 'companyContent') and contains(@class, 'smallWord')]"
            )
            logger.info(f"Found {len(tables)} tables")

            # ページのHTMLを出力（デバッグ用）
            logger.debug(f"Page HTML: {self.driver.page_source}")
            for table in tables:
                try:
                    # テーブルのヘッダーを取得
                    headers = table.find_elements(By.TAG_NAME, "th")
                    header_texts = [h.text.strip() for h in headers]
                    
                    # 財務諸表の種類を判定
                    if "決算期" in header_texts:
                        # データ行を取得
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        statement_data = []
                        
                        for row in rows[1:]:  # ヘッダー行をスキップ
                            cells = row.find_elements(By.TAG_NAME, "td")
                            row_data = {}
                            
                            for i, cell in enumerate(cells):
                                header = header_texts[i] if i < len(header_texts) else f"column_{i}"
                                value = cell.text.strip()
                                
                                # 数値の処理
                                if "百万" in value:
                                    try:
                                        # "1,234百万"のような形式を数値に変換
                                        numeric_value = float(value.replace("百万", "").replace(",", "")) * 1_000_000
                                        row_data[header] = numeric_value
                                    except ValueError:
                                        row_data[header] = value
                                else:
                                    row_data[header] = value
                            
                            statement_data.append(row_data)
                        
                        # 財務諸表の種類を判定してデータを格納
                        if "売上高" in header_texts:
                            financial_data["data"]["income_statement"] = statement_data
                        elif "総資産" in header_texts:
                            financial_data["data"]["balance_sheet"] = statement_data
                        elif "営業活動によるキャッシュフロー" in header_texts:
                            financial_data["data"]["cash_flow"] = statement_data
                
                except Exception as e:
                    logger.error(f"Error processing table: {str(e)}")
                    continue

            # 財務指標の取得
            indicator_data = {}
            
            # 財務指標のテーブルを取得
            logger.info("Searching for financial indicator tables...")
            indicator_tables = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'contentPart')]//table[contains(@class, 'companyContent') and contains(@class, 'smallWord')]"
            )
            logger.info(f"Found {len(indicator_tables)} indicator tables")

            # テーブルの内容を出力（デバッグ用）
            for i, table in enumerate(indicator_tables):
                logger.debug(f"Table {i} content: {table.text}")
                try:
                    # 財務指標の行を取得
                    logger.info("Searching for financial indicator rows...")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    logger.info(f"Found {len(rows)} rows in table")

                    # 行の内容を出力（デバッグ用）
                    for row in rows:
                        logger.debug(f"Row content: {row.text}")
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            
                            # 数値の処理
                            try:
                                if "%" in value:
                                    value = float(value.replace("%", "")) / 100
                                elif "倍" in value:
                                    value = float(value.replace("倍", ""))
                                elif "円" in value:
                                    value = float(value.replace("円", "").replace(",", ""))
                            except ValueError:
                                pass
                            
                            indicator_data[key] = value
                except Exception as e:
                    logger.error(f"Error processing indicators: {str(e)}")
                    continue
            
            financial_data["data"]["indicators"] = indicator_data

            return financial_data

        except Exception as e:
            logger.error(f"Error fetching financial info for {ticker}: {str(e)}")
            return {"error": str(e)}

    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """企業概要の取得"""
        url = f"{self.base_url}?code={ticker}&market=HKM&type=outline"
        try:
            self.driver.get(url)
            time.sleep(2)  # ページの読み込みを待機

            company_data = {
                "ticker": ticker,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "basic_info": {},
                    "business_description": "",
                    "market_info": {}
                }
            }

            # 市場情報の取得
            market_info = self.driver.find_element(By.CLASS_NAME, "middleWord")
            if market_info:
                market_cells = market_info.find_elements(By.TAG_NAME, "td")
                if len(market_cells) >= 3:
                    market_text = market_cells[0].text.strip()
                    industry = market_cells[2].text.strip()
                    company_data["data"]["market_info"] = {
                        "market": market_text.split()[0],  # "メインボード"
                        "ticker": market_text.split()[-1],  # "02312"
                        "industry": industry  # "金融・証券・保険"
                    }

            # 基本情報の取得
            basic_info_table = self.driver.find_element(By.CLASS_NAME, "companyContent1")
            if basic_info_table:
                rows = basic_info_table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            
                            # URLの場合、リンク先も取得
                            if key == "URL":
                                link = cells[1].find_element(By.TAG_NAME, "a")
                                if link:
                                    value = link.get_attribute("href")
                            
                            # 不要な文字を削除
                            key = key.replace(" ", "")
                            company_data["data"]["basic_info"][key] = value
                    except Exception as e:
                        logger.error(f"Error processing basic info row: {str(e)}")
                        continue

            # 企業概要の取得
            summary_content = self.driver.find_element(By.CLASS_NAME, "summaryContent")
            if summary_content:
                description = summary_content.text.strip()
                # ログインが必要な部分を除去
                if "＜続きを読むにはログインが必要です＞" in description:
                    description = description.split("＜続きを読むにはログインが必要です＞")[0].strip()
                company_data["data"]["business_description"] = description

            return company_data

        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {str(e)}")
            return {"error": str(e)}

    def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """株価情報の取得"""
        url = f"{self.base_url}?code={ticker}&market=HKM&type=price"
        try:
            self.driver.get(url)
            time.sleep(2)  # ページの読み込みを待機

            # ページのHTMLを出力（デバッグ用）
            logger.debug(f"Price page HTML: {self.driver.page_source}")

            price_data = {
                "ticker": ticker,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "current_price": {},
                    "trading_info": {},
                    "price_history": []
                }
            }

            # 現在の株価情報を取得
            logger.info("Searching for current price table...")
            try:
                # 株価情報のテーブルを取得（取引値のセル）
                price_cell = self.driver.find_element(By.XPATH, "//td[text()='取引値']")
                price_table = price_cell.find_element(By.XPATH, "./ancestor::table[1]")
                logger.info("Found current price table")
                rows = price_table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            
                            # 数値の処理
                            try:
                                if "HK$" in value:
                                    value = float(value.replace("HK$", "").replace(",", ""))
                                elif "%" in value:
                                    value = float(value.replace("%", "")) / 100
                            except ValueError:
                                pass
                            
                            key = key.replace(" ", "_").lower()
                            price_data["data"]["current_price"][key] = value
                    except Exception as e:
                        logger.error(f"Error processing price info row: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Error finding current price table: {str(e)}")

            # 取引情報を取得
            logger.info("Searching for trading info table...")
            try:
                # 取引情報のテーブルを取得（売気配のセル）
                trading_cell = self.driver.find_element(By.XPATH, "//td[text()='売気配1']")
                trading_table = trading_cell.find_element(By.XPATH, "./ancestor::table[1]")
                logger.info("Found trading info table")
                rows = trading_table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            # セルのペアを処理
                            if len(cells) >= 6:  # 6つのセルがある場合（売気配1/買気配1のペアなど）
                                # 売気配と数量
                                sell_key = cells[0].text.strip()
                                sell_value = cells[1].text.strip()
                                sell_pair = {
                                    "price": float(sell_value.replace("HK$", "").replace(",", "")) if "HK$" in sell_value else None,
                                    "volume": int(sell_value.replace("株", "").replace(",", "")) if "株" in sell_value else None
                                }
                                
                                # 買気配と数量
                                buy_key = cells[2].text.strip()
                                buy_value = cells[3].text.strip()
                                buy_pair = {
                                    "price": float(buy_value.replace("HK$", "").replace(",", "")) if "HK$" in buy_value else None,
                                    "volume": int(buy_value.replace("株", "").replace(",", "")) if "株" in buy_value else None
                                }
                                
                                # 追加の情報（存在する場合）
                                if len(cells) >= 6:
                                    extra_key = cells[4].text.strip()
                                    extra_value = cells[5].text.strip()
                                    try:
                                        if "株" in extra_value:
                                            extra_value = int(extra_value.replace("株", "").replace(",", ""))
                                        elif "HK$" in extra_value:
                                            extra_value = float(extra_value.replace("HK$", "").replace(",", ""))
                                    except ValueError:
                                        pass
                                    
                                    # キーを正規化して保存
                                    extra_key = extra_key.replace(" ", "_").lower()
                                    price_data["data"]["trading_info"][extra_key] = extra_value
                                
                                # 売買気配をペアとして保存
                                level = sell_key.replace("売気配", "").replace(" ", "")
                                price_data["data"]["trading_info"][f"level_{level}"] = {
                                    "sell": sell_pair,
                                    "buy": buy_pair
                                }
                    except Exception as e:
                        logger.error(f"Error processing trading info row: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Error finding trading info table: {str(e)}")

            # 株価推移データを取得
            logger.info("Searching for price history table...")
            try:
                # 株価推移のテーブルを取得（週間騰落のセル）
                history_cell = self.driver.find_element(By.XPATH, "//td[text()='週間騰落(%)']")
                history_table = history_cell.find_element(By.XPATH, "./ancestor::table[1]")
                logger.info("Found price history table")
                rows = history_table.find_elements(By.TAG_NAME, "tr")
                headers = [h.text.strip() for h in rows[0].find_elements(By.TAG_NAME, "th")]
                
                for row in rows[1:]:  # ヘッダー行をスキップ
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        # 左側のデータ（基本情報）
                        left_key = cells[0].text.strip()
                        left_value = cells[1].text.strip()
                        
                        # 数値の処理（左側）
                        try:
                            if "千株" in left_key:
                                left_value = int(left_value)
                            elif "百万" in left_key:
                                left_value = float(left_value)
                            elif "HK$" in left_value:
                                left_value = float(left_value.replace("HK$", "").replace(",", ""))
                        except ValueError:
                            pass
                        
                        # 右側のデータ（騰落率など）
                        right_key = cells[2].text.strip() if len(cells) > 2 else None
                        right_value = cells[3].text.strip() if len(cells) > 3 else None
                        
                        # 数値の処理（右側）
                        if right_value and right_value != "—":
                            try:
                                if "%" in right_value:
                                    right_value = float(right_value.replace("%", "")) / 100
                                elif "倍" in right_value:
                                    right_value = float(right_value.replace("倍", ""))
                            except ValueError:
                                pass
                        
                        # キーを正規化
                        left_key = left_key.replace("(千株)", "").replace("(百万)", "").replace(" ", "_").lower()
                        if right_key:
                            right_key = right_key.replace("(%)", "").replace("(倍)", "").replace("(RMB)", "").replace(" ", "_").lower()
                        
                        # データを構造化して保存
                        row_data = {
                            "basic_info": {
                                left_key: left_value
                            }
                        }
                        if right_key and right_value:
                            row_data["market_info"] = {
                                right_key: right_value
                            }
                        
                        price_data["data"]["price_history"].append(row_data)
                    except Exception as e:
                        logger.error(f"Error processing price history row: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Error finding price history table: {str(e)}")

            return price_data

        except Exception as e:
            logger.error(f"Error fetching stock price for {ticker}: {str(e)}")
            return {"error": str(e)}

    def get_all_info(self, ticker: str) -> Dict[str, Any]:
        """全ての情報を取得"""
        try:
            self.setup_driver()

            all_data = {
                "ticker": ticker,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "financial_info": self.get_financial_info(ticker),
                "company_info": self.get_company_info(ticker),
                "stock_price": self.get_stock_price(ticker)
            }

            return all_data

        except Exception as e:
            logger.error(f"Error fetching all info for {ticker}: {str(e)}")
            return {"error": str(e)}

        finally:
            self.close_driver()

def save_to_json(data: Dict[str, Any], filename: str):
    """データをJSONファイルに保存"""
    filepath = os.path.join("data", "china_stocks", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved data to {filepath}")

def main():
    """メイン処理"""
    scraper = ChinaStockScraper()
    ticker = "02312"  # テスト用のティッカー
    
    try:
        data = scraper.get_all_info(ticker)
        save_to_json(data, f"{ticker}_data.json")
        logger.info(f"Successfully collected data for {ticker}")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()
