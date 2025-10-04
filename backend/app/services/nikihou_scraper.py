#!/usr/bin/env python3
"""
日経報企業情報スクレイピングサービス
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Any, Optional, List
import time
from urllib.parse import urljoin, urlparse

class NikihouScraper:
    def __init__(self):
        self.base_url = "https://www.nikihou.jp"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def scrape_company_info(self, ticker: str, market: str = "HKM") -> Dict[str, Any]:
        """
        企業情報を包括的にスクレイピング
        
        Args:
            ticker: 企業のティッカーコード
            market: 市場コード (HKM, TSE, NASDAQ等)
            
        Returns:
            統合された企業情報
        """
        try:
            print(f"Starting Nikihou scraping for ticker: {ticker}, market: {market}")
            
            # 各ページの情報を取得
            outline_info = self._scrape_outline(ticker, market)
            finance_info = self._scrape_finance(ticker, market)
            achievement_info = self._scrape_achievement(ticker, market)
            
            # 情報を統合
            combined_info = {
                **outline_info,
                **finance_info,
                **achievement_info,
                "ticker": ticker,
                "market": market,
                "country": "CN",  # 日経報スクレイピングは中国企業用
                "data_source": "NIKIHOU",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            print(f"Successfully scraped info for {ticker}: {list(combined_info.keys())}")
            return combined_info
            
        except Exception as e:
            print(f"Error scraping company info for {ticker}: {str(e)}")
            return {}
    
    def _scrape_outline(self, ticker: str, market: str) -> Dict[str, Any]:
        """企業概要ページをスクレイピング"""
        try:
            url = f"{self.base_url}/company/company.html?code={ticker}&market={market}&type=outline"
            print(f"Scraping outline: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            info = {}
            
            # 企業名を取得（複数のパターンを試す）
            company_name = None
            
            # 1. strongタグ内の企業名を探す
            strong_elem = soup.find('strong')
            if strong_elem:
                strong_text = strong_elem.get_text(strip=True)
                if strong_text and len(strong_text) > 0 and not strong_text.isdigit():
                    company_name = strong_text
                    print(f"Found company name in strong tag: {company_name}")
            
            # 2. 企業名ラベルの隣のセルを探す
            if not company_name:
                company_name_elem = soup.find('td', string=re.compile(r'企業名'))
                if company_name_elem:
                    next_td = company_name_elem.find_next_sibling('td')
                    if next_td:
                        # strongタグ内のテキストを優先
                        strong_in_td = next_td.find('strong')
                        if strong_in_td:
                            company_name = strong_in_td.get_text(strip=True)
                        else:
                            company_name = next_td.get_text(strip=True)
                        print(f"Found company name in table: {company_name}")
            
            # 3. タイトルから企業名を抽出
            if not company_name:
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # タイトルから企業名を抽出
                    if '|' in title_text:
                        company_name = title_text.split('|')[0].strip()
                        print(f"Found company name in title: {company_name}")
            
            # 4. h1タグを探す
            if not company_name:
                h1_elem = soup.find('h1')
                if h1_elem:
                    h1_text = h1_elem.get_text(strip=True)
                    if h1_text and len(h1_text) > 0:
                        company_name = h1_text
                        print(f"Found company name in h1: {company_name}")
            
            # 5. テーブル内の最初の大きなテキストを探す
            if not company_name:
                first_td = soup.find('td')
                if first_td:
                    # strongタグ内のテキストを優先
                    strong_in_td = first_td.find('strong')
                    if strong_in_td:
                        company_name = strong_in_td.get_text(strip=True)
                    else:
                        first_text = first_td.get_text(strip=True)
                        if first_text and len(first_text) > 5 and not first_text.isdigit():
                            company_name = first_text
                    print(f"Found company name in first td: {company_name}")
            
            # 企業名が取得できない場合は、ティッカーコードを企業名として使用
            if not company_name:
                company_name = f"企業_{ticker}"
                print(f"Using fallback company name: {company_name}")
            
            info['company_name'] = company_name
            
            # 設立年を取得
            founded_elem = soup.find('td', string=re.compile(r'設立'))
            if founded_elem:
                next_td = founded_elem.find_next_sibling('td')
                if next_td:
                    founded_text = next_td.get_text(strip=True)
                    founded_match = re.search(r'(\d{4})年', founded_text)
                    if founded_match:
                        info['founded_year'] = int(founded_match.group(1))
            
            # 代表者を取得
            ceo_elem = soup.find('td', string=re.compile(r'代表'))
            if ceo_elem:
                next_td = ceo_elem.find_next_sibling('td')
                if next_td:
                    info['ceo'] = next_td.get_text(strip=True)
            
            # 本社所在地を取得
            address_elem = soup.find('td', string=re.compile(r'本社'))
            if address_elem:
                next_td = address_elem.find_next_sibling('td')
                if next_td:
                    info['headquarters'] = next_td.get_text(strip=True)
            
            # URLを取得
            url_elem = soup.find('td', string=re.compile(r'URL'))
            if url_elem:
                next_td = url_elem.find_next_sibling('td')
                if next_td:
                    url_link = next_td.find('a')
                    if url_link:
                        info['website'] = url_link.get('href', '').strip()
            
            # 事業概要を取得（複数のパターンを試す）
            business_description = None
            
            # 1. summaryContentクラスのdivを探す
            summary_elem = soup.find('div', class_='summaryContent')
            if summary_elem:
                business_description = summary_elem.get_text(strip=True)
                print(f"Found business description in summaryContent: {business_description[:100]}...")
            
            # 2. 事業概要ラベルの隣のセルを探す
            if not business_description:
                business_desc_elem = soup.find('td', string=re.compile(r'事業概要'))
                if business_desc_elem:
                    next_td = business_desc_elem.find_next_sibling('td')
                    if next_td:
                        business_description = next_td.get_text(strip=True)
                        print(f"Found business description in table: {business_description[:100]}...")
            
            # 3. 事業内容ラベルの隣のセルを探す
            if not business_description:
                business_desc_elem = soup.find('td', string=re.compile(r'事業内容'))
                if business_desc_elem:
                    next_td = business_desc_elem.find_next_sibling('td')
                    if next_td:
                        business_description = next_td.get_text(strip=True)
                        print(f"Found business description in table (事業内容): {business_description[:100]}...")
            
            # 4. 企業概要ラベルの隣のセルを探す
            if not business_description:
                business_desc_elem = soup.find('td', string=re.compile(r'企業概要'))
                if business_desc_elem:
                    next_td = business_desc_elem.find_next_sibling('td')
                    if next_td:
                        business_description = next_td.get_text(strip=True)
                        print(f"Found business description in table (企業概要): {business_description[:100]}...")
            
            if business_description:
                info['business_description'] = business_description
            
            print(f"Outline info scraped: {list(info.keys())}")
            return info
            
        except Exception as e:
            print(f"Error scraping outline for {ticker}: {str(e)}")
            return {}
    
    def _scrape_finance(self, ticker: str, market: str) -> Dict[str, Any]:
        """財務ページをスクレイピング"""
        try:
            url = f"{self.base_url}/company/company.html?code={ticker}&market={market}&type=finance"
            print(f"Scraping finance: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            info = {}
            
            # 財務データのテーブルを探す
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        # 数値データを抽出（より柔軟なマッチング）
                        if any(keyword in key for keyword in ['時価総額', '時価', 'Market Cap']):
                            info['market_cap'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['売上高', '売上', 'Revenue', '収益']):
                            info['revenue'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['営業利益', '営業', 'Operating', '営業収益']):
                            info['operating_profit'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['純利益', '純', 'Net', '当期純利益']):
                            info['net_profit'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['総資産', '資産', 'Total Assets', '総資産額']):
                            info['total_assets'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['自己資本', '資本', 'Equity', '株主資本']):
                            info['equity'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['PER', 'P/E', '株価収益率']):
                            info['per'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['PBR', 'P/B', '株価純資産倍率']):
                            info['pbr'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['ROE', '自己資本利益率']):
                            info['roe'] = self._extract_number(value)
                        elif any(keyword in key for keyword in ['ROA', '総資産利益率']):
                            info['roa'] = self._extract_number(value)
            
            print(f"Finance info scraped: {list(info.keys())}")
            return info
            
        except Exception as e:
            print(f"Error scraping finance for {ticker}: {str(e)}")
            return {}
    
    def _scrape_achievement(self, ticker: str, market: str) -> Dict[str, Any]:
        """業績ページをスクレイピング"""
        try:
            url = f"{self.base_url}/company/company.html?code={ticker}&market={market}&type=achievement"
            print(f"Scraping achievement: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            info = {}
            
            # 業績データのテーブルを探す
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        # 業績データを抽出
                        if '従業員数' in key:
                            info['employees'] = self._extract_number(value)
                        elif '配当利回り' in key:
                            info['dividend_yield'] = self._extract_number(value)
            
            print(f"Achievement info scraped: {list(info.keys())}")
            return info
            
        except Exception as e:
            print(f"Error scraping achievement for {ticker}: {str(e)}")
            return {}
    
    def _extract_number(self, text: str) -> Optional[float]:
        """テキストから数値を抽出"""
        if not text or text == '-':
            return None
        
        # カンマを削除
        text = text.replace(',', '')
        
        # 数値パターンを検索
        patterns = [
            r'(\d+\.?\d*)\s*億円',  # 億円
            r'(\d+\.?\d*)\s*万円',  # 万円
            r'(\d+\.?\d*)\s*千円',  # 千円
            r'(\d+\.?\d*)\s*円',    # 円
            r'(\d+\.?\d*)\s*%',     # パーセント
            r'(\d+\.?\d*)',         # 通常の数値
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                
                # 単位に応じて調整
                if '億円' in text:
                    return value * 100_000_000
                elif '万円' in text:
                    return value * 10_000
                elif '千円' in text:
                    return value * 1_000
                elif '%' in text:
                    return value
                else:
                    return value
        
        return None
    
    def batch_scrape_companies(self, tickers: List[str], market: str = "HKM") -> Dict[str, Dict[str, Any]]:
        """複数企業を一括スクレイピング"""
        results = {}
        
        for i, ticker in enumerate(tickers):
            try:
                print(f"Scraping {i+1}/{len(tickers)}: {ticker}")
                company_info = self.scrape_company_info(ticker, market)
                if company_info:
                    results[ticker] = company_info
                
                # レート制限を避けるため少し待機
                time.sleep(1)
                
            except Exception as e:
                print(f"Error scraping {ticker}: {str(e)}")
                results[ticker] = {}
        
        return results
