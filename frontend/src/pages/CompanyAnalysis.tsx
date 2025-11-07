import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Loader2, ArrowLeft, Download, ExternalLink, BarChart3, Table } from 'lucide-react';
import { CompanyAnalysisCharts } from '../components/CompanyAnalysisCharts';
import { CompanyScore } from '../components/CompanyScore';
import { TradingViewChart } from '../components/TradingViewChart';
import { TradingViewAdvancedChart } from '../components/TradingViewAdvancedChart';

interface SpreadsheetData {
  title: string;
  sheets: string[];
  sheets_data: {
    [sheetName: string]: {
      headers: string[];
      data: string[][];
      range: string;
    };
  };
}

interface CompanyAnalysisData {
  companyName: string;
  spreadsheetData: SpreadsheetData;
  analysis: {
    financialMetrics: any[];
    businessDescription: string;
    keyInsights: string[];
    riskFactors: string[];
    opportunities: string[];
  };
  scores: {
    growth: number;
    profitability: number;
    stability: number;
    efficiency: number;
    overall: number;
  };
  ticker?: string;
  market?: string;
}

const CompanyAnalysis: React.FC = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<CompanyAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'charts'>('table');
  const [activeTab, setActiveTab] = useState<string>('');

  useEffect(() => {
    if (companyId) {
      fetchCompanyAnalysis(companyId);
    }
  }, [companyId]);

  // データが読み込まれたときに最初のタブを設定
  useEffect(() => {
    if (data && data.spreadsheetData.sheets.length > 0 && !activeTab) {
      const firstSheet = data.spreadsheetData.sheets.find(sheet => !sheet.includes('シート1'));
      if (firstSheet) {
        setActiveTab(firstSheet);
      }
    }
  }, [data, activeTab]);

  const fetchCompanyAnalysis = async (spreadsheetId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // スプレッドシートデータを取得
      const response = await fetch(`http://localhost:8000/api/companies/spreadsheet/${spreadsheetId}`);
      
      if (!response.ok) {
        throw new Error('企業データの取得に失敗しました');
      }
      
      const spreadsheetData = await response.json();
      
      // 企業分析を実行
      const analysis = analyzeCompanyData(spreadsheetData);
      
      // スコア計算
      const scores = calculateCompanyScores(spreadsheetData);
      
      // ティッカーと市場情報を抽出
      const { ticker, market } = extractTickerAndMarket(spreadsheetData, spreadsheetData.title);
      
      setData({
        companyName: spreadsheetData.title,
        spreadsheetData,
        analysis,
        scores,
        ticker,
        market
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  // スコア計算関数
  const calculateCompanyScores = (spreadsheetData: SpreadsheetData) => {
    const performanceSheet = spreadsheetData.sheets_data['業績'];
    const financialSheet = spreadsheetData.sheets_data['財務'];
    
    if (!performanceSheet || !financialSheet) {
      return {
        growth: 50,
        profitability: 50,
        stability: 50,
        efficiency: 50,
        overall: 50
      };
    }

    // 成長性スコア（売上成長率ベース）
    const growthScore = calculateGrowthScore(performanceSheet);
    
    // 収益性スコア（営業利益率ベース）
    const profitabilityScore = calculateProfitabilityScore(performanceSheet);
    
    // 安定性スコア（自己資本比率ベース）
    const stabilityScore = calculateStabilityScore(financialSheet);
    
    // 効率性スコア（総資産回転率ベース）
    const efficiencyScore = calculateEfficiencyScore(financialSheet);
    
    const overall = Math.round((growthScore + profitabilityScore + stabilityScore + efficiencyScore) / 4);
    
    return {
      growth: growthScore,
      profitability: profitabilityScore,
      stability: stabilityScore,
      efficiency: efficiencyScore,
      overall
    };
  };

  // ティッカーと市場情報抽出関数
  const extractTickerAndMarket = (spreadsheetData: SpreadsheetData, companyName: string) => {
    const companyOverviewSheet = spreadsheetData.sheets_data['企業概要'];
    
    if (!companyOverviewSheet) {
      return { ticker: '', market: '' };
    }

    // 企業概要からティッカーと市場を抽出
    let ticker = '';
    let market = '';
    
    for (const row of companyOverviewSheet.data) {
      if (row[0] && row[1]) {
        const key = row[0].toLowerCase().trim();
        const value = row[1].trim();
        
        // ティッカー情報の抽出
        if (key.includes('ティッカー') || key.includes('ticker') || 
            key.includes('コード') || key.includes('code') ||
            key.includes('銘柄コード') || key.includes('証券コード')) {
          ticker = value;
        }
        
        // 市場情報の抽出
        if (key.includes('市場') || key.includes('market') || 
            key.includes('取引所') || key.includes('exchange') ||
            key.includes('上場市場')) {
          market = value;
        }
      }
    }

    // ティッカーが見つからない場合、企業名から推測
    if (!ticker && companyName) {
      // 企業名に含まれる可能性のあるティッカーを抽出
      
      // 一般的なティッカーパターンを試す
      if (companyName.includes('Apple')) ticker = 'AAPL';
      else if (companyName.includes('Microsoft')) ticker = 'MSFT';
      else if (companyName.includes('Google')) ticker = 'GOOGL';
      else if (companyName.includes('Amazon')) ticker = 'AMZN';
      else if (companyName.includes('Meta')) ticker = 'META';
      else if (companyName.includes('Tesla')) ticker = 'TSLA';
      else if (companyName.includes('NVIDIA')) ticker = 'NVDA';
      else if (companyName.includes('Netflix')) ticker = 'NFLX';
      else if (companyName.includes('伊藤忠')) ticker = '8001';
      else if (companyName.includes('GMO')) ticker = '9449';
      else if (companyName.includes('中国')) ticker = '000001'; // 中国企業のデフォルト
      else if (companyName.includes('IGG')) ticker = '00799'; // IGG Inc
    }

    // それでもティッカーが見つからない場合は、デフォルトを設定
    if (!ticker) {
      ticker = 'AAPL'; // Appleをデフォルトとして使用
    }

    // 市場が見つからない場合、デフォルト値を設定
    if (!market) {
      market = 'US'; // デフォルトは米国市場
    }

    console.log('Extracted ticker and market:', { ticker, market, companyName });

    return { ticker, market };
  };

  // 成長性スコア計算
  const calculateGrowthScore = (performanceSheet: any) => {
    try {
      const data = performanceSheet.data;
      if (data.length < 2) return 50;

      // 売上高の列を探す
      const revenueIndex = performanceSheet.headers.findIndex((h: string) => 
        h.includes('売上') || h.includes('収益')
      );
      
      if (revenueIndex === -1) return 50;

      // 最新2年の売上高を取得
      const recentRevenues = data.slice(0, 2).map((row: string[]) => 
        parseFloat(row[revenueIndex]?.replace(/,/g, '') || '0')
      );

      if (recentRevenues.length < 2 || recentRevenues[1] === 0) return 50;

      const growthRate = ((recentRevenues[0] - recentRevenues[1]) / recentRevenues[1]) * 100;
      
      // 成長率をスコアに変換（0-100）
      if (growthRate > 20) return 90;
      if (growthRate > 10) return 80;
      if (growthRate > 5) return 70;
      if (growthRate > 0) return 60;
      if (growthRate > -5) return 50;
      if (growthRate > -10) return 40;
      if (growthRate > -20) return 30;
      return 20;
    } catch {
      return 50;
    }
  };

  // 収益性スコア計算
  const calculateProfitabilityScore = (performanceSheet: any) => {
    try {
      const data = performanceSheet.data;
      if (data.length < 1) return 50;

      // 営業利益率の列を探す
      const profitIndex = performanceSheet.headers.findIndex((h: string) => 
        h.includes('営業利益') || h.includes('利益率')
      );
      
      if (profitIndex === -1) return 50;

      const profit = parseFloat(data[0][profitIndex]?.replace(/,/g, '') || '0');
      
      // 営業利益率をスコアに変換
      if (profit > 15) return 90;
      if (profit > 10) return 80;
      if (profit > 5) return 70;
      if (profit > 0) return 60;
      if (profit > -5) return 50;
      if (profit > -10) return 40;
      return 30;
    } catch {
      return 50;
    }
  };

  // 安定性スコア計算
  const calculateStabilityScore = (financialSheet: any) => {
    try {
      const data = financialSheet.data;
      if (data.length < 1) return 50;

      // 自己資本比率の列を探す
      const equityIndex = financialSheet.headers.findIndex((h: string) => 
        h.includes('自己資本') || h.includes('資本比率')
      );
      
      if (equityIndex === -1) return 50;

      const equityRatio = parseFloat(data[0][equityIndex]?.replace(/,/g, '') || '0');
      
      // 自己資本比率をスコアに変換
      if (equityRatio > 50) return 90;
      if (equityRatio > 30) return 80;
      if (equityRatio > 20) return 70;
      if (equityRatio > 10) return 60;
      if (equityRatio > 0) return 50;
      return 30;
    } catch {
      return 50;
    }
  };

  // 効率性スコア計算
  const calculateEfficiencyScore = (financialSheet: any) => {
    try {
      const data = financialSheet.data;
      if (data.length < 1) return 50;

      // 総資産回転率の列を探す
      const turnoverIndex = financialSheet.headers.findIndex((h: string) => 
        h.includes('回転率') || h.includes('効率')
      );
      
      if (turnoverIndex === -1) return 50;

      const turnover = parseFloat(data[0][turnoverIndex]?.replace(/,/g, '') || '0');
      
      // 総資産回転率をスコアに変換
      if (turnover > 1.5) return 90;
      if (turnover > 1.0) return 80;
      if (turnover > 0.8) return 70;
      if (turnover > 0.5) return 60;
      if (turnover > 0.3) return 50;
      return 40;
    } catch {
      return 50;
    }
  };

  const analyzeCompanyData = (spreadsheetData: SpreadsheetData) => {
    // 企業概要シートから基本情報を抽出
    const companyOverviewSheet = spreadsheetData.sheets_data['企業概要'];
    const companyInfo = extractCompanyInfo(companyOverviewSheet);
    
    // 業績シートから財務指標を抽出
    const performanceSheet = spreadsheetData.sheets_data['業績'];
    const financialMetrics = performanceSheet ? extractFinancialMetricsFromPerformance(performanceSheet) : [];
    
    // 財務シートから財務データを抽出
    const financialSheet = spreadsheetData.sheets_data['財務'];
    const financialData = financialSheet ? extractFinancialData(financialSheet) : [];
    
    // キーインサイトを生成
    const keyInsights = generateKeyInsights(companyInfo, financialMetrics, financialData);
    
    // リスク要因を抽出
    const riskFactors = extractRiskFactors(companyInfo);
    
    // 機会を抽出
    const opportunities = extractOpportunities(companyInfo);
    
    return {
      companyInfo,
      financialMetrics,
      financialData,
      keyInsights,
      riskFactors,
      opportunities
    };
  };

  const extractCompanyInfo = (sheet: any) => {
    if (!sheet || !sheet.data) return {};
    
    const companyInfo: { [key: string]: string } = {};
    
    // A列に項目名、B列に値が記載されている形式を処理
    sheet.data.forEach((row: string[]) => {
      if (row.length >= 2) {
        const key = row[0]?.trim();
        const value = row[1]?.trim();
        if (key && value) {
          companyInfo[key] = value;
        }
      }
    });
    
    return companyInfo;
  };

  const extractFinancialMetricsFromPerformance = (sheet: any) => {
    if (!sheet || !sheet.data) return [];
    
    const metrics = [];
    const financialKeywords = ['売上', '収益', '利益', '資産', '負債', '資本', 'ROE', 'ROA', 'PER', 'PBR', '配当', 'EPS'];
    
    sheet.data.forEach((row: string[]) => {
      if (row.length >= 2) {
        const key = row[0]?.trim();
        const value = row[1]?.trim();
        
        if (key && value && financialKeywords.some(keyword => key.includes(keyword))) {
          metrics.push({
            name: key,
            value: value,
            trend: 'stable' // 業績データからは単一の値なので、トレンドは計算できない
          });
        }
      }
    });
    
    return metrics;
  };

  const extractFinancialData = (sheet: any) => {
    if (!sheet || !sheet.data) return [];
    
    const financialData: { [key: string]: string } = {};
    
    sheet.data.forEach((row: string[]) => {
      if (row.length >= 2) {
        const key = row[0]?.trim();
        const value = row[1]?.trim();
        if (key && value) {
          financialData[key] = value;
        }
      }
    });
    
    return financialData;
  };

  const extractRiskFactors = (companyInfo: { [key: string]: string }) => {
    const risks = [];
    
    // 企業概要からリスク要因を抽出
    Object.entries(companyInfo).forEach(([key, value]) => {
      if (key.includes('赤字') || key.includes('損失') || key.includes('減益') || 
          key.includes('課題') || key.includes('懸念') || key.includes('問題')) {
        risks.push(`${key}: ${value}`);
      }
    });
    
    return risks.slice(0, 5); // 最大5つまで
  };

  const extractOpportunities = (companyInfo: { [key: string]: string }) => {
    const opportunities = [];
    
    // 企業概要から成長機会を抽出
    Object.entries(companyInfo).forEach(([key, value]) => {
      if (key.includes('成長') || key.includes('拡大') || key.includes('新規') || 
          key.includes('戦略') || key.includes('計画') || key.includes('展望') ||
          key.includes('今後の計画')) {
        opportunities.push(`${key}: ${value}`);
      }
    });
    
    return opportunities.slice(0, 5); // 最大5つまで
  };

  const generateKeyInsights = (companyInfo: { [key: string]: string }, financialMetrics: any[], financialData: any[]) => {
    const insights = [];
    
    // 企業概要からインサイトを生成
    const businessDescription = companyInfo['企業概要'] || '';
    if (businessDescription.includes('AI') || businessDescription.includes('人工知能')) {
      insights.push('AI技術を活用した事業展開を行っています');
    }
    if (businessDescription.includes('海外') || businessDescription.includes('国際') || businessDescription.includes('世界')) {
      insights.push('海外展開を積極的に行っています');
    }
    if (businessDescription.includes('ゲーム') || businessDescription.includes('モバイル')) {
      insights.push('ゲーム・モバイル事業に強みがあります');
    }
    
    // 財務指標からインサイトを生成
    financialMetrics.forEach(metric => {
      if (metric.value && !isNaN(parseFloat(metric.value.replace(/[^\d.-]/g, '')))) {
        insights.push(`${metric.name}: ${metric.value}`);
      }
    });
    
    // 設立年から企業の成熟度を判断
    const establishmentYear = companyInfo['設立日'];
    if (establishmentYear) {
      const year = parseInt(establishmentYear.replace(/[^\d]/g, ''));
      if (year && year < 2010) {
        insights.push('老舗企業としての安定性があります');
      } else if (year && year >= 2010) {
        insights.push('比較的新しい企業で成長性が期待されます');
      }
    }
    
    return insights.slice(0, 5); // 最大5つまで
  };

  const calculateTrend = (values: string[]) => {
    if (values.length < 2) return 'stable';
    
    // 数値に変換可能な値のみを対象
    const numericValues = values
      .map(val => parseFloat(val.replace(/[^\d.-]/g, '')))
      .filter(val => !isNaN(val));
    
    if (numericValues.length < 2) return 'stable';
    
    const first = numericValues[0];
    const last = numericValues[numericValues.length - 1];
    
    if (last > first * 1.1) return 'up';
    if (last < first * 0.9) return 'down';
    return 'stable';
  };

  const handleDownload = () => {
    if (!data) return;
    
    // すべてのシートのデータをCSVに変換
    let csvContent = '';
    
    Object.entries(data.spreadsheetData.sheets_data).forEach(([sheetName, sheetData]) => {
      csvContent += `\n=== ${sheetName} ===\n`;
      csvContent += sheetData.data.map(row => 
        row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
      ).join('\n');
      csvContent += '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${data.companyName}_analysis.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const openInGoogleSheets = () => {
    if (companyId) {
      window.open(`https://docs.google.com/spreadsheets/d/${companyId}/edit`, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>企業分析を読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'データが見つかりません'}</p>
          <Button onClick={() => navigate('/company-search')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            検索ページに戻る
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/company-search')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              戻る
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{data.companyName}</h1>
              <p className="text-gray-600">企業分析レポート</p>
            </div>
          </div>
          <div className="flex gap-2">
            <div className="flex border rounded-lg">
              <Button
                variant={viewMode === 'table' ? 'default' : 'ghost'}
                onClick={() => setViewMode('table')}
                className="flex items-center gap-2 rounded-r-none"
              >
                <Table className="h-4 w-4" />
                テーブル
              </Button>
              <Button
                variant={viewMode === 'charts' ? 'default' : 'ghost'}
                onClick={() => setViewMode('charts')}
                className="flex items-center gap-2 rounded-l-none"
              >
                <BarChart3 className="h-4 w-4" />
                グラフ
              </Button>
            </div>
            <Button
              variant="outline"
              onClick={handleDownload}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              CSV ダウンロード
            </Button>
            <Button
              variant="outline"
              onClick={openInGoogleSheets}
              className="flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Google Sheets で開く
            </Button>
          </div>
        </div>

        {/* スコア表示とTradingViewチャート */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="flex flex-col">
            <CompanyScore 
              companyName={data.companyName} 
              scores={data.scores} 
            />
          </div>
          <div className="flex flex-col">
            <TradingViewChart 
              symbol={data.ticker || 'AAPL'}
              market={data.market || 'US'}
              companyName={data.companyName}
            />
            {/* デバッグ情報 */}
            <div className="mt-2 text-xs text-gray-500">
              <p>ティッカー: {data.ticker || 'AAPL (デフォルト)'}</p>
              <p>市場: {data.market || 'US (デフォルト)'}</p>
              <p>企業名: {data.companyName}</p>
              <p>利用可能なシート: {data.spreadsheetData.sheets.join(', ')}</p>
            </div>
          </div>
        </div>

        {/* データ表示 */}
        <div className="mt-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="w-full overflow-x-auto">
              <div className="flex min-w-max space-x-1">
                {data.spreadsheetData.sheets
                  .filter(sheetName => !sheetName.includes('シート1'))
                  .map((sheetName) => (
                    <TabsTrigger key={sheetName} value={sheetName} className="text-sm whitespace-nowrap">
                      {sheetName}
                    </TabsTrigger>
                  ))}
              </div>
            </TabsList>
            
            {data.spreadsheetData.sheets
              .filter(sheetName => !sheetName.includes('シート1'))
              .map((sheetName) => (
                <TabsContent key={sheetName} value={sheetName} className="mt-6">
                  {viewMode === 'table' ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>{sheetName}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="min-w-full border-collapse border border-gray-300">
                            <thead>
                              <tr className="bg-gray-100">
                                {data.spreadsheetData.sheets_data[sheetName]?.headers.map((header, index) => (
                                  <th
                                    key={index}
                                    className="border border-gray-300 px-4 py-2 text-left font-medium text-gray-900"
                                  >
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {data.spreadsheetData.sheets_data[sheetName]?.data.slice(0, 21).map((row, rowIndex) => (
                                <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                  {data.spreadsheetData.sheets_data[sheetName]?.headers.map((_, colIndex) => (
                                    <td
                                      key={colIndex}
                                      className="border border-gray-300 px-4 py-2 text-sm text-gray-900"
                                    >
                                      {row[colIndex] || ''}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {data.spreadsheetData.sheets_data[sheetName]?.data.length > 21 && (
                            <p className="text-sm text-gray-500 mt-2">
                              表示件数: 20件 / 総件数: {data.spreadsheetData.sheets_data[sheetName]?.data.length}件
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <div>
                      <CompanyAnalysisCharts 
                        sheetsData={{ [sheetName]: data.spreadsheetData.sheets_data[sheetName] }} 
                      />
                    </div>
                  )}
                </TabsContent>
              ))}
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default CompanyAnalysis;
