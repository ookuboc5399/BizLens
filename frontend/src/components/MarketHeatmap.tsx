import React from 'react';

interface MarketHeatmapProps {
  className?: string;
}

const MarketHeatmap: React.FC<MarketHeatmapProps> = ({ className }) => {
  const tradingViewUrl = "https://jp.tradingview.com/heatmap/stock/?color=change&dataset=NASDAQ100&group=sector&size=market_cap_basic";

  return (
    <div className={className}>
      <div className="relative w-full h-full">
        <iframe
          src={tradingViewUrl}
          className="absolute inset-0 w-full h-full"
          frameBorder="0"
          allowTransparency={true}
          scrolling="no"
          style={{
            backgroundColor: 'transparent',
            transform: 'scale(1)',
            transformOrigin: 'center center',
            minHeight: '400px'
          }}
        />
      </div>
    </div>
  );
};

export default MarketHeatmap;
