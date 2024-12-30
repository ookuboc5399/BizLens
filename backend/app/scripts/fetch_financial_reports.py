import os
import asyncio
from datetime import datetime, timedelta
import aiohttp
import logging
from bs4 import BeautifulSoup
from ..services.financial_report_service import FinancialReportService
from ..models.financial_report import FinancialReportCreate
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialReportCollector:
    def __init__(self):
        self.financial_report_service = FinancialReportService()
        self.session = None
        self.driver = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    async def close(self):
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()

    async def fetch_edinet_reports(self, company_id: str, ticker: str):
        """EDINETから決算資料を取得"""
        try:
            # EDINETのAPIエンドポイント
            base_url = "https://disclosure.edinet-fsa.go.jp/api/v1"
            
            # 直近1年分の書類を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # 書類一覧APIを呼び出し
            params = {
                "date": end_date.strftime("%Y-%m-%d"),
                "type": 2,  # 通期・四半期報告書等
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            
            async with self.session.get(f"{base_url}/documents.json", params=params) as response:
                if response.status != 200:
                    logger.error(f"EDINET API error: {response.status}")
                    return
                
                data = await response.json()
                
                for doc in data.get("results", []):
                    if doc.get("secCode") == ticker:
                        # 書類の詳細情報を取得
                        doc_id = doc["docID"]
                        
                        # PDFのURLを生成
                        pdf_url = f"{base_url}/documents/{doc_id}/pdf"
                        
                        # 決算期を解析
                        fiscal_info = self._parse_fiscal_info(doc["docDescription"])
                        
                        if fiscal_info:
                            report = FinancialReportCreate(
                                company_id=company_id,
                                fiscal_year=fiscal_info["year"],
                                quarter=fiscal_info["quarter"],
                                report_type="有価証券報告書",
                                file_url=pdf_url,
                                source="EDINET",
                                report_date=datetime.strptime(doc["submitDateTime"], "%Y-%m-%d %H:%M")
                            )
                            
                            await self.financial_report_service.create_report(report)
                            logger.info(f"Created EDINET report for {ticker}: {fiscal_info}")

        except Exception as e:
            logger.error(f"Error fetching EDINET reports for {ticker}: {str(e)}")

    async def fetch_tdnet_reports(self, company_id: str, ticker: str):
        """TDnetから決算資料を取得"""
        try:
            # TDnetのURLを構築
            url = f"https://www.release.tdnet.info/inbs/I_list_{ticker}.html"
            
            # Seleniumを使用してページを取得
            self.driver.get(url)
            
            # 決算短信のリンクを探す
            wait = WebDriverWait(self.driver, 10)
            links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            
            for link in links:
                text = link.text
                if "決算短信" in text:
                    href = link.get_attribute("href")
                    fiscal_info = self._parse_tdnet_title(text)
                    
                    if fiscal_info:
                        report = FinancialReportCreate(
                            company_id=company_id,
                            fiscal_year=fiscal_info["year"],
                            quarter=fiscal_info["quarter"],
                            report_type="決算短信",
                            file_url=href,
                            source="TDnet",
                            report_date=datetime.now()
                        )
                        
                        await self.financial_report_service.create_report(report)
                        logger.info(f"Created TDnet report for {ticker}: {fiscal_info}")

        except Exception as e:
            logger.error(f"Error fetching TDnet reports for {ticker}: {str(e)}")

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
                            report = FinancialReportCreate(
                                company_id=company_id,
                                fiscal_year=fiscal_info["year"],
                                quarter=fiscal_info["quarter"],
                                report_type="決算説明資料",
                                file_url=href,
                                source="企業ウェブサイト",
                                report_date=datetime.now()
                            )
                            
                            await self.financial_report_service.create_report(report)
                            logger.info(f"Created company website report for {ticker}: {fiscal_info}")

        except Exception as e:
            logger.error(f"Error fetching company website reports for {ticker}: {str(e)}")

    def _parse_fiscal_info(self, description: str) -> dict:
        """有価証券報告書の説明から決算期情報を抽出"""
        try:
            import re
            
            # 通期の場合
            annual_match = re.search(r"第(\d+)期\s*有価証券報告書", description)
            if annual_match:
                return {
                    "year": str(datetime.now().year),
                    "quarter": "4"
                }
            
            # 四半期の場合
            quarter_match = re.search(r"第(\d+)期第(\d)四半期", description)
            if quarter_match:
                return {
                    "year": str(datetime.now().year),
                    "quarter": quarter_match.group(2)
                }
            
            return None
        except Exception:
            return None

    def _parse_tdnet_title(self, title: str) -> dict:
        """TDnetのタイトルから決算期情報を抽出"""
        try:
            import re
            
            # 例: "2024年3月期 第2四半期決算短信"
            match = re.search(r"(\d{4})年.*?第(\d)四半期", title)
            if match:
                return {
                    "year": match.group(1),
                    "quarter": match.group(2)
                }
            
            # 通期の場合
            annual_match = re.search(r"(\d{4})年.*?決算短信", title)
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
    collector = FinancialReportCollector()
    await collector.initialize()
    
    try:
        # テスト用の企業コード
        test_companies = [
            {"id": "test1", "ticker": "7203", "website": "https://global.toyota/jp/"},
            {"id": "test2", "ticker": "6758", "website": "https://www.sony.co.jp/"},
            {"id": "test3", "ticker": "9984", "website": "https://group.softbank/"}
        ]
        
        for company in test_companies:
            logger.info(f"Fetching reports for {company['ticker']}")
            
            # 各ソースから決算資料を取得
            await collector.fetch_edinet_reports(company["id"], company["ticker"])
            await asyncio.sleep(1)  # APIレート制限を考慮
            
            await collector.fetch_tdnet_reports(company["id"], company["ticker"])
            await asyncio.sleep(1)
            
            await collector.fetch_company_website_reports(
                company["id"], 
                company["ticker"], 
                company["website"]
            )
            await asyncio.sleep(1)
            
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
