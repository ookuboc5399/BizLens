import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Chart } from "react-google-charts"
import apiClient from "@/api/client"

interface CompanyData {
  id: string;
  name: string;
  code: string;
  description?: string;
  financials: {
    revenue: { year: number; value: number }[];
    netIncome: { year: number; value: number }[];
    roe: { year: number; value: number }[];
    per: { year: number; value: number }[];
    assets: { type: string; value: number }[];
    liabilities: { type: string; value: number }[];
    equity: number;
  };
}

export function CompanyDetailPage() {
  const { id } = useParams();
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<CompanyData>(`/api/companies/${id}`);
        setCompany(response.data);
      } catch (error) {
        console.error("Error fetching company:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchCompany();
    }
  }, [id]);

  useEffect(() => {
    if (!company || isLoading) return;
    // Google Charts will automatically handle the rendering
  }, [company, activeTab, isLoading]);

  const getChartData = () => {
    if (!company) return null;

    switch (activeTab) {
      case "overview":
        return {
          title: "主要財務指標の推移",
          data: [
            ["年度", "売上高", "純利益", "ROE"],
            ...company.financials.revenue.map((item, index) => [
              item.year.toString(),
              item.value,
              company.financials.netIncome[index].value,
              company.financials.roe[index].value,
            ]),
          ],
        };
      case "valuation":
        return {
          title: "PER推移",
          data: [
            ["年度", "PER"],
            ...company.financials.per.map((item) => [
              item.year.toString(),
              item.value,
            ]),
          ],
        };
      case "profit":
        return {
          title: "純利益推移",
          data: [
            ["年度", "純利益"],
            ...company.financials.netIncome.map((item) => [
              item.year.toString(),
              item.value,
            ]),
          ],
        };
      case "balance":
        return {
          title: "バランスシート",
          data: [
            ["項目", "金額"],
            ...company.financials.assets.map((item) => [item.type, item.value]),
            ...company.financials.liabilities.map((item) => [item.type, item.value]),
            ["純資産", company.financials.equity],
          ],
        };
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <Skeleton className="h-12 w-64 mb-4" />
        <Skeleton className="h-8 w-32 mb-8" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!company) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <p className="text-lg text-red-600">企業情報が見つかりませんでした。</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{company.name}</h1>
        <p className="text-lg text-gray-600">{company.code}</p>
        {company.description && (
          <p className="mt-4 text-gray-700">{company.description}</p>
        )}
        <div className="mt-4">
          <Link to={`/companies/${company.code}/comparison`}>
            <Button variant="outline">企業比較</Button>
          </Link>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="valuation">評価額</TabsTrigger>
          <TabsTrigger value="profit">純利益</TabsTrigger>
          <TabsTrigger value="balance">バランスシート</TabsTrigger>
        </TabsList>

        {["overview", "valuation", "profit", "balance"].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <Card>
              <CardHeader>
                <CardTitle>
                  {tab === "overview" && "企業概要"}
                  {tab === "valuation" && "企業価値評価"}
                  {tab === "profit" && "純利益推移"}
                  {tab === "balance" && "バランスシート"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Chart
                  chartType={activeTab === "balance" ? "PieChart" : "LineChart"}
                  width="100%"
                  height="400px"
                  data={getChartData()?.data}
                  options={{
                    title: getChartData()?.title,
                    legend: { position: "bottom" },
                    hAxis: { title: "年度" },
                    vAxis: { title: activeTab === "balance" ? "金額" : "値" },
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
