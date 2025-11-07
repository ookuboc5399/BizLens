import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { TradingViewChart } from '../components/TradingViewChart';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { formatNumber, formatFinancialData } from '../utils/format';

interface CompanyData {
  ticker: string;
  company_name: string;
  market: string;
  sector: string;
  industry: string;
  country: string;
  website: string;
  business_description: string;
  data_source: string;
  last_updated: string;
  current_price: number;
  market_cap: number;
  per: number;
  pbr: number;
  eps: number;
  bps: number;
  roe: number;
  roa: number;
  current_assets: number;
  total_assets: number;
  current_liabilities: number;
  total_liabilities: number;
  capital: number;
  minority_interests: number;
  shareholders_equity: number;
  debt_ratio: number;
  current_ratio: number;
  equity_ratio: number;
  operating_cash_flow: number;
  investing_cash_flow: number;
  financing_cash_flow: number;
  cash_and_equivalents: number;
  revenue: number;
  operating_income: number;
  net_income: number;
  operating_margin: number;
  net_margin: number;
  dividend_yield: number;
  dividend_per_share: number;
  payout_ratio: number;
  beta: number;
  shares_outstanding: number;
  market_type: string;
  currency: string;
  collected_at: string;
}

interface FinancialHistory {
  date: string;
  revenue: number;
  operating_income: number;
  net_income: number;
  operating_margin: number;
  net_margin: number;
  roe: number;
  roa: number;
  current_ratio: number;
  debt_ratio: number;
  equity_ratio: number;
}

export default function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [financialHistory, setFinancialHistory] = useState<FinancialHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCompanyData = async () => {
      try {
        setLoading(true);
        console.log('Fetching company data for ticker:', companyId);
        
        // API_BASE_URLを使用
        const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
        
        // 企業データを取得
        const companyResponse = await fetch(`${API_BASE_URL}/companies/${companyId}`);
        if (!companyResponse.ok) {
          throw new Error('Failed to fetch company data');
        }
        const companyData = await companyResponse.json();
        console.log('Company data:', companyData);
        setCompany(companyData);
        
        // 財務履歴データを取得
        const financialResponse = await fetch(`${API_BASE_URL}/companies/${companyId}/financial-history`);
        if (financialResponse.ok) {
          const financialData = await financialResponse.json();
          console.log('Financial history data:', financialData);
          setFinancialHistory(financialData.data || []);
        }
      } catch (error) {
        console.error('Error fetching company data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (companyId) {
      fetchCompanyData();
    }
  }, [companyId]);

  if (loading) {
    return <div className="p-4">
      <Skeleton className="h-12 w-full mb-4" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Skeleton className="h-[400px]" />
        <Skeleton className="h-[400px]" />
      </div>
    </div>;
  }

  if (!company) {
    return <div className="p-4">企業情報が見つかりませんでした。</div>;
  }

  // TradingView用のシンボルを生成
  const getTradingViewSymbol = (ticker: string, market: string) => {
    if (market === 'JP') {
      return `${ticker}.T`;
    } else if (market === 'US') {
      return ticker;
    }
    return ticker;
  };

  return (
    <div className="p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          {company.company_name} ({company.ticker})
        </h1>
        <div className="text-sm text-gray-600">
          {company.sector} | {company.market}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>株価情報</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">株価</div>
                <div className="text-xl font-bold">{company.currency === 'USD' ? '$' : '¥'}{company.current_price ? formatNumber(company.current_price) : '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">時価総額</div>
                <div className="text-xl font-bold">{company.currency === 'USD' ? '$' : '¥'}{company.market_cap ? formatNumber(company.market_cap / 1000000) + 'M' : '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">PER</div>
                <div className="text-xl font-bold">{company.per ? company.per.toFixed(2) + '倍' : '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">PBR</div>
                <div className="text-xl font-bold">{company.pbr ? company.pbr.toFixed(2) + '倍' : '-'}</div>
              </div>
              <div>
              <div className="text-sm text-gray-600">ROE</div>
              <div className="text-xl font-bold">{company.roe ? company.roe.toFixed(2) + '%' : '-'}</div>
              </div>
              <div>
              <div className="text-sm text-gray-600">配当利回り</div>
              <div className="text-xl font-bold">{company.dividend_yield ? company.dividend_yield.toFixed(2) + '%' : '-'}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>株価チャート</CardTitle>
          </CardHeader>
          <CardContent>
            <TradingViewChart 
              symbol={getTradingViewSymbol(company.ticker, company.market)} 
              market={company.market || 'US'}
              companyName={company.company_name}
            />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="financial" className="mb-6">
        <TabsList>
          <TabsTrigger value="financial">財務情報</TabsTrigger>
          <TabsTrigger value="company">企業情報</TabsTrigger>
          <TabsTrigger value="reports">決算資料</TabsTrigger>
        </TabsList>
        
        <TabsContent value="financial">
          <Card>
          <CardHeader>
            <CardTitle>財務情報{financialHistory.length > 0 && financialHistory[0]?.date ? `（${new Date(financialHistory[0].date).toLocaleDateString()}）` : ''}</CardTitle>
          </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                {financialHistory.length > 0 && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">売上高</div>
                      <div className="text-xl font-bold">
                        {formatFinancialData(financialHistory[0].revenue, company.currency)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">営業利益</div>
                      <div className="text-xl font-bold">
                        {formatFinancialData(financialHistory[0].operating_income, company.currency)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">純利益</div>
                      <div className="text-xl font-bold">
                        {formatFinancialData(financialHistory[0].net_income, company.currency)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">自己資本比率</div>
                      <div className="text-xl font-bold">
                        {financialHistory[0].equity_ratio ? financialHistory[0].equity_ratio.toFixed(2) + '%' : '-'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">営業利益率</div>
                      <div className="text-xl font-bold">
                        {financialHistory[0].operating_margin ? financialHistory[0].operating_margin.toFixed(2) + '%' : '-'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">純利益率</div>
                      <div className="text-xl font-bold">
                        {financialHistory[0].net_margin ? financialHistory[0].net_margin.toFixed(2) + '%' : '-'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="company">
          <Card>
            <CardHeader>
              <CardTitle>企業概要</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">業種</h3>
                  <p>{company.industry || '-'}</p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">ウェブサイト</h3>
                  <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                    {company.website || '-'}
                  </a>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">事業概要</h3>
                  <p className="whitespace-pre-wrap">{company.business_description || '-'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>決算資料</CardTitle>
            </CardHeader>
            <CardContent>
              <Link 
                to={`/financial-reports?company=${encodeURIComponent(company.company_name)}&ticker=${encodeURIComponent(company.ticker)}`}
                className="text-blue-500 hover:text-blue-700"
              >
                決算資料を閲覧する →
              </Link>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
