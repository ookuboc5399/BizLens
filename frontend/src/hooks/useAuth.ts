interface AuthUser {
  id: string;
  email: string;
  role: 'admin' | 'user';
}

export function useAuth() {
  // TODO: 実際の認証ロジックを実装
  // 今はテスト用に常に管理者権限を持つように
  const user: AuthUser = {
    id: '1',
    email: 'admin@example.com',
    role: 'admin'
  };

  return {
    user,
    isAdmin: user.role === 'admin',
    isAuthenticated: true,
    login: async () => {},
    logout: async () => {},
  };
} 