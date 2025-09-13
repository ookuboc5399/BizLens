import React, { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ symbol }) => {
  const container = useRef<HTMLDivElement>(null);
  
  console.log('TradingViewChart: Loading symbol:', symbol);

  useEffect(() => {
    if (!container.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      const initializeWidget = () => {
        if (window.TradingView && window.TradingView.widget) {
          if (container.current) {
            console.log('TradingViewChart: Initializing widget for symbol:', symbol);
            new window.TradingView.widget({
              "width": "100%",
              "height": "400",
              "symbol": symbol,
              "interval": "D",
              "timezone": "Asia/Tokyo",
              "theme": "dark",
              "style": "1",
              "locale": "ja",
              "toolbar_bg": "#f1f3f6",
              "enable_publishing": false,
              "hide_top_toolbar": false,
              "hide_legend": false,
              "save_image": false,
              "container_id": container.current.id,
              "studies": [
                "MASimple@tv-basicstudies",
                "RSI@tv-basicstudies"
              ],
              "show_popup_button": true,
              "popup_width": "1000",
              "popup_height": "650"
            });
          }
        } else {
          // TradingViewオブジェクトがまだ利用可能でない場合、少し待って再試行
          setTimeout(initializeWidget, 100);
        }
      };
      initializeWidget();
    };
    
    script.onerror = () => {
      console.error('Failed to load TradingView script');
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
      id={`tradingview_${symbol.replace(/[^a-zA-Z0-9]/g, '_')}`} 
      ref={container} 
      style={{ height: '400px', width: '100%' }}
    />
  );
}
