import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
import aiohttp
import logging
from bs4 import BeautifulSoup
import re

# backendディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.bigquery_service import BigQueryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialReportCollector:
    def __init__(self):
        self.bigquery_service = BigQueryService()
        self.session = None

    async def initialize(self):
        """HTTPセッションの初期化"""
        self.session = aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })
        
    async def close(self):
        """セッションのクローズ"""
        if self.session:
            await self.session.close()

    async def fetch_tdnet_reports(self):
        """TDnetから決算資料を取得"""
        try:
            # TDnetのベースURL
            base_url = "https://www.release.tdnet.info"
            
            # 日付リストの設定（2024/12/02から2025/01/01まで）
            start_date = datetime(2024, 12, 2)
            end_date = datetime(2025, 1, 1)
            dates = []
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date.strftime('%Y%m%d'))
                current_date += timedelta(days=1)
            
            found_reports = 0
            
            for date in dates:
                list_url = f"{base_url}/inbs/I_list_{date}.html"
                logger.info(f"Accessing TDnet list page for {date}: {list_url}")
                
                try:
                    async with self.session.get(list_url, timeout=30) as response:
                        if response.status != 200:
                            logger.error(f"TDnet error for {date}: {response.status}")
                            continue
                        
                        html = await response.text(encoding='utf-8')
                        logger.debug(f"Response HTML for {date}: {html[:1000]}")  # デバッグ用に最初の1000文字を出力
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout while accessing TDnet for {date}")
                    continue
                except aiohttp.ClientError as e:
                    logger.error(f"Network error while accessing TDnet for {date}: {str(e)}")
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # 検索結果のテーブルを探す
                main_table = soup.find('table', class_='list-table')
                if not main_table:
                    logger.info(f"No results table found for {date}")
                    continue
                    
                for row in main_table.find_all('tr')[1:]:  # ヘッダー行をスキップ
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 5:  # 日付、時間、コード、会社名、タイトルの5列が必要
                            continue
                            
                        # 証券コード、会社名、日付、時間を取得
                        code = cells[2].text.strip()
                        company_name = cells[3].text.strip()
                        date_str = cells[0].text.strip()
                        time_str = cells[1].text.strip()
                        
                        logger.info(f"Processing: {company_name} ({code})")
                        
                        # タイトルとPDFリンクを取得
                        title_cell = cells[4]
                        title_link = title_cell.find('a')
                        if not title_link:
                            continue
                        
                        text = title_link.text.strip()
                        if '決算説明資料' not in text:  # 決算説明資料のみを対象とする
                            continue
                            
                        href = title_link.get('href')
                        if not href:
                            continue
                        
                        # PDFのURLを構築
                        if not href.startswith('http'):
                            href = f"{base_url}/inbs/{href.lstrip('/')}"
                        
                        logger.info(f"Found PDF for {company_name} ({code}): {text}")
                        
                        # タイトルから決算期情報を抽出
                        fiscal_info = self._parse_tdnet_title(text)
                        if fiscal_info:
                            # 日付と時間を組み合わせて datetime オブジェクトを作成
                            report_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                            
                            await self._save_report(
                                company_id=code,  # 証券コードをcompany_idとして使用
                                company_name=company_name,  # 会社名を追加
                                fiscal_year=fiscal_info["year"],
                                quarter=fiscal_info["quarter"],
                                report_type="決算説明資料",
                                file_url=href,
                                source="TDnet",
                                report_date=report_datetime
                            )
                            found_reports += 1
                            logger.info(f"Saved 決算説明資料 for {company_name} ({code}): {fiscal_info}")
                    
                    except Exception as e:
                        logger.error(f"Error processing row: {str(e)}")
                        continue
                
                await asyncio.sleep(1)  # APIレート制限を考慮
            
            logger.info(f"Successfully processed {found_reports} reports")
            
        except Exception as e:
            logger.error(f"Error fetching TDnet reports: {str(e)}")

    async def _save_report(self, company_id: str, company_name: str, fiscal_year: str, quarter: str,
                          report_type: str, file_url: str, source: str, report_date: datetime):
        """決算資料をBigQueryに保存"""
        report_data = {
            "company_id": company_id,
            "company_name": company_name,
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
        logger.info(f"Created {source} report for {company_name} ({company_id}): {fiscal_year}Q{quarter}")

    def _parse_tdnet_title(self, title: str) -> dict:
        """TDnetのタイトルから決算期情報を抽出"""
        try:
            # 四半期の場合（決算短信、決算説明資料など）
            quarter_match = re.search(r"(\d{4})年.*?第(\d)四半期", title)
            if quarter_match:
                return {
                    "year": quarter_match.group(1),
                    "quarter": quarter_match.group(2)
                }
            
            # 通期の場合（決算短信、決算説明資料など）
            annual_match = re.search(r"(\d{4})年.*?期.*?(決算|通期)", title)
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
        
        # TDnetから決算説明資料を取得
        logger.info("Fetching financial reports from TDnet")
        await collector.fetch_tdnet_reports()
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
        
    finally:
        if collector:
            await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
