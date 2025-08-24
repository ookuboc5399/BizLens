// 市場データAPIサービス
const API_KEY = '7V74LNWZOR8ZG6BD'; // Alpha Vantageの無料APIキー
const BASE_URL = 'https://www.alphavantage.co/query';

// NewsAPIの設定
const NEWS_API_KEY = import.meta.env.VITE_NEWS_API_KEY || 'demo';
const NEWS_API_URL = 'https://newsapi.org/v2';

export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
}

export interface SectorPerformance {
  sector: string;
  performance: number;
  change: number;
}

export interface NewsItem {
  title: string;
  description: string;
  publishedAt: string;
  url: string;
  source: string;
}

export const marketDataService = {
  // 日経平均とTOPIXのデータを取得
  async getMarketIndices(): Promise<MarketData[]> {
    try {
      // 日本の主要指数のシンボル
      const symbols = ['^N225', '^TOPIX', '^DJI', '^GSPC']; // 日経平均、TOPIX、ダウ、S&P500
      const promises = symbols.map(async (symbol) => {
        const response = await fetch(
          `${BASE_URL}?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${API_KEY}`
        );
        const data = await response.json();
        
        if (data['Global Quote']) {
          const quote = data['Global Quote'];
          const symbolName = this.getSymbolName(symbol);
          return {
            symbol: symbolName,
            price: parseFloat(quote['05. price']),
            change: parseFloat(quote['09. change']),
            changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
            volume: parseInt(quote['06. volume'])
          };
        }
        return null;
      });

      const results = await Promise.all(promises);
      const validResults = results.filter(Boolean) as MarketData[];
      
      // 結果が空の場合はフォールバックデータを返す
      if (validResults.length === 0) {
        console.log('APIからデータが取得できませんでした。フォールバックデータを使用します。');
        return this.getFallbackMarketData();
      }
      
      return validResults;
    } catch (error) {
      console.error('市場データの取得に失敗:', error);
      return this.getFallbackMarketData();
    }
  },

  // シンボル名を日本語に変換
  getSymbolName(symbol: string): string {
    const symbolMap: { [key: string]: string } = {
      '^N225': '日経平均',
      '^TOPIX': 'TOPIX',
      '^DJI': 'ダウ平均',
      '^GSPC': 'S&P500'
    };
    return symbolMap[symbol] || symbol;
  },

  // フォールバック市場データ
  getFallbackMarketData(): MarketData[] {
    return [
      {
        symbol: '日経平均',
        price: 35000.00,
        change: 150.50,
        changePercent: 0.43,
        volume: 1234567
      },
      {
        symbol: 'TOPIX',
        price: 2500.00,
        change: 12.30,
        changePercent: 0.49,
        volume: 987654
      },
      {
        symbol: 'ダウ平均',
        price: 38000.00,
        change: 200.00,
        changePercent: 0.53,
        volume: 2345678
      },
      {
        symbol: 'S&P500',
        price: 4800.00,
        change: 25.00,
        changePercent: 0.52,
        volume: 3456789
      }
    ];
  },

  // 出来高上位銘柄を取得
  async getTopVolumeStocks(): Promise<MarketData[]> {
    try {
      // 主要銘柄のシンボルリスト
      const symbols = ['7203.T', '6758.T', '9984.T', '6861.T', '6954.T']; // トヨタ、ソニー、ソフトバンクG、キーエンス、ファナック
      const promises = symbols.map(async (symbol) => {
        const response = await fetch(
          `${BASE_URL}?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${API_KEY}`
        );
        const data = await response.json();
        
        if (data['Global Quote']) {
          const quote = data['Global Quote'];
          return {
            symbol: quote['01. symbol'],
            price: parseFloat(quote['05. price']),
            change: parseFloat(quote['09. change']),
            changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
            volume: parseInt(quote['06. volume'])
          };
        }
        return null;
      });

      const results = await Promise.all(promises);
      const validResults = results.filter(Boolean) as MarketData[];
      
      // 出来高でソート
      return validResults.sort((a, b) => (b.volume || 0) - (a.volume || 0));
    } catch (error) {
      console.error('出来高データの取得に失敗:', error);
      // フォールバックデータ
      return [
        {
          symbol: '7203.T',
          price: 2500.00,
          change: 25.50,
          changePercent: 1.03,
          volume: 15000000
        },
        {
          symbol: '6758.T',
          price: 12000.00,
          change: -120.00,
          changePercent: -0.99,
          volume: 12000000
        },
        {
          symbol: '9984.T',
          price: 8500.00,
          change: 85.00,
          changePercent: 1.01,
          volume: 10000000
        }
      ];
    }
  },

  // 業種別パフォーマンスを取得
  async getSectorPerformance(): Promise<SectorPerformance[]> {
    try {
      // 業種別ETFのシンボル
      const sectorETFs = [
        { symbol: 'XLK', sector: 'テクノロジー' },
        { symbol: 'XLF', sector: '金融' },
        { symbol: 'XLE', sector: 'エネルギー' },
        { symbol: 'XLV', sector: 'ヘルスケア' },
        { symbol: 'XLI', sector: '工業' }
      ];

      const promises = sectorETFs.map(async ({ symbol, sector }) => {
        const response = await fetch(
          `${BASE_URL}?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${API_KEY}`
        );
        const data = await response.json();
        
        if (data['Global Quote']) {
          const quote = data['Global Quote'];
          return {
            sector,
            performance: parseFloat(quote['05. price']),
            change: parseFloat(quote['09. change'])
          };
        }
        return null;
      });

      const results = await Promise.all(promises);
      return results.filter(Boolean) as SectorPerformance[];
    } catch (error) {
      console.error('業種別パフォーマンスの取得に失敗:', error);
      // フォールバックデータ
      return [
        { sector: 'テクノロジー', performance: 150.25, change: 2.50 },
        { sector: '金融', performance: 35.80, change: -0.30 },
        { sector: 'エネルギー', performance: 85.40, change: 1.20 },
        { sector: 'ヘルスケア', performance: 125.60, change: 0.80 },
        { sector: '工業', performance: 95.30, change: -0.50 }
      ];
    }
  },

  // 実際のニュースを取得（NewsAPI使用）
  async getNews(): Promise<NewsItem[]> {
    try {
      // NewsAPIを使用して実際のニュースを取得
      const response = await fetch(
        `${NEWS_API_URL}/everything?` +
        `q=stock market OR "日経平均" OR "株式市場" OR "金融市場"&` +
        `language=ja&` +
        `sortBy=publishedAt&` +
        `pageSize=5&` +
        `apiKey=${NEWS_API_KEY}`
      );

      if (!response.ok) {
        throw new Error(`NewsAPI error: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === 'ok' && data.articles) {
        return data.articles.map((article: any) => ({
          title: article.title,
          description: article.description || article.content?.substring(0, 100) + '...' || '詳細なし',
          publishedAt: article.publishedAt,
          url: article.url,
          source: article.source?.name || 'Unknown'
        }));
      } else {
        throw new Error('NewsAPI response format error');
      }
    } catch (error) {
      console.error('ニュースの取得に失敗:', error);
      
      // NewsAPIが失敗した場合のフォールバック
      if (NEWS_API_KEY === 'demo') {
        console.log('デモAPIキーのため、モックデータを使用します。');
      }
      
      return [
        {
          title: '日経平均、3万5000円台で推移 米国株高を受けて上昇',
          description: '東京株式市場で日経平均株価が3万5000円台で推移している。米国株高を受けて上昇基調を維持。',
          publishedAt: new Date().toISOString(),
          url: '#',
          source: 'Yahoo Finance'
        },
        {
          title: '米国金利動向に注目 市場関係者が注視',
          description: '米連邦準備制度理事会（FRB）の金融政策を巡り、市場関係者が注視している。',
          publishedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          url: '#',
          source: 'Reuters'
        },
        {
          title: '円安進行で輸出企業の業績改善期待',
          description: '円安進行により、輸出企業の業績改善が期待されている。',
          publishedAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
          url: '#',
          source: 'Bloomberg'
        },
        {
          title: 'AI関連株が上昇 テクノロジーセクターが好調',
          description: '人工知能（AI）関連株が上昇し、テクノロジーセクター全体が好調な展開を見せている。',
          publishedAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
          url: '#',
          source: 'TechCrunch'
        },
        {
          title: 'ESG投資が拡大 環境配慮企業に注目集まる',
          description: '環境・社会・ガバナンス（ESG）投資が拡大し、環境配慮企業への注目が高まっている。',
          publishedAt: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
          url: '#',
          source: 'Financial Times'
        }
      ];
    }
  }
};
