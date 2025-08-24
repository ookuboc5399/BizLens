import React, { useState, useEffect } from 'react';
import { marketDataService, MarketData, SectorPerformance } from '../services/marketData';

interface MarketDataDisplayProps {
  type: 'market-data' | 'volume-analysis' | 'sector-performance';
}

export const MarketDataDisplay: React.FC<MarketDataDisplayProps> = ({ type }) => {
  const [data, setData] = useState<MarketData[] | SectorPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log(`Fetching ${type} data...`);
        let result;
        
        switch (type) {
          case 'market-data':
            result = await marketDataService.getMarketIndices();
            break;
          case 'volume-analysis':
            result = await marketDataService.getTopVolumeStocks();
            break;
          case 'sector-performance':
            result = await marketDataService.getSectorPerformance();
            break;
          default:
            result = [];
        }
        
        console.log(`${type} data result:`, result);
        setData(result);
        setError(null);
      } catch (err) {
        setError('データの取得に失敗しました');
        console.error('データ取得エラー:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [type]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-center h-48 flex items-center justify-center">
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-gray-400 text-center h-48 flex items-center justify-center">
        データがありません
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
  };

  const formatPrice = (price: number): string => {
    return price.toLocaleString('ja-JP', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const renderMarketData = () => {
    const marketData = data as MarketData[];
    return (
      <div className="space-y-2">
        {marketData.map((item, index) => (
          <div key={index} className="flex justify-between items-center">
            <span className="text-sm">{item.symbol}</span>
            <div className="text-right">
              <div className={`text-sm font-semibold ${item.change >= 0 ? 'text-red-500' : 'text-blue-500'}`}>
                {formatPrice(item.price)}
              </div>
              <div className={`text-xs ${item.change >= 0 ? 'text-red-400' : 'text-blue-400'}`}>
                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)} ({item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderVolumeAnalysis = () => {
    const volumeData = data as MarketData[];
    return (
      <div className="space-y-3">
        {volumeData.slice(0, 5).map((item, index) => (
          <div key={index} className="flex justify-between items-center">
            <div className="flex-1">
              <div className="text-sm font-medium">{item.symbol}</div>
              <div className="text-xs text-gray-400">
                出来高: {item.volume ? formatNumber(item.volume) : 'N/A'}
              </div>
            </div>
            <div className="text-right">
              <div className={`text-sm font-semibold ${item.change >= 0 ? 'text-red-500' : 'text-blue-500'}`}>
                {formatPrice(item.price)}
              </div>
              <div className={`text-xs ${item.change >= 0 ? 'text-red-400' : 'text-blue-400'}`}>
                {item.change >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderSectorPerformance = () => {
    const sectorData = data as SectorPerformance[];
    return (
      <div className="space-y-3">
        {sectorData.map((item, index) => (
          <div key={index} className="flex justify-between items-center">
            <span className="text-sm">{item.sector}</span>
            <div className="text-right">
              <div className={`text-sm font-semibold ${item.change >= 0 ? 'text-red-500' : 'text-blue-500'}`}>
                {formatPrice(item.performance)}
              </div>
              <div className={`text-xs ${item.change >= 0 ? 'text-red-400' : 'text-blue-400'}`}>
                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  switch (type) {
    case 'market-data':
      return renderMarketData();
    case 'volume-analysis':
      return renderVolumeAnalysis();
    case 'sector-performance':
      return renderSectorPerformance();
    default:
      return <div>データがありません</div>;
  }
};
