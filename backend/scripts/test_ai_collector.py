#!/usr/bin/env python3
"""
AI企業情報収集サービスのテストスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# .envファイルを読み込み
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)

from app.services.ai_company_collector import AICompanyCollector

def test_ai_collector():
    """AI企業情報収集サービスのテスト"""
    
    print("=== AI企業情報収集サービス テスト ===")
    
    # AI企業情報収集サービスを初期化
    collector = AICompanyCollector()
    
    # テスト用の企業情報（スタートアップ企業）
    test_company = "メリービズ株式会社"
    test_website = "https://merrybiz.co.jp/"
    test_country = "JP"
    
    print(f"テスト企業: {test_company}")
    print(f"ウェブサイト: {test_website}")
    print(f"国: {test_country}")
    print()
    
    try:
        # 企業情報を収集
        print("企業情報を収集中...")
        company_info = collector.collect_company_info(test_company, test_website, test_country)
        
        print("\n=== 収集結果 ===")
        print(f"企業名: {company_info.get('company_name', 'N/A')}")
        print(f"ウェブサイト: {company_info.get('website', 'N/A')}")
        print(f"国: {company_info.get('country', 'N/A')}")
        print()
        
        for key, value in company_info.items():
            if value is not None and value != "" and key not in ['company_name', 'website', 'country']:
                print(f"{key}: {value}")
        
        # 重要なフィールドの確認
        important_fields = [
            'sector', 'industry', 'business_description', 'company_type',
            'ceo', 'estimated_employees', 'founded_year', 'funding_series'
        ]
        
        print("\n=== 重要フィールド確認 ===")
        for field in important_fields:
            value = company_info.get(field, 'N/A')
            print(f"{field}: {value}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_collector()
