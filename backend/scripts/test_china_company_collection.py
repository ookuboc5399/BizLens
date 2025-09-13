#!/usr/bin/env python3
"""
中国企業のAI企業情報収集をテストするスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.ai_company_collector import AICompanyCollector

def test_china_company_collection():
    """中国企業のAI企業情報収集をテスト"""
    
    print("=== 中国企業AI企業情報収集テスト ===")
    
    # AI企業情報収集サービスを初期化
    collector = AICompanyCollector()
    
    # テスト用の中国企業情報
    test_companies = [
        {
            'company_name': '字节跳动科技有限公司',
            'website_url': 'https://www.bytedance.com/',
            'country': 'CN',
            'ticker': 'BDNCE'
        },
        {
            'company_name': '美团点评集团',
            'website_url': 'https://about.meituan.com/',
            'country': 'CN',
            'ticker': 'MEITUAN'
        },
        {
            'company_name': '滴滴出行科技有限公司',
            'website_url': 'https://www.didiglobal.com/',
            'country': 'CN',
            'ticker': 'DIDI'
        }
    ]
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n--- テスト企業 {i}: {company['company_name']} ---")
        print(f"ウェブサイト: {company['website_url']}")
        print(f"国: {company['country']}")
        print(f"TICKER: {company['ticker']}")
        
        try:
            # 企業情報を収集
            print(f"\n{company['company_name']}の企業情報を収集中...")
            company_info = collector.collect_company_info(
                company['company_name'], 
                company['website_url'], 
                company['country']
            )
            
            print("\n=== 収集結果 ===")
            print(f"企業名: {company_info.get('company_name', 'N/A')}")
            print(f"ウェブサイト: {company_info.get('website', 'N/A')}")
            print(f"国: {company_info.get('country', 'N/A')}")
            print()
            
            # 重要なフィールドの確認
            important_fields = [
                'sector', 'industry', 'business_description', 'company_type',
                'ceo', 'estimated_employees', 'founded_year', 'funding_series'
            ]
            
            print("=== 重要フィールド確認 ===")
            for field in important_fields:
                value = company_info.get(field, 'N/A')
                print(f"{field}: {value}")
            
            # データベースに保存
            print(f"\n{company['company_name']}をデータベースに保存中...")
            company_info['ticker'] = company['ticker']
            success = collector.save_to_database(company_info)
            
            if success:
                print(f"✅ {company['company_name']}の保存が完了しました")
            else:
                print(f"❌ {company['company_name']}の保存に失敗しました")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
    
    print("\n=== 中国企業AI企業情報収集テスト完了 ===")

if __name__ == "__main__":
    test_china_company_collection()
