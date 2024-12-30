import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2 } from "lucide-react";
import { companyApi } from "@/api/client";

interface ScreeningResult {
  id: string;
  name: string;
  ticker: string;
  latest_metrics: {
    revenue: number;
    roe: number;
    per: number;
  };
}

export function ScreeningPage() {
  const navigate = useNavigate();
  const [minRevenue, setMinRevenue] = useState("");
  const [minRoe, setMinRoe] = useState("");
  const [maxPer, setMaxPer] = useState("");
  const [results, setResults] = useState<ScreeningResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 初期データの読み込み
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
        const response = await companyApi.screenCompanies(
          100000000000, // デフォルト: 1000億円
          12,           // デフォルト: ROE 12%
          30            // デフォルト: PER 30倍
        );
        if (response && Array.isArray(response)) {
          setResults(response);
        }
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const validateInputs = () => {
    // Check if at least one field is filled
    if (!minRevenue && !minRoe && !maxPer) {
      setError("少なくとも1つの条件を入力してください。");
      return false;
    }

    // Validate revenue if provided
    if (minRevenue) {
      const revenue = Number(minRevenue);
      if (isNaN(revenue) || revenue < 100000000000) {
        setError("売上高は1,000億円以上を入力してください。");
        return false;
      }
    }

    // Validate ROE if provided
    if (minRoe) {
      const roe = Number(minRoe);
      if (isNaN(roe) || roe < 12) {
        setError("ROEは12%以上を入力してください。");
        return false;
      }
    }

    // Validate PER if provided
    if (maxPer) {
      const per = Number(maxPer);
      if (isNaN(per) || per > 30) {
        setError("PERは30倍以下を入力してください。");
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateInputs()) return;

    try {
      setIsLoading(true);
      setError(null);

      console.log('Sending screening request with params:', {
        minRevenue: Number(minRevenue),
        minRoe: Number(minRoe),
        maxPer: Number(maxPer)
      });

      const response = await companyApi.screenCompanies(
        minRevenue ? Number(minRevenue) : 100000000000,
        minRoe ? Number(minRoe) : 12,
        maxPer ? Number(maxPer) : 30
      );

      console.log('Received screening response:', response);

      if (response && Array.isArray(response)) {
        console.log('Processing response data...');
        const processedResults = response.map(company => {
          console.log('Processing company:', company);
          return {
            id: company.id || '',
            name: company.name || '',
            ticker: company.ticker || '',
            latest_metrics: {
              revenue: company.latest_metrics?.revenue || 0,
              roe: company.latest_metrics?.roe || 0,
              per: company.latest_metrics?.per || 0
            }
          };
        });
        console.log('Processed results:', processedResults);
        setResults(processedResults);
      } else {
        console.error('Invalid response format:', response);
        setError("データの取得に失敗しました。");
      }
    } catch (err) {
      setError("検索中にエラーが発生しました。");
      console.error("Error during screening:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <h1 className="text-2xl font-bold">企業スクリーニング</h1>

      <Card>
        <CardHeader>
          <CardTitle>スクリーニング条件</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium">売上高（円）</label>
                <Input
                  type="number"
                  min="100000000000"
                  step="100000000"
                  placeholder="1000億円以上"
                  value={minRevenue}
                  onChange={(e) => {
                    setMinRevenue(e.target.value);
                    setError(null);
                  }}
                />
                <p className="text-sm text-muted-foreground">1,000億円以上</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">ROE（%）</label>
                <Input
                  type="number"
                  min="12"
                  step="0.1"
                  placeholder="12%以上"
                  value={minRoe}
                  onChange={(e) => {
                    setMinRoe(e.target.value);
                    setError(null);
                  }}
                />
                <p className="text-sm text-muted-foreground">12%以上</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">PER（倍）</label>
                <Input
                  type="number"
                  max="30"
                  step="0.1"
                  placeholder="30倍以下"
                  value={maxPer}
                  onChange={(e) => {
                    setMaxPer(e.target.value);
                    setError(null);
                  }}
                />
                <p className="text-sm text-muted-foreground">30倍以下</p>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600">{error}</p>
            )}

            <div className="flex justify-end">
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    検索中...
                  </>
                ) : (
                  "検索"
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {results.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>検索結果（{results.length}件）</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>企業名</TableHead>
                    <TableHead>証券コード</TableHead>
                    <TableHead className="text-right">売上高（円）</TableHead>
                    <TableHead className="text-right">ROE（%）</TableHead>
                    <TableHead className="text-right">PER（倍）</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((company) => (
                    <TableRow
                      key={company.id}
                      className="cursor-pointer hover:bg-muted"
                      onClick={() => navigate(`/company/${company.id}`)}
                    >
                      <TableCell>{company.name}</TableCell>
                      <TableCell>{company.ticker}</TableCell>
                      <TableCell className="text-right">{company.latest_metrics.revenue.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{company.latest_metrics.roe.toFixed(2)}</TableCell>
                      <TableCell className="text-right">{company.latest_metrics.per.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-muted">
          <CardContent className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">
              {isLoading ? "検索中..." : "条件を入力して検索してください。"}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
