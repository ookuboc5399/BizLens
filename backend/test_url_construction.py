#!/usr/bin/env python3
"""
SEC EDGAR URL構築のテスト
"""

import requests

def test_url_construction():
    print("=== SEC EDGAR URL構築テスト ===")
    
    # Apple Inc.の実際のデータを使用
    accession_number = "0000320193-24-000123"
    primary_document = "aapl-20240928.htm"
    cik = "0000320193"
    
    print(f"アクセッション番号: {accession_number}")
    print(f"プライマリドキュメント: {primary_document}")
    print(f"CIK: {cik}")
    
    # 異なるURL構築方法をテスト
    methods = [
        {
            "name": "Method 1: CIK with leading zeros",
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/24-000123/{primary_document}"
        },
        {
            "name": "Method 2: CIK without leading zeros",
            "url": f"https://www.sec.gov/Archives/edgar/data/320193/24-000123/{primary_document}"
        },
        {
            "name": "Method 3: Full accession path",
            "url": f"https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/{primary_document}"
        },
        {
            "name": "Method 4: Alternative path format",
            "url": f"https://www.sec.gov/Archives/edgar/data/320193/24-000123/{primary_document}"
        }
    ]
    
    headers = {
        "User-Agent": "BizLens Financial Data Collector (contact@example.com)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    for method in methods:
        print(f"\n--- {method['name']} ---")
        print(f"URL: {method['url']}")
        
        try:
            response = requests.get(method['url'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Success! Content length: {len(response.content)} bytes")
                print(f"Content type: {response.headers.get('content-type', 'Unknown')}")
                break
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_url_construction()
