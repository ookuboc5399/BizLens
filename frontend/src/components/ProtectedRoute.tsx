import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SupabaseClient } from '@supabase/supabase-js'; // SupabaseClientをインポート

// ProtectedRouteコンポーネントがsupabaseプロップを受け取るように型定義
interface ProtectedRouteProps {
  children: React.ReactNode;
  supabase: SupabaseClient; // supabaseインスタンスを受け取る
}

// ProtectedRouteコンポーネントがsupabaseプロップを受け取るように修正
export function ProtectedRoute({ children, supabase }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuth(supabase); // useAuthフックにsupabaseインスタンスを渡す

  if (!isAuthenticated) {
    // ログインしていない場合はログインページにリダイレクト
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
}
