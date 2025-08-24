import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SupabaseClient } from '@supabase/supabase-js'; // SupabaseClientをインポート

// AdminRouteコンポーネントがsupabaseプロップを受け取るように型定義
interface AdminRouteProps {
  children: React.ReactNode;
  supabase: SupabaseClient; // supabaseインスタンスを受け取る
}

// AdminRouteコンポーネントがsupabaseプロップを受け取るように修正
export function AdminRoute({ children, supabase }: AdminRouteProps) {
  const { isAuthenticated, isAdmin, user, isInitialized } = useAuth(supabase); // useAuthフックにsupabaseインスタンスを渡す

  console.log('AdminRoute - isAuthenticated:', isAuthenticated);
  console.log('AdminRoute - isAdmin:', isAdmin);
  console.log('AdminRoute - user:', user);
  console.log('AdminRoute - isInitialized:', isInitialized);

  // デバッグ用：常に何かを表示
  if (!isInitialized) {
    console.log('AdminRoute - Loading authentication state...');
    return <div>Loading authentication state...</div>;
  }

  if (!isAuthenticated) {
    // ログインしていない場合は管理者用ログインページにリダイレクト
    console.log('AdminRoute - Redirecting to admin login');
    return <Navigate to="/admin/login" />;
  }

  if (!isAdmin) {
    // 管理者ではない場合はホームにリダイレクト
    console.log('AdminRoute - Redirecting to home (not admin)');
    return <Navigate to="/" />;
  }

  console.log('AdminRoute - Rendering admin content');
  return <>{children}</>;
}