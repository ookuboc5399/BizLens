import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// API設定
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// 型定義
export interface Company {
  ticker: string;
  company_name: string;
  market: string;
  sector: string;
  industry: string;
  country: string;
  website: string;
  business_description: string;
  market_cap: number | null;
  current_price: number | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  roa: number | null;
  dividend_yield: number | null;
  company_type: string | null;
  ceo: string | null;
}

export interface CompanyMetrics {
  // 企業メトリクスの型定義
}

export interface CompanyComparison {
  // 企業比較の型定義
}

export const companyApi = {
  // 企業関連API
  getCompanies: async () => {
    const response = await fetch(`${API_BASE_URL}/companies`);
    return response.json();
  },
  
  getCompany: async (id: string) => {
    const response = await fetch(`${API_BASE_URL}/companies/${id}`);
    return response.json();
  }
};

export const chatApi = {
  // チャット関連API
  sendMessage: async (message: string) => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    return response.json();
  }
};

export const apiClient = {
  // 基本設定
  baseURL: API_BASE_URL,
  
  // ヘルスチェック
  async healthCheck() {
    const response = await fetch(`${this.baseURL}/health`);
    return response.json();
  },

  // 企業関連
  async getCompanies() {
    const response = await fetch(`${this.baseURL}/companies`);
    return response.json();
  },

  async getCompany(id: string) {
    const response = await fetch(`${this.baseURL}/companies/${id}`);
    return response.json();
  },

  // 決算関連
  async getEarningsCalendar() {
    const response = await fetch(`${this.baseURL}/earnings`);
    return response.json();
  },

  async getFinancialReports() {
    const response = await fetch(`${this.baseURL}/financial-reports`);
    return response.json();
  },

  // 管理者関連
  async getAdminData() {
    const response = await fetch(`${this.baseURL}/admin`);
    return response.json();
  },

  // チャット関連
  async sendChatMessage(message: string) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    return response.json();
  }
};
