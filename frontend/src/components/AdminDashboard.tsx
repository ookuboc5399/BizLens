import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Button } from './ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table'
import { getFinancialData, collectData } from '../api/admin'
import { useToast } from '../hooks/use-toast'
import FinancialReportManager from './FinancialReportManager'

interface Company {
  symbol: string;
  company_name: string;
  sector: string;
  industry: string;
}

interface FinancialDataResponse {
  companies: Company[];
}

export default function AdminDashboard() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('')
  const { toast } = useToast()

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const data = await getFinancialData() as FinancialDataResponse;
      setCompanies(data.companies);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "エラー",
        description: "企業データの取得に失敗しました"
      })
    }
    setLoading(false);
  };

  const handleCollectData = async () => {
    if (!symbol) {
      toast({
        variant: "destructive",
        title: "警告",
        description: "証券コードを入力してください"
      })
      return;
    }
    setLoading(true);
    try {
      const result = await collectData([symbol]);
      toast({
        title: "成功",
        description: `${symbol}のデータを取得しました`
      })
      fetchCompanies();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "エラー",
        description: "データの取得に失敗しました"
      })
    }
    setLoading(false);
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>企業データ管理</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <Input
              placeholder="証券コードを入力"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="max-w-[200px]"
            />
            <Button
              onClick={handleCollectData}
              disabled={loading}
            >
              {loading ? "取得中..." : "データを取得"}
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>証券コード</TableHead>
                <TableHead>企業名</TableHead>
                <TableHead>セクター</TableHead>
                <TableHead>業種</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <TableRow key={company.symbol}>
                  <TableCell>{company.symbol}</TableCell>
                  <TableCell>{company.company_name}</TableCell>
                  <TableCell>{company.sector}</TableCell>
                  <TableCell>{company.industry}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <FinancialReportManager />
    </div>
  )
}
