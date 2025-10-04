from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List
import os
import csv
import io
from app.services.snowflake_service import SnowflakeService
from app.services.ai_company_collector import AICompanyCollector
from app.services.nikihou_scraper import NikihouScraper

router = APIRouter()

@router.post("/companies/add")
async def add_company(company_data: Dict[str, Any]):
    """企業情報をSnowflakeに追加"""
    try:
        snowflake_service = SnowflakeService()
        required_fields = ['ticker', 'company_name']
        for field in required_fields:
            if not company_data.get(field):
                raise HTTPException(status_code=400, detail=f"必須フィールド '{field}' が不足しています")
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        country = company_data.get('country', 'JP')
        table_name = 'COMPANIES_JP' if country == 'JP' else 'COMPANIES_US'
        ticker = company_data.get('ticker', '')
        if ticker and ticker.strip():
            check_query = f"""
            SELECT COUNT(*) as count
            FROM {db_name}.{schema_name}.{table_name}
            WHERE LOWER(COMPANY_NAME) = LOWER(%s) OR (TICKER IS NOT NULL AND LOWER(TICKER) = LOWER(%s))
            """
            cursor = snowflake_service.conn.cursor()
            cursor.execute(check_query, (company_data['company_name'], ticker))
        else:
            check_query = f"""
            SELECT COUNT(*) as count
            FROM {db_name}.{schema_name}.{table_name}
            WHERE LOWER(COMPANY_NAME) = LOWER(%s)
            """
            cursor = snowflake_service.conn.cursor()
            cursor.execute(check_query, (company_data['company_name'],))
        result = cursor.fetchone()
        if result[0] > 0:
            cursor.close()
            raise HTTPException(
                status_code=400,
                detail=f"企業名 '{company_data['company_name']}' または証券コード '{ticker}' は既にデータベースに存在します"
            )
        columns = [
            'TICKER', 'COMPANY_NAME', 'SECTOR', 'INDUSTRY', 'COUNTRY', 'MARKET',
            'WEBSITE', 'BUSINESS_DESCRIPTION', 'DESCRIPTION', 'MARKET_CAP',
            'EMPLOYEES', 'CURRENT_PRICE', 'SHARES_OUTSTANDING', 'VOLUME',
            'PER', 'PBR', 'EPS', 'BPS', 'ROE', 'ROA', 'REVENUE',
            'OPERATING_PROFIT', 'NET_PROFIT', 'TOTAL_ASSETS', 'EQUITY',
            'OPERATING_MARGIN', 'NET_MARGIN', 'DIVIDEND_YIELD', 'COMPANY_TYPE', 'CEO'
        ]
        values = []
        placeholders = []
        for column in columns:
            value = company_data.get(column)
            if value is not None and value != '':
                values.append(value)
                placeholders.append('%s')
            else:
                values.append(None)
                placeholders.append('%s')
        insert_query = f"""
        INSERT INTO {db_name}.{schema_name}.{table_name}
        ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        cursor.execute(insert_query, tuple(values))
        snowflake_service.conn.commit()
        cursor.close()
        return {
            "message": "企業情報が正常に追加されました",
            "ticker": company_data['ticker'],
            "table": table_name
        }
    except Exception as e:
        print(f"Error adding company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"企業情報の追加に失敗しました: {str(e)}")

@router.get("/companies/search")
async def search_companies(query: str = "", country: str = ""):
    """企業名で検索してデータベースから情報を取得"""
    try:
        snowflake_service = SnowflakeService()
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        
        # 検索条件を構築
        conditions = []
        params = []
        
        if query:
            # 企業名またはティッカーで検索
            conditions.append("(LOWER(COMPANY_NAME) LIKE LOWER(%s) OR LOWER(TICKER) LIKE LOWER(%s))")
            params.append(f"%{query}%")
            params.append(f"%{query}%")
        
        if country and country != "all":
            conditions.append("COUNTRY = %s")
            params.append(country)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 各テーブルから検索
        tables = ['COMPANIES_JP', 'COMPANIES_US', 'COMPANIES_CN']
        all_results = []
        
        for table in tables:
            # テーブルに応じてカラム名を調整
            if table == 'COMPANIES_CN':
                search_query = f"""
                SELECT 
                    TICKER, COMPANY_NAME, SECTOR, INDUSTRY, COUNTRY, MARKET,
                    WEBSITE, BUSINESS_DESCRIPTION, DESCRIPTION, MARKET_CAP,
                    EMPLOYEES, CURRENT_PRICE, SHARES_OUTSTANDING, VOLUME,
                    PER, PBR, EPS, BPS, ROE, ROA, REVENUE,
                    OPERATING_INCOME as OPERATING_PROFIT, NET_INCOME as NET_PROFIT, 
                    TOTAL_ASSETS, SHAREHOLDERS_EQUITY as EQUITY,
                    OPERATING_MARGIN, NET_MARGIN, DIVIDEND_YIELD, COMPANY_TYPE, CEO
                FROM {db_name}.{schema_name}.{table}
                WHERE {where_clause}
                ORDER BY COMPANY_NAME
                LIMIT 50
                """
            else:
                search_query = f"""
                SELECT 
                    TICKER, COMPANY_NAME, SECTOR, INDUSTRY, COUNTRY, MARKET,
                    WEBSITE, BUSINESS_DESCRIPTION, DESCRIPTION, MARKET_CAP,
                    EMPLOYEES, CURRENT_PRICE, SHARES_OUTSTANDING, VOLUME,
                    PER, PBR, EPS, BPS, ROE, ROA, REVENUE,
                    OPERATING_PROFIT, NET_PROFIT, TOTAL_ASSETS, EQUITY,
                    OPERATING_MARGIN, NET_MARGIN, DIVIDEND_YIELD, COMPANY_TYPE, CEO
                FROM {db_name}.{schema_name}.{table}
                WHERE {where_clause}
                ORDER BY COMPANY_NAME
                LIMIT 50
                """
            
            results = snowflake_service.query(search_query, tuple(params))
            # キー名を小文字に変換してフロントエンドと互換性を保つ
            converted_results = []
            for result in results:
                converted_result = {}
                for key, value in result.items():
                    # 大文字のキーを小文字に変換
                    converted_key = key.lower() if key.isupper() else key
                    converted_result[converted_key] = value
                converted_results.append(converted_result)
            all_results.extend(converted_results)
        
        # 結果を企業名でソート
        all_results.sort(key=lambda x: x.get('company_name', '') or '')
        
        return {
            "companies": all_results,
            "total": len(all_results)
        }
        
    except Exception as e:
        print(f"Error searching companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"企業検索に失敗しました: {str(e)}")

@router.get("/companies/{ticker}")
async def get_company_by_ticker(ticker: str):
    """TICKERで企業情報を取得"""
    try:
        snowflake_service = SnowflakeService()
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        
        # 各テーブルから検索
        tables = ['COMPANIES_JP', 'COMPANIES_US', 'COMPANIES_CN']
        
        for table in tables:
            query = f"""
            SELECT 
                TICKER, COMPANY_NAME, SECTOR, INDUSTRY, COUNTRY, MARKET,
                WEBSITE, BUSINESS_DESCRIPTION, DESCRIPTION, MARKET_CAP,
                EMPLOYEES, CURRENT_PRICE, SHARES_OUTSTANDING, VOLUME,
                PER, PBR, EPS, BPS, ROE, ROA, REVENUE,
                OPERATING_PROFIT, NET_PROFIT, TOTAL_ASSETS, EQUITY,
                OPERATING_MARGIN, NET_MARGIN, DIVIDEND_YIELD, COMPANY_TYPE, CEO
            FROM {db_name}.{schema_name}.{table}
            WHERE TICKER = %s
            """
            
            results = snowflake_service.query(query, (ticker,))
            if results:
                return results[0]
        
        raise HTTPException(status_code=404, detail="企業が見つかりません")
        
    except Exception as e:
        print(f"Error getting company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"企業情報の取得に失敗しました: {str(e)}")

@router.put("/companies/{ticker}")
async def update_company(ticker: str, company_data: Dict[str, Any]):
    """企業情報を更新"""
    try:
        snowflake_service = SnowflakeService()
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        
        # まず企業がどのテーブルにあるかを確認
        tables = ['COMPANIES_JP', 'COMPANIES_US', 'COMPANIES_CN']
        target_table = None
        
        for table in tables:
            check_query = f"""
            SELECT COUNT(*) as count
            FROM {db_name}.{schema_name}.{table}
            WHERE TICKER = %s
            """
            results = snowflake_service.query(check_query, (ticker,))
            if results and results[0]['count'] > 0:
                target_table = table
                break
        
        if not target_table:
            raise HTTPException(status_code=404, detail="更新対象の企業が見つかりません")
        
        # 更新可能なフィールド
        updatable_fields = [
            'company_name', 'sector', 'industry', 'country', 'market',
            'website', 'business_description', 'description', 'market_cap',
            'employees', 'current_price', 'shares_outstanding', 'volume',
            'PER', 'PBR', 'EPS', 'BPS', 'ROE', 'ROA', 'REVENUE',
            'OPERATING_PROFIT', 'NET_PROFIT', 'TOTAL_ASSETS', 'EQUITY',
            'OPERATING_MARGIN', 'NET_MARGIN', 'DIVIDEND_YIELD', 'COMPANY_TYPE', 'CEO'
        ]
        
        # 更新クエリを構築
        update_parts = []
        update_params = []
        
        for field in updatable_fields:
            if field in company_data and company_data[field] is not None:
                update_parts.append(f"{field} = %s")
                update_params.append(company_data[field])
        
        if not update_parts:
            raise HTTPException(status_code=400, detail="更新するフィールドがありません")
        
        update_query = f"""
        UPDATE {db_name}.{schema_name}.{target_table}
        SET {', '.join(update_parts)}
        WHERE TICKER = %s
        """
        
        update_params.append(ticker)
        
        cursor = snowflake_service.conn.cursor()
        cursor.execute(update_query, tuple(update_params))
        snowflake_service.conn.commit()
        cursor.close()
        
        return {
            "message": "企業情報が正常に更新されました",
            "ticker": ticker,
            "table": target_table
        }
        
    except Exception as e:
        print(f"Error updating company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"企業情報の更新に失敗しました: {str(e)}")

@router.delete("/companies/{ticker}")
async def delete_company(ticker: str):
    """企業情報を削除"""
    try:
        snowflake_service = SnowflakeService()
        db_name = os.getenv("SNOWFLAKE_DATABASE")
        schema_name = os.getenv("SNOWFLAKE_SCHEMA")
        
        # まず企業がどのテーブルにあるかを確認
        tables = ['COMPANIES_JP', 'COMPANIES_US', 'COMPANIES_CN']
        target_table = None
        
        for table in tables:
            check_query = f"""
            SELECT COUNT(*) as count
            FROM {db_name}.{schema_name}.{table}
            WHERE TICKER = %s
            """
            results = snowflake_service.query(check_query, (ticker,))
            if results and results[0]['count'] > 0:
                target_table = table
                break
        
        if not target_table:
            raise HTTPException(status_code=404, detail="削除対象の企業が見つかりません")
        
        # 削除クエリ
        delete_query = f"""
        DELETE FROM {db_name}.{schema_name}.{target_table}
        WHERE TICKER = %s
        """
        
        cursor = snowflake_service.conn.cursor()
        cursor.execute(delete_query, (ticker,))
        snowflake_service.conn.commit()
        cursor.close()
        
        return {
            "message": "企業情報が正常に削除されました",
            "ticker": ticker,
            "table": target_table
        }
        
    except Exception as e:
        print(f"Error deleting company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"企業情報の削除に失敗しました: {str(e)}")

@router.post("/ai/collect-company")
async def collect_company_with_ai(request_data: Dict[str, Any]):
    """AIを使って企業情報を自動収集"""
    try:
        print(f"AI company collection request: {request_data}")
        
        company_name = request_data.get('company_name')
        website_url = request_data.get('website_url')
        country = request_data.get('country', 'JP')
        ticker = request_data.get('ticker', '')
        
        print(f"Parsed parameters - company_name: {company_name}, website_url: {website_url}, country: {country}, ticker: {ticker}")
        
        if not company_name or not website_url:
            print("Missing required parameters")
            raise HTTPException(status_code=400, detail="企業名とウェブサイトURLは必須です")
        
        print("Creating AICompanyCollector instance...")
        collector = AICompanyCollector()
        
        print("Checking for duplicate company...")
        if collector.check_duplicate_company(company_name, ticker, country):
            print(f"Duplicate company found: {company_name} / {ticker}")
            raise HTTPException(
                status_code=400,
                detail=f"企業名 '{company_name}' またはTICKER '{ticker}' は既にデータベースに存在します"
            )
        
        print("Starting AI company collection...")
        result = collector.collect_and_save_with_ticker(company_name, website_url, ticker, country)
        print(f"Collection result: {result}")
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "company_info": result['company_info']
            }
        else:
            print(f"Collection failed: {result['message']}")
            raise HTTPException(status_code=500, detail=result['message'])
            
    except HTTPException as he:
        print(f"HTTPException in AI company collection: {he.detail}")
        raise he
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Unexpected error in AI company collection: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"AI企業情報収集に失敗しました: {str(e)}")

@router.post("/data/collect")
async def collect_data():
    """データ収集のエンドポイント（既存の実装）"""
    pass

@router.get("/env-check")
async def check_environment():
    """環境変数の設定状況を確認"""
    import os
    env_vars = {
        "SNOWFLAKE_ACCOUNT": bool(os.getenv("SNOWFLAKE_ACCOUNT")),
        "SNOWFLAKE_USER": bool(os.getenv("SNOWFLAKE_USER")),
        "SNOWFLAKE_PASSWORD": bool(os.getenv("SNOWFLAKE_PASSWORD")),
        "SNOWFLAKE_WAREHOUSE": bool(os.getenv("SNOWFLAKE_WAREHOUSE")),
        "SNOWFLAKE_DATABASE": bool(os.getenv("SNOWFLAKE_DATABASE")),
        "SNOWFLAKE_SCHEMA": bool(os.getenv("SNOWFLAKE_SCHEMA")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4"),
        "GOOGLE_DRIVE_FOLDER_ID": bool(os.getenv("GOOGLE_DRIVE_FOLDER_ID")),
        "GOOGLE_DRIVE_CREDENTIALS": bool(os.getenv("GOOGLE_DRIVE_CREDENTIALS")),
    }
    
    missing_vars = [var for var, exists in env_vars.items() if not exists and var != "OPENAI_MODEL"]
    
    return {
        "environment_variables": env_vars,
        "missing_variables": missing_vars,
        "all_configured": len(missing_vars) == 0
    }

@router.get("/debug/ai-collect")
async def debug_ai_collect():
    """AI企業情報収集のデバッグ用エンドポイント"""
    return {
        "message": "AI企業情報収集エンドポイントは正常に動作しています",
        "endpoint": "/api/admin/ai/collect-company",
        "method": "POST",
        "required_fields": ["company_name", "website_url", "country", "ticker"]
    }

@router.post("/debug/ai-collect")
async def debug_ai_collect_post():
    """AI企業情報収集のデバッグ用POSTエンドポイント"""
    return {
        "message": "POSTメソッドでAI企業情報収集エンドポイントにアクセスできました",
        "status": "success"
    }

@router.put("/companies/{ticker}/business-description")
async def update_business_description(ticker: str, request_data: Dict[str, Any]):
    """企業の事業内容を手動で更新"""
    try:
        business_description = request_data.get('business_description')
        description = request_data.get('description')
        
        if not business_description and not description:
            raise HTTPException(status_code=400, detail="事業内容または詳細説明が必要です")
        
        # 国を特定してテーブルを決定
        country = request_data.get('country', 'JP')
        if country == 'JP':
            table_name = 'COMPANIES_JP'
        elif country == 'CN':
            table_name = 'COMPANIES_CN'
        else:
            table_name = 'COMPANIES_US'
        
        # Snowflakeで更新
        snowflake_service = SnowflakeService()
        
        update_fields = []
        params = []
        
        if business_description:
            update_fields.append("BUSINESS_DESCRIPTION = %s")
            params.append(business_description)
        
        if description:
            update_fields.append("DESCRIPTION = %s")
            params.append(description)
        
        params.append(ticker)
        
        query = f"""
        UPDATE {os.getenv('SNOWFLAKE_DATABASE')}.{os.getenv('SNOWFLAKE_SCHEMA')}.{table_name}
        SET {', '.join(update_fields)}
        WHERE TICKER = %s
        """
        
        cursor = snowflake_service.conn.cursor()
        cursor.execute(query, params)
        cursor.close()
        
        return {
            "success": True,
            "message": f"企業 {ticker} の事業内容を更新しました",
            "updated_fields": {
                "business_description": business_description,
                "description": description
            }
        }
        
    except Exception as e:
        print(f"Error updating business description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"事業内容の更新に失敗しました: {str(e)}")

@router.post("/nikihou/scrape-company")
async def scrape_company_from_nikihou(request_data: Dict[str, Any]):
    """日経報から企業情報をスクレイピング"""
    try:
        ticker = request_data.get('ticker')
        market = request_data.get('market', 'HKM')
        
        if not ticker:
            raise HTTPException(status_code=400, detail="ティッカーコードが必要です")
        
        print(f"Starting Nikihou scraping for {ticker} in {market}")
        
        scraper = NikihouScraper()
        company_info = scraper.scrape_company_info(ticker, market)
        
        if not company_info:
            raise HTTPException(status_code=404, detail=f"企業情報が見つかりませんでした: {ticker}")
        
        # データベースに保存
        snowflake_service = SnowflakeService()
        success = snowflake_service.upsert_companies([company_info])
        
        if success:
            return {
                "success": True,
                "message": f"企業 {ticker} の情報を日経報から取得・保存しました",
                "company_info": company_info
            }
        else:
            return {
                "success": False,
                "message": "データベースへの保存に失敗しました",
                "company_info": company_info
            }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in Nikihou scraping: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"日経報スクレイピングに失敗しました: {str(e)}")

@router.post("/nikihou/batch-scrape")
async def batch_scrape_from_nikihou(request_data: Dict[str, Any]):
    """日経報から複数企業を一括スクレイピング"""
    try:
        tickers = request_data.get('tickers', [])
        market = request_data.get('market', 'HKM')
        
        if not tickers or not isinstance(tickers, list):
            raise HTTPException(status_code=400, detail="ティッカーコードのリストが必要です")
        
        print(f"Starting batch Nikihou scraping for {len(tickers)} companies")
        
        scraper = NikihouScraper()
        results = scraper.batch_scrape_companies(tickers, market)
        
        # 成功した企業のみをデータベースに保存
        successful_companies = []
        failed_companies = []
        
        for ticker, company_info in results.items():
            if company_info:
                try:
                    snowflake_service = SnowflakeService()
                    success = snowflake_service.upsert_companies([company_info])
                    if success:
                        successful_companies.append(ticker)
                    else:
                        failed_companies.append(ticker)
                except Exception as e:
                    print(f"Error saving {ticker}: {str(e)}")
                    failed_companies.append(ticker)
            else:
                failed_companies.append(ticker)
        
        return {
            "success": True,
            "message": f"一括スクレイピング完了: 成功 {len(successful_companies)}件, 失敗 {len(failed_companies)}件",
            "successful_companies": successful_companies,
            "failed_companies": failed_companies,
            "results": results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in batch Nikihou scraping: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"一括スクレイピングに失敗しました: {str(e)}")

@router.get("/nikihou/test-scrape/{ticker}")
async def test_nikihou_scrape(ticker: str, market: str = "HKM"):
    """日経報スクレイピングのテスト用エンドポイント"""
    try:
        scraper = NikihouScraper()
        company_info = scraper.scrape_company_info(ticker, market)
        
        return {
            "success": True,
            "ticker": ticker,
            "market": market,
            "company_info": company_info
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in test Nikihou scraping: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"テストスクレイピングに失敗しました: {str(e)}")

@router.post("/companies/upload-csv")
async def upload_companies_csv(file: UploadFile = File(...), country: str = "JP"):
    """CSVファイルから企業情報を一括アップロード"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="CSVファイルをアップロードしてください")
        
        # ファイル内容を読み取り
        content = await file.read()
        csv_content = content.decode('utf-8-sig')  # BOMを除去
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        companies = []
        for row in csv_reader:
            # 空の行をスキップ
            if not any(row.values()):
                continue
                
            # 国を設定
            row['country'] = country
            
            # 数値フィールドを変換
            numeric_fields = [
                'market_cap', 'employees', 'current_price', 'shares_outstanding', 'volume',
                'per', 'pbr', 'eps', 'bps', 'roe', 'roa', 'revenue',
                'operating_profit', 'net_profit', 'total_assets', 'equity',
                'operating_margin', 'net_margin', 'dividend_yield', 'founded_year'
            ]
            
            for field in numeric_fields:
                if field in row and row[field]:
                    try:
                        # カンマを除去して数値に変換
                        value = str(row[field]).replace(',', '').replace('¥', '').replace('$', '')
                        if value and value != '':
                            row[field] = float(value) if '.' in value else int(value)
                        else:
                            row[field] = None
                    except (ValueError, TypeError):
                        row[field] = None
                else:
                    row[field] = None
            
            companies.append(row)
        
        if not companies:
            raise HTTPException(status_code=400, detail="有効な企業データが見つかりませんでした")
        
        # データベースに保存
        snowflake_service = SnowflakeService()
        success = snowflake_service.upsert_companies(companies)
        
        if success:
            return {
                "success": True,
                "message": f"{len(companies)}件の企業情報をアップロードしました",
                "uploaded_count": len(companies),
                "country": country
            }
        else:
            raise HTTPException(status_code=500, detail="データベースへの保存に失敗しました")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in CSV upload: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"CSVアップロードに失敗しました: {str(e)}")

