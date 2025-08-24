import React, { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ symbol }) => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.onload = () => {
      if (container.current) {
        new window.TradingView.MediumWidget({
          "container_id": container.current.id,
          "symbols": [[symbol]],
          "chartOnly": false,
          "width": "100%",
          "height": "100%",
          "locale": "ja",
          "colorTheme": "dark",
          "gridLineColor": "#2A2E39",
          "trendLineColor": "#1976D2",
          "fontColor": "#787B86",
          "underLineColor": "rgba(55, 166, 239, 0.15)",
          "isTransparent": true,
          "autosize": true,
          "container": container.current.id,
          "showFloatingTooltip": true
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [symbol]);

  return (
    <div 
      id={`tradingview_${symbol}`} 
      ref={container} 
      style={{ height: '400px', width: '100%' }}
    />
  );
}
