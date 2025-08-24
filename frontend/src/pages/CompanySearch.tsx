import React, { useState, useEffect, useRef, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { Button } from '../components/ui/button';
import { Search, Loader2, Filter } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

interface SearchResult {
  companies: Company[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface Company {
  ticker: string;
  company_name: string;
  market: string;
  sector: string;
  industry: string;
  country: string;
  market_cap: number;
  current_price: number;
  currency: string;
}

function CompanySearch() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const PAGE_SIZE = 10;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<string>("");
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedSector, setSelectedSector] = useState<string>("");

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResult(null);
      setTotalResults(0);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        query: query,
        page: page.toString(),
        page_size: PAGE_SIZE.toString(),
        ...(selectedMarket && { market: selectedMarket }),
        ...(selectedCountry && { country: selectedCountry }),
        ...(selectedSector && { sector: selectedSector }),
      });

      const response = await fetch(`/api/companies/search?${params}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '検索に失敗しました');
      }

      const data = await response.json();
      setSearchResult(data);
      setTotalResults(data.total);
      setShowSuggestions(true);
      setSelectedIndex(-1);

      // ページ番号が総ページ数を超えている場合は1ページ目に戻す
      if (data.total_pages > 0 && page > data.total_pages) {
        setPage(1);
      }

    } catch (error) {
      setError(error instanceof Error ? error.message : '検索中にエラーが発生しました');
      setSearchResult(null);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);

    if (searchTimer) {
      clearTimeout(searchTimer);
    }

    // 検索語が変更されたら1ページ目に戻す
    setPage(1);

    const timer = setTimeout(() => {
      handleSearch(value);
    }, 300);

    setSearchTimer(timer);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!searchResult?.companies.length) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev < (searchResult?.companies.length || 0) - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleCompanySelect(searchResult.companies[selectedIndex]);
        } else {
          handleSearch(searchTerm);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
    }
  };

  const handleCompanySelect = (company: Company) => {
    navigate(`/company/${company.ticker}`);
    setShowSuggestions(false);
    setSearchTerm('');
  };

  // フィルター変更時に検索を実行
  useEffect(() => {
    if (searchTerm) {
      // フィルターが変更されたら1ページ目に戻す
      setPage(1);
      handleSearch(searchTerm);
    }
  }, [selectedMarket, selectedCountry, selectedSector]);

  // ページ変更時に検索を実行
  useEffect(() => {
    if (searchTerm && searchResult) {
      handleSearch(searchTerm);
    }
  }, [page]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      if (searchTimer) {
        clearTimeout(searchTimer);
      }
    };
  }, [searchTimer]);

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="relative">
        <div className="space-y-4">
          <div className="flex gap-2">
          <Input
            ref={inputRef}
            type="text"
            placeholder="企業名、証券コードで検索"
            value={searchTerm}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            className="w-full h-12 px-4 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          />
          <Button
            onClick={() => handleSearch(searchTerm)}
            className="h-12 px-6 min-w-[100px]"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                <span>検索中</span>
              </>
            ) : (
              <>
                <Search className="h-5 w-5 mr-2" />
                <span>検索</span>
              </>
            )}
          </Button>
          </div>

          <div className="flex gap-2">
            <Select value={selectedMarket} onValueChange={(value) => setSelectedMarket(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="市場を選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">すべての市場</SelectItem>
                <SelectItem value="US">米国市場</SelectItem>
                <SelectItem value="China">中国市場</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedCountry} onValueChange={(value) => setSelectedCountry(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="国を選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">すべての国</SelectItem>
                <SelectItem value="US">アメリカ</SelectItem>
                <SelectItem value="China">中国</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedSector} onValueChange={(value) => setSelectedSector(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="業種を選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">すべての業種</SelectItem>
                <SelectItem value="Technology">テクノロジー</SelectItem>
                <SelectItem value="Finance">金融</SelectItem>
                <SelectItem value="Healthcare">ヘルスケア</SelectItem>
                <SelectItem value="Consumer">消費財</SelectItem>
                <SelectItem value="Industrial">工業</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading && (
          <div className="mt-2">
            <Progress value={undefined} className="w-full h-1" />
            <p className="text-sm text-gray-500 mt-1 text-center animate-pulse">データを検索しています...</p>
          </div>
        )}

        {error && (
          <p className="text-red-500 mt-2">{error}</p>
        )}

        {!loading && !error && searchTerm && (
          <div className="mt-2 text-sm text-gray-600">
            {totalResults > 0 ? (
              <p>
                {totalResults}件の検索結果（{page} / {searchResult?.total_pages}ページ）
              </p>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg text-center">
                <p className="text-gray-600">
                  「{searchTerm}」に一致する企業が見つかりませんでした
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  別のキーワードで検索してください
                </p>
              </div>
            )}
          </div>
        )}

        {showSuggestions && searchResult && searchResult.companies.length > 0 && !loading && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden max-h-[60vh] overflow-y-auto"
          >
            {searchResult.companies.map((company, index) => (
              <div
                key={company.ticker}
                className={`px-4 py-3 cursor-pointer ${
                  index === selectedIndex ? 'bg-gray-50' : ''
                } hover:bg-gray-50`}
                onClick={() => handleCompanySelect(company)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex items-center">
                  <div className="flex-1">
                    <div className="text-base">
                      {company.company_name}
                    </div>
                    <div className="text-sm text-gray-500 flex flex-wrap items-center gap-2">
                      <span className="font-medium">{company.ticker}</span>
                      <span className="text-gray-300">|</span>
                      <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-xs">
                        {company.market}
                      </span>
                      <span className="text-gray-300">|</span>
                      <span className="bg-gray-50 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                        {company.sector}
                      </span>
                      {company.market_cap && (
                        <>
                          <span className="text-gray-300">|</span>
                          <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs">
                            {company.currency === 'USD' ? '$' : '¥'}
                            {(company.market_cap / 1000000).toFixed(0)}M
                          </span>
                        </>
                      )}
                      {company.current_price && (
                        <>
                          <span className="text-gray-300">|</span>
                          <span className="text-gray-600">
                            {company.currency === 'USD' ? '$' : '¥'}
                            {company.current_price.toLocaleString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!showSuggestions && searchResult && searchResult.total_pages > 1 && (
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(prev => Math.max(1, prev - 1))}
              disabled={page === 1}
            >
              前へ
            </Button>
            <div className="flex flex-wrap items-center gap-2">
              {Array.from({ length: searchResult.total_pages }, (_, i) => i + 1)
                .filter(num => {
                  // 現在のページの前後2ページまでと、最初と最後のページを表示
                  return num === 1 || 
                         num === searchResult.total_pages || 
                         Math.abs(num - page) <= 2;
                })
                .map((pageNum, index, array) => (
                  <React.Fragment key={pageNum}>
                    {index > 0 && array[index - 1] !== pageNum - 1 && (
                      <span key={`ellipsis-${pageNum}`} className="text-gray-400">...</span>
                    )}
                    <Button
                      variant={pageNum === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setPage(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  </React.Fragment>
                ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(prev => Math.min(searchResult.total_pages, prev + 1))}
              disabled={page === searchResult.total_pages}
            >
              次へ
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default CompanySearch;
