import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { TradingViewChart } from '../components/TradingViewChart';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { useAuth } from '../hooks/useAuth';

interface CompanyData {
  ticker: string;
  company_name: string;
  market_price: number;
  market_cap: number;
  per: number;
  roe: number;
  dividend_yield: number;
  market: string;
  sector: string;
  pbr: number;
  roa: number;
  net_margin: number;
  dividend_per_share: number;
  payout_ratio: number;
  beta: number;
  description?: string;
}

interface FinancialHistory {
  year: number;
  revenue: number;
  operating_profit: number;
  net_income: number;
  gross_profit_margin: number;
  operating_margin: number;
  net_profit_margin: number;
  roe: number;
}

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>();
  const { isAdmin } = useAuth();
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [financialHistory, setFinancialHistory] = useState<FinancialHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCompanyData = async () => {
      try {
        setLoading(true);
        console.log('Fetching company data for ticker:', id);
        const response = await fetch(`/api/companies/${id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch company data');
        }
        const data = await response.json();
        console.log('Company data:', data);
        setCompany(data);

        // 財務データの取得
        const historyResponse = await fetch(`/api/companies/${id}/financial-history`);
        if (!historyResponse.ok) {
          throw new Error('Failed to fetch financial history');
        }
        const historyData = await historyResponse.json();
        console.log('Financial history:', historyData);
        setFinancialHistory(historyData.data || []);
      } catch (error) {
        console.error('Error fetching company data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchCompanyData();
    }
  }, [id]);

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

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ja-JP').format(num);
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
                <div className="text-xl font-bold">¥{company.market_price ? formatNumber(company.market_price) : '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">時価総額</div>
                <div className="text-xl font-bold">¥{company.market_cap ? formatNumber(company.market_cap / 1000000) + 'M' : '-'}</div>
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
                <div className="text-xl font-bold">{company.roe ? (company.roe * 100).toFixed(2) + '%' : '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">配当利回り</div>
                <div className="text-xl font-bold">{company.dividend_yield ? (company.dividend_yield * 100).toFixed(2) + '%' : '-'}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>株価チャート</CardTitle>
          </CardHeader>
          <CardContent>
            <TradingViewChart symbol={`${id}.T`} />
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
              <CardTitle>財務情報</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="text-left p-2">年度</th>
                      <th className="text-right p-2">売上高</th>
                      <th className="text-right p-2">営業利益</th>
                      <th className="text-right p-2">純利益</th>
                      <th className="text-right p-2">営業利益率</th>
                      <th className="text-right p-2">ROE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {financialHistory.map((history) => (
                      <tr key={history.year}>
                        <td className="p-2">{history.year}</td>
                        <td className="text-right p-2">{formatNumber(history.revenue / 1000000)}M</td>
                        <td className="text-right p-2">{formatNumber(history.operating_profit / 1000000)}M</td>
                        <td className="text-right p-2">{formatNumber(history.net_income / 1000000)}M</td>
                        <td className="text-right p-2">{(history.operating_margin * 100).toFixed(2)}%</td>
                        <td className="text-right p-2">{(history.roe * 100).toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
              <p className="whitespace-pre-wrap">{company.description}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>決算資料</CardTitle>
            </CardHeader>
            <CardContent>
              {isAdmin ? (
                <Link 
                  to={`/financial-reports/${company.ticker}`}
                  className="text-blue-500 hover:text-blue-700"
                >
                  決算資料を閲覧する →
                </Link>
              ) : (
                <p className="text-gray-500">この機能を利用するには管理者権限が必要です</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
