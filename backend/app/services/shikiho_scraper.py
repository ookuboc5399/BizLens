#!/usr/bin/env python3
"""
四季報オンライン スクレイピングサービス
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class ShikihoScraper:
    def __init__(self):
        self.base_url = "https://shikiho.toyokeizai.net/us"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """
        四季報オンラインから企業情報を取得
        
        Args:
            ticker: 企業のティッカーシンボル (例: NVDA)
            
        Returns:
            企業情報の辞書
        """
        try:
            url = f"{self.base_url}/{ticker}"
            logger.info(f"Fetching company info from: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 広告ブロッカーやCookie警告をチェック
            if self._check_for_blocking_warnings(soup, ticker):
                logger.warning(f"Ad blocker or cookie warning detected for {ticker}")
                return {
                    'ticker': ticker,
                    'error': 'Ad blocker or cookie warning detected. Please disable ad blockers and accept cookies.',
                    'warning': 'コンテンツブロック機能が検知されました。広告ブロッカーを無効にし、Cookieを許可してください。'
                }
            
            # 企業基本情報を抽出
            company_info = self._extract_company_basic_info(soup, ticker)
            
            # 財務情報を抽出
            financial_info = self._extract_financial_info(soup)
            
            # 業績情報を抽出
            performance_info = self._extract_performance_info(soup)
            
            # 統合
            result = {
                **company_info,
                **financial_info,
                **performance_info
            }
            
            logger.info(f"Successfully extracted info for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'error': str(e),
                'warning': 'データの取得に失敗しました。'
            }
    
    def _extract_company_basic_info(self, soup: BeautifulSoup, ticker: str) -> Dict:
        """企業基本情報を抽出"""
        info = {
            'ticker': ticker,
            'company_name': '',
            'english_name': '',
            'industry': '',
            'sector': '',
            'market_cap': '',
            'shares_outstanding': '',
            'listing_date': '',
            'headquarters': '',
            'website': '',
            'description': ''
        }
        
        try:
            # 四季報オンライン特有のセレクターを試す
            # 企業名の抽出
            company_name_selectors = [
                'h1.titles__title',
                '.company-name',
                '.stock-name',
                'h1',
                '.title'
            ]
            
            for selector in company_name_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and '会社四季報オンライン' not in text and len(text) > 3:
                        info['company_name'] = text
                        break
            
            # 英文名の抽出
            english_name_selectors = [
                '.titles__name',
                '.english-name',
                '.company-english-name'
            ]
            
            for selector in english_name_selectors:
                element = soup.select_one(selector)
                if element:
                    info['english_name'] = element.get_text(strip=True)
                    break
            
            # 業種の抽出
            industry_selectors = [
                '.company-content__mark .item',
                '.industry',
                '.sector'
            ]
            
            for selector in industry_selectors:
                element = soup.select_one(selector)
                if element:
                    info['industry'] = element.get_text(strip=True)
                    break
            
            # セクターの抽出
            sector_selectors = [
                '.ticker-and-labels__labels span',
                '.market',
                '.exchange'
            ]
            
            for selector in sector_selectors:
                element = soup.select_one(selector)
                if element:
                    info['sector'] = element.get_text(strip=True)
                    break
            
            # 時価総額の抽出
            market_cap_selectors = [
                '.stock-index-list .card__body__list__item span:nth-child(2)',
                '.market-cap',
                '.market-value'
            ]
            
            for selector in market_cap_selectors:
                element = soup.select_one(selector)
                if element:
                    info['market_cap'] = element.get_text(strip=True)
                    break
            
            # 基本情報テーブルから抽出
            basic_info_table = soup.select_one('.basic-information table')
            if basic_info_table:
                rows = basic_info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if '発行済み株式数' in key or 'Shares Outstanding' in key:
                            info['shares_outstanding'] = value
                        elif '上場日' in key or 'Listing Date' in key:
                            info['listing_date'] = value
                        elif '本社' in key or 'Headquarters' in key:
                            info['headquarters'] = value
                        elif 'ウェブサイト' in key or 'Website' in key:
                            info['website'] = value
            
            # 企業説明の抽出
            description_selectors = [
                '.overview-articles dd',
                '.company-description',
                '.business-description'
            ]
            
            for selector in description_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if len(text) > 50:
                        info['description'] = text
                        break
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {str(e)}")
        
        return info
    
    def _extract_financial_info(self, soup: BeautifulSoup) -> Dict:
        """財務情報を抽出"""
        financial_info = {
            'revenue': '',
            'operating_income': '',
            'net_income': '',
            'total_assets': '',
            'total_liabilities': '',
            'shareholders_equity': '',
            'roe': '',
            'roa': '',
            'per': '',
            'pbr': '',
            'dividend_yield': '',
            'eps': ''
        }
        
        try:
            # 四季報オンライン特有の財務情報セレクター
            # 年次業績テーブルから最新データを抽出
            performance_table = soup.select_one('.performance-section .performance-table table tbody')
            if performance_table:
                rows = performance_table.find_all('tr')
                for row in rows:
                    if not row.select_one('.is-future'):  # 実績データのみ
                        cols = row.find_all('td')
                        if len(cols) >= 8:
                            financial_info['revenue'] = cols[1].get_text(strip=True)
                            financial_info['operating_income'] = cols[2].get_text(strip=True)
                            financial_info['net_income'] = cols[4].get_text(strip=True)
                            financial_info['eps'] = cols[6].get_text(strip=True)
                        break
            
            # 株価指標から抽出
            stock_index_list = soup.select_one('.stock-index-list .card__body__list')
            if stock_index_list:
                for item in stock_index_list.find_all('li'):
                    label_element = item.select_one('span:nth-of-type(1) span:nth-of-type(1)')
                    value_element = item.select_one('span:nth-of-type(2)')
                    if label_element and value_element:
                        label = label_element.get_text(strip=True)
                        value = value_element.get_text(strip=True)
                        
                        if '予想PER' in label:
                            financial_info['per'] = value
                        elif '実績PER' in label:
                            financial_info['per'] = value
                        elif '実績PBR' in label:
                            financial_info['pbr'] = value
                        elif '予想配当利回り' in label:
                            financial_info['dividend_yield'] = value
            
            # 財務情報から抽出
            finance_list = soup.select_one('.finance-list .card__body__list')
            if finance_list:
                for item in finance_list.find_all('li'):
                    label_element = item.select_one('span:nth-of-type(1)')
                    value_element = item.select_one('span:nth-of-type(2)')
                    if label_element and value_element:
                        label = label_element.get_text(strip=True)
                        value = value_element.get_text(strip=True)
                        
                        if '総資産' in label:
                            financial_info['total_assets'] = value
                        elif '自己資本' in label:
                            financial_info['shareholders_equity'] = value
                        elif '自己資本比率' in label:
                            financial_info['roe'] = value  # ROEの代わりに自己資本比率
            
            # 平均営業利益率、平均ROE
            average_list = soup.select_one('.stock-index-list .card__body__average-list')
            if average_list:
                for item in average_list.find_all('.card__body__average-item'):
                    label_element = item.select_one('span:nth-of-type(1)')
                    value_element = item.select_one('span:nth-of-type(2)')
                    if label_element and value_element:
                        label = label_element.get_text(strip=True)
                        value = value_element.get_text(strip=True)
                        
                        if '平均営業利益率' in label:
                            financial_info['roa'] = value  # ROAの代わりに平均営業利益率
                        elif '平均ROE' in label:
                            financial_info['roe'] = value
            
        except Exception as e:
            logger.error(f"Error extracting financial info: {str(e)}")
        
        return financial_info
    
    def _extract_performance_info(self, soup: BeautifulSoup) -> Dict:
        """業績情報を抽出"""
        performance_info = {
            'latest_revenue': '',
            'latest_operating_income': '',
            'latest_net_income': '',
            'revenue_growth': '',
            'profit_growth': '',
            'quarterly_revenue': '',
            'quarterly_profit': '',
            'forecast_revenue': '',
            'forecast_profit': ''
        }
        
        try:
            # 四半期業績テーブルから抽出
            quarterly_performance_table = soup.select_one('.performance-section:nth-of-type(2) .performance-table table tbody')
            if quarterly_performance_table:
                rows = quarterly_performance_table.find_all('tr')
                for row in rows:
                    if not row.select_one('.is-future'):  # 実績データのみ
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            performance_info['quarterly_revenue'] = cols[1].get_text(strip=True)
                            performance_info['quarterly_profit'] = cols[2].get_text(strip=True)
                        break
            
            # 年次業績テーブルから最新データを抽出（実績と予想）
            performance_table = soup.select_one('.performance-section .performance-table table tbody')
            if performance_table:
                rows = performance_table.find_all('tr')
                latest_actual = None
                latest_forecast = None
                
                for row in rows:
                    if not row.select_one('.is-future'):
                        latest_actual = row
                    else:
                        latest_forecast = row
                        break
                
                # 最新実績データ
                if latest_actual:
                    cols = latest_actual.find_all('td')
                    if len(cols) >= 8:
                        performance_info['latest_revenue'] = cols[1].get_text(strip=True)
                        performance_info['latest_operating_income'] = cols[2].get_text(strip=True)
                        performance_info['latest_net_income'] = cols[4].get_text(strip=True)
                
                # 最新予想データ
                if latest_forecast:
                    cols = latest_forecast.find_all('td')
                    if len(cols) >= 8:
                        performance_info['forecast_revenue'] = cols[1].get_text(strip=True)
                        performance_info['forecast_profit'] = cols[2].get_text(strip=True)
            
        except Exception as e:
            logger.error(f"Error extracting performance info: {str(e)}")
        
        return performance_info
    
    def batch_scrape_companies(self, tickers: List[str], delay: float = 1.0) -> List[Dict]:
        """
        複数企業の情報を一括取得
        
        Args:
            tickers: ティッカーシンボルのリスト
            delay: リクエスト間の遅延時間（秒）
            
        Returns:
            企業情報のリスト
        """
        results = []
        
        for i, ticker in enumerate(tickers):
            logger.info(f"Scraping {ticker} ({i+1}/{len(tickers)})")
            
            company_info = self.get_company_info(ticker)
            if company_info:
                results.append(company_info)
            
            # レート制限を避けるため遅延
            if i < len(tickers) - 1:
                time.sleep(delay)
        
        return results
    
    def _check_for_blocking_warnings(self, soup: BeautifulSoup, ticker: str = "") -> bool:
        """広告ブロッカーやCookie警告をチェック"""
        # 広告ブロッカー警告のセレクター
        ad_blocker_selectors = [
            '.notification-unsupported.is-visible',
            '.tp_modal',
            '.ad-blocker-warning',
            '.content-blocked',
            '[class*="adblock"]',
            '[class*="blocker"]'
        ]
        
        for selector in ad_blocker_selectors:
            if soup.select_one(selector):
                return True
        
        # Cookie同意モーダル
        cookie_selectors = [
            '.cookie-consent',
            '.cookie-notice',
            '.gdpr-notice',
            '[class*="cookie"]'
        ]
        
        for selector in cookie_selectors:
            if soup.select_one(selector):
                return True
        
        # ページタイトルが一般的なものかチェック
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if '会社四季報オンライン' in title_text and ticker.upper() not in title_text:
                return True
        
        return False
