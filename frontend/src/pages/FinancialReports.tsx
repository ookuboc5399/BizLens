import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { useAuth } from '../hooks/useAuth';

interface FinancialReport {
  date: string;
  time: string;
  code: string;
  company: string;
  title: string;
  pdf_url: string;
  exchange: string;
}

function FinancialReports() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/financial-reports/search?company_name=${encodeURIComponent(searchTerm)}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '検索に失敗しました');
      }

      const data = await response.json();
      setReports(data || []);

    } catch (error) {
      setError(error instanceof Error ? error.message : '検索中にエラーが発生しました');
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleReportClick = (code: string) => {
    navigate(`/financial-reports/${code}`);
  };

  if (!isAdmin) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-center text-red-500">この機能を利用するには管理者権限が必要です</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>決算資料検索</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="企業名、証券コードで検索"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={loading}>
              検索
            </Button>
          </div>

          {loading && (
            <div className="space-y-2">
              <Progress value={undefined} className="w-full" />
              <p className="text-sm text-muted-foreground">検索中...</p>
            </div>
          )}

          {error && (
            <p className="text-red-500">{error}</p>
          )}

          {reports.length > 0 && (
            <div className="space-y-4">
              {reports.map((report) => (
                <Card
                  key={`${report.code}-${report.date}-${report.time}`}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleReportClick(report.code)}
                >
                  <CardContent className="pt-6">
                    <div>
                      <h3 className="font-semibold">
                        {report.company} ({report.code})
                      </h3>
                      <p className="text-sm text-gray-500">
                        {report.date} {report.time} - {report.title}
                      </p>
                      <p className="text-sm text-gray-500">
                        {report.exchange}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!loading && !error && reports.length === 0 && searchTerm && (
            <p className="text-gray-500">検索結果が見つかりませんでした</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancialReports;
