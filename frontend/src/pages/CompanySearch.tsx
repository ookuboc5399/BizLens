import React, { useState, useEffect, useRef, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';

interface Company {
  ticker: string;
  company_name: string;
  sector: string;
  industry: string;
}

function CompanySearch() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // 検索を遅延実行するためのタイマーID
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setCompanies([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/companies/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '検索に失敗しました');
      }

      const data = await response.json();
      setCompanies(data.companies || []);
      setShowSuggestions(true);
      setSelectedIndex(-1);

    } catch (error) {
      setError(error instanceof Error ? error.message : '検索中にエラーが発生しました');
      setCompanies([]);
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

    const timer = setTimeout(() => {
      handleSearch(value);
    }, 300);

    setSearchTimer(timer);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!companies.length) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev < companies.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleCompanySelect(companies[selectedIndex]);
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

        {loading && (
          <div className="mt-2">
            <Progress value={undefined} className="w-full" />
          </div>
        )}

        {error && (
          <p className="text-red-500 mt-2">{error}</p>
        )}

        {showSuggestions && companies.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
          >
            {companies.map((company, index) => (
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
                    <div className="text-sm text-gray-500">
                      {company.ticker} - {company.sector}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default CompanySearch;
