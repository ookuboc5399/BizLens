import { useEffect, useRef, memo } from 'react';

function TradingViewTickerTape() {
  const container = useRef<HTMLDivElement>(null);

  useEffect(
    () => {
      if (!container.current) return;

      container.current.innerHTML = ''; // Clear existing widgets

      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js";
      script.type = "text/javascript";
      script.async = true;
      script.innerHTML = `
        {
          "symbols": [
            {
              "proName": "FOREXCOM:SPXUSD",
              "title": "S&P 500 Index"
            },
            {
              "proName": "FOREXCOM:NSXUSD",
              "title": "US 100 Cash CFD"
            },
            {
              "proName": "FX_IDC:EURUSD",
              "title": "EUR to USD"
            },
            {
              "proName": "BITSTAMP:BTCUSD",
              "title": "Bitcoin"
            },
            {
              "proName": "BITSTAMP:ETHUSD",
              "title": "Ethereum"
            }
          ],
          "colorTheme": "light",
          "locale": "en",
          "largeChartUrl": "",
          "isTransparent": false,
          "showSymbolLogo": true,
          "displayMode": "adaptive"
        }`;
      container.current.appendChild(script);

      return () => {
        if (container.current) {
          container.current.innerHTML = '';
        }
      };
    },
    []
  );

  return (
    <div className="tradingview-widget-container" ref={container}>
      <div className="tradingview-widget-container__widget"></div>
      <div className="tradingview-widget-copyright">
        <a href="https://www.tradingview.com/markets/" rel="noopener nofollow" target="_blank">
          <span className="blue-text">Ticker tape</span>
        </a>
        <span className="trademark"> by TradingView</span>
      </div>
    </div>
  );
}

export default memo(TradingViewTickerTape);


