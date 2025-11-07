#!/usr/bin/env python3
"""
SEC EDGAR API を使用してアメリカ企業の決算資料を収集するサービス
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SECEdgarService:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.user_agent = "BizLens Financial Data Collector (contact@example.com)"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }
        
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """SEC EDGAR APIにリクエストを送信"""
        try:
            # SEC EDGAR APIのレート制限に従う（10リクエスト/秒）
            time.sleep(0.1)
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SEC EDGAR API request failed: {str(e)}")
            raise Exception(f"SEC EDGAR API request failed: {str(e)}")
    
    def search_company(self, company_name: str) -> List[Dict]:
        """企業名でSEC EDGARから企業を検索"""
        try:
            # 企業検索API
            search_url = f"{self.base_url}/api/xbrl/companyfacts/CIK0000000000.json"
            
            # 企業検索のための別のアプローチ
            # SEC EDGARの企業検索は直接的なAPIがないため、CIKを推測するか
            # 事前にCIKマッピングを使用する必要がある
            
            # 一般的な企業のCIKマッピング（例）
            cik_mapping = {
                "Apple Inc.": "0000320193",
                "Microsoft Corporation": "0000789019",
                "Amazon.com Inc.": "0001018724",
                "Alphabet Inc.": "0001652044",
                "Tesla Inc.": "0001318605",
                "Meta Platforms Inc.": "0001326801",
                "NVIDIA Corporation": "0001045810",
                "Netflix Inc.": "0001065280",
                "Salesforce Inc.": "0001108524",
                "Adobe Inc.": "0000796343"
            }
            
            # 企業名からCIKを取得
            cik = None
            for mapped_name, mapped_cik in cik_mapping.items():
                if company_name.lower() in mapped_name.lower() or mapped_name.lower() in company_name.lower():
                    cik = mapped_cik
                    break
            
            if not cik:
                # CIKが見つからない場合は、企業名から推測を試みる
                logger.warning(f"CIK not found for company: {company_name}")
                return []
            
            return [{"cik": cik, "name": company_name}]
            
        except Exception as e:
            logger.error(f"Error searching company {company_name}: {str(e)}")
            return []
    
    def get_company_facts(self, cik: str) -> Dict:
        """企業のファクトデータを取得"""
        try:
            # CIKを10桁のゼロパディング形式に変換
            cik_padded = cik.zfill(10)
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik_padded}.json"
            
            print(f"Requesting company facts from: {url}")
            result = self._make_request(url)
            print(f"Company facts response keys: {list(result.keys()) if result else 'None'}")
            
            if "filings" in result:
                print(f"Filings structure: {list(result['filings'].keys()) if result['filings'] else 'None'}")
                if "recent" in result["filings"]:
                    recent = result["filings"]["recent"]
                    print(f"Recent filings keys: {list(recent.keys()) if recent else 'None'}")
                    if "form" in recent:
                        print(f"Available forms: {recent['form'][:10]}")  # 最初の10個のフォーム
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting company facts for CIK {cik}: {str(e)}")
            raise
    
    def get_filings(self, cik: str, form_type: str = "10-K", limit: int = 10) -> List[Dict]:
        """企業の提出書類を取得"""
        try:
            # CIKを10桁のゼロパディング形式に変換
            cik_padded = cik.zfill(10)
            
            # submissions エンドポイントを使用して提出書類を取得
            url = f"{self.base_url}/submissions/CIK{cik_padded}.json"
            
            print(f"Requesting filings from: {url}")
            submissions = self._make_request(url)
            print(f"Submissions response keys: {list(submissions.keys()) if submissions else 'None'}")
            
            # 提出書類の情報を抽出
            filings = []
            if "filings" in submissions:
                recent_filings = submissions["filings"]["recent"]
                
                # フォームタイプのリストを取得
                forms = recent_filings.get("form", [])
                filing_dates = recent_filings.get("filingDate", [])
                report_dates = recent_filings.get("reportDate", [])
                accession_numbers = recent_filings.get("accessionNumber", [])
                primary_documents = recent_filings.get("primaryDocument", [])
                
                print(f"Available forms: {forms[:10]}")  # 最初の10個のフォーム
                
                # 指定されたフォームタイプの提出書類を検索
                for i, form in enumerate(forms):
                    if form == form_type and len(filings) < limit:
                        filing = {
                            "form": form,
                            "filingDate": filing_dates[i] if i < len(filing_dates) else None,
                            "reportDate": report_dates[i] if i < len(report_dates) else None,
                            "accessionNumber": accession_numbers[i] if i < len(accession_numbers) else None,
                            "primaryDocument": primary_documents[i] if i < len(primary_documents) else None
                        }
                        filings.append(filing)
                        print(f"Found {form_type} filing: {filing}")
            
            return filings
            
        except Exception as e:
            logger.error(f"Error getting filings for CIK {cik}: {str(e)}")
            return []
    
    def get_filing_document(self, accession_number: str, primary_document: str) -> bytes:
        """提出書類の実際のドキュメントを取得"""
        try:
            # アクセッション番号からファイルパスを構築
            # 例: 0000320193-24-000123 -> 320193/000032019324000123/
            accession_clean = accession_number.replace("-", "")
            cik = accession_clean[:10]
            
            # CIKから先頭のゼロを除去
            cik_clean = str(int(cik))
            
            # ドキュメントURLを構築（正しい形式）
            document_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{primary_document}"
            
            print(f"Downloading document from: {document_url}")
            
            # ドキュメントをダウンロード
            response = requests.get(document_url, headers=self.headers)
            response.raise_for_status()
            
            print(f"Document downloaded successfully, size: {len(response.content)} bytes")
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting filing document {accession_number}: {str(e)}")
            raise
    
    def get_company_financial_data(self, company_name: str) -> Dict:
        """企業の財務データを取得"""
        try:
            # 企業を検索
            companies = self.search_company(company_name)
            if not companies:
                return {"error": f"Company not found: {company_name}"}
            
            company = companies[0]
            cik = company["cik"]
            
            # 企業ファクトを取得
            company_facts = self.get_company_facts(cik)
            
            # 財務データを抽出
            financial_data = {
                "cik": cik,
                "company_name": company_name,
                "facts": company_facts.get("facts", {}),
                "filings": self.get_filings(cik, "10-K", 5)  # 過去5年分の10-K
            }
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial data for {company_name}: {str(e)}")
            return {"error": str(e)}
    
    def download_latest_10k(self, company_name: str) -> Dict:
        """最新の10-Kレポートをダウンロード"""
        try:
            # 企業を検索
            companies = self.search_company(company_name)
            if not companies:
                return {"error": f"Company not found: {company_name}"}
            
            company = companies[0]
            cik = company["cik"]
            
            # 最新の10-Kを取得
            filings = self.get_filings(cik, "10-K", 1)
            if not filings:
                return {"error": f"No 10-K filings found for {company_name}"}
            
            latest_filing = filings[0]
            
            # ドキュメントをダウンロード
            document_content = self.get_filing_document(
                latest_filing["accessionNumber"],
                latest_filing["primaryDocument"]
            )
            
            return {
                "company_name": company_name,
                "cik": cik,
                "filing_date": latest_filing["filingDate"],
                "report_date": latest_filing["reportDate"],
                "accession_number": latest_filing["accessionNumber"],
                "document_name": latest_filing["primaryDocument"],
                "document_content": document_content,
                "document_size": len(document_content)
            }
            
        except Exception as e:
            logger.error(f"Error downloading 10-K for {company_name}: {str(e)}")
            return {"error": str(e)}
