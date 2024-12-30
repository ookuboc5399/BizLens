import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CompanyMetrics, CompanyComparison, companyApi } from "@/api/client"
import { Loader2 } from "lucide-react"
import { Chart } from "react-google-charts"

export function ComparisonPage() {
  const { ticker } = useParams<{ ticker: string }>()
  const [selectedCompany, setSelectedCompany] = useState<CompanyMetrics | null>(null)
  const [comparisonData, setComparisonData] = useState<CompanyComparison | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (ticker) {
      handleInitialSearch(ticker)
    }
  }, [ticker])

  useEffect(() => {
    if (selectedCompany?.ticker) {
      loadComparisonData(selectedCompany.ticker)
    }
  }, [selectedCompany])

  const handleInitialSearch = async (tickerSymbol: string) => {
    try {
      console.log("Initial search for ticker:", tickerSymbol)
      setIsLoading(true)
      setError(null)
      const companies = await companyApi.searchCompanies(tickerSymbol)
      console.log("Initial search results:", companies)

      if (!companies || companies.length === 0) {
        setError("企業が見つかりませんでした。")
        return
      }

      setSelectedCompany(companies[0])
    } catch (err) {
      console.error("Error details:", err)
      setError("企業の検索中にエラーが発生しました。")
      console.error("Error in initial search:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const loadComparisonData = async (ticker: string) => {
    try {
      console.log("Loading comparison data for ticker:", ticker)
      setIsLoading(true)
      setError(null)
      const data = await companyApi.getCompanyComparison(ticker)
      console.log("Comparison data:", data)
      setComparisonData(data)
    } catch (err) {
      console.error("Error details:", err)
      setError("企業の比較データの取得中にエラーが発生しました。")
      console.error("Error loading comparison data:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setError("企業名または証券コードを入力してください。")
      return
    }

    try {
      console.log("Searching for company:", searchTerm)
      setIsLoading(true)
      setError(null)
      const companies = await companyApi.searchCompanies(searchTerm)
      console.log("Search results:", companies)

      if (!companies || companies.length === 0) {
        setError("企業が見つかりませんでした。")
        return
      }

      setSelectedCompany(companies[0])
      setSearchTerm("")
    } catch (err) {
      console.error("Error details:", err)
      setError("企業の検索中にエラーが発生しました。")
      console.error("Error searching company:", err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">企業比較</h1>
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>企業を検索</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-4">
              <Input
                placeholder="企業名または証券コードを入力"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setError(null)
                }}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                disabled={isLoading}
              />
              <Button onClick={handleSearch} disabled={isLoading}>
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
            {error && (
              <p className="text-sm text-red-600">{error}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {comparisonData ? (
        <>
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>企業比較表</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>企業名</TableHead>
                      <TableHead>証券コード</TableHead>
                      <TableHead className="text-right">売上高</TableHead>
                      <TableHead className="text-right">営業利益</TableHead>
                      <TableHead className="text-right">純利益</TableHead>
                      <TableHead className="text-right">ROE</TableHead>
                      <TableHead className="text-right">PER</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>{comparisonData.company.name}</TableCell>
                      <TableCell>{comparisonData.company.ticker}</TableCell>
                      <TableCell className="text-right">
                        {comparisonData.company.latest_metrics?.revenue?.toLocaleString() ?? 'N/A'}円
                      </TableCell>
                      <TableCell className="text-right">
                        {comparisonData.company.latest_metrics?.operating_income?.toLocaleString() ?? 'N/A'}円
                      </TableCell>
                      <TableCell className="text-right">
                        {comparisonData.company.latest_metrics?.net_income?.toLocaleString() ?? 'N/A'}円
                      </TableCell>
                      <TableCell className="text-right">
                        {comparisonData.company.latest_metrics?.roe?.toFixed(2) ?? 'N/A'}%
                      </TableCell>
                      <TableCell className="text-right">
                        {comparisonData.company.latest_metrics?.per?.toFixed(2) ?? 'N/A'}倍
                      </TableCell>
                    </TableRow>
                    {comparisonData.peer_companies.map((company) => (
                      <TableRow key={company.id}>
                        <TableCell>{company.name}</TableCell>
                        <TableCell>{company.ticker}</TableCell>
                        <TableCell className="text-right">
                          {company.latest_metrics?.revenue?.toLocaleString() ?? 'N/A'}円
                        </TableCell>
                        <TableCell className="text-right">
                          {company.latest_metrics?.operating_income?.toLocaleString() ?? 'N/A'}円
                        </TableCell>
                        <TableCell className="text-right">
                          {company.latest_metrics?.net_income?.toLocaleString() ?? 'N/A'}円
                        </TableCell>
                        <TableCell className="text-right">
                          {company.latest_metrics?.roe?.toFixed(2) ?? 'N/A'}%
                        </TableCell>
                        <TableCell className="text-right">
                          {company.latest_metrics?.per?.toFixed(2) ?? 'N/A'}倍
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <Card>
              <CardHeader>
                <CardTitle>財務指標比較</CardTitle>
              </CardHeader>
              <CardContent>
                <Chart
                  chartType="ColumnChart"
                  width="100%"
                  height="400px"
                  data={[
                    ['企業', '売上高', 'ROE'],
                    [comparisonData.company.name,
                     comparisonData.company.latest_metrics?.revenue || 0,
                     comparisonData.company.latest_metrics?.roe || 0],
                    ...comparisonData.peer_companies.map(company => [
                      company.name,
                      company.latest_metrics?.revenue || 0,
                      company.latest_metrics?.roe || 0
                    ])
                  ]}
                  options={{
                    title: '主要財務指標の比較',
                    legend: { position: 'bottom' },
                    vAxis: { title: '値' },
                    seriesType: 'bars'
                  }}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>PER比較</CardTitle>
              </CardHeader>
              <CardContent>
                <Chart
                  chartType="LineChart"
                  width="100%"
                  height="400px"
                  data={[
                    ['企業', 'PER'],
                    [comparisonData.company.name,
                     comparisonData.company.latest_metrics?.per || 0],
                    ...comparisonData.peer_companies.map(company => [
                      company.name,
                      company.latest_metrics?.per || 0
                    ])
                  ]}
                  options={{
                    title: 'PER比較',
                    legend: { position: 'bottom' },
                    vAxis: { title: '倍' },
                    curveType: 'function'
                  }}
                />
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        <Card className="bg-muted">
          <CardContent className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">
              企業を検索して比較を開始してください。
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
