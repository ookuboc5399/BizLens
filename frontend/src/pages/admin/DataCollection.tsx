import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { useAuth } from '../../hooks/useAuth';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { ScrollArea } from '../../components/ui/scroll-area';
import { SupabaseClient } from '@supabase/supabase-js';

const API_BASE_URL = '/api';

interface DataCollectionPageProps {
  supabase: SupabaseClient;
}

function DataCollectionPage({ supabase }: DataCollectionPageProps) {
  const { isAdmin } = useAuth(supabase);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);

  const handleCollectData = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setStatus('データ収集を開始します...');
    setLogs([]);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/data/collect`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'データ収集に失敗しました');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('レスポンスの読み取りに失敗しました');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.progress !== undefined) {
                setProgress(data.progress);
                if (data.current && data.total) {
                  const message = `${data.progress}% 完了 (${data.current}/${data.total}企業)`;
                  setStatus(message);
                  setLogs(prev => [...prev, message]);
                }
              }
              if (data.error) {
                setLogs(prev => [...prev, `エラー: ${data.error}`]);
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing progress data:', e);
            }
          }
        }
      }

      const completionMessage = 'データ収集が完了しました';
      setStatus(completionMessage);
      setLogs(prev => [...prev, completionMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'データ収集中にエラーが発生しました';
      setError(errorMessage);
      setLogs(prev => [...prev, `エラー: ${errorMessage}`]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCollectReports = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setStatus('決算資料の収集を開始します...');
    setLogs([]);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/financial-reports/fetch`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '決算資料の収集に失敗しました');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('レスポンスの読み取りに失敗しました');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.progress !== undefined) {
                setProgress(data.progress);
                if (data.message) {
                  setStatus(data.message);
                  setLogs(prev => [...prev, data.message]);
                }
              }
              if (data.error) {
                setLogs(prev => [...prev, `エラー: ${data.error}`]);
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing progress data:', e);
            }
          }
        }
      }

      const completionMessage = '決算資料の収集が完了しました';
      setStatus(completionMessage);
      setLogs(prev => [...prev, completionMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '決算資料の収集中にエラーが発生しました';
      setError(errorMessage);
      setLogs(prev => [...prev, `エラー: ${errorMessage}`]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">データ収集管理</h1>
        <Button 
          variant="outline" 
          onClick={() => navigate('/')}
          className="flex items-center gap-2"
        >
          ← ホームに戻る
        </Button>
      </div>

      <Tabs defaultValue="company-data">
        <TabsList>
          <TabsTrigger value="company-data">企業データ</TabsTrigger>
          <TabsTrigger value="financial-reports">決算資料</TabsTrigger>
        </TabsList>

        <TabsContent value="company-data">
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
        </TabsContent>

        <TabsContent value="financial-reports">
          <Card>
            <CardHeader>
              <CardTitle>決算資料収集</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-500 mb-4">
                EDINET、TDnet、企業サイトから決算資料を収集します。
                収集した資料はGoogle Cloud Storageに保存され、アプリ内で閲覧できるようになります。
              </div>
              <Button 
                onClick={handleCollectReports} 
                disabled={isLoading}
              >
                {isLoading ? '収集中...' : '決算資料を収集'}
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

              {/* ログ表示エリア */}
              {logs.length > 0 && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle>処理ログ</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                      {logs.map((log, index) => (
                        <div
                          key={index}
                          className={`text-sm ${
                            log.startsWith('エラー') ? 'text-red-500' : 'text-gray-700'
                          } mb-1`}
                        >
                          {log}
                        </div>
                      ))}
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DataCollectionPage;
