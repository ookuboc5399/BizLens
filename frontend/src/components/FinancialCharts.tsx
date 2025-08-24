import React from 'react';
import { Chart } from 'react-google-charts';

interface FinancialData {
  year: string;
  revenue: number;
  operatingProfit: number;
  netIncome: number;
  grossProfitMargin: number;
  operatingMargin: number;
  netProfitMargin: number;
  roe: number;
}

interface FinancialChartsProps {
  data: FinancialData[];
}

export const FinancialCharts: React.FC<FinancialChartsProps> = ({ data }) => {
  // 売上高・利益率のチャートデータ
  const revenueMarginData = [
    [
      '年度',
      '売上高',
      '粗利率',
      '営業利益率',
      '純利益率',
      'ROE',
    ],
    ...data.map(item => [
      item.year,
      item.revenue,
      item.grossProfitMargin,
      item.operatingMargin,
      item.netProfitMargin,
      item.roe,
    ]),
  ];

  // 利益のチャートデータ
  const profitData = [
    ['年度', '売上高営業利益', '営業利益', '当期純利益'],
    ...data.map(item => [
      item.year,
      item.operatingProfit,
      item.operatingProfit,
      item.netIncome,
    ]),
  ];

  return (
    <div className="financial-charts">
      {/* 売上高・利益率チャート */}
      <Chart
        width={'100%'}
        height={'400px'}
        chartType="ComboChart"
        loader={<div>Loading Chart...</div>}
        data={revenueMarginData}
        options={{
          title: '売上高・利益率推移',
          seriesType: 'bars',
          series: {
            0: { type: 'bars', targetAxisIndex: 0 },
            1: { type: 'line', targetAxisIndex: 1 },
            2: { type: 'line', targetAxisIndex: 1 },
            3: { type: 'line', targetAxisIndex: 1 },
            4: { type: 'line', targetAxisIndex: 1 },
          },
          vAxes: {
            0: { title: '売上高（百万円）', format: 'short' },
            1: { title: '比率（%）', format: '#.#%' },
          },
          bars: { groupWidth: '70%' },
          legend: { position: 'bottom' },
        }}
      />

      {/* 利益チャート */}
      <Chart
        width={'100%'}
        height={'400px'}
        chartType="ColumnChart"
        loader={<div>Loading Chart...</div>}
        data={profitData}
        options={{
          title: '利益推移',
          vAxis: { title: '金額（百万円）', format: 'short' },
          hAxis: { title: '年度' },
          legend: { position: 'bottom' },
          isStacked: false,
        }}
      />
    </div>
  );
}; 