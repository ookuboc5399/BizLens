import yfinance as yf
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    async def collect_nikkei_data(self, ticker: str):
        """日経から企業情報を取得"""
        logger.info(f"Collecting Nikkei data for {ticker}")
        url = f"https://www.nikkei.com/nkd/company/?scode={ticker}"
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Nikkei data: {response.status}")
                    return {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # デバッグ用にHTMLを保存
                with open(f'debug_nikkei_company_{ticker}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                data = {}
                
                # 企業名を取得
                name_elem = soup.find('h1', class_='m-headlineLarge_text')
                if name_elem:
                    data['company_name'] = name_elem.text.strip()
                
                # 財務データを取得
                financial_section = soup.find('div', class_='m-articleFrame')
                if financial_section:
                    # 財務指標テーブルを探す
                    tables = financial_section.find_all('table', class_='w668')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 2:
                                label = cells[0].text.strip()
                                value = cells[1].text.strip()
                                
                                try:
                                    # 数値データの処理
                                    value = value.replace('円', '').replace('倍', '').replace('%', '').replace(',', '').strip()
                                    if value and value != '－' and value != '-':
                                        numeric_value = float(value)
                                        
                                        # 財務指標の取得
                                        if '売上高' in label:
                                            data['revenue'] = numeric_value * 1_000_000  # 百万円を円に変換
                                        elif '営業利益' in label:
                                            data['operating_profit'] = numeric_value * 1_000_000
                                        elif '当期利益' in label or '純利益' in label:
                                            data['net_profit'] = numeric_value * 1_000_000
                                        elif '総資産' in label:
                                            data['total_assets'] = numeric_value * 1_000_000
                                        elif '純資産' in label or '自己資本' in label:
                                            data['equity'] = numeric_value * 1_000_000
                                        elif 'EPS' in label or '1株利益' in label:
                                            data['eps'] = numeric_value
                                        elif 'BPS' in label or '1株純資産' in label:
                                            data['bps'] = numeric_value
                                        elif 'ROE' in label:
                                            data['roe'] = numeric_value / 100
                                        elif 'ROA' in label:
                                            data['roa'] = numeric_value / 100
                                        elif '配当利回り' in label:
                                            data['dividend_yield'] = numeric_value / 100
                                        elif '1株配当' in label:
                                            data['dividend_per_share'] = numeric_value
                                        elif 'PER' in label:
                                            data['per'] = numeric_value
                                        elif 'PBR' in label:
                                            data['pbr'] = numeric_value
                                except (ValueError, TypeError):
                                    continue
                                    
                    # 業績サマリーテーブルを探す
                    summary_table = financial_section.find('table', class_='w668 m-tableType01')
                    if summary_table:
                        rows = summary_table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 2:
                                label = cells[0].text.strip()
                                value = cells[1].text.strip()
                                
                                try:
                                    value = value.replace('円', '').replace('倍', '').replace('%', '').replace(',', '').strip()
                                    if value and value != '－' and value != '-':
                                        numeric_value = float(value)
                                        
                                        if '売上高' in label:
                                            data['revenue'] = numeric_value * 1_000_000
                                        elif '営業利益' in label:
                                            data['operating_profit'] = numeric_value * 1_000_000
                                        elif '純利益' in label:
                                            data['net_profit'] = numeric_value * 1_000_000
                                except (ValueError, TypeError):
                                    continue
                
                logger.info(f"Nikkei data collected for {ticker}: {data}")
                return data
                
        except Exception as e:
            logger.error(f"Error collecting Nikkei data for {ticker}: {str(e)}")
            return {}

    async def collect_basic_info(self, ticker: str):
        """Yahoo FinanceとNikkeiから企業の基本情報を収集"""
        logger.info(f"Collecting basic info for {ticker}")
        try:
            # Yahoo Financeから基本情報を取得
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(None, lambda: yf.Ticker(f"{ticker}.T"))
            info = ticker_obj.info
            
            # 日経からデータを取得
            nikkei_data = await self.collect_nikkei_data(ticker)
            
            # 基本情報を抽出（日経のデータを優先）
            basic_info = {
                "company_name": nikkei_data.get('company_name') or info.get('longName', ''),
                "sector": info.get('sector', ''),
                "industry": info.get('industry', ''),
                "description": info.get('longBusinessSummary', ''),
                "market": "東証",  # デフォルト値
                "website": info.get('website', ''),
                "country": "Japan"
            }
            
            # データの検証
            if not basic_info["company_name"]:
                logger.warning(f"Company name not found for {ticker}")
            if not basic_info["sector"]:
                logger.warning(f"Sector not found for {ticker}")
            if not basic_info["industry"]:
                logger.warning(f"Industry not found for {ticker}")
            
            logger.info(f"Basic info collected for {ticker}: {basic_info}")
            return basic_info
            
        except Exception as e:
            logger.error(f"Error collecting basic info for {ticker}: {str(e)}")
            return {
                "company_name": "",
                "sector": "",
                "industry": "",
                "description": "",
                "market": "東証",
                "website": "",
                "country": "Japan"
            }

    async def collect_financial_data(self, ticker: str):
        """Yahoo FinanceとNikkeiから財務データを収集"""
        logger.info(f"Collecting financial data for {ticker}")
        try:
            # Yahoo Financeから財務データを取得
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(None, lambda: yf.Ticker(f"{ticker}.T"))
            info = ticker_obj.info
            
            # 日経からデータを取得
            nikkei_data = await self.collect_nikkei_data(ticker)
            
            # 日経とYahoo Financeの財務データを組み合わせる（日経のデータを優先）
            financial_data = {
                "revenue": nikkei_data.get('revenue') or info.get('totalRevenue', 0),
                "operating_profit": nikkei_data.get('operating_profit') or info.get('operatingIncome', 0),
                "net_profit": nikkei_data.get('net_profit') or info.get('netIncome', 0),
                "total_assets": nikkei_data.get('total_assets') or info.get('totalAssets', 0),
                "equity": nikkei_data.get('equity') or info.get('totalStockholderEquity', 0),
                "eps": nikkei_data.get('eps') or info.get('trailingEPS', 0),
                "bps": nikkei_data.get('bps') or info.get('bookValue', 0),
                "per": nikkei_data.get('per') or info.get('forwardPE', 0),
                "pbr": nikkei_data.get('pbr') or info.get('priceToBook', 0),
                "roe": nikkei_data.get('roe') or 0,
                "roa": nikkei_data.get('roa') or 0,
                "dividend_yield": nikkei_data.get('dividend_yield') or info.get('dividendYield', 0),
                "dividend_per_share": nikkei_data.get('dividend_per_share') or info.get('lastDividendValue', 0),
            }
            
            # 比率の計算（日経からデータが取得できなかった場合のみ）
            if not financial_data["roe"] and financial_data["equity"] != 0:
                financial_data["roe"] = financial_data["net_profit"] / financial_data["equity"]
                
            if not financial_data["roa"] and financial_data["total_assets"] != 0:
                financial_data["roa"] = financial_data["net_profit"] / financial_data["total_assets"]
            
            if financial_data["revenue"] != 0:
                financial_data["operating_margin"] = financial_data["operating_profit"] / financial_data["revenue"]
                financial_data["net_margin"] = financial_data["net_profit"] / financial_data["revenue"]
            else:
                financial_data["operating_margin"] = 0
                financial_data["net_margin"] = 0
            
            # データの検証
            for key, value in financial_data.items():
                if value == 0:
                    logger.warning(f"{key} is zero for {ticker}")
            
            logger.info(f"Financial data collected for {ticker}")
            return financial_data
            
        except Exception as e:
            logger.error(f"Error collecting financial data for {ticker}: {str(e)}")
            return {
                "revenue": 0,
                "operating_profit": 0,
                "net_profit": 0,
                "total_assets": 0,
                "equity": 0,
                "operating_margin": 0,
                "net_margin": 0,
                "roe": 0,
                "roa": 0
            }

    async def collect_stock_data(self, ticker: str):
        """Yahoo Financeから株価データを取得"""
        logger.info(f"Collecting stock data for {ticker}")
        try:
            loop = asyncio.get_event_loop()
            stock_data = await loop.run_in_executor(None, self._get_stock_data, f"{ticker}.T")
            logger.info(f"Stock data collected for {ticker}")
            return stock_data
        except Exception as e:
            logger.error(f"Error collecting stock data for {ticker}: {str(e)}")
            return {
                "market_price": 0,
                "volume": 0,
                "market_cap": 0,
                "shares_outstanding": 0,
                "per": 0,
                "pbr": 0,
                "eps": 0,
                "bps": 0,
                "dividend_yield": 0,
                "dividend_per_share": 0,
                "payout_ratio": 0,
                "beta": 0,
                "employees": 0,
                "collected_at": datetime.now(timezone.utc).isoformat()
            }

    def _get_stock_data(self, ticker_symbol: str):
        """株価データの取得（同期処理）"""
        stock = yf.Ticker(ticker_symbol)
        
        # 株価情報の取得
        hist = stock.history(period="1d")
        info = stock.info
        
        if hist.empty:
            logger.warning(f"No stock price data available for {ticker_symbol}")
            return {}
            
        try:
            data = {
                "market_price": float(hist['Close'].iloc[-1]),
                "volume": int(hist['Volume'].iloc[-1]),
                "market_cap": info.get('marketCap', 0),
                "shares_outstanding": info.get('sharesOutstanding', 0),
                "per": info.get('forwardPE', 0),
                "pbr": info.get('priceToBook', 0),
                "eps": info.get('trailingEPS', 0),
                "bps": info.get('bookValue', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "dividend_per_share": info.get('lastDividendValue', 0),
                "payout_ratio": info.get('payoutRatio', 0),
                "beta": info.get('beta', 0),
                "employees": info.get('fullTimeEmployees', 0),
                "collected_at": datetime.now(timezone.utc).isoformat()
            }
            
            # データの検証とクリーニング
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if value is None or str(value).lower() == 'nan':
                        data[key] = 0
                        logger.warning(f"{key} is None/NaN for {ticker_symbol}, setting to 0")
                    elif value == 0:
                        logger.warning(f"{key} is zero for {ticker_symbol}")
                    
            return data
            
        except Exception as e:
            logger.error(f"Error processing stock data for {ticker_symbol}: {str(e)}")
            return {}

    async def collect_all_data(self, ticker: str):
        """全てのデータを収集して結合"""
        logger.info(f"Starting data collection for {ticker}")
        try:
            # 基本情報の取得
            basic_info = await self.collect_basic_info(ticker)
            logger.info(f"Basic info: {basic_info}")
            
            # 株価データの取得（遅延を入れて制限回避）
            await asyncio.sleep(1)
            stock_data = await self.collect_stock_data(ticker)
            logger.info(f"Stock data: {stock_data}")
            
            # 財務データの取得
            financial_data = await self.collect_financial_data(ticker)
            logger.info(f"Financial data: {financial_data}")
            
            # データの結合
            combined_data = {
                "ticker": ticker,
                **basic_info,
                **stock_data,
                **financial_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Data collection completed for {ticker}")
            return combined_data

        except Exception as e:
            logger.error(f"Error in collect_all_data for {ticker}: {str(e)}")
            raise

    async def close(self):
        await self.session.close()
