import asyncio
import logging
import sys
import os

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.financial_report_service import FinancialReportService
from app.scripts.fetch_financial_reports import FinancialReportCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fetch_reports():
    """決算資料取得のテスト"""
    collector = None
    try:
        # コレクターの初期化
        collector = FinancialReportCollector()
        await collector.initialize()
        
        # テスト用の企業
        test_companies = [
            {
                "ticker": "7203",
                "company_name": "トヨタ自動車",
                "website": "https://global.toyota/jp/"
            },
            {
                "ticker": "6758",
                "company_name": "ソニーグループ",
                "website": "https://www.sony.co.jp/"
            },
            {
                "ticker": "9984",
                "company_name": "ソフトバンクグループ",
                "website": "https://group.softbank/"
            }
        ]
        
        total = len(test_companies)
        logger.info(f"Testing with {total} companies")
        
        # 企業ごとに決算資料を取得
        for i, company in enumerate(test_companies, 1):
            try:
                logger.info(f"Processing {i}/{total}: {company['company_name']} ({company['ticker']})")
                
                # EDINETから取得
                logger.info("Fetching from EDINET...")
                await collector.fetch_edinet_reports(company['ticker'], company['ticker'])
                await asyncio.sleep(1)
                
                # TDnetから取得
                logger.info("Fetching from TDnet...")
                await collector.fetch_tdnet_reports(company['ticker'], company['ticker'])
                await asyncio.sleep(1)
                
                # 企業サイトから取得
                if company.get('website'):
                    logger.info("Fetching from company website...")
                    await collector.fetch_company_website_reports(
                        company['ticker'],
                        company['ticker'],
                        company['website']
                    )
                    await asyncio.sleep(1)
                
                logger.info(f"Completed processing {company['company_name']}")
                
            except Exception as e:
                logger.error(f"Error processing {company['ticker']}: {str(e)}")
        
        # 保存された決算資料を確認
        logger.info("Verifying saved reports...")
        report_service = FinancialReportService()
        for company in test_companies:
            reports = await report_service.get_company_reports(company['ticker'])
            logger.info(f"Found {len(reports)} reports for {company['company_name']}")
            
            # 各レポートの詳細を表示
            for report in reports:
                logger.info(f"- {report.fiscal_year}年度 第{report.quarter}四半期 "
                          f"({report.report_type}) from {report.source}")
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
        
    finally:
        if collector:
            await collector.close()

if __name__ == "__main__":
    asyncio.run(test_fetch_reports())
