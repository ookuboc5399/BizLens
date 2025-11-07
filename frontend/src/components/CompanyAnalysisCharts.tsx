import React from 'react';
import { Chart } from 'react-google-charts';

interface SheetData {
  headers: string[];
  data: string[][];
  range: string;
}

interface CompanyAnalysisChartsProps {
  sheetsData: {
    [sheetName: string]: SheetData;
  };
}

export const CompanyAnalysisCharts: React.FC<CompanyAnalysisChartsProps> = ({ sheetsData }) => {
  // 年度文字列を日付に変換する関数
  const parseYearToDate = (yearStr: string): Date => {
    if (!yearStr) return new Date();
    
    // 様々な年度形式に対応
    const yearMatch = yearStr.match(/(\d{4})/);
    if (yearMatch) {
      const year = parseInt(yearMatch[1]);
      // 年度の場合は4月1日、年のみの場合は1月1日とする
      if (yearStr.includes('年度') || yearStr.includes('FY')) {
        return new Date(year, 3, 1); // 4月1日
      } else {
        return new Date(year, 0, 1); // 1月1日
      }
    }
    
    // 年月形式 (例: 2023年12月, 2023/12)
    const monthMatch = yearStr.match(/(\d{4})[年\/](\d{1,2})/);
    if (monthMatch) {
      const year = parseInt(monthMatch[1]);
      const month = parseInt(monthMatch[2]) - 1; // JavaScriptの月は0ベース
      return new Date(year, month, 1);
    }
    
    // 年月日形式 (例: 2023年12月31日, 2023/12/31)
    const dateMatch = yearStr.match(/(\d{4})[年\/](\d{1,2})[月\/](\d{1,2})/);
    if (dateMatch) {
      const year = parseInt(dateMatch[1]);
      const month = parseInt(dateMatch[2]) - 1;
      const day = parseInt(dateMatch[3]);
      return new Date(year, month, day);
    }
    
    return new Date();
  };

  // 業績データをグラフ用に変換
  const getPerformanceChartData = (performanceData: SheetData) => {
    if (!performanceData || !performanceData.headers || !performanceData.data) {
      return null;
    }

    const headers = performanceData.headers;
    const data = performanceData.data;

    // 年度列（最初の列）と数値列を特定
    const yearColumnIndex = 0;
    const numericColumns = headers.slice(1).map((header, index) => ({
      header: header.trim(),
      index: index + 1
    }));

    // チャートデータを構築
    const chartData = [
      ['年度', ...numericColumns.map(col => col.header)],
      ...data.map(row => {
        const yearStr = row[yearColumnIndex] || '';
        const date = parseYearToDate(yearStr);
        const values = numericColumns.map(col => {
          const value = row[col.index] || '';
          // 数値に変換（カンマを除去）
          const numericValue = parseFloat(value.replace(/,/g, ''));
          return isNaN(numericValue) ? 0 : numericValue;
        });
        return [date, ...values];
      })
    ];

    return chartData;
  };

  // 地域別売上データを円グラフ用に変換
  const getRegionalSalesChartData = (regionalData: SheetData) => {
    if (!regionalData || !regionalData.data) {
      return null;
    }

    const chartData = [
      ['地域', '売上割合'],
      ...regionalData.data.map(row => {
        if (row.length >= 2) {
          const region = row[0] || '';
          const percentage = row[1] || '';
          // パーセンテージから数値に変換
          const numericValue = parseFloat(percentage.replace('%', ''));
          return [region, isNaN(numericValue) ? 0 : numericValue];
        }
        return ['', 0];
      }).filter(row => row[0] !== '') // 空の行を除外
    ];

    return chartData;
  };

  // 財務データをグラフ用に変換
  const getFinancialChartData = (financialData: SheetData) => {
    if (!financialData || !financialData.headers || !financialData.data) {
      return null;
    }

    const headers = financialData.headers;
    const data = financialData.data;

    // 年度列を特定（2列目以降）
    const yearColumns = headers.slice(1);
    const itemRows = data;

    // チャートデータを構築
    const chartData = [
      ['項目', ...yearColumns],
      ...itemRows.map(row => {
        const item = row[0] || '';
        const values = yearColumns.map((_, index) => {
          const value = row[index + 1] || '';
          const numericValue = parseFloat(value.replace(/,/g, ''));
          return isNaN(numericValue) ? 0 : numericValue;
        });
        return [item, ...values];
      })
    ];

    return chartData;
  };

  return (
    <div className="space-y-8">
      {/* 業績グラフ */}
      {sheetsData['業績'] && getPerformanceChartData(sheetsData['業績']) && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">業績推移</h3>
          <Chart
            width={'100%'}
            height={'400px'}
            chartType="LineChart"
            loader={<div>グラフを読み込み中...</div>}
            data={getPerformanceChartData(sheetsData['業績']) || []}
            options={{
              title: '業績推移',
              hAxis: { 
                title: '年度',
                format: 'yyyy年',
                gridlines: { count: -1 },
                minorGridlines: { count: 0 }
              },
              vAxis: { 
                title: '金額',
                format: 'short'
              },
              legend: { position: 'bottom' },
              curveType: 'function',
              pointSize: 5,
              tooltip: { isHtml: true },
              focusTarget: 'category'
            }}
          />
        </div>
      )}

      {/* 財務グラフ */}
      {sheetsData['財務'] && getFinancialChartData(sheetsData['財務']) && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">財務状況</h3>
          <Chart
            width={'100%'}
            height={'400px'}
            chartType="ColumnChart"
            loader={<div>グラフを読み込み中...</div>}
            data={getFinancialChartData(sheetsData['財務']) || []}
            options={{
              title: '財務状況',
              hAxis: { title: '項目' },
              vAxis: { title: '金額' },
              legend: { position: 'bottom' },
              isStacked: false,
            }}
          />
        </div>
      )}

      {/* 地域別売上円グラフ */}
      {sheetsData['地域別売上'] && getRegionalSalesChartData(sheetsData['地域別売上']) && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">地域別売上構成</h3>
          <Chart
            width={'100%'}
            height={'400px'}
            chartType="PieChart"
            loader={<div>グラフを読み込み中...</div>}
            data={getRegionalSalesChartData(sheetsData['地域別売上']) || []}
            options={{
              title: '地域別売上構成',
              pieHole: 0.4,
              legend: { position: 'bottom' },
              pieSliceText: 'percentage',
              tooltip: { trigger: 'selection' },
            }}
          />
        </div>
      )}

      {/* 指標等グラフ */}
      {sheetsData['指標等'] && getFinancialChartData(sheetsData['指標等']) && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">財務指標</h3>
          <Chart
            width={'100%'}
            height={'400px'}
            chartType="BarChart"
            loader={<div>グラフを読み込み中...</div>}
            data={getFinancialChartData(sheetsData['指標等']) || []}
            options={{
              title: '財務指標',
              hAxis: { title: '項目' },
              vAxis: { title: '値' },
              legend: { position: 'bottom' },
            }}
          />
        </div>
      )}

      {/* キャッシュフローグラフ */}
      {sheetsData['キャッシュフロー'] && getFinancialChartData(sheetsData['キャッシュフロー']) && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">キャッシュフロー</h3>
          <Chart
            width={'100%'}
            height={'400px'}
            chartType="ColumnChart"
            loader={<div>グラフを読み込み中...</div>}
            data={getFinancialChartData(sheetsData['キャッシュフロー']) || []}
            options={{
              title: 'キャッシュフロー',
              hAxis: { title: '項目' },
              vAxis: { title: '金額' },
              legend: { position: 'bottom' },
              isStacked: false,
            }}
          />
        </div>
      )}
    </div>
  );
};
