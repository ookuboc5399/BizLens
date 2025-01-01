import os
import asyncio
from datetime import datetime, timedelta, timezone
import aiohttp
import logging
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.bigquery_service import BigQueryService
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialReportCollector:
    def __init__(self):
        self.bigquery_service = BigQueryService()
        self.session = None
        self.driver = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
        # Chromeオプションの設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--lang=ja-JP')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        })
        
        try:
            # ChromeDriverのインストールと設定
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver installed at: {driver_path}")
            
            # Serviceの設定
            service = Service(executable_path=driver_path)
            
            # WebDriverの初期化
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # ブラウザの設定
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            self.driver.implicitly_wait(10)
            self.driver.set_window_size(1920, 1080)
            
            # JavaScriptを実行してwebdriverフラグを削除
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome browser initialized successfully")
            
        except WebDriverException as e:
            logger.error(f"WebDriver error: {str(e)}")
            if hasattr(e, 'msg'):
                logger.error(f"Error message: {e.msg}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Chrome browser: {str(e)}")
            if hasattr(e, '__cause__'):
                logger.error(f"Cause: {e.__cause__}")
            raise
        
    async def close(self):
        if self.session:
            await self.session.close()
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

    async def fetch_all_companies(self):
        """BigQueryから全企業の情報を取得"""
        query = f"""
        SELECT DISTINCT ticker, company_name, website
        FROM `{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.{self.bigquery_service.table}`
        ORDER BY ticker
        """
        results = self.bigquery_service.query(query)
        return [dict(row) for row in results]

    async def fetch_edinet_reports(self, company_id: str, ticker: str):
        """EDINETから決算資料を取得"""
        try:
            # まずAPIを試す
            success = await self._fetch_edinet_api(company_id, ticker)
            
            # APIが失敗した場合、ウェブスクレイピングを試みる
            if not success:
                logger.info(f"API failed for {ticker}, trying web scraping...")
                await self._fetch_edinet_web(company_id, ticker)
                
        except Exception as e:
            logger.error(f"Error fetching EDINET reports for {ticker}: {str(e)}")
            raise

    async def _fetch_edinet_api(self, company_id: str, ticker: str) -> bool:
        """EDINETのAPIを使用して資料を取得"""
        try:
            base_url = "https://disclosure.edinet-fsa.go.jp/api/v1"
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            
            # 直近1年分の書類を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            params = {
                "date": end_date.strftime("%Y-%m-%d"),
                "type": 2,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            
            async with self.session.get(
                f"{base_url}/documents.json",
                params=params,
                headers=headers,
                ssl=False
            ) as response:
                if response.status != 200:
                    logger.error(f"EDINET API error: {response.status}")
                    return False
                
                data = await response.json()
                success = False
                
                for doc in data.get("results", []):
                    if doc.get("secCode") == ticker:
                        doc_id = doc["docID"]
                        pdf_url = f"{base_url}/documents/{doc_id}/pdf"
                        
                        # PDFが取得可能か確認
                        async with self.session.head(pdf_url, headers=headers, ssl=False) as pdf_response:
                            if pdf_response.status != 200:
                                continue
                        
                        fiscal_info = self._parse_fiscal_info(doc["docDescription"])
                        if fiscal_info:
                            await self._save_report(
                                company_id=company_id,
                                fiscal_year=fiscal_info["year"],
                                quarter=fiscal_info["quarter"],
                                report_type="有価証券報告書",
                                file_url=pdf_url,
                                source="EDINET",
                                report_date=datetime.strptime(doc["submitDateTime"], "%Y-%m-%d %H:%M")
                            )
                            success = True
                
                return success
                
        except Exception as e:
            logger.error(f"Error in EDINET API: {str(e)}")
            return False

    async def _fetch_edinet_web(self, company_id: str, ticker: str):
        """EDINETのウェブページから資料を取得"""
        try:
            url = "https://disclosure2.edinet-fsa.go.jp/WEEE0030.aspx"
            
            # Seleniumを使用してページを取得
            self.driver.get(url)
            logger.info(f"Accessed EDINET search page for {ticker}")
            
            # 証券コードを入力
            wait = WebDriverWait(self.driver, 20)
            code_input = wait.until(EC.presence_of_element_located((By.ID, "txtStockCode")))
            code_input.clear()
            code_input.send_keys(ticker)
            logger.info(f"Input ticker: {ticker}")
            
            try:
                # 検索ボタンをクリック
                search_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSearch")))
                self.driver.execute_script("arguments[0].click();", search_button)
                logger.info("Clicked search button")
            except Exception as e:
                logger.error(f"Error clicking search button: {str(e)}")
                # スクリーンショットを保存して状態を確認
                self.driver.save_screenshot(f"edinet_error_{ticker}_search.png")
                # ページソースも保存
                with open(f"edinet_error_{ticker}_search.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise
            
            # 検索結果を待機
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            logger.info("Found results table")
            
            # 検索結果のテーブルを取得
            table = self.driver.find_element(By.TAG_NAME, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # ヘッダー行をスキップ
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:  # 必要なセルの数を確認
                    doc_link = cells[1].find_element(By.TAG_NAME, "a")  # 書類名列のリンク
                    doc_text = doc_link.text
                    if "有価証券報告書" in doc_text or "四半期報告書" in doc_text:
                        submit_date = cells[0].text.strip()  # 提出日列
                        pdf_link = cells[3].find_element(By.CSS_SELECTOR, "a[href$='.pdf']")  # PDF列のリンク
                        href = pdf_link.get_attribute("href")
                        
                        fiscal_info = self._parse_fiscal_info(doc_text)
                        if fiscal_info:
                            report_type = "有価証券報告書" if "有価証券報告書" in doc_text else "四半期報告書"
                            await self._save_report(
                                company_id=company_id,
                                fiscal_year=fiscal_info["year"],
                                quarter=fiscal_info["quarter"],
                                report_type=report_type,
                                file_url=href,
                                source="EDINET",
                                report_date=datetime.strptime(submit_date, "%Y/%m/%d")
                            )
                            logger.info(f"Found and saved report for {ticker}")
                            
        except Exception as e:
            logger.error(f"Error in EDINET web scraping: {str(e)}")
            raise

    async def _save_report(self, company_id: str, fiscal_year: str, quarter: str, 
                          report_type: str, file_url: str, source: str, report_date: datetime):
        """決算資料をBigQueryに保存"""
        report_data = {
            "company_id": company_id,
            "fiscal_year": fiscal_year,
            "quarter": quarter,
            "report_type": report_type,
            "file_url": file_url,
            "source": source,
            "report_date": report_date.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        table_id = f"{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.financial_reports"
        errors = self.bigquery_service.client.insert_rows_json(table_id, [report_data])
        if errors:
            logger.error(f"Error inserting rows: {errors}")
            raise Exception(f"Failed to insert rows: {errors}")
        logger.info(f"Created {source} report for {company_id}: {fiscal_year}Q{quarter}")

    async def fetch_tdnet_reports(self, company_id: str, ticker: str):
        """TDnetから決算資料を取得"""
        try:
            # TDnetのトップページにアクセス
            url = "https://www.release.tdnet.info/index.html"
            
            # Seleniumを使用してページを取得
            self.driver.get(url)
            await asyncio.sleep(2)  # ページの読み込みを待つ
            logger.info(f"Accessed TDnet page for {ticker}")
            
            try:
                # 検索フォームに証券コードを入力
                wait = WebDriverWait(self.driver, 20)
                search_input = wait.until(EC.presence_of_element_located((By.ID, "qk")))
                search_input.clear()
                await asyncio.sleep(1)
                search_input.send_keys(ticker)
                logger.info(f"Input ticker {ticker} to search form")
                
                # 検索ボタンをクリック
                search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
                search_button.click()
                await asyncio.sleep(2)
                logger.info("Clicked search button")
                
                # 検索結果を待機
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "list-table")))
                logger.info("Found results table")
                
            except Exception as e:
                logger.error(f"Error in TDnet search process: {str(e)}")
                # スクリーンショットを保存
                self.driver.save_screenshot(f"tdnet_error_{ticker}_search.png")
                raise
            
            try:
                # 検索結果のテーブルを取得
                table = self.driver.find_element(By.CLASS_NAME, "list-table")
                rows = table.find_elements(By.TAG_NAME, "tr")
                logger.info(f"Found {len(rows)-1} results for {ticker}")  # ヘッダー行を除く
            
                found_reports = 0
                for row in rows[1:]:  # ヘッダー行をスキップ
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:  # 日付、時間、タイトル、PDFリンクのセルがある
                            date_str = cells[0].text.strip()  # 日付
                            time_str = cells[1].text.strip()  # 時間
                            title_cell = cells[2]
                            
                            # タイトルとPDFリンクを取得
                            title_link = title_cell.find_element(By.TAG_NAME, "a")
                            text = title_link.text
                            
                            # PDFリンクを探す（より詳細なログ出力を追加）
                            logger.info(f"Processing title: {text}")
                            pdf_links = title_cell.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
                            if not pdf_links:
                                logger.info(f"No PDF links found for: {text}")
                                continue
                    
                            href = pdf_links[0].get_attribute("href")
                            logger.info(f"Found PDF link: {href}")
                            fiscal_info = None
                            report_type = None
                            
                            # タイトルの解析（より詳細なログ出力を追加）
                            if "決算短信" in text:
                                fiscal_info = self._parse_tdnet_title(text)
                                report_type = "決算短信"
                                logger.info(f"Detected 決算短信: {text}")
                            # 決算説明資料の場合（検出条件を拡充）
                            elif any(keyword in text for keyword in ["決算説明資料", "決算補足資料", "決算参考資料"]):
                                fiscal_info = self._parse_tdnet_title(text)
                                report_type = "決算説明資料"
                                logger.info(f"Detected 決算説明資料: {text}")
                                
                            if fiscal_info and report_type:
                                # 日付と時間を組み合わせて datetime オブジェクトを作成
                                report_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                                
                                await self._save_report(
                                    company_id=company_id,
                                    fiscal_year=fiscal_info["year"],
                                    quarter=fiscal_info["quarter"],
                                    report_type=report_type,
                                    file_url=href,
                                    source="TDnet",
                                    report_date=report_datetime
                                )
                                found_reports += 1
                                logger.info(f"Saved {report_type} for {ticker}: {fiscal_info}")
                                
                    except Exception as e:
                        logger.error(f"Error processing row for {ticker}: {str(e)}")
                        continue
                        
                logger.info(f"Successfully processed {found_reports} reports for {ticker}")
                
            except Exception as e:
                logger.error(f"Error processing TDnet results for {ticker}: {str(e)}")
                raise
                    

        except Exception as e:
            logger.error(f"Error fetching TDnet reports for {ticker}: {str(e)}")
            # スクリーンショットを保存して状態を確認
            self.driver.save_screenshot(f"tdnet_error_{ticker}_final.png")
            raise

    async def fetch_company_website_reports(self, company_id: str, ticker: str, website: str):
        """企業の公式ウェブサイトから決算資料を取得"""
        try:
            if not website:
                return

            # Seleniumを使用してページを取得
            self.driver.get(website)
            
            # IR情報や決算情報へのリンクを探す
            wait = WebDriverWait(self.driver, 10)
            links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            
            ir_keywords = ["IR情報", "投資家情報", "決算情報", "財務情報"]
            ir_link = None
            
            for link in links:
                text = link.text
                if any(keyword in text for keyword in ir_keywords):
                    ir_link = link
                    break
            
            if ir_link:
                ir_link.click()
                
                # 決算資料へのリンクを探す
                wait = WebDriverWait(self.driver, 10)
                doc_links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                
                for link in doc_links:
                    text = link.text
                    if "決算" in text and ("資料" in text or "説明" in text):
                        href = link.get_attribute("href")
                        fiscal_info = self._parse_company_website_title(text)
                        
                        if fiscal_info:
                            # financial_reportsテーブルにデータを挿入
                            report_data = {
                                "company_id": company_id,
                                "fiscal_year": fiscal_info["year"],
                                "quarter": fiscal_info["quarter"],
                                "report_type": "決算説明資料",
                                "file_url": href,
                                "source": "企業ウェブサイト",
                                "report_date": datetime.now(timezone.utc).isoformat(),
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                            
                            table_id = f"{self.bigquery_service.project_id}.{self.bigquery_service.dataset}.financial_reports"
                            errors = self.bigquery_service.client.insert_rows_json(table_id, [report_data])
                            if errors:
                                logger.error(f"Error inserting rows: {errors}")
                                raise Exception(f"Failed to insert rows: {errors}")
                            logger.info(f"Created company website report for {ticker}: {fiscal_info}")

        except Exception as e:
            logger.error(f"Error fetching company website reports for {ticker}: {str(e)}")
            raise

    def _parse_fiscal_info(self, description: str) -> dict:
        """有価証券報告書の説明から決算期情報を抽出"""
        try:
            import re
            
            # 年度を抽出（例：2024年3月期）
            year_match = re.search(r"(\d{4})年", description)
            if not year_match:
                return None
            
            year = year_match.group(1)
            
            # 四半期の場合
            quarter_match = re.search(r"第(\d)四半期", description)
            if quarter_match:
                return {
                    "year": year,
                    "quarter": quarter_match.group(1)
                }
            
            # 通期の場合
            if "有価証券報告書" in description and "四半期" not in description:
                return {
                    "year": year,
                    "quarter": "4"
                }
            
            return None
        except Exception:
            return None

    def _parse_tdnet_title(self, title: str) -> dict:
        """TDnetのタイトルから決算期情報を抽出"""
        try:
            import re
            
            # 四半期の場合（決算短信、決算説明資料など）
            # 例: "2024年3月期 第2四半期決算短信" or "2024年3月期 第2四半期決算説明資料"
            quarter_match = re.search(r"(\d{4})年.*?第(\d)四半期", title)
            if quarter_match:
                return {
                    "year": quarter_match.group(1),
                    "quarter": quarter_match.group(2)
                }
            
            # 通期の場合（決算短信、決算説明資料など）
            # 例: "2024年3月期 決算短信" or "2024年3月期 決算説明資料"
            annual_match = re.search(r"(\d{4})年.*?期.*?(決算|通期)", title)
            if annual_match:
                return {
                    "year": annual_match.group(1),
                    "quarter": "4"
                }
            
            return None
        except Exception:
            return None

    def _parse_company_website_title(self, title: str) -> dict:
        """企業ウェブサイトのタイトルから決算期情報を抽出"""
        try:
            import re
            
            # 四半期の場合
            quarter_match = re.search(r"(\d{4})年.*?第(\d)四半期", title)
            if quarter_match:
                return {
                    "year": quarter_match.group(1),
                    "quarter": quarter_match.group(2)
                }
            
            # 通期の場合
            annual_match = re.search(r"(\d{4})年.*?期末|通期", title)
            if annual_match:
                return {
                    "year": annual_match.group(1),
                    "quarter": "4"
                }
            
            return None
        except Exception:
            return None

async def main():
    collector = None
    try:
        collector = FinancialReportCollector()
        await collector.initialize()
        
        # BigQueryから全企業の情報を取得
        companies = await collector.fetch_all_companies()
        total = len(companies)
        logger.info(f"Total companies to process: {total}")
        
        for i, company in enumerate(companies, 1):
            try:
                logger.info(f"Processing {i}/{total}: {company['company_name']} ({company['ticker']})")
                
                # TDnetから取得
                logger.info(f"Fetching from TDnet for {company['ticker']}")
                await collector.fetch_tdnet_reports(company["ticker"], company["ticker"])
                await asyncio.sleep(2)  # 待機時間を増やす
                
                # 企業サイトから取得
                if company.get("website"):
                    logger.info(f"Fetching from company website for {company['ticker']}")
                    await collector.fetch_company_website_reports(
                        company["ticker"], 
                        company["ticker"], 
                        company["website"]
                    )
                    await asyncio.sleep(1)
                
                logger.info(f"Completed processing {company['company_name']}")
                
            except Exception as e:
                logger.error(f"Error processing company {company['ticker']}: {str(e)}")
                continue  # エラーが発生しても次の企業の処理を続行
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
        
    finally:
        if collector:
            await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
