import React, { useEffect, useRef, memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface TradingViewChartProps {
  symbol: string;
  market: string;
  companyName: string;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = memo(({ 
  symbol, 
  market, 
  companyName 
}) => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;

    // 既存のウィジェットをクリア
    container.current.innerHTML = '';

    // 市場に応じてシンボルを調整
    let tradingViewSymbol = symbol;
    
    // 日本市場の場合、.Tを追加
    if (market === 'JP') {
      tradingViewSymbol = `${symbol}.T`;
    }
    // 米国市場の場合、NASDAQ:プレフィックスを追加
    else if (market === 'US') {
      tradingViewSymbol = `NASDAQ:${symbol}`;
    }
    // 中国市場の場合、.HKを追加（香港市場として）
    else if (market === 'CN') {
      tradingViewSymbol = `${symbol}.HK`;
    }

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = `
      {
        "allow_symbol_change": true,
        "calendar": false,
        "details": false,
        "hide_side_toolbar": true,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "hide_volume": false,
        "hotlist": false,
        "interval": "D",
        "locale": "ja",
        "save_image": true,
        "style": "1",
        "symbol": "${tradingViewSymbol}",
        "theme": "light",
        "timezone": "Asia/Tokyo",
        "backgroundColor": "#ffffff",
        "gridColor": "rgba(46, 46, 46, 0.06)",
        "watchlist": [],
        "withdateranges": false,
        "compareSymbols": [],
        "studies": [],
        "width": "100%",
        "height": 600
      }`;
    container.current.appendChild(script);

    return () => {
      if (container.current) {
        container.current.innerHTML = '';
      }
    };
  }, [symbol, market]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-800">
          {companyName} 株価チャート
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div 
          className="tradingview-widget-container" 
          ref={container}
          style={{ height: "600px", width: "100%", overflow: "hidden" }}
        >
          <div className="tradingview-widget-container__widget"></div>
          <div className="tradingview-widget-copyright">
            <a 
              href={`https://www.tradingview.com/symbols/${symbol}/`} 
              rel="noopener nofollow" 
              target="_blank"
            >
              <span className="blue-text">{symbol} stock chart</span>
            </a>
            <span className="trademark"> by TradingView</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});