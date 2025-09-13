// Google OAuth認証サービス
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const GOOGLE_CLIENT_SECRET = import.meta.env.VITE_GOOGLE_CLIENT_SECRET || '';

export interface GoogleAuthConfig {
  clientId: string;
  scope: string;
  redirectUri: string;
}

export interface GoogleAuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
}

class GoogleAuthService {
  private token: GoogleAuthToken | null = null;
  private tokenExpiry: number = 0;

  constructor() {
    // ローカルストレージからトークンを復元
    const savedToken = localStorage.getItem('google_auth_token');
    if (savedToken) {
      try {
        this.token = JSON.parse(savedToken);
        this.tokenExpiry = parseInt(localStorage.getItem('google_auth_token_expiry') || '0');
      } catch (error) {
        console.error('トークンの復元に失敗:', error);
        this.clearToken();
      }
    }
  }

  // OAuth認証を開始
  async authenticate(): Promise<GoogleAuthToken> {
    if (!GOOGLE_CLIENT_ID) {
      throw new Error('Google Client IDが設定されていません');
    }

    const config: GoogleAuthConfig = {
      clientId: GOOGLE_CLIENT_ID,
      scope: 'https://www.googleapis.com/auth/drive.readonly',
      redirectUri: window.location.origin + '/auth/callback'
    };

    // Google OAuth認証URLを生成
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${encodeURIComponent(config.clientId)}&` +
      `redirect_uri=${encodeURIComponent(config.redirectUri)}&` +
      `scope=${encodeURIComponent(config.scope)}&` +
      `response_type=code&` +
      `access_type=offline&` +
      `prompt=consent`;

    // 認証ページにリダイレクト
    window.location.href = authUrl;
    
    // この時点ではトークンを返せないので、Promiseを待機状態にする
    return new Promise((resolve, reject) => {
      // 認証コールバックでトークンを取得する
      this.waitForAuthCallback().then(resolve).catch(reject);
    });
  }

  // 認証コールバックを待機
  private async waitForAuthCallback(): Promise<GoogleAuthToken> {
    return new Promise((resolve, reject) => {
      const checkAuth = () => {
        const token = localStorage.getItem('google_auth_token');
        if (token) {
          try {
            const parsedToken = JSON.parse(token);
            resolve(parsedToken);
          } catch (error) {
            reject(error);
          }
        } else {
          setTimeout(checkAuth, 100);
        }
      };
      checkAuth();
    });
  }

  // 認証コードからトークンを取得
  async getTokenFromCode(code: string): Promise<GoogleAuthToken> {
    const response = await fetch('/api/auth/google/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      throw new Error('トークン取得に失敗しました');
    }

    const token = await response.json();
    this.setToken(token);
    return token;
  }

  // トークンを設定
  private setToken(token: GoogleAuthToken): void {
    this.token = token;
    this.tokenExpiry = Date.now() + (token.expires_in * 1000);
    
    localStorage.setItem('google_auth_token', JSON.stringify(token));
    localStorage.setItem('google_auth_token_expiry', this.tokenExpiry.toString());
  }

  // 有効なトークンを取得
  async getValidToken(): Promise<string | null> {
    if (!this.token) {
      return null;
    }

    // トークンが期限切れの場合は更新を試行
    if (Date.now() >= this.tokenExpiry) {
      try {
        await this.refreshToken();
      } catch (error) {
        console.error('トークン更新に失敗:', error);
        this.clearToken();
        return null;
      }
    }

    return this.token.access_token;
  }

  // トークンを更新
  private async refreshToken(): Promise<void> {
    if (!this.token?.refresh_token) {
      throw new Error('リフレッシュトークンがありません');
    }

    const response = await fetch('/api/auth/google/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        refresh_token: this.token.refresh_token 
      }),
    });

    if (!response.ok) {
      throw new Error('トークン更新に失敗しました');
    }

    const newToken = await response.json();
    this.setToken(newToken);
  }

  // トークンをクリア
  clearToken(): void {
    this.token = null;
    this.tokenExpiry = 0;
    localStorage.removeItem('google_auth_token');
    localStorage.removeItem('google_auth_token_expiry');
  }

  // 認証状態を確認
  isAuthenticated(): boolean {
    return this.token !== null && Date.now() < this.tokenExpiry;
  }

  // ログアウト
  logout(): void {
    this.clearToken();
    // Googleのログアウトページにリダイレクト
    window.location.href = 'https://accounts.google.com/logout';
  }
}

export const googleAuthService = new GoogleAuthService();
