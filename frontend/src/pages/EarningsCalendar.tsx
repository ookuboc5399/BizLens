import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { format, addMonths, startOfMonth, endOfMonth, eachDayOfInterval } from "date-fns";
import { ja } from "date-fns/locale";

interface DailyCount {
  date: string;
  count: number;
}

interface MonthlyData {
  [date: string]: DailyCount;
}

interface Company {
  code: string;
  name: string;
  market: string;
  fiscal_year: string;
  quarter: string;
}

export default function EarningsCalendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [monthlyData, setMonthlyData] = useState<{ [key: string]: { [date: string]: DailyCount } }>({});
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  useEffect(() => {
    const fetchMonthlyData = async () => {
      const months = [currentMonth, addMonths(currentMonth, 1)];
      const newData: { [key: string]: { [date: string]: DailyCount } } = {};

      for (const month of months) {
        const year = month.getFullYear();
        const monthNum = month.getMonth() + 1;
        try {
          console.log(`Fetching data for ${year}-${monthNum}`);
          const response = await fetch(`http://localhost:8000/api/companies/earnings/monthly/${year}/${monthNum}`);
          const data = await response.json();
          console.log(`Received data for ${year}-${monthNum}:`, data);
          newData[`${year}-${monthNum}`] = data as MonthlyData;
        } catch (error) {
          console.error(`Failed to fetch data for ${year}-${monthNum}:`, error);
        }
      }

      setMonthlyData(newData);
    };

    fetchMonthlyData();
  }, [currentMonth]);

  const handleDateClick = async (date: string) => {
    setSelectedDate(date);
    try {
      console.log(`Fetching companies for date: ${date}`);
      const response = await fetch(`http://localhost:8000/api/companies/earnings/daily/${date}`);
      const companies = await response.json();
      console.log(`Received companies:`, companies);
      setSelectedCompanies(companies);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    }
  };

  const renderCalendarGrid = (month: Date) => {
    const start = startOfMonth(month);
    const end = endOfMonth(month);
    const days = eachDayOfInterval({ start, end });
    const year = month.getFullYear();
    const monthNum = month.getMonth() + 1;
    const monthKey = `${year}-${monthNum}`;
    const monthData = monthlyData[monthKey] || {};

    // 週の行を作成
    const weeks: (Date | null)[][] = [];
    let currentWeek: (Date | null)[] = [];

    // 月の最初の日の前に空白を追加
    const firstDayOfWeek = start.getDay();
    for (let i = 0; i < firstDayOfWeek; i++) {
      currentWeek.push(null);
    }

    days.forEach(day => {
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      currentWeek.push(day);
    });

    // 最後の週の残りを空白で埋める
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);

    return (
      <div className="grid grid-cols-7 gap-1">
        {/* 曜日のヘッダー */}
        {['日', '月', '火', '水', '木', '金', '土'].map((day, i) => (
          <div
            key={day}
            className={`text-center p-2 font-bold ${
              i === 0 ? 'text-red-500' : i === 6 ? 'text-blue-500' : ''
            }`}
          >
            {day}
          </div>
        ))}

        {/* 日付のグリッド */}
        {weeks.map((week, weekIndex) =>
          week.map((day, dayIndex) => {
            if (!day) return <div key={`empty-${weekIndex}-${dayIndex}`} className="p-2" />;

            const dateStr = format(day, 'yyyy-MM-dd');
            const dayData = monthData[dateStr];
            const hasEarnings = dayData && dayData.count > 0;
            const isSelected = dateStr === selectedDate;

            return (
              <div
                key={dateStr}
                onClick={() => hasEarnings && handleDateClick(dateStr)}
                className={`
                  p-2 text-center border rounded relative
                  ${hasEarnings ? 'cursor-pointer hover:bg-gray-100' : 'bg-gray-50'}
                  ${isSelected ? 'ring-2 ring-blue-500' : ''}
                  ${dayIndex === 0 ? 'text-red-500' : dayIndex === 6 ? 'text-blue-500' : ''}
                `}
              >
                <div className="font-medium">{format(day, 'd')}</div>
                {hasEarnings && (
                  <div className={`
                    text-xs font-semibold rounded-full px-2 py-1 mt-1
                    ${dayData.count > 10 ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-700'}
                  `}>
                    {dayData.count}社
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-2 gap-4">
        {[currentMonth, addMonths(currentMonth, 1)].map((month) => (
          <Card key={month.toISOString()}>
            <CardHeader>
              <CardTitle>{format(month, 'yyyy年M月', { locale: ja })}</CardTitle>
            </CardHeader>
            <CardContent>
              {renderCalendarGrid(month)}
            </CardContent>
          </Card>
        ))}
      </div>

      {selectedDate && selectedCompanies.length > 0 && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>{selectedDate} の決算発表企業</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {selectedCompanies.map((company, index) => (
                <div key={index} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-bold text-lg">{company.name}</span>
                      <span className="ml-2 text-sm text-gray-500">({company.code})</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-gray-100 rounded text-sm">{company.market}</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                        {company.fiscal_year}年度 {company.quarter}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
