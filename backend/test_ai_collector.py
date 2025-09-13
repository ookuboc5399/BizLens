#!/usr/bin/env python3
"""
AI企業情報収集機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_company_collector import AICompanyCollector

def test_ai_collector():
    """AI企業情報収集機能をテスト"""
    print("=== AI企業情報収集機能テスト ===")
    
    # AICompanyCollectorのインスタンスを作成
    collector = AICompanyCollector()
    
    # テスト用の企業情報
    test_company_name = "テスト企業"
    test_website_url = "https://example.com"
    test_ticker = "TEST"
    test_country = "JP"
    
    print(f"テスト企業名: {test_company_name}")
    print(f"テストウェブサイト: {test_website_url}")
    print(f"テストティッカー: {test_ticker}")
    print(f"テスト国: {test_country}")
    print()
    
    try:
        # 企業情報収集を実行
        print("企業情報収集中...")
        result = collector.collect_and_save_with_ticker(
            test_company_name, 
            test_website_url, 
            test_ticker, 
            test_country
        )
        
        print("=== 結果 ===")
        print(f"成功: {result['success']}")
        print(f"メッセージ: {result['message']}")
        print(f"企業情報: {result['company_info']}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_collector()
