import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from '../hooks/useAuth'; // useAuthフックをインポート
import { SupabaseClient } from '@supabase/supabase-js'; // SupabaseClientをインポート

// Loginコンポーネントがsupabaseプロップを受け取るように型定義
interface LoginProps {
  supabase: SupabaseClient;
}

// Loginコンポーネントがsupabaseプロップを受け取るように修正
function Login({ supabase }: LoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { login } = useAuth(supabase); // useAuthフックにsupabaseインスタンスを渡す

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("handleLogin called");
    setError(null);

    const result = await login(email, password);

    if (result.success) {
      navigate('/');
    } else {
      setError(result.message || 'ログインに失敗しました');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <Card>
        <CardHeader>
          <CardTitle>ログイン</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Input
              type="email"
              placeholder="メールアドレス"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="パスワード"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button type="submit" className="w-full">ログイン</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default Login;
