#!/usr/bin/env python3
"""
CSVアップロード機能のテスト
"""

import requests
import json

def test_csv_upload():
    print("=== CSVアップロード機能テスト ===")
    
    base_url = "http://localhost:8000"
    
    # 1. テンプレートダウンロードのテスト
    print("\n--- テンプレートダウンロードテスト ---")
    try:
        response = requests.get(f"{base_url}/api/admin/companies/csv-template")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ テンプレート取得成功")
            print(f"   ファイル名: {data.get('filename')}")
            print(f"   CSV内容の長さ: {len(data.get('csv_content', ''))}")
        else:
            print(f"❌ テンプレート取得失敗: HTTP {response.status_code}")
            print(f"   エラー: {response.text}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    # 2. CSVアップロードのテスト
    print("\n--- CSVアップロードテスト ---")
    try:
        with open('test_companies.csv', 'rb') as f:
            files = {'file': ('test_companies.csv', f, 'text/csv')}
            data = {'country': 'JP'}
            
            response = requests.post(f"{base_url}/api/admin/companies/upload-csv", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ CSVアップロード成功")
                print(f"   ステータス: {result.get('success')}")
                print(f"   メッセージ: {result.get('message')}")
                print(f"   アップロード件数: {result.get('uploaded_count')}")
                print(f"   保存先: {result.get('country')}")
            else:
                print(f"❌ CSVアップロード失敗: HTTP {response.status_code}")
                print(f"   エラー: {response.text}")
                
    except Exception as e:
        print(f"❌ エラー: {str(e)}")

if __name__ == "__main__":
    test_csv_upload()

