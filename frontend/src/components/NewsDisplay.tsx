import React, { useState, useEffect } from 'react';
import { marketDataService, NewsItem } from '../services/marketData';

export const NewsDisplay: React.FC = () => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const newsData = await marketDataService.getNews();
        setNews(newsData);
        setError(null);
      } catch (err) {
        setError('ニュースの取得に失敗しました');
        console.error('ニュース取得エラー:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

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

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes}分前`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}時間前`;
    } else {
      return date.toLocaleDateString('ja-JP');
    }
  };

  return (
    <div className="space-y-3">
      {news.map((item, index) => (
        <div key={index} className="border-b border-gray-700 pb-3 last:border-b-0">
          <div className="flex justify-between items-start mb-1">
            <h4 className="text-sm font-medium text-blue-400 hover:text-blue-300 cursor-pointer line-clamp-2">
              {item.title}
            </h4>
            <span className="text-xs text-gray-400 ml-2 flex-shrink-0">
              {formatTime(item.publishedAt)}
            </span>
          </div>
          <p className="text-xs text-gray-300 line-clamp-2 mb-1">
            {item.description}
          </p>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">{item.source}</span>
            {item.url !== '#' && (
              <a 
                href={item.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                詳細 →
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
