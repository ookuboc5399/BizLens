from fastapi import APIRouter, HTTPException, Query
import os
import yfinance as yf
from dotenv import load_dotenv
from ...services.company_service import CompanyService
from ...services.snowflake_service import SnowflakeService
from ...services.google_drive_service import GoogleDriveService

router = APIRouter()
company_service = CompanyService()
snowflake_service = SnowflakeService()

@router.get("/search")
async def search_companies(
    query: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    market: str = None,
    sector: str = None,
    country: str = None
):
    try:
        # デバッグ: パラメータをログ出力
        print(f"Search parameters - query: '{query}', market: '{market}', sector: '{sector}', country: '{country}'")
        
        # 中国市場、米国市場、または日本市場が選択されている場合はGoogle Driveから検索
        if market and (market.upper() == "CN" or market.upper() == "US" or market.upper() == "JP"):
            market = market.upper()  # 大文字に統一
            try:
                print(f"Searching Google Drive for {market} companies with query: '{query}'")
                
                drive_service = GoogleDriveService()
                
                # Google Driveサービスが初期化されているか確認
                if not drive_service.service:
                    print("Google Drive service not initialized")
                    raise HTTPException(
                        status_code=500,
                        detail="Google Driveサービスが初期化されていません。設定を確認してください。"
                    )
                
                # 市場に応じてフォルダIDを設定
                if market == "CN":
                    folder_id = "1uragZmOuCVZYJ_9Wcyxe6R9-dnyI8-fi"  # 中国企業用フォルダ
                    market_label = "中国企業"
                    currency = "CNY"
                elif market == "US":
                    folder_id = "1JDah1KWIgrGwktuxnF0yGz3WyBR6yDb2"  # 米国企業用フォルダ
                    market_label = "米国企業"
                    currency = "USD"
                else:  # JP
                    folder_id = "1UCVDgNvrei0HPuWmM_BJaaHYAUNg3gO9"  # 日本企業用フォルダ
                    market_label = "日本企業"
                    currency = "JPY"
                
                folders = drive_service.search_company_folders(query, folder_id)
                
                print(f"Google Drive search returned {len(folders)} items")
                print(f"Folders/items: {folders}")
                
                # Google Driveの結果をCompany形式に変換
                companies = []
                for item in folders:
                    try:
                        if item['type'] == 'folder':
                            # フォルダの場合
                            files = drive_service.get_company_folder_files(item['id'])
                            file_count = len(files)
                        else:
                            # スプレッドシートファイルの場合
                            file_count = 1
                        
                        company = {
                            "ticker": item['name'],  # アイテム名をtickerとして使用
                            "company_name": item['name'],
                            "market": market,
                            "sector": market_label,
                            "industry": market_label,
                            "country": market,
                            "market_cap": 0,  # Google Driveには市場価値情報がない
                            "current_price": 0,  # Google Driveには価格情報がない
                            "currency": currency,
                            "company_type": market_label,
                            "ceo": None,
                            "folder_id": item['id'],
                            "file_count": file_count,
                            "web_view_link": item.get('webViewLink', ''),
                            "created_time": item.get('createdTime', ''),
                            "modified_time": item.get('modifiedTime', ''),
                            "item_type": item['type']  # 'folder' または 'spreadsheet'
                        }
                        companies.append(company)
                    except Exception as e:
                        print(f"Error processing item {item}: {str(e)}")
                        continue
                
                # ページネーション処理
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_companies = companies[start_idx:end_idx]
                
                print(f"Final result: {len(companies)} total companies, returning {len(paginated_companies)} for page {page}")
                print(f"Companies: {[c['company_name'] for c in paginated_companies]}")
                
                return {
                    "companies": paginated_companies,
                    "total": len(companies),
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (len(companies) + page_size - 1) // page_size if companies else 0
                }
            except HTTPException:
                raise
            except Exception as e:
                print(f"Error searching Google Drive: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Google Drive検索中にエラーが発生しました: {str(e)}"
                )
        
        # その他の市場は従来通りSnowflakeから検索
        print(f"Searching Snowflake for market: '{market}' (not CN/US/JP)")
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        conditions = ["1=1"]
        query_params = []

        if query:
            conditions.append("""
                (LOWER(COMPANY_NAME) LIKE LOWER(%s)
                OR LOWER(TICKER) LIKE LOWER(%s))
            """)
            query_params.append(f"%{query}%")
            query_params.append(f"%{query}%")

        if sector:
            conditions.append("LOWER(SECTOR) = LOWER(%s)")
            query_params.append(sector)

        if country:
            conditions.append("LOWER(COUNTRY) = LOWER(%s)")
            query_params.append(country)

        offset = (page - 1) * page_size

        # まずCOMPANIES_JPから検索
        jp_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            MARKET_CAP,
            CURRENT_PRICE,
            PER,
            PBR,
            ROE,
            ROA,
            DIVIDEND_YIELD,
            COMPANY_TYPE,
            CEO
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE {" AND ".join(conditions)}
        """
        
        # 次にCOMPANIES_USから検索
        us_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            MARKET_CAP,
            CURRENT_PRICE,
            PER,
            PBR,
            ROE,
            ROA,
            DIVIDEND_YIELD,
            COMPANY_TYPE,
            CEO
        FROM {db_name}.{schema_name}.COMPANIES_US
        WHERE {" AND ".join(conditions)}
        """
        
        # COMPANIES_CNから検索
        cn_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            MARKET_CAP,
            CURRENT_PRICE,
            PER,
            PBR,
            ROE,
            ROA,
            DIVIDEND_YIELD,
            COMPANY_TYPE,
            CEO
        FROM {db_name}.{schema_name}.COMPANIES_CN
        WHERE {" AND ".join(conditions)}
        """
        
        # 3つのクエリを実行
        jp_results = snowflake_service.query(jp_query, tuple(query_params))
        us_results = snowflake_service.query(us_query, tuple(query_params))
        cn_results = snowflake_service.query(cn_query, tuple(query_params))
        
        # 結果を結合
        all_results = jp_results + us_results + cn_results
        
        # market_capでソート（降順）
        all_results.sort(key=lambda x: (x['market_cap'] or 0), reverse=True)
        
        # ページネーション
        start_idx = offset
        end_idx = start_idx + page_size
        results = all_results[start_idx:end_idx]

        # LIMITとOFFSETのパラメータは不要になったので削除
        # query_params.append(page_size)
        # query_params.append(offset)

        # results = snowflake_service.query(bq_query, tuple(query_params))  # この行は削除

        # カウントクエリも個別に実行
        jp_count_query = f"""
        SELECT COUNT(*) as total
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE {" AND ".join(conditions)}
        """
        
        us_count_query = f"""
        SELECT COUNT(*) as total
        FROM {db_name}.{schema_name}.COMPANIES_US
        WHERE {" AND ".join(conditions)}
        """
        
        cn_count_query = f"""
        SELECT COUNT(*) as total
        FROM {db_name}.{schema_name}.COMPANIES_CN
        WHERE {" AND ".join(conditions)}
        """
        
        jp_count_results = snowflake_service.query(jp_count_query, tuple(query_params))
        us_count_results = snowflake_service.query(us_count_query, tuple(query_params))
        cn_count_results = snowflake_service.query(cn_count_query, tuple(query_params))
        
        # カウント結果が空でないことを確認
        jp_total = jp_count_results[0]['total'] if jp_count_results and len(jp_count_results) > 0 else 0
        us_total = us_count_results[0]['total'] if us_count_results and len(us_count_results) > 0 else 0
        cn_total = cn_count_results[0]['total'] if cn_count_results and len(cn_count_results) > 0 else 0
        
        total = jp_total + us_total + cn_total

        companies = []
        for row in results:
            company = {
                "ticker": row['ticker'],
                "company_name": row['company_name'],
                "market": row['market'],
                "sector": row['sector'],
                "industry": row['industry'],
                "country": row['country'],
                "website": row['website'],
                "business_description": row['business_description'],
                "market_cap": row['market_cap'],
                "current_price": row['current_price'],
                "per": row['per'],
                "pbr": row['pbr'],
                "roe": row['roe'],
                "roa": row['roa'],
                "dividend_yield": row['dividend_yield'],
                "company_type": row['company_type'],
                "ceo": row['ceo']
            }
            companies.append(company)

        return {
            "companies": companies,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"Error in search_companies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}")
async def get_company_detail(ticker: str):
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        # まずCOMPANIES_JPから検索
        jp_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            DESCRIPTION,
            MARKET_CAP,
            EMPLOYEES,
            CURRENT_PRICE,
            SHARES_OUTSTANDING,
            VOLUME,
            PER,
            PBR,
            EPS,
            BPS,
            ROE,
            ROA,
            REVENUE,
            OPERATING_PROFIT,
            NET_PROFIT,
            TOTAL_ASSETS,
            EQUITY,
            OPERATING_MARGIN,
            NET_MARGIN,
            TRADINGVIEW_SUMMARY,
            DIVIDEND_YIELD
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE TICKER = %s
        """
        
        # 次にCOMPANIES_USから検索
        us_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            DESCRIPTION,
            MARKET_CAP,
            EMPLOYEES,
            CURRENT_PRICE,
            SHARES_OUTSTANDING,
            VOLUME,
            PER,
            PBR,
            EPS,
            BPS,
            ROE,
            ROA,
            REVENUE,
            OPERATING_PROFIT,
            NET_PROFIT,
            TOTAL_ASSETS,
            EQUITY,
            OPERATING_MARGIN,
            NET_MARGIN,
            TRADINGVIEW_SUMMARY,
            DIVIDEND_YIELD
        FROM {db_name}.{schema_name}.COMPANIES_US
        WHERE TICKER = %s
        """
        
        # COMPANIES_CNから検索
        cn_query = f"""
        SELECT
            TICKER,
            COMPANY_NAME,
            MARKET,
            SECTOR,
            INDUSTRY,
            COUNTRY,
            WEBSITE,
            BUSINESS_DESCRIPTION,
            DESCRIPTION,
            MARKET_CAP,
            EMPLOYEES,
            CURRENT_PRICE,
            SHARES_OUTSTANDING,
            VOLUME,
            PER,
            PBR,
            EPS,
            BPS,
            ROE,
            ROA,
            REVENUE,
            OPERATING_INCOME as OPERATING_PROFIT,
            NET_INCOME as NET_PROFIT,
            TOTAL_ASSETS,
            SHAREHOLDERS_EQUITY as EQUITY,
            OPERATING_MARGIN,
            NET_MARGIN,
            NULL as TRADINGVIEW_SUMMARY,
            DIVIDEND_YIELD
        FROM {db_name}.{schema_name}.COMPANIES_CN
        WHERE TICKER = %s
        """
        
        # 3つのクエリを実行
        jp_results = snowflake_service.query(jp_query, (ticker,))
        us_results = snowflake_service.query(us_query, (ticker,))
        cn_results = snowflake_service.query(cn_query, (ticker,))
        
        # 結果を結合（通常は1つしか結果がないはず）
        results = jp_results + us_results + cn_results
        
        if not results:
            raise HTTPException(status_code=404, detail="Company not found")
            
        row = results[0]
        # リアルタイム株価データを取得
        realtime_data = _get_realtime_stock_data(ticker)
        
        # Snowflakeのクエリ結果の列名は小文字になっているため、小文字でアクセス
        return {
            "ticker": row['ticker'],
            "company_name": row['company_name'],
            "market": row['market'],
            "sector": row['sector'],
            "industry": row['industry'],
            "country": row['country'],
            "website": row['website'],
            "business_description": row['description'] or row['business_description'],
            "description": row['description'],
            # リアルタイム株価データを使用
            "current_price": realtime_data.get('current_price', row['current_price']),
            "market_cap": realtime_data.get('market_cap', row['market_cap']),
            "volume": realtime_data.get('volume', row['volume']),
            "per": realtime_data.get('pe_ratio', row['per']),
            "pbr": realtime_data.get('pb_ratio', row['pbr']),
            "dividend_yield": realtime_data.get('dividend_yield', row['dividend_yield']),
            # データベースの財務データ
            "employees": row['employees'],
            "shares_outstanding": row['shares_outstanding'],
            "eps": row['eps'],
            "bps": row['bps'],
            "roe": row['roe'],
            "roa": row['roa'],
            "revenue": row['revenue'],
            "operating_income": row['operating_profit'],  # マッピング
            "net_income": row['net_profit'],  # マッピング
            "total_assets": row['total_assets'],
            "shareholders_equity": row['equity'],  # マッピング
            "operating_margin": row['operating_margin'],
            "net_margin": row['net_margin'],
            "tradingview_summary": row['tradingview_summary'],
            # フロントエンドで期待されるフィールドのデフォルト値
            "data_source": "Snowflake + yfinance",
            "last_updated": realtime_data.get('last_updated'),
            "current_assets": None,
            "current_liabilities": None,
            "total_liabilities": None,
            "capital": None,
            "minority_interests": None,
            "debt_ratio": None,
            "current_ratio": None,
            "equity_ratio": None,
            "operating_cash_flow": None,
            "investing_cash_flow": None,
            "financing_cash_flow": None,
            "cash_and_equivalents": None,
            "dividend_per_share": None,
            "payout_ratio": None,
            "beta": realtime_data.get('beta'),
            "market_type": row['market'],
            "currency": "JPY" if row['country'] == 'JP' else "USD",
            "collected_at": None
        }
        
    except Exception as e:
        print(f"Error in get_company_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_realtime_stock_data(ticker: str) -> dict:
    """yfinanceを使用してリアルタイム株価データを取得"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 最新の株価データを取得
        hist = stock.history(period="1d", interval="1m")
        latest_price = None
        if not hist.empty:
            latest_price = float(hist['Close'].iloc[-1])
        
        return {
            'current_price': latest_price or info.get('currentPrice'),
            'market_cap': info.get('marketCap'),
            'volume': info.get('volume'),
            'pe_ratio': info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'beta': info.get('beta'),
            'last_updated': info.get('regularMarketTime')
        }
    except Exception as e:
        print(f"リアルタイム株価取得エラー {ticker}: {str(e)}")
        return {}

