import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
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

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/companies/search?query=${encodeURIComponent(searchTerm)}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '検索に失敗しました');
      }

      const data = await response.json();
      setCompanies(data.companies || []);

    } catch (error) {
      setError(error instanceof Error ? error.message : '検索中にエラーが発生しました');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleCompanyClick = (ticker: string) => {
    navigate(`/company/${ticker}`);
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>企業検索</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="企業名、証券コードで検索"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={loading}>
              検索
            </Button>
          </div>

          {loading && (
            <div className="space-y-2">
              <Progress value={undefined} className="w-full" />
              <p className="text-sm text-muted-foreground">検索中...</p>
            </div>
          )}

          {error && (
            <p className="text-red-500">{error}</p>
          )}

          {companies.length > 0 && (
            <div className="space-y-4">
              {companies.map((company) => (
                <Card
                  key={company.ticker}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleCompanyClick(company.ticker)}
                >
                  <CardContent className="pt-6">
                    <div>
                      <h3 className="font-semibold">
                        {company.company_name} ({company.ticker})
                      </h3>
                      <p className="text-sm text-gray-500">
                        {company.sector} - {company.industry}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!loading && !error && companies.length === 0 && searchTerm && (
            <p className="text-gray-500">検索結果が見つかりませんでした</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default CompanySearch;
