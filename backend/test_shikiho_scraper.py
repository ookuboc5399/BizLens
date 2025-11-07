#!/usr/bin/env python3
"""
四季報オンライン スクレイピングテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.shikiho_scraper import ShikihoScraper

def test_shikiho_scraper():
    """四季報オンラインスクレイピングをテスト"""
    ticker = "NVDA"
    
    print(f"Testing Shikiho scraper for: {ticker}")
    print("=" * 50)
    
    try:
        # スクレイパーを初期化
        scraper = ShikihoScraper()
        print("✅ Shikiho scraper initialized")
        
        # 企業情報を取得
        company_info = scraper.get_company_info(ticker)
        
        if not company_info:
            print("❌ Failed to get company info")
            return
        
        print("✅ Company info retrieved successfully")
        print(f"Company: {company_info.get('company_name', 'N/A')}")
        print(f"English Name: {company_info.get('english_name', 'N/A')}")
        print(f"Industry: {company_info.get('industry', 'N/A')}")
        print(f"Sector: {company_info.get('sector', 'N/A')}")
        print(f"Market Cap: {company_info.get('market_cap', 'N/A')}")
        print(f"Revenue: {company_info.get('revenue', 'N/A')}")
        print(f"Operating Income: {company_info.get('operating_income', 'N/A')}")
        print(f"Net Income: {company_info.get('net_income', 'N/A')}")
        print(f"PER: {company_info.get('per', 'N/A')}")
        print(f"PBR: {company_info.get('pbr', 'N/A')}")
        print(f"ROE: {company_info.get('roe', 'N/A')}")
        print(f"ROA: {company_info.get('roa', 'N/A')}")
        
        print("\n" + "=" * 50)
        print("FULL DATA:")
        print("=" * 50)
        
        for key, value in company_info.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_batch_scraping():
    """一括スクレイピングをテスト"""
    tickers = ["NVDA", "AAPL", "MSFT"]
    
    print(f"Testing batch scraping for: {tickers}")
    print("=" * 50)
    
    try:
        scraper = ShikihoScraper()
        results = scraper.batch_scrape_companies(tickers, delay=1.0)
        
        print(f"✅ Batch scraping completed: {len(results)} companies")
        
        for i, company in enumerate(results):
            print(f"\n--- Company {i+1} ---")
            print(f"Ticker: {company.get('ticker', 'N/A')}")
            print(f"Company: {company.get('company_name', 'N/A')}")
            print(f"Industry: {company.get('industry', 'N/A')}")
            print(f"Market Cap: {company.get('market_cap', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing single company scraping...")
    test_shikiho_scraper()
    
    print("\n" + "=" * 80 + "\n")
    
    print("Testing batch scraping...")
    test_batch_scraping()
