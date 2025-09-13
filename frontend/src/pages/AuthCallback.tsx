import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { googleAuthService } from '../services/googleAuthService';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const error = searchParams.get('error');

        if (error) {
          setError(`認証エラー: ${error}`);
          setStatus('error');
          return;
        }

        if (!code) {
          setError('認証コードが見つかりません');
          setStatus('error');
          return;
        }

        // 認証コードからトークンを取得
        await googleAuthService.getTokenFromCode(code);
        
        setStatus('success');
        
        // 成功後、元のページに戻る
        setTimeout(() => {
          navigate('/financial-reports');
        }, 2000);

      } catch (err) {
        console.error('認証コールバックエラー:', err);
        setError('認証に失敗しました');
        setStatus('error');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>認証中...</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={undefined} className="w-full" />
            <p className="text-sm text-gray-500">Googleアカウントで認証しています...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>認証エラー</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => navigate('/financial-reports')}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
            >
              戻る
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="w-96">
        <CardHeader>
          <CardTitle>認証成功</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-green-500">Googleアカウントでの認証が完了しました</p>
          <p className="text-sm text-gray-500">決算資料ページにリダイレクトします...</p>
        </CardContent>
      </Card>
    </div>
  );
}
