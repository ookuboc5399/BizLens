#!/usr/bin/env python3
"""
AIを使った企業情報自動収集サービス
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from pathlib import Path
from dotenv import load_dotenv
from app.services.snowflake_service import SnowflakeService

# .envファイルを読み込み
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

class AICompanyCollector:
    def __init__(self):
        self.snowflake_service = SnowflakeService()
        # OpenAI APIキー（環境変数から取得）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")  # デフォルトはgpt-4
        self.openai_base_url = "https://api.openai.com/v1"
        
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
        else:
            print(f"Using OpenAI model: {self.openai_model}")
        
    def collect_company_info(self, company_name: str, website_url: str, country: str = "JP") -> Dict[str, Any]:
        """
        企業名とウェブサイトから企業情報を収集
        
        Args:
            company_name: 企業名
            website_url: 企業のウェブサイトURL
            country: 国コード（JP/US/CN）
            
        Returns:
            収集した企業情報の辞書
        """
        try:
            # 1. 外部データベースから情報を取得
            external_info = self._fetch_external_company_info(company_name, country)
            
            # 2. ウェブサイトから基本情報をスクレイピング
            basic_info = self._scrape_website_info(website_url)
            
            # 3. AIを使って企業情報を分析・補完（外部情報も含める）
            combined_basic = {**basic_info, **external_info}
            ai_enhanced_info = self._enhance_with_ai(company_name, website_url, combined_basic)
            
            # 4. 財務情報を取得（可能な場合）
            financial_info = self._get_financial_info(company_name, country)
            
            # 5. 情報を統合（AIで収集した企業名を優先、なければ入力された企業名を使用）
            # AIで収集した企業名がある場合はそれを使用
            final_company_name = ai_enhanced_info.get('company_name', company_name)
            if not final_company_name or final_company_name.strip() == '':
                final_company_name = company_name
            
            combined_info = {
                **basic_info,
                **external_info,
                **ai_enhanced_info,
                **financial_info,
                "company_name": final_company_name,  # AIで収集した企業名を優先
                "country": country,
                "market": country,  # デフォルトで国と同じ
                "website": website_url
            }
            
            return combined_info
            
        except Exception as e:
            print(f"Error collecting company info: {str(e)}")
            raise
    
    def _fetch_external_company_info(self, company_name: str, country: str = "JP") -> Dict[str, Any]:
        """外部データベースから企業情報を取得"""
        external_info = {}
        
        try:
            # 企業名からスタートアップかどうかを判断
            if self._is_likely_startup(company_name, country):
                # STARTUP DBから情報を取得
                startup_db_info = self._fetch_from_startup_db(company_name)
                if startup_db_info:
                    external_info.update(startup_db_info)
                    print(f"STARTUP DBから情報を取得: {company_name}")
            else:
                print(f"Skipping STARTUP DB search for: {company_name} (likely not a startup)")
            
            # その他の外部データベースも追加可能
            # 例: Crunchbase, PitchBook, 日本の企業情報データベースなど
            
        except Exception as e:
            print(f"Error fetching external info: {str(e)}")
        
        return external_info

    def _is_likely_startup(self, company_name: str, country: str = "JP") -> bool:
        """企業名からスタートアップかどうかを判断"""
        # 国別の非スタートアップキーワード
        non_startup_keywords = {
            "JP": [
                '石油', '資源', '開発', '電力', 'ガス', '水道', '鉄道', '航空', '海運',
                '銀行', '保険', '証券', '信託', '生命', '損保', '農協', '漁協',
                '商工', '信用', '金庫', '中央', '日本', '三菱', '三井', '住友', '芙蓉',
                'トヨタ', '日産', 'ホンダ', 'ソニー', 'パナソニック', 'シャープ', '日立',
                '東芝', '富士通', 'NEC', 'NTT', 'KDDI', 'ソフトバンク', 'シチズン',
                '時計', '精工', 'セイコー', 'カシオ', 'リコー', 'キヤノン', 'ニコン',
                'オリンパス', '富士フイルム', 'コニカ', 'ミノルタ', 'ヤマハ', 'ローランド',
                'コルグ', 'テクニクス', 'パイオニア', 'オンキヨー', 'デノン', 'マランツ'
            ],
            "CN": [
                '石油', '石化', '電力', '銀行', '保険', '証券', '信託', '生命', '損保',
                '中国', '中華', '華', '中', '国', '中央', '人民', '国家', '政府',
                '建設', '工商', '農業', '民生', '招商', '交通', '中信', '平安',
                '人寿', '太保', '人保', '国寿', '太保', '人保', '国寿', '太保',
                '移动', '联通', '电信', '石油', '石化', '电力', '银行', '保险',
                '证券', '信托', '生命', '损保', '中国', '中华', '华', '中', '国',
                '中央', '人民', '国家', '政府', '建设', '工商', '农业', '民生',
                '招商', '交通', '中信', '平安', '人寿', '太保', '人保', '国寿',
                '移动', '联通', '电信', '阿里巴巴', '腾讯', '百度', '京东', '美团',
                '滴滴', '字节跳动', '小米', '华为', 'OPPO', 'vivo', '联想'
            ]
        }
        
        # 国別のキーワードを取得
        keywords = non_startup_keywords.get(country, non_startup_keywords["JP"])
        
        # 企業名に非スタートアップキーワードが含まれているかチェック
        for keyword in keywords:
            if keyword in company_name:
                return False
        
        return True

    def _fetch_from_startup_db(self, company_name: str) -> Dict[str, Any]:
        """STARTUP DBから企業情報を取得"""
        try:
            print(f"Searching STARTUP DB for: {company_name}")
            
            # STARTUP DBの検索URL
            search_url = f"https://startup-db.com/search?q={company_name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 検索ページを取得
            response = requests.get(search_url, headers=headers, timeout=15)
            
            # 404エラーの場合は企業が見つからない（スタートアップでない）
            if response.status_code == 404:
                print(f"Company not found in STARTUP DB: {company_name} (likely not a startup)")
                return {}
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 検索結果から企業ページのリンクを探す
            company_links = soup.find_all('a', href=True)
            company_url = None
            
            for link in company_links:
                href = link.get('href', '')
                if '/companies/' in href and company_name.lower() in link.get_text().lower():
                    company_url = f"https://startup-db.com{href}"
                    print(f"Found company URL: {company_url}")
                    break
            
            if not company_url:
                print(f"No company URL found for: {company_name}")
                return {}
            
            # 企業詳細ページを取得
            company_response = requests.get(company_url, headers=headers, timeout=15)
            company_response.raise_for_status()
            
            company_soup = BeautifulSoup(company_response.content, 'html.parser')
            
            # 企業情報を抽出
            info = {}
            
            # 従業員数
            employees_text = company_soup.find(text=lambda text: text and '従業員数' in text)
            if employees_text:
                import re
                employees_match = re.search(r'(\d+)', employees_text)
                if employees_match:
                    info['employees'] = int(employees_match.group(1))
                    print(f"Found employees: {info['employees']}")
            
            # 設立日
            founded_text = company_soup.find(text=lambda text: text and '設立日' in text)
            if founded_text:
                import re
                founded_match = re.search(r'(\d{4})', founded_text)
                if founded_match:
                    info['founded_year'] = int(founded_match.group(1))
                    print(f"Found founded year: {info['founded_year']}")
            
            # 代表者情報
            ceo_elements = company_soup.find_all(text=lambda text: text and ('代表' in text or 'CEO' in text or '社長' in text))
            if ceo_elements:
                for element in ceo_elements:
                    import re
                    ceo_match = re.search(r'([^\s]+)', element)
                    if ceo_match:
                        info['ceo'] = ceo_match.group(1)
                        print(f"Found CEO: {info['ceo']}")
                        break
            
            # 事業内容
            business_desc_elements = company_soup.find_all('p')
            for element in business_desc_elements:
                text = element.get_text().strip()
                if len(text) > 50 and ('サービス' in text or '事業' in text or 'ビジネス' in text):
                    info['business_description'] = text[:500]
                    print(f"Found business description: {info['business_description'][:100]}...")
                    break
            
            # 企業タイプ（スタートアップDBなのでSTARTUP）
            info['company_type'] = 'STARTUP'
            
            print(f"Total info extracted from STARTUP DB: {len(info)} fields")
            return info
            
        except Exception as e:
            print(f"Error fetching from STARTUP DB: {str(e)}")
            return {}

    def _scrape_website_info(self, url: str) -> Dict[str, Any]:
        """ウェブサイトから基本情報をスクレイピング"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 基本情報を抽出
            info = {
                "company_name": "",
                "business_description": "",
                "description": "",
                "employees": None,
                "website": url
            }
            
            # タイトルから企業名を抽出
            title = soup.find('title')
            if title:
                info["company_name"] = title.get_text().strip()
            
            # メタディスクリプションから事業内容を抽出
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                info["business_description"] = meta_desc.get('content', '').strip()
            
            # 本文から企業説明を抽出
            main_content = soup.find('main') or soup.find('body')
            if main_content:
                # 最初の段落を企業説明として使用
                paragraphs = main_content.find_all('p')
                if paragraphs:
                    info["description"] = paragraphs[0].get_text().strip()[:500]  # 500文字まで
            
            return info
            
        except Exception as e:
            print(f"Error scraping website: {str(e)}")
            return {
                "company_name": "",
                "business_description": "",
                "description": "",
                "employees": None,
                "website": url
            }
    
    def _enhance_with_ai(self, company_name: str, website_url: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """AIを使って企業情報を分析・補完"""
        if not self.openai_api_key:
            print("OpenAI API key not found, skipping AI enhancement")
            return {}
        
        print(f"Starting AI analysis for company: {company_name}")
        print(f"Basic info available: {list(basic_info.keys())}")
        
        try:
            # AIに送信するプロンプトを作成
            prompt = f"""
            以下の企業情報を分析し、不足している情報を補完してください。
            
            企業名: {company_name}
            ウェブサイト: {website_url}
            基本情報: {json.dumps(basic_info, ensure_ascii=False)}
            
            外部データベース（STARTUP DBなど）から取得した情報も含まれている可能性があります。
            これらの情報を活用して、より正確な分析を行ってください。
            
            以下の形式でJSONを返してください：
            {{
                "company_name": "正確な企業名（正式名称）",
                "sector": "業種（例：テクノロジー、金融、製造業、ヘルスケア、教育、小売など）",
                "industry": "業界（例：ソフトウェア、銀行、自動車、医療機器、EdTech、ECなど）",
                "business_description": "事業内容の詳細説明（100-200文字程度）",
                "description": "企業の詳細説明（200-300文字程度）",
                "estimated_employees": "推定従業員数（数値のみ、既に取得済みの場合はその値を使用）",
                "estimated_market_cap": "推定時価総額（数値のみ、単位は円）",
                "estimated_revenue": "推定売上高（数値のみ、単位は円）",
                "estimated_operating_profit": "推定営業利益（数値のみ、単位は円）",
                "estimated_net_profit": "推定純利益（数値のみ、単位は円）",
                "estimated_total_assets": "推定総資産（数値のみ、単位は円）",
                "estimated_equity": "推定純資産（数値のみ、単位は円）",
                "company_type": "企業タイプ（LISTED: 上場企業、STARTUP: スタートアップ、PRIVATE: 非上場企業）",
                "ceo": "代表者名（CEO/代表取締役、既に取得済みの場合はその値を使用）",
                "founded_year": "設立年（数値のみ）",
                "funding_series": "資金調達シリーズ（シード、シリーズA、B、C、D、E、IPOなど）",
                "total_funding": "総資金調達額（数値のみ、単位は円）",
                "latest_funding": "最新資金調達額（数値のみ、単位は円）",
                "investors": "主要投資家（配列形式）",
                "business_model": "ビジネスモデル（B2B、B2C、B2B2C、SaaS、マーケットプレイスなど）",
                "target_market": "ターゲット市場（企業規模、業界、地域など）",
                "competitive_advantage": "競合優位性（技術、ブランド、ネットワーク効果など）",
                "growth_stage": "成長段階（アイデア、プロトタイプ、製品市場適合、スケール、成熟など）"
            }}
            
            企業タイプの判別基準：
            - LISTED: 証券取引所に上場している企業、大企業、時価総額が大きい企業、従業員数1000名以上、設立から10年以上
            - STARTUP: ベンチャー企業、新興企業、革新的なビジネスモデル、急成長中、従業員数1000名未満、設立から10年未満
            - PRIVATE: 非上場の大企業、家族企業、中堅企業、従業員数1000名以上、設立から10年以上
            
            資金調達シリーズの判別基準：
            - シード: 初期段階、資金調達額数百万円〜数千万円、従業員数10名未満
            - シリーズA: 製品開発・市場検証段階、資金調達額数千万円〜数億円、従業員数10-50名
            - シリーズB: 事業拡大段階、資金調達額数億円〜数十億円、従業員数50-200名
            - シリーズC: スケール段階、資金調達額数十億円〜数百億円、従業員数200-1000名
            - シリーズD以降: 成熟段階、資金調達額数百億円以上、従業員数1000名以上
            
            既に取得済みの情報（従業員数、代表者名など）がある場合は、その値を優先してください。
            推定値が不明な場合はnullを設定してください。
            """
            
            # OpenAI APIを呼び出し
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは企業情報分析の専門家です。与えられた情報から企業の詳細情報を分析し、不足している情報を推定してください。必ず指定されたJSON形式で回答してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # モデルに応じてパラメータを調整
            if "gpt-5-mini" in self.openai_model:
                # GPT-5-mini用の設定（最小限のパラメータ）
                data["max_completion_tokens"] = 2000
            elif "gpt-5" in self.openai_model:
                # その他のGPT-5モデル用
                data["max_completion_tokens"] = 2000
                data["temperature"] = 0.1
            else:
                # その他のモデル用（GPT-4、GPT-3.5など）
                data["max_tokens"] = 2000
                data["temperature"] = 0.1
            
            print(f"Sending request to OpenAI API with model: {self.openai_model}")
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # タイムアウトをさらに延長
            )
            
            print(f"OpenAI API response status: {response.status_code}")
            print(f"OpenAI API response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content']
                    print(f"AI Response received: {ai_response[:200]}...")  # 最初の200文字を表示
                except Exception as json_error:
                    print(f"Error parsing OpenAI response JSON: {str(json_error)}")
                    print(f"Raw response text: {response.text[:500]}...")
                    return {}
            else:
                print(f"OpenAI API error: {response.status_code}")
                print(f"Response text: {response.text[:500]}...")
                return {}
            
            # JSONレスポンスを解析
            try:
                # JSONブロックを抽出（```json ... ```の形式の場合）
                if '```json' in ai_response:
                    json_start = ai_response.find('```json') + 7
                    json_end = ai_response.find('```', json_start)
                    if json_end != -1:
                        ai_response = ai_response[json_start:json_end].strip()
                
                # 通常のJSON解析
                ai_data = json.loads(ai_response)
                print(f"Successfully parsed AI response with {len(ai_data)} fields")
                
                # 企業名の処理
                if 'company_name' in ai_data and ai_data['company_name']:
                    print(f"AI collected company name: {ai_data['company_name']}")
                else:
                    print("No company name collected by AI")
                
                # 数値フィールドの型変換
                numeric_fields = [
                    'estimated_employees', 'estimated_market_cap', 'estimated_revenue',
                    'estimated_operating_profit', 'estimated_net_profit', 'estimated_total_assets', 'estimated_equity',
                    'founded_year', 'total_funding', 'latest_funding'
                ]
                
                for field in numeric_fields:
                    if field in ai_data and ai_data[field] is not None:
                        try:
                            if isinstance(ai_data[field], str):
                                # 文字列から数値に変換
                                ai_data[field] = int(ai_data[field])
                        except (ValueError, TypeError):
                            ai_data[field] = None
                
                return ai_data
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response: {ai_response}")
                print(f"JSON decode error: {str(e)}")
                return {}
            except Exception as e:
                print(f"Error processing AI response: {str(e)}")
                return {}
                
        except Exception as e:
            print(f"Error in AI enhancement: {str(e)}")
            return {}
    
    def _get_financial_info(self, company_name: str, country: str) -> Dict[str, Any]:
        """財務情報を取得（外部APIを使用）"""
        # ここでは簡易的な実装。実際の運用では以下のような外部APIを使用：
        # - Yahoo Finance API
        # - Alpha Vantage API
        # - Financial Modeling Prep API
        # - 日本の場合は、EDINET APIやTDnet API
        
        try:
            # 例：Yahoo Finance APIを使用する場合
            # 実際の実装では適切なAPIキーとエンドポイントを使用
            return {
                "current_price": None,
                "market_cap": None,
                "per": None,
                "pbr": None,
                "eps": None,
                "bps": None,
                "roe": None,
                "roa": None,
                "volume": None,
                "shares_outstanding": None,
                "operating_margin": None,
                "net_margin": None,
                "dividend_yield": None
            }
        except Exception as e:
            print(f"Error getting financial info: {str(e)}")
            return {}
    
    def check_duplicate_company(self, company_name: str, ticker: str = None, country: str = "JP") -> bool:
        """企業名とTICKERの重複をチェック"""
        try:
            db_name = os.getenv("SNOWFLAKE_DATABASE")
            schema_name = os.getenv("SNOWFLAKE_SCHEMA")
            
            # テーブル名を決定
            if country == 'JP':
                table_name = 'companies_jp'
            elif country == 'CN':
                table_name = 'companies_cn'
            else:
                table_name = 'companies_us'
            
            # 企業名とTICKERの両方で検索
            if ticker and ticker.strip():
                query = f"""
                SELECT COUNT(*) as count
                FROM {db_name}.{schema_name}.{table_name}
                WHERE LOWER(company_name) = LOWER(%s) OR (ticker IS NOT NULL AND LOWER(ticker) = LOWER(%s))
                """
                cursor = self.snowflake_service.conn.cursor()
                cursor.execute(query, (company_name, ticker))
            else:
                query = f"""
                SELECT COUNT(*) as count
                FROM {db_name}.{schema_name}.{table_name}
                WHERE LOWER(company_name) = LOWER(%s)
                """
                cursor = self.snowflake_service.conn.cursor()
                cursor.execute(query, (company_name,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] > 0
            
        except Exception as e:
            print(f"Error checking duplicate: {str(e)}")
            return False

    def save_to_database(self, company_info: Dict[str, Any]) -> bool:
        """収集した企業情報をデータベースに保存"""
        try:
            # 重複チェック
            company_name = company_info.get('company_name', '')
            ticker = company_info.get('ticker', '')
            country = company_info.get('country', 'JP')
            
            if self.check_duplicate_company(company_name, ticker, country):
                raise Exception(f"企業名 '{company_name}' またはTICKER '{ticker}' は既にデータベースに存在します")
            
            # TICKERが空文字列の場合はnullに設定
            if ticker == '':
                company_info['ticker'] = None
            
            # テーブル名を決定
            if country == 'JP':
                table_name = 'companies_jp'
            elif country == 'CN':
                table_name = 'companies_cn'
            else:
                table_name = 'companies_us'
            
            # Snowflakeに保存
            self.snowflake_service.upsert_companies([company_info])
            
            return True
            
        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            return False
    
    def _generate_ticker(self, company_name: str) -> str:
        """企業名から証券コードを生成（簡易版）- 非推奨"""
        # このメソッドは使用しない。TICKERは手動で指定する必要があります。
        raise Exception("TICKERの自動生成は無効化されています。TICKERは手動で指定してください。")
    
    def collect_and_save(self, company_name: str, website_url: str, country: str = "JP") -> Dict[str, Any]:
        """企業情報を収集してデータベースに保存（非推奨）"""
        raise Exception("このメソッドは非推奨です。collect_and_save_with_tickerを使用してください。")

    def collect_and_save_with_ticker(self, company_name: str, website_url: str, ticker: str, country: str = "JP") -> Dict[str, Any]:
        """企業情報を収集してデータベースに保存（TICKER指定）"""
        try:
            # 情報を収集
            company_info = self.collect_company_info(company_name, website_url, country)
            
            # TICKERを設定
            company_info['ticker'] = ticker
            
            # データベースに保存
            success = self.save_to_database(company_info)
            
            return {
                "success": success,
                "company_info": company_info,
                "message": "企業情報が正常に収集・保存されました" if success else "保存に失敗しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "company_info": {},
                "message": f"エラーが発生しました: {str(e)}"
            }
