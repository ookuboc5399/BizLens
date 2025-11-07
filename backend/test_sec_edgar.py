#!/usr/bin/env python3
"""
SEC EDGAR API機能のテスト
"""

import requests
import json

def test_sec_edgar():
    print("=== SEC EDGAR API機能テスト ===")
    
    base_url = "http://localhost:8000"
    
    # 1. 企業検索のテスト
    print("\n--- 企業検索テスト ---")
    try:
        response = requests.get(f"{base_url}/api/admin/sec-edgar/search-company?company_name=Apple Inc.")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 企業検索成功")
            print(f"   検索クエリ: {data.get('search_query')}")
            print(f"   見つかった企業数: {len(data.get('companies', []))}")
            for company in data.get('companies', []):
                print(f"   - {company.get('name')} (CIK: {company.get('cik')})")
        else:
            print(f"❌ 企業検索失敗: HTTP {response.status_code}")
            print(f"   エラー: {response.text}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    # 2. 単一企業の決算資料収集テスト
    print("\n--- 単一企業決算資料収集テスト ---")
    try:
        response = requests.post(f"{base_url}/api/admin/sec-edgar/collect-reports", 
                               json={"company_name": "Apple Inc."})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 決算資料収集成功")
            print(f"   企業名: {data.get('company_name')}")
            print(f"   CIK: {data.get('cik')}")
            print(f"   提出日: {data.get('filing_date')}")
            print(f"   報告日: {data.get('report_date')}")
            print(f"   ドキュメント名: {data.get('document_name')}")
            print(f"   ファイルサイズ: {data.get('document_size')} bytes")
        else:
            print(f"❌ 決算資料収集失敗: HTTP {response.status_code}")
            print(f"   エラー: {response.text}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    # 3. 一括決算資料収集テスト
    print("\n--- 一括決算資料収集テスト ---")
    try:
        company_names = ["Apple Inc.", "Microsoft Corporation", "Amazon.com Inc."]
        response = requests.post(f"{base_url}/api/admin/sec-edgar/batch-collect", 
                               json={"company_names": company_names})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 一括決算資料収集成功")
            print(f"   メッセージ: {data.get('message')}")
            print(f"   処理件数: {data.get('total_processed')}")
            print(f"   成功件数: {len(data.get('successful_companies', []))}")
            print(f"   失敗件数: {len(data.get('failed_companies', []))}")
            
            if data.get('successful_companies'):
                print("   成功した企業:")
                for company in data.get('successful_companies', []):
                    print(f"     - {company.get('company_name')} ({company.get('document_name')})")
            
            if data.get('failed_companies'):
                print("   失敗した企業:")
                for company in data.get('failed_companies', []):
                    print(f"     - {company.get('company_name')}: {company.get('error')}")
        else:
            print(f"❌ 一括決算資料収集失敗: HTTP {response.status_code}")
            print(f"   エラー: {response.text}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")

if __name__ == "__main__":
    test_sec_edgar()
