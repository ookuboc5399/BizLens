import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Loader2, Download, ExternalLink } from 'lucide-react';

interface SpreadsheetData {
  title: string;
  sheets: string[];
  headers: string[];
  data: string[][];
  range: string;
}

interface SpreadsheetViewerProps {
  isOpen: boolean;
  onClose: () => void;
  spreadsheetId: string;
  companyName: string;
}

export const SpreadsheetViewer: React.FC<SpreadsheetViewerProps> = ({
  isOpen,
  onClose,
  spreadsheetId,
  companyName
}) => {
  const [data, setData] = useState<SpreadsheetData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && spreadsheetId) {
      fetchSpreadsheetData();
    }
  }, [isOpen, spreadsheetId]);

  const fetchSpreadsheetData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/companies/spreadsheet/${spreadsheetId}`);
      
      if (!response.ok) {
        throw new Error('スプレッドシートの取得に失敗しました');
      }
      
      const spreadsheetData = await response.json();
      setData(spreadsheetData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const csvContent = data ? convertToCSV(data.data) : '';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${companyName}_data.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const convertToCSV = (data: string[][]) => {
    return data.map(row => 
      row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
    ).join('\n');
  };

  const openInGoogleSheets = () => {
    window.open(`https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`, '_blank');
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{companyName} - 企業データ</span>
            <div className="flex gap-2">
              {data && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    className="flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    CSV ダウンロード
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={openInGoogleSheets}
                    className="flex items-center gap-2"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Google Sheets で開く
                  </Button>
                </>
              )}
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">データを読み込み中...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchSpreadsheetData}
                className="mt-2"
              >
                再試行
              </Button>
            </div>
          )}

          {data && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-2">{data.title}</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">シート数:</span> {data.sheets.length}
                  </div>
                  <div>
                    <span className="font-medium">データ行数:</span> {data.data.length - 1}
                  </div>
                  <div>
                    <span className="font-medium">列数:</span> {data.headers.length}
                  </div>
                  <div>
                    <span className="font-medium">範囲:</span> {data.range}
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      {data.headers.map((header, index) => (
                        <th
                          key={index}
                          className="border border-gray-300 px-4 py-2 text-left font-medium text-gray-700"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.data.slice(1, 101).map((row, rowIndex) => (
                      <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {data.headers.map((_, colIndex) => (
                          <td
                            key={colIndex}
                            className="border border-gray-300 px-4 py-2 text-sm"
                          >
                            {row[colIndex] || ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {data.data.length > 101 && (
                  <p className="text-sm text-gray-500 mt-2">
                    表示件数: 100件 / 総件数: {data.data.length - 1}件
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
