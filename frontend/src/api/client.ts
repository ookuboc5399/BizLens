import axios from 'axios'

export interface CompanyMetrics {
  id: string
  name: string
  ticker: string
  latest_metrics: {
    revenue: number
    operating_income: number
    net_income: number
    roe: number
    per: number
    fiscal_year: number
    fiscal_quarter: number
  }
}

export interface CompanyComparison {
  company: CompanyMetrics
  peer_companies: CompanyMetrics[]
  industry_averages: {
    revenue: number
    operating_income: number
    net_income: number
    roe: number
    per: number
  }
}

export interface ChatMessage {
  message: string
}

export interface ChatResponse {
  response: string
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const companyApi = {
  searchCompanies: async (query: string): Promise<CompanyMetrics[]> => {
    try {
      const response = await apiClient.get<CompanyMetrics[]>(`/api/companies/search?q=${encodeURIComponent(query)}`)
      return response.data
    } catch (error) {
      console.error('Error searching companies:', error)
      throw error
    }
  },
  screenCompanies: async (minRevenue: number, minRoe: number, maxPer: number): Promise<CompanyMetrics[]> => {
    try {
      console.log('Making API request with params:', {
        min_revenue: minRevenue,
        min_roe: minRoe,
        max_per: maxPer
      })
      const response = await apiClient.get<CompanyMetrics[]>('/api/companies/screen', {
        params: {
          min_revenue: minRevenue,
          min_roe: minRoe,
          max_per: maxPer,
        },
      })
      console.log('API response:', response)
      return response.data
    } catch (error) {
      console.error('Error screening companies:', error)
      throw error
    }
  },
  getCompanyComparison: async (ticker: string): Promise<CompanyComparison> => {
    try {
      const response = await apiClient.get<CompanyComparison>(`/api/companies/${encodeURIComponent(ticker)}/comparison`)
      return response.data
    } catch (error) {
      console.error('Error getting company comparison:', error)
      throw error
    }
  },
}

export const chatApi = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/api/chat', { message })
    return response.data
  },
}

export default apiClient
