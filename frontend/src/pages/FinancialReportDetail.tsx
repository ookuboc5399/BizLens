import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { SupabaseClient } from '@supabase/supabase-js';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import PDFViewer from '../components/PDFViewer';
import { useAuth } from '../hooks/useAuth';

interface FinancialReport {
  company_id: string;
  fiscal_year: string;
  quarter: string;
  report_type: string;
  source: string;
  original_url: string;
  gcs_path: string;
  report_date: string;
  created_at: string;
  signed_url: string;
}

interface FinancialReportDetailProps {
  supabase: SupabaseClient;
}

function FinancialReportDetail({ supabase }: FinancialReportDetailProps) {
  const { companyId } = useParams();
  const { isAdmin } = useAuth(supabase);
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<FinancialReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [companyInfo, setCompanyInfo] = useState<{
    company_name: string;
    ticker: string;
  } | null>(null);

  useEffect(() => {
    const fetchCompanyInfo = async () => {
      try {
        const response = await fetch(`/api/companies/${companyId}`);
        if (!response.ok) {
          throw new Error('企業情報の取得に失敗しました');
        }
        const data = await response.json();
        setCompanyInfo({
          company_name: data.company_name,
          ticker: data.ticker,
        });
      } catch (error) {
        setError(error instanceof Error ? error.message : '予期せぬエラーが発生しました');
      }
    };

    const fetchReports = async () => {
      if (!isAdmin) {
        setError('この機能を利用するには管理者権限が必要です');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/financial-reports/${companyId}`);
        if (!response.ok) {
          throw new Error('決算資料の取得に失敗しました');
        }

        const data = await response.json();
        setReports(data || []);
        if (data && data.length > 0) {
          setSelectedReport(data[0]);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : '予期せぬエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    if (companyId) {
      fetchCompanyInfo();
      fetchReports();
    }
  }, [companyId, isAdmin]);

  const handleReportSelect = (report: FinancialReport) => {
    setSelectedReport(report);
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
    <div className="max-w-7xl mx-auto p-4 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>
            {companyInfo ? `${companyInfo.company_name} (${companyInfo.ticker}) の決算資料` : '決算資料'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-2">
              <Progress value={undefined} className="w-full" />
              <p className="text-sm text-muted-foreground">データを読み込み中...</p>
            </div>
          )}

          {error && (
            <p className="text-red-500 mb-4">{error}</p>
          )}

          {reports.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="lg:col-span-1 space-y-4">
                <div className="space-y-2">
                  {reports.map((report) => (
                    <Button
                      key={report.gcs_path}
                      variant={selectedReport?.gcs_path === report.gcs_path ? "default" : "outline"}
                      className="w-full justify-start"
                      onClick={() => handleReportSelect(report)}
                    >
                      <div className="text-left">
                        <div>{report.fiscal_year}年度 Q{report.quarter}</div>
                        <div className="text-sm text-gray-500">{report.report_type}</div>
                        <div className="text-xs text-gray-400">{new Date(report.report_date).toLocaleDateString()}</div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>
              <div className="lg:col-span-3">
                {selectedReport && (
                  <div className="h-[800px]">
                    <PDFViewer url={selectedReport.signed_url} />
                  </div>
                )}
              </div>
            </div>
          )}

          {!loading && !error && reports.length === 0 && (
            <p className="text-gray-500">決算資料が見つかりませんでした</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancialReportDetail;
