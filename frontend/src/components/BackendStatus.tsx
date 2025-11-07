import { useState, useEffect } from 'react';

interface BackendStatusProps {
  className?: string;
}

export const BackendStatus: React.FC<BackendStatusProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [apiUrl, setApiUrl] = useState<string>('');

  useEffect(() => {
    const checkBackendConnection = async () => {
      const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
      setApiUrl(API_BASE_URL);

      try {
        // タイムアウトを設定（5秒）
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${API_BASE_URL}/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'healthy') {
            setStatus('connected');
          } else {
            setStatus('disconnected');
          }
        } else {
          setStatus('disconnected');
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          console.error('Backend connection check timed out');
        } else {
          console.error('Backend connection check failed:', error);
        }
        setStatus('disconnected');
      }
    };

    // 初回チェック
    checkBackendConnection();

    // 30秒ごとにチェック
    const interval = setInterval(checkBackendConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'disconnected':
        return 'bg-red-500';
      case 'checking':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return '接続中';
      case 'disconnected':
        return '切断';
      case 'checking':
        return '確認中';
      default:
        return '不明';
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex items-center gap-1">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`}></div>
        <span className="text-xs text-gray-300">
          {getStatusText()}
        </span>
      </div>
      <span className="text-xs text-gray-500" title={`API URL: ${apiUrl}`}>
        ({apiUrl === '/api' ? '相対パス' : apiUrl})
      </span>
    </div>
  );
};