@router.get("/companies/csv-template")
async def get_csv_template():
    """CSVテンプレートのダウンロード用エンドポイント"""
    try:
        # CSVテンプレートの作成
        template_data = [
            {
                "ticker": "例: 7203",
                "company_name": "例: トヨタ自動車",
                "sector": "例: 自動車",
                "industry": "例: 自動車製造",
                "market": "例: TSE",
                "website": "例: https://www.toyota.co.jp",
                "business_description": "例: 自動車の製造・販売",
                "description": "例: 詳細な事業説明",
                "market_cap": "例: 30000000000000",
                "employees": "例: 370000",
                "current_price": "例: 2500.50",
                "shares_outstanding": "例: 12000000000",
                "volume": "例: 5000000",
                "per": "例: 15.5",
                "pbr": "例: 1.2",
                "eps": "例: 150.0",
                "bps": "例: 2000.0",
                "roe": "例: 7.5",
                "roa": "例: 5.0",
                "revenue": "例: 30000000000000",
                "operating_profit": "例: 3000000000000",
                "net_profit": "例: 2500000000000",
                "total_assets": "例: 50000000000000",
                "equity": "例: 20000000000000",
                "operating_margin": "例: 10.0",
                "net_margin": "例: 8.3",
                "dividend_yield": "例: 2.5",
                "company_type": "例: 上場企業",
                "ceo": "例: 豊田章男",
                "founded_year": "例: 1937"
            }
        ]
        
        # CSV文字列を生成
        output = io.StringIO()
        fieldnames = template_data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(template_data)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            "csv_content": csv_content,
            "filename": "companies_template.csv"
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating CSV template: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"CSVテンプレートの生成に失敗しました: {str(e)}")
