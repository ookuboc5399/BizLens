import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const API_BASE_URL = '/api';

interface FinancialReport {
  id: string;
  fiscal_year: string;
  quarter: string;
  report_type: string;
  file_url: string;
  source: string;
  report_date: string;
}

interface Company {
  company_name: string;
  ticker: string;
  sector: string;
}

export default function FinancialReportDetail() {
  const { ticker } = useParams<{ ticker: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [companyResponse, reportsResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/companies/${ticker}`),
          fetch(`${API_BASE_URL}/financial-reports/${ticker}`)
        ]);

        if (!companyResponse.ok || !reportsResponse.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const [companyData, reportsData] = await Promise.all([
          companyResponse.json(),
          reportsResponse.json()
        ]);

        setCompany(companyData);
        setReports(reportsData);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error instanceof Error ? error.message : 'データの取得中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    if (ticker) {
      fetchData();
    }
  }, [ticker]);

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center">読み込み中...</div>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-red-500">{error || 'データが見つかりませんでした'}</div>
      </div>
    );
  }

  const groupedReports = reports.reduce<Record<string, FinancialReport[]>>((acc, report) => {
    const year = report.fiscal_year;
    if (!acc[year]) {
      acc[year] = [];
    }
    acc[year].push(report);
    return acc;
  }, {});

  const years = Object.keys(groupedReports).sort((a, b) => Number(b) - Number(a));

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">
          {company.company_name} ({company.ticker}) の決算資料
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>企業情報</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500">証券コード</div>
              <div>{company.ticker}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">業種</div>
              <div>{company.sector}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>決算資料一覧</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue={years[0]} className="w-full">
            <TabsList>
              {years.map((year) => (
                <TabsTrigger key={year} value={year}>
                  {year}年度
                </TabsTrigger>
              ))}
            </TabsList>
            {years.map((year) => (
              <TabsContent key={year} value={year}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>期間</TableHead>
                      <TableHead>種類</TableHead>
                      <TableHead>取得元</TableHead>
                      <TableHead>公開日</TableHead>
                      <TableHead>資料</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupedReports[year]
                      .sort((a, b) => b.quarter.localeCompare(a.quarter))
                      .map((report) => (
                        <TableRow key={report.id}>
                          <TableCell>{report.quarter}四半期</TableCell>
                          <TableCell>{report.report_type}</TableCell>
                          <TableCell>{report.source}</TableCell>
                          <TableCell>{new Date(report.report_date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => window.open(report.file_url, '_blank')}
                            >
                              閲覧
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
