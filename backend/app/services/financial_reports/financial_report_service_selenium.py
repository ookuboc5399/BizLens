import os
import asyncio
from datetime import datetime, timezone, timedelta
import logging
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, NoSuchFrameException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ログファイルのパスを設定
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'tdnet_scraping.log')

# ファイルハンドラーの追加
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# コンソールハンドラーの追加
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

class TDNetScraper:
    def __init__(self):
        self.driver = None
        logger.info("TDNetScraper initialized")

    def initialize(self):
        """Chromeドライバーの初期化"""
        if not self.driver:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--lang=ja')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            logger.info("Chrome driver initialized")

    def close(self):
        """ドライバーのクローズ"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.debug("Chrome driver closed")

    async def _wait_for_page_load(self, timeout=20):
        """ページの読み込みを待機"""
        try:
            # DOMの準備完了を待機
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            
            # スクリーンショットを保存（デバッグ用）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = os.path.join(log_dir, f'tdnet_page_{timestamp}.png')
            self.driver.save_screenshot(screenshot_path)
            logger.debug(f"Saved screenshot to {screenshot_path}")
            
            # ページソースをログに出力（デバッグ用）
            logger.debug(f"Page source: {self.driver.page_source[:1000]}...")
            
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return False

    async def _switch_to_frame(self, frame_index, timeout=10):
        """指定されたフレームに切り替え"""
        try:
            # デフォルトのコンテンツに戻る
            self.driver.switch_to.default_content()
            await asyncio.sleep(1)
            
            # フレームが存在するまで待機
            WebDriverWait(self.driver, timeout).until(
                EC.frame_to_be_available_and_switch_to_it(frame_index)
            )
            logger.info(f"Switched to frame {frame_index}")
            return True
            
        except (TimeoutException, NoSuchFrameException) as e:
            logger.error(f"Error switching to frame {frame_index}: {str(e)}")
            return False

    async def _set_search_criteria(self, start_date, end_date):
        """メインサイトの検索条件を設定"""
        try:
            # 最初のiframeに切り替え
            if not await self._switch_to_frame(0):
                return False
            
            # 日付選択
            date_dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "t0"))
            )
            date_dropdown.click()
            await asyncio.sleep(1)
            
            # 最も古い日付を選択
            select = Select(date_dropdown)
            options = select.options
            if options:
                last_option = options[-1]
                select.select_by_visible_text(last_option.text)
                await asyncio.sleep(1)
                logger.info(f"Selected date: {last_option.text}")
            
            # 検索フォームを探す
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "freewordtxt"))
            )
            
            # 既存の値をクリア
            search_input.clear()
            await asyncio.sleep(1)
            
            # 検索キーワードを設定
            search_input.send_keys("決算説明資料")
            await asyncio.sleep(1)
            logger.info("Set search keyword")
            
            # 検索ボタンをクリック
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#searchbtn > img"))
            )
            search_button.click()
            await asyncio.sleep(2)
            logger.info("Clicked search button")
            
            # 検索結果のページが読み込まれるまで待機
            if not await self._wait_for_page_load():
                return False
            
            # 結果のiframeに切り替え
            if not await self._switch_to_frame(0):
                return False
            
            # テーブルが表示されるまで待機
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr.odd, tr.even"))
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting search criteria: {str(e)}")
            return False

    async def _process_page(self, start_date, end_date, reports):
        """ページ内の決算資料を処理"""
        try:
            # テーブルの行を探す
            rows = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.odd, tr.even"))
            )
            if not rows:
                logger.error("No rows found in the table")
                return False
            
            processed_rows = 0
            found_in_range = False
            
            for row in rows:
                try:
                    # 証券コード、会社名、日付、時間を取得
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:
                        continue
                    
                    code = cells[2].text.strip()
                    company_name = cells[3].text.strip()
                    date_str = cells[0].text.strip()
                    time_str = cells[1].text.strip()
                    
                    # 日付をパース
                    try:
                        row_date = datetime.strptime(date_str, "%Y/%m/%d").date()
                        found_in_range = True
                    except ValueError:
                        logger.error(f"Invalid date format: {date_str}")
                        continue
                    
                    logger.debug("Processing row: %s (%s) at %s %s", company_name, code, date_str, time_str)
                    
                    # タイトルとPDFリンクを取得
                    title_cell = cells[4]
                    title_link = title_cell.find_element(By.TAG_NAME, "a")
                    if not title_link:
                        logger.debug("No link found for %s (%s)", company_name, code)
                        continue
                    
                    text = title_link.text.strip()
                    if '決算説明資料' not in text:
                        logger.debug("Skipping non-financial report: %s", text)
                        continue
                    
                    href = title_link.get_attribute("href")
                    if not href:
                        logger.debug("No href found for %s (%s)", company_name, code)
                        continue
                    
                    # PDFのURLを構築
                    if not href.startswith('http'):
                        href = f"https://www.release.tdnet.info{href}"
                    
                    logger.info("Found PDF: %s for %s (%s)", href, company_name, code)
                    
                    # タイトルから決算期情報を抽出
                    fiscal_info = self._parse_tdnet_title(text)
                    if fiscal_info:
                        report_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                        
                        report = {
                            "company_id": code,
                            "company_name": company_name,
                            "fiscal_year": fiscal_info["year"],
                            "quarter": fiscal_info["quarter"],
                            "report_type": "決算説明資料",
                            "file_url": href,
                            "source": "TDnet",
                            "report_date": report_datetime
                        }
                        reports.append(report)
                        logger.info("Found report: %s (%s) %sQ%s", company_name, code, fiscal_info["year"], fiscal_info["quarter"])
                
                except Exception as e:
                    logger.error("Error processing row: %s", str(e), exc_info=True)
                    continue
                
                processed_rows += 1
                if processed_rows % 10 == 0:
                    await asyncio.sleep(1)
            
            return found_in_range
            
        except Exception as e:
            logger.error(f"Error processing page: {str(e)}", exc_info=True)
            return False

    async def _find_next_button(self):
        """次のページボタンを探す"""
        try:
            # 次へボタンを探す
            next_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '次へ')]"))
            )
            if next_button and next_button.is_displayed() and next_button.is_enabled():
                return next_button
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding next button: {str(e)}")
            return None

    async def fetch_reports(self, start_date=None, end_date=None):
        """TDnetから決算資料を取得"""
        try:
            self.initialize()
            
            # TDnetのベースURL
            base_url = "https://www.release.tdnet.info/index.html"
            logger.info("Starting TDnet scraping with URL: %s", base_url)
            
            reports = []
            page_number = 1
            max_retries = 3
            
            # メインページにアクセス
            for retry in range(max_retries):
                try:
                    self.driver.get(base_url)
                    logger.info("Accessed TDnet main page")
                    
                    if await self._wait_for_page_load():
                        break
                    
                    if retry < max_retries - 1:
                        logger.warning(f"Retrying page load (attempt {retry + 2}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        return {"status": "error", "message": "Failed to load initial page"}
                        
                except Exception as e:
                    if retry < max_retries - 1:
                        logger.warning(f"Error accessing page (attempt {retry + 1}/{max_retries}): {str(e)}")
                        await asyncio.sleep(2)
                    else:
                        raise
            
            # 検索条件を設定
            if not await self._set_search_criteria(start_date, end_date):
                logger.warning("Failed to set search criteria")
                return {"status": "error", "message": "Failed to set search criteria"}
            
            while True:
                logger.info(f"Processing page {page_number}")
                
                # 現在のページを処理
                if not await self._process_page(start_date, end_date, reports):
                    logger.info("No more data in date range")
                    break
                
                # 次のページがあるか確認
                next_button = await self._find_next_button()
                if not next_button:
                    logger.info("No more pages available")
                    break
                
                # 次のページへ移動
                next_button.click()
                await asyncio.sleep(2)
                
                # 新しいページが読み込まれるまで待機
                if not await self._wait_for_page_load():
                    logger.error("Failed to load next page")
                    break
                
                page_number += 1
            
            if reports:
                logger.info("Successfully found %d reports", len(reports))
                return {"status": "success", "reports": reports}
            
            return {"status": "error", "message": "No reports found"}
            
        except Exception as e:
            logger.error("Error fetching TDnet reports: %s", str(e))
            return {"status": "error", "message": str(e)}
        finally:
            self.close()

    def _parse_tdnet_title(self, title: str) -> dict:
        """TDnetのタイトルから決算期情報を抽出"""
        try:
            logger.debug("Parsing title: %s", title)
            
            # 四半期の場合（決算短信、決算説明資料など）
            quarter_match = re.search(r"(\d{4})年.*?第(\d)四半期", title)
            if quarter_match:
                result = {
                    "year": quarter_match.group(1),
                    "quarter": quarter_match.group(2)
                }
                logger.debug("Parsed quarterly result: %s", result)
                return result
            
            # 通期の場合（決算短信、決算説明資料など）
            annual_match = re.search(r"(\d{4})年.*?期.*?(決算|通期)", title)
            if annual_match:
                result = {
                    "year": annual_match.group(1),
                    "quarter": "4"
                }
                logger.debug("Parsed annual result: %s", result)
                return result
            
            logger.debug("No fiscal info found in title")
            return None
            
        except Exception as e:
            logger.error("Error parsing title: %s", str(e))
            return None
