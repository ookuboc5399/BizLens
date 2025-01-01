import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';

interface EarningsData {
  date: string;
  count: number;
}

interface CompanyEarnings {
  code: string;
  name: string;
  market: string;
  fiscal_year: string;
  quarter: string;
  description?: string;
  sector?: string;
  industry?: string;
  market_segment?: string;
  market_cap?: number;
  per?: number;
  pbr?: number;
  dividend_yield?: number;
}

function EarningsCalendar() {
  const navigate = useNavigate();
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [monthlyData, setMonthlyData] = useState<{ [key: string]: EarningsData }>({});
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [companies, setCompanies] = useState<CompanyEarnings[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMonthlyData = async (year: number, month: number) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/earnings/monthly/${year}/${month}`);
      if (!response.ok) {
        throw new Error('決算データの取得に失敗しました');
      }

      const data = await response.json();
      setMonthlyData(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : '予期せぬエラーが発生しました');
      setMonthlyData({});
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyData = async (date: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/earnings/daily/${date}`);
      if (!response.ok) {
        throw new Error('企業データの取得に失敗しました');
      }

      const data = await response.json();
      setCompanies(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : '予期せぬエラーが発生しました');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonthlyData(currentYear, currentMonth);
  }, [currentYear, currentMonth]);

  const handleDateClick = (date: string) => {
    setSelectedDate(date);
    fetchDailyData(date);
  };

  const handleMonthChange = (increment: number) => {
    let newMonth = currentMonth + increment;
    let newYear = currentYear;

    if (newMonth > 12) {
      newMonth = 1;
      newYear += 1;
    } else if (newMonth < 1) {
      newMonth = 12;
      newYear -= 1;
    }

    setCurrentMonth(newMonth);
    setCurrentYear(newYear);
  };

  const renderCalendar = () => {
    const firstDay = new Date(currentYear, currentMonth - 1, 1);
    const lastDay = new Date(currentYear, currentMonth, 0);
    const days = [];
    const dayOfWeek = ['日', '月', '火', '水', '木', '金', '土'];

    // 曜日ヘッダー
    days.push(
      <div key="header" className="grid grid-cols-7 gap-1 mb-2">
        {dayOfWeek.map((day, index) => (
          <div
            key={day}
            className={`text-center py-2 ${
              index === 0 ? 'text-red-500' : index === 6 ? 'text-blue-500' : ''
            }`}
          >
            {day}
          </div>
        ))}
      </div>
    );

    // 前月の日付を埋める
    const firstDayOfWeek = firstDay.getDay();
    for (let i = 0; i < firstDayOfWeek; i++) {
      days.push(
        <div key={`prev-${i}`} className="text-gray-400 p-2 text-center">
          {new Date(currentYear, currentMonth - 1, -firstDayOfWeek + i + 1).getDate()}
        </div>
      );
    }

    // 当月の日付
    for (let date = 1; date <= lastDay.getDate(); date++) {
      const dateStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(
        date
      ).padStart(2, '0')}`;
      const dayData = monthlyData[dateStr];
      const isSelected = dateStr === selectedDate;

      days.push(
        <div
          key={date}
          onClick={() => handleDateClick(dateStr)}
          className={`p-2 text-center cursor-pointer transition-colors ${
            isSelected
              ? 'bg-blue-500 text-white'
              : dayData
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'hover:bg-gray-100'
          }`}
        >
          <div>{date}</div>
          {dayData && <div className="text-xs">{dayData.count}社</div>}
        </div>
      );
    }

    return <div className="grid grid-cols-7 gap-1">{days}</div>;
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>決算カレンダー</CardTitle>
            <div className="flex items-center gap-4">
              <Button onClick={() => handleMonthChange(-1)} variant="outline">
                前月
              </Button>
              <div className="text-lg font-semibold">
                {currentYear}年{currentMonth}月
              </div>
              <Button onClick={() => handleMonthChange(1)} variant="outline">
                翌月
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-2">
              <Progress value={undefined} className="w-full" />
              <p className="text-sm text-muted-foreground">データを読み込み中...</p>
            </div>
          )}

          {error && <p className="text-red-500 mb-4">{error}</p>}

          {renderCalendar()}

          {selectedDate && companies.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4">{selectedDate} の決算発表企業</h3>
              <div className="space-y-2">
                {companies.map((company) => (
                  <Card
                    key={company.code}
                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => navigate(`/company/${company.code}`)}
                  >
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="font-semibold">
                            {company.name} ({company.code})
                          </h4>
                          <p className="text-sm text-gray-500">
                            {company.market} - {company.fiscal_year}年度{company.quarter}
                          </p>
                          {company.sector && (
                            <p className="text-sm text-gray-500">
                              {company.sector} / {company.industry}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default EarningsCalendar;