@router.get("/sectors")
async def get_sectors():
    """利用可能な業種（SECTOR）の一覧を取得"""
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        # シンプルなクエリでテスト
        simple_query = f"""
        SELECT DISTINCT SECTOR
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE SECTOR IS NOT NULL AND SECTOR != ''
        LIMIT 10
        """
        
        print(f"Executing simple sectors query...")
        results = snowflake_service.query(simple_query)
        print(f"Results: {len(results)}")
        
        # 結果を処理
        sectors = []
        for row in results:
            sectors.append(row['sector'])
        
        sectors = sorted(sectors)
        
        return {"sectors": sectors}
        
    except Exception as e:
        print(f"Error in get_sectors: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in get_sectors: {str(e)}")

@router.get("/countries")
async def get_countries():
    """利用可能な国（COUNTRY）の一覧を取得"""
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        # まずCOMPANIES_JPから国一覧を取得
        jp_query = f"""
        SELECT DISTINCT COUNTRY
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE COUNTRY IS NOT NULL AND COUNTRY != ''
        """
        
        # 次にCOMPANIES_USから国一覧を取得
        us_query = f"""
        SELECT DISTINCT COUNTRY
        FROM {db_name}.{schema_name}.COMPANIES_US
        WHERE COUNTRY IS NOT NULL AND COUNTRY != ''
        """
        
        # COMPANIES_CNから国一覧を取得
        cn_query = f"""
        SELECT DISTINCT COUNTRY
        FROM {db_name}.{schema_name}.COMPANIES_CN
        WHERE COUNTRY IS NOT NULL AND COUNTRY != ''
        """
        
        jp_results = snowflake_service.query(jp_query)
        us_results = snowflake_service.query(us_query)
        cn_results = snowflake_service.query(cn_query)
        
        # 結果を結合して重複を除去
        all_countries = set()
        for row in jp_results:
            all_countries.add(row['country'])
        for row in us_results:
            all_countries.add(row['country'])
        for row in cn_results:
            all_countries.add(row['country'])
        
        countries = sorted(list(all_countries))
        
        # results = snowflake_service.query(query)  # この行を削除
        # countries = [row['country'] for row in results]  # この行を削除
        
        return {"countries": countries}
        
    except Exception as e:
        print(f"Error in get_countries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/financial-history")
