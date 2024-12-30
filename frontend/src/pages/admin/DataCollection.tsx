import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";

const API_BASE_URL = 'http://localhost:8000';

function DataCollectionPage() {
  const { isAdmin } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>('');

  const handleCollectData = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setStatus('データ収集を開始します...');
    console.log('Starting data collection...');

    try {
      console.log('Sending request to API...');
      const response = await fetch(`${API_BASE_URL}/api/companies/collect-data`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Origin': 'http://localhost:5173'
        },
        credentials: 'include',
        mode: 'cors'
      });

      if (!response.ok) {
        console.error('API response not OK:', response.status, response.statusText);
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Method Not Allowed');
      }

      console.log('Got response, starting to read stream...');
      const reader = response.body?.getReader();
      if (!reader) throw new Error('レスポンスの読み取りに失敗しました');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('Stream completed');
          break;
        }

        const chunk = decoder.decode(value);
        console.log('Received chunk:', chunk);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              console.log('Parsed progress data:', data);
              if (data.progress !== undefined) {
                setProgress(data.progress);
                if (data.current && data.total) {
                  const statusText = `${data.progress}% 完了 (${data.current}/${data.total}企業)`;
                  console.log('Updating status:', statusText);
                  setStatus(statusText);
                }
              }
              if (data.error) {
                console.error('Received error:', data.error);
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing progress data:', line, e);
            }
          }
        }
      }

      setStatus('データ収集が完了しました');
    } catch (error) {
      console.error('Data collection failed:', error);
      setError(error instanceof Error ? error.message : 'データ収集中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAdmin) {
    return <div>アクセス権限がありません</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <h1 className="text-2xl font-bold">データ収集管理</h1>

      <Card>
        <CardHeader>
          <CardTitle>企業データ収集</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleCollectData} 
            disabled={isLoading}
          >
            {isLoading ? 'データ収集中...' : 'データを収集'}
          </Button>

          {isLoading && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-muted-foreground">{status}</p>
            </div>
          )}

          {error && (
            <p className="text-red-500 mt-2">{error}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DataCollectionPage; 