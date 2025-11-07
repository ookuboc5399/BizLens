import React, { useEffect, useRef, memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface TradingViewAdvancedChartProps {
  symbol: string;
  market: string;
  companyName: string;
}

export const TradingViewAdvancedChart: React.FC<TradingViewAdvancedChartProps> = memo(({ 
  symbol, 
  market, 
  companyName 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // 既存のウィジェットをクリア
    containerRef.current.innerHTML = '';

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
    script.innerHTML = JSON.stringify({
      "autosize": true,
      "symbol": tradingViewSymbol,
      "interval": "D",
      "timezone": "Asia/Tokyo",
      "theme": "light",
      "style": "1",
      "locale": "ja",
      "toolbar_bg": "#f1f3f4",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": `tradingview_${symbol}_${Date.now()}`,
      "studies": [
        "RSI@tv-basicstudies",
        "MACD@tv-basicstudies",
        "Volume@tv-basicstudies"
      ],
      "show_popup_button": true,
      "popup_width": "1000",
      "popup_height": "650",
      "no_referral_id": true,
      "referrer_id": "bizlens",
      "hide_side_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "details": true,
      "hotlist": true,
      "calendar": true,
      "show_volume": true,
      "hide_volume": false,
      "volume_analysis": true,
      "support_multicharts": true,
      "disabled_features": [
        "use_localstorage_for_settings",
        "volume_force_overlay",
        "create_volume_indicator_by_default"
      ],
      "enabled_features": [
        "side_toolbar_in_fullscreen_mode",
        "header_in_fullscreen_mode"
      ],
      "overrides": {
        "paneProperties.background": "#ffffff",
        "paneProperties.vertGridProperties.color": "#e1e1e1",
        "paneProperties.horzGridProperties.color": "#e1e1e1",
        "symbolWatermarkProperties.transparency": 90,
        "scalesProperties.textColor": "#131722"
      }
    });

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbol, market]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-800">
          {companyName} 詳細チャート
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div 
          ref={containerRef}
          id={`tradingview_${symbol}_${Date.now()}`}
          className="w-full h-96"
        />
      </CardContent>
    </Card>
  );
});


