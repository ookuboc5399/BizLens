import asyncio
import logging
from app.services.data_collector import DataCollector
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_collection():
    """データ収集処理のテスト"""
    # テスト用の証券コード
    test_tickers = ['7203', '6758', '9984']  # トヨタ、ソニー、ソフトバンクG
    
    collector = DataCollector()
    try:
        print("\n=== Starting data collection test ===")
        
        # 出力ディレクトリの作成
        output_dir = 'test_output'
        os.makedirs(output_dir, exist_ok=True)
        
        for ticker in test_tickers:
            print(f"\n--- Testing data collection for {ticker} ---")
            
            # 基本情報の取得をテスト
            print("\nTesting basic info collection...")
            basic_info = await collector.collect_basic_info(ticker)
            print(f"Basic info: {json.dumps(basic_info, indent=2, ensure_ascii=False)}")
            
            # 株価データの取得をテスト
            print("\nTesting stock data collection...")
            stock_data = await collector.collect_stock_data(ticker)
            print(f"Stock data: {json.dumps(stock_data, indent=2, ensure_ascii=False)}")
            
            # 財務データの取得をテスト
            print("\nTesting financial data collection...")
            financial_data = await collector.collect_financial_data(ticker)
            print(f"Financial data: {json.dumps(financial_data, indent=2, ensure_ascii=False)}")
            
            # 全データの結合をテスト
            print("\nTesting complete data collection...")
            all_data = await collector.collect_all_data(ticker)
            
            # 結果をファイルに保存
            output_file = os.path.join(output_dir, f'test_data_{ticker}.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            print(f"\nComplete data saved to {output_file}")
            
            # 重要なフィールドの確認
            print("\nChecking important fields:")
            important_fields = [
                'company_name', 'ticker', 'market_price', 'market_cap',
                'per', 'pbr', 'eps', 'roe', 'revenue', 'operating_profit'
            ]
            for field in important_fields:
                value = all_data.get(field)
                print(f"{field}: {value}")
            
            # 遅延を入れて制限を回避
            await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(test_data_collection())
