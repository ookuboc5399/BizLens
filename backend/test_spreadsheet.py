#!/usr/bin/env python3
"""
指定されたスプレッドシートの内容をテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.google_drive_service import GoogleDriveService

def test_spreadsheet():
    """スプレッドシートの内容をテスト"""
    spreadsheet_id = "1XGBAK_BPGKz4mUB-INZ-W6H_Ja2fqUFr_g0WRbYGrcY"
    
    print(f"Testing spreadsheet: {spreadsheet_id}")
    print("=" * 50)
    
    try:
        # Google Driveサービスを初期化
        drive_service = GoogleDriveService()
        
        if not drive_service.sheets_service:
            print("❌ Google Sheets service not initialized")
            return
        
        print("✅ Google Sheets service initialized")
        
        # スプレッドシートのデータを取得（すべてのシート）
        data = drive_service.get_all_sheets_data(spreadsheet_id)
        
        if not data:
            print("❌ Failed to get spreadsheet data")
            return
        
        print("✅ Spreadsheet data retrieved successfully")
        print(f"Title: {data['title']}")
        print(f"Sheets: {data['sheets']}")
        
        print("\n" + "=" * 50)
        print("SHEETS DATA:")
        print("=" * 50)
        
        for sheet_name, sheet_data in data['sheets_data'].items():
            print(f"\n--- {sheet_name} ---")
            print(f"Headers: {sheet_data['headers']}")
            print(f"Data rows: {len(sheet_data['data'])}")
            
            # 最初の5行を表示
            for i, row in enumerate(sheet_data['data'][:5]):
                print(f"Row {i}: {row}")
            
            if len(sheet_data['data']) > 5:
                print(f"... and {len(sheet_data['data']) - 5} more rows")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spreadsheet()
