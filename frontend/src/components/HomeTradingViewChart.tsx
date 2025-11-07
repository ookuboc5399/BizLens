import React, { useEffect, useRef, memo } from 'react';

interface HomeTradingViewChartProps {
  symbol: string;
}

export const HomeTradingViewChart: React.FC<HomeTradingViewChartProps> = memo(({ symbol }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // 既存のウィジェットをクリア
    containerRef.current.innerHTML = '';

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      "symbol": symbol,
      "chartOnly": false,
      "dateRange": "12M",
      "noTimeScale": false,
      "colorTheme": "dark",
      "isTransparent": false,
      "locale": "ja",
      "width": "100%",
      "autosize": true,
      "height": "100%"
    });

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbol]);

  return (
    <div className="tradingview-widget-container" ref={containerRef}>
      <div className="tradingview-widget-container__widget"></div>
      <div className="tradingview-widget-copyright">
        <a 
          href={`https://www.tradingview.com/symbols/${symbol}/`} 
          rel="noopener nofollow" 
          target="_blank"
        >
          <span className="blue-text">{symbol} stock price</span>
        </a>
        <span className="trademark"> by TradingView</span>
      </div>
    </div>
  );
});


