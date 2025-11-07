import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

interface CompanyScoreProps {
  companyName: string;
  scores: {
    growth: number;
    profitability: number;
    stability: number;
    efficiency: number;
    overall: number;
  };
}

export const CompanyScore: React.FC<CompanyScoreProps> = ({ companyName, scores }) => {
  // スコアを1-5の範囲に変換
  const convertToFivePointScale = (score: number) => {
    if (score >= 80) return 5;
    if (score >= 60) return 4;
    if (score >= 40) return 3;
    if (score >= 20) return 2;
    return 1;
  };

  // レーダーチャート用のデータを準備（recharts形式）
  const radarData = [
    {
      subject: '成長性',
      score: convertToFivePointScale(scores.growth),
      industry: 3
    },
    {
      subject: '収益性',
      score: convertToFivePointScale(scores.profitability),
      industry: 3
    },
    {
      subject: '安全性',
      score: convertToFivePointScale(scores.stability),
      industry: 3
    },
    {
      subject: '規模',
      score: convertToFivePointScale(scores.efficiency),
      industry: 3
    },
    {
      subject: '割安度',
      score: convertToFivePointScale(scores.overall),
      industry: 3
    },
    {
      subject: '値上がり',
      score: convertToFivePointScale(scores.growth),
      industry: 3
    }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '優秀';
    if (score >= 60) return '良好';
    if (score >= 40) return '普通';
    return '要改善';
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle className="text-center text-xl font-bold text-gray-800 flex items-center justify-center gap-2">
          <span>四季報スコア</span>
          <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-xs text-gray-600">?</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
          {/* レーダーチャート */}
          <div className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis 
                  angle={90} 
                  domain={[0, 5]} 
                  tickCount={6}
                  tick={{ fontSize: 10 }}
                />
                <Radar
                  name="スコア"
                  dataKey="score"
                  stroke="#ff6b35"
                  fill="#ff6b35"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                <Radar
                  name="業界中央値"
                  dataKey="industry"
                  stroke="#cccccc"
                  fill="transparent"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* スコア一覧 */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">成長性</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.growth) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.growth)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">規模</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.efficiency) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.efficiency)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">収益性</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.profitability) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.profitability)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">割安度</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.overall) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.overall)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">安全性</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.stability) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.stability)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">値上がり</span>
              <span className={`text-sm font-semibold ${convertToFivePointScale(scores.growth) >= 4 ? 'text-red-600' : 'text-gray-800'}`}>
                {convertToFivePointScale(scores.growth)}
              </span>
            </div>
          </div>
        </div>

        {/* 凡例 */}
        <div className="mt-4 text-xs text-gray-500 text-right">
          <span>業種: 一般</span>
          <div className="flex items-center justify-end gap-1 mt-1">
            <div className="w-3 h-3 border border-gray-400 border-dashed"></div>
            <span>は 業種中央値</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
