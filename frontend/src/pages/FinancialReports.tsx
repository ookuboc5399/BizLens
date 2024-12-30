import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const API_BASE_URL = '/api';

interface Company {
  company_name: string;
  ticker: string;
  sector: string;
  latest_report?: {
    fiscal_year: string;
    quarter: string;
    file_url: string;
    report_date: string;
  };
}

interface SearchResponse {
  companies: Company[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function FinancialReports() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [suggestions, setSuggestions] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchTerm.length < 2) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE_URL}/companies/search?query=${encodeURIComponent(searchTerm)}&page_size=5&include_reports=true`
        );
        
        if (!response.ok) {
          throw new Error('検索に失敗しました');
        }
        
        const data: SearchResponse = await response.json();
        setSuggestions(data.companies);
        setShowSuggestions(true);
        setSelectedIndex(-1);
      } catch (error) {
        console.error('Suggestion fetch failed:', error);
      }
    };

    const debounceTimer = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }
    if (!searchTerm) return;
    
    setIsLoading(true);
    setError(null);
    setShowSuggestions(false);
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/companies/search?query=${encodeURIComponent(searchTerm)}&include_reports=true`
      );
      
      if (!response.ok) {
        throw new Error('検索に失敗しました');
      }
      
      const data: SearchResponse = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
      setError(error instanceof Error ? error.message : '検索中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        handleSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSuggestionClick(suggestions[selectedIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleSuggestionClick = (company: Company) => {
    setSearchTerm(company.company_name);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    navigate(`/financial-reports/${company.ticker}`);
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">決算資料検索</h1>

      <Card>
        <CardHeader>
          <CardTitle>企業名または証券コードで検索</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative" ref={searchRef}>
            <form 
              onSubmit={handleSearch} 
              autoComplete="off" 
              role="search" 
              data-search-form="true"
              data-lpignore="true"
              noValidate
            >
              <div className="flex gap-4">
                <div className="flex-1 max-w-md">
                  <input
                    type="text"
                    name="search"
                    placeholder="企業名または証券コードを入力"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="w-full h-10 px-3 py-2 bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 border border-input rounded-md"
                    autoComplete="off"
                    autoCorrect="false"
                    autoCapitalize="off"
                    spellCheck="false"
                    inputMode="text"
                    results={0}
                    data-form-type="other"
                    data-lpignore="true"
                    role="combobox"
                    aria-autocomplete="list"
                    aria-expanded={showSuggestions}
                    aria-controls="company-search-suggestions"
                    aria-activedescendant={selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined}
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <div 
                      id="company-search-suggestions"
                      role="listbox"
                      className="absolute z-10 w-full mt-1 bg-gray-900 border border-gray-700 rounded-md shadow-lg overflow-hidden"
                    >
                      {suggestions.map((company, index) => (
                        <div
                          key={company.ticker}
                          id={`suggestion-${index}`}
                          role="option"
                          aria-selected={index === selectedIndex}
                          className={`p-3 cursor-pointer border-b border-gray-800 last:border-b-0 ${
                            index === selectedIndex ? 'bg-blue-900/30' : 'hover:bg-gray-800'
                          }`}
                          onClick={() => handleSuggestionClick(company)}
                          onMouseEnter={() => setSelectedIndex(index)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="bg-gray-800 px-2 py-1 rounded text-sm text-gray-300 min-w-[4rem] text-center">
                              {company.ticker}
                            </span>
                            <span className="text-gray-100 font-medium flex-1 truncate">
                              {company.company_name}
                            </span>
                          </div>
                          {company.latest_report && (
                            <div className="mt-1 text-sm text-gray-500 pl-[4.5rem]">
                              最新の決算資料: {company.latest_report.fiscal_year}年度 {company.latest_report.quarter}四半期
                            </div>
                          )}
                        </div>
                      ))}
                      <div className="p-2 bg-gray-800 border-t border-gray-700 text-sm text-gray-400 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-700 rounded">↑↓</kbd>
                            <span>選択</span>
                          </span>
                          <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-700 rounded">Enter</kbd>
                            <span>決定</span>
                          </span>
                          <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-700 rounded">Esc</kbd>
                            <span>閉じる</span>
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {suggestions.length}件の候補
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? '検索中...' : '検索'}
                </Button>
              </div>
            </form>
          </div>
          {error && (
            <p className="text-red-500 mt-2">{error}</p>
          )}
        </CardContent>
      </Card>

      {results && results.companies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              検索結果 ({results.total}件中 {results.companies.length}件表示)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>証券コード</TableHead>
                  <TableHead>企業名</TableHead>
                  <TableHead>業種</TableHead>
                  <TableHead>最新の決算資料</TableHead>
                  <TableHead>詳細</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.companies.map((company) => (
                  <TableRow key={company.ticker}>
                    <TableCell>{company.ticker}</TableCell>
                    <TableCell>{company.company_name}</TableCell>
                    <TableCell>{company.sector}</TableCell>
                    <TableCell>
                      {company.latest_report ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(company.latest_report?.file_url, '_blank')}
                        >
                          {company.latest_report.fiscal_year}年度 {company.latest_report.quarter}四半期
                        </Button>
                      ) : (
                        '未取得'
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/financial-reports/${company.ticker}`)}
                      >
                        過去の資料
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
