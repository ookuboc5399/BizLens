import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Chart } from "react-google-charts"
import { apiClient } from "@/api/client"
import { formatNumber } from "@/utils/format";

interface Company {
  ticker: string;
  company_name: string;
  sector: string;
  industry: string;
  country: string;
  website: string;
  description: string;
  market_cap: number;
  employees: number;
  market: string;
  current_price: number;
}

interface Financials {
  revenue: { year: number; value: number }[];
  netIncome: { year: number; value: number }[];
  roe: { year: number; value: number }[];
  per: { year: number; value: number }[];
  assets: { type: string; value: number }[];
  liabilities: { type: string; value: number }[];
  equity: number;
}

interface CompanyDetailsData {
  company: Company;
  financials: Financials;
}

export function CompanyDetailPage() {
  const { id: ticker } = useParams<{ id: string }>();
  const [details, setDetails] = useState<CompanyDetailsData | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [isLoading, setIsLoading] = useState(true);

  console.log("Ticker:", ticker); // 追加

  useEffect(() => {
    const fetchDetails = async () => {
      if (!ticker) return;
      try {
        setIsLoading(true);
        const response = await fetch(`/api/companies/${ticker}/details`);
        if (!response.ok) {
          throw new Error("Failed to fetch company details");
        }
        const data: CompanyDetailsData = await response.json();
        console.log("Received data from API:", data); // 追加
        setDetails(data);
      } catch (error) {
        console.error("Error fetching company details:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetails();
  }, [ticker]);

  useEffect(() => {
    if (!details || isLoading) return;
    // Google Charts will automatically handle the rendering
  }, [details, activeTab, isLoading]);

  const getChartData = () => {
    if (!details) return null;
    const { company, financials } = details;

    switch (activeTab) {
      case "overview":
        return {
          title: "主要財務指標の推移",
          data: [
            ["年度", "売上高", "純利益", "ROE"],
            ...financials.revenue.map((item, index) => [
              item.year.toString(),
              item.value,
              financials.netIncome[index].value,
              financials.roe[index].value,
            ]),
          ],
        };
      case "valuation":
        return {
          title: "PER推移",
          data: [
            ["年度", "PER"],
            ...financials.per.map((item) => [
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
            ...financials.netIncome.map((item) => [
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
            ...financials.assets.map((item) => [item.type, item.value]),
            ...financials.liabilities.map((item) => [item.type, item.value]),
            ["純資産", financials.equity],
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

  if (!details) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <p className="text-lg text-red-600">企業情報が見つかりませんでした。</p>
      </div>
    );
  }

  const { company, financials } = details;

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{company.company_name}</h1>
        <p className="text-lg text-gray-600">{company.ticker}</p>
        {company.business_description && (
          <p className="mt-4 text-gray-700">{company.business_description}</p>
        )}
        {company.market_cap && (
          <p className="text-lg text-gray-600">時価総額: {formatNumber(company.market_cap)}</p>
        )}
        {company.current_price && (
          <p className="text-lg text-gray-600">現在価格: {formatNumber(company.current_price)}</p>
        )}
        <div className="mt-4">
          <Link to={`/companies/${company.ticker}/comparison`}>
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