async def get_financial_history(ticker: str):
    try:
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")

        # まずCOMPANIES_JPから検索
        jp_query = f"""
        SELECT
            REVENUE,
            OPERATING_PROFIT as operating_income,
            NET_PROFIT as net_income,
            OPERATING_MARGIN,
            NET_MARGIN,
            ROE,
            roa
        FROM {db_name}.{schema_name}.COMPANIES_JP
        WHERE TICKER = %s
        """
        
        # 次にCOMPANIES_USから検索
        us_query = f"""
        SELECT
            REVENUE,
            OPERATING_PROFIT as operating_income,
            NET_PROFIT as net_income,
            OPERATING_MARGIN,
            NET_MARGIN,
            ROE,
            roa
        FROM {db_name}.{schema_name}.COMPANIES_US
        WHERE TICKER = %s
        """
        
        # 両方のクエリを実行
        jp_results = snowflake_service.query(jp_query, (ticker,))
        us_results = snowflake_service.query(us_query, (ticker,))
        
        # 結果を結合
        results = jp_results + us_results
        
        # results = snowflake_service.query(query, (ticker,))  # この行は削除
        
        if not results:
            return {"data": []}
        
        # 現在のデータを履歴として返す
        row = results[0]
        return {
            "data": [{
                "date": "2024-01-01",  # 仮の日付
                "revenue": row['revenue'],
                "operating_income": row['operating_income'],
                "net_income": row['net_income'],
                "operating_margin": row['operating_margin'],
                "net_margin": row['net_margin'],
                "roe": row['roe'],
                "roa": row['roa'],
                "current_ratio": None,
                "debt_ratio": None,
                "equity_ratio": None
            }]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spreadsheet/{spreadsheet_id}")
async def get_spreadsheet_data(spreadsheet_id: str):
    """Google Sheetsからデータを取得"""
    try:
        drive_service = GoogleDriveService()
        data = drive_service.get_all_sheets_data(spreadsheet_id)
        
        if not data:
            raise HTTPException(status_code=404, detail="スプレッドシートが見つからないか、アクセスできません")
        
        return data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"スプレッドシートデータの取得に失敗しました: {str(e)}")
