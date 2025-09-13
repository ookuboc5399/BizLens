import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { ScrollArea } from '../../components/ui/scroll-area';


const API_BASE_URL = '/api';



function DataCollectionPage() {

  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  
  // 企業情報入力フォームの状態
  const [companyMode, setCompanyMode] = useState<'new' | 'update'>('new');
  const [companyForm, setCompanyForm] = useState({
    ticker: '',
    company_name: '',
    sector: '',
    industry: '',
    country: 'JP',
    market: 'JP',
    website: '',
    business_description: '',
    description: '',
    market_cap: '',
    employees: '',
    current_price: '',
    shares_outstanding: '',
    volume: '',
    per: '',
    pbr: '',
    eps: '',
    bps: '',
    roe: '',
    roa: '',
    revenue: '',
    operating_profit: '',
    net_profit: '',
    total_assets: '',
    equity: '',
    operating_margin: '',
    net_margin: '',
    dividend_yield: '',
    company_type: 'LISTED',
    ceo: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // AI企業情報収集の状態
  const [aiForm, setAiForm] = useState({
    company_name: '',
    website_url: '',
    country: 'JP',
    ticker: ''
  });
  const [isAiCollecting, setIsAiCollecting] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  const handleCollectData = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setStatus('データ収集を開始します...');
    setLogs([]);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/data/collect`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'データ収集に失敗しました');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('レスポンスの読み取りに失敗しました');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.progress !== undefined) {
                setProgress(data.progress);
                if (data.current && data.total) {
                  const message = `${data.progress}% 完了 (${data.current}/${data.total}企業)`;
                  setStatus(message);
                  setLogs(prev => [...prev, message]);
                }
              }
              if (data.error) {
                setLogs(prev => [...prev, `エラー: ${data.error}`]);
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing progress data:', e);
            }
          }
        }
      }

      const completionMessage = 'データ収集が完了しました';
      setStatus(completionMessage);
      setLogs(prev => [...prev, completionMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'データ収集中にエラーが発生しました';
      setError(errorMessage);
      setLogs(prev => [...prev, `エラー: ${errorMessage}`]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setCompanyForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 企業検索機能
  const handleSearchCompanies = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/companies/search?query=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.companies || []);
      } else {
        setError('企業検索に失敗しました');
      }
    } catch (err) {
      setError('企業検索中にエラーが発生しました');
    } finally {
      setIsSearching(false);
    }
  };

  // 既存企業を選択してフォームに設定
  const handleSelectCompany = (company: any) => {
    setCompanyForm({
      ticker: company.ticker || '',
      company_name: company.company_name || '',
      sector: company.sector || '',
      industry: company.industry || '',
      country: company.country || 'JP',
      market: company.market || 'JP',
      website: company.website || '',
      business_description: company.business_description || '',
      description: company.description || '',
      market_cap: company.market_cap?.toString() || '',
      employees: company.employees?.toString() || '',
      current_price: company.current_price?.toString() || '',
      shares_outstanding: company.shares_outstanding?.toString() || '',
      volume: company.volume?.toString() || '',
      per: company.per?.toString() || '',
      pbr: company.pbr?.toString() || '',
      eps: company.eps?.toString() || '',
      bps: company.bps?.toString() || '',
      roe: company.roe?.toString() || '',
      roa: company.roa?.toString() || '',
      revenue: company.revenue?.toString() || '',
      operating_profit: company.operating_profit?.toString() || '',
      net_profit: company.net_profit?.toString() || '',
      total_assets: company.total_assets?.toString() || '',
      equity: company.equity?.toString() || '',
      operating_margin: company.operating_margin?.toString() || '',
      net_margin: company.net_margin?.toString() || '',
      dividend_yield: company.dividend_yield?.toString() || '',
      company_type: company.company_type || 'LISTED',
      ceo: company.ceo || ''
    });
    setSearchResults([]);
    setSearchQuery('');
  };


  const handleAiInputChange = (field: string, value: string) => {
    setAiForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAiCollectCompany = async () => {
    setIsAiCollecting(true);
    setAiResult(null);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/ai/collect-company`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(aiForm),
      });

      if (!response.ok) {
        let errorMessage = 'AI企業情報収集に失敗しました';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (jsonError) {
          // JSON解析に失敗した場合、レスポンステキストを使用
          const responseText = await response.text();
          errorMessage = `HTTP ${response.status}: ${responseText}`;
        }
        throw new Error(errorMessage);
      }

      let result;
      try {
        result = await response.json();
      } catch (jsonError) {
        const responseText = await response.text();
        throw new Error(`レスポンスの解析に失敗しました: ${responseText}`);
      }
      setAiResult(result);
      
      // 成功メッセージを表示
      setSubmitMessage(`AI企業情報収集が完了しました: ${result.company_info.company_name || aiForm.company_name}`);
      
      // フォームをリセット
      setAiForm({
        company_name: '',
        website_url: '',
        country: 'JP',
        ticker: ''
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'AI企業情報収集中にエラーが発生しました';
      setError(errorMessage);
    } finally {
      setIsAiCollecting(false);
    }
  };

  const handleSubmitCompany = async () => {
    if (!companyForm.company_name.trim()) {
      setError('企業名は必須です');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSubmitMessage('');

    try {
      // 数値フィールドを変換
      const formData = {
        ...companyForm,
        market_cap: companyForm.market_cap ? parseFloat(companyForm.market_cap) : null,
        employees: companyForm.employees ? parseInt(companyForm.employees) : null,
        current_price: companyForm.current_price ? parseFloat(companyForm.current_price) : null,
        shares_outstanding: companyForm.shares_outstanding ? parseFloat(companyForm.shares_outstanding) : null,
        volume: companyForm.volume ? parseFloat(companyForm.volume) : null,
        per: companyForm.per ? parseFloat(companyForm.per) : null,
        pbr: companyForm.pbr ? parseFloat(companyForm.pbr) : null,
        eps: companyForm.eps ? parseFloat(companyForm.eps) : null,
        bps: companyForm.bps ? parseFloat(companyForm.bps) : null,
        roe: companyForm.roe ? parseFloat(companyForm.roe) : null,
        roa: companyForm.roa ? parseFloat(companyForm.roa) : null,
        revenue: companyForm.revenue ? parseFloat(companyForm.revenue) : null,
        operating_profit: companyForm.operating_profit ? parseFloat(companyForm.operating_profit) : null,
        net_profit: companyForm.net_profit ? parseFloat(companyForm.net_profit) : null,
        total_assets: companyForm.total_assets ? parseFloat(companyForm.total_assets) : null,
        equity: companyForm.equity ? parseFloat(companyForm.equity) : null,
        operating_margin: companyForm.operating_margin ? parseFloat(companyForm.operating_margin) : null,
        net_margin: companyForm.net_margin ? parseFloat(companyForm.net_margin) : null,
        dividend_yield: companyForm.dividend_yield ? parseFloat(companyForm.dividend_yield) : null
      };

      const url = companyMode === 'new' 
        ? `${API_BASE_URL}/admin/companies/add`
        : `${API_BASE_URL}/admin/companies/${companyForm.ticker}`;
      
      const method = companyMode === 'new' ? 'POST' : 'PUT';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        setSubmitMessage(result.message);
        // フォームをリセット（新規追加の場合のみ）
        if (companyMode === 'new') {
          setCompanyForm({
            ticker: '',
            company_name: '',
            sector: '',
            industry: '',
            country: 'JP',
            market: 'JP',
            website: '',
            business_description: '',
            description: '',
            market_cap: '',
            employees: '',
            current_price: '',
            shares_outstanding: '',
            volume: '',
            per: '',
            pbr: '',
            eps: '',
            bps: '',
            roe: '',
            roa: '',
            revenue: '',
            operating_profit: '',
            net_profit: '',
            total_assets: '',
            equity: '',
            operating_margin: '',
            net_margin: '',
            dividend_yield: '',
            company_type: 'LISTED',
            ceo: ''
          });
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '送信に失敗しました');
      }
    } catch (err) {
      setError('送信中にエラーが発生しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCollectReports = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setStatus('決算資料の収集を開始します...');
    setLogs([]);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/financial-reports/fetch`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '決算資料の収集に失敗しました');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('レスポンスの読み取りに失敗しました');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.progress !== undefined) {
                setProgress(data.progress);
                if (data.message) {
                  setStatus(data.message);
                  setLogs(prev => [...prev, data.message]);
                }
              }
              if (data.error) {
                setLogs(prev => [...prev, `エラー: ${data.error}`]);
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing progress data:', e);
            }
          }
        }
      }

      const completionMessage = '決算資料の収集が完了しました';
      setStatus(completionMessage);
      setLogs(prev => [...prev, completionMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '決算資料の収集中にエラーが発生しました';
      setError(errorMessage);
      setLogs(prev => [...prev, `エラー: ${errorMessage}`]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">データ収集管理</h1>
        <Button 
          variant="outline" 
          onClick={() => navigate('/')}
          className="flex items-center gap-2"
        >
          ← ホームに戻る
        </Button>
      </div>

      <Tabs defaultValue="company-data">
        <TabsList>
          <TabsTrigger value="company-data">企業データ</TabsTrigger>
          <TabsTrigger value="company-input">企業情報入力</TabsTrigger>
          <TabsTrigger value="ai-collect">AI企業情報収集</TabsTrigger>
          <TabsTrigger value="financial-reports">決算資料</TabsTrigger>
        </TabsList>

        <TabsContent value="company-data">
          <Card>
            <CardHeader>
              <CardTitle>企業データ収集</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={handleCollectData} 
                disabled={isLoading}
              >
                {isLoading ? 'データ収集中...' : 'データを収集'}
              </Button>

              {isLoading && (
                <div className="space-y-2">
                  <Progress value={progress} className="w-full" />
                  <p className="text-sm text-muted-foreground">{status}</p>
                </div>
              )}

              {error && (
                <p className="text-red-500 mt-2">{error}</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="company-input">
          <Card>
            <CardHeader>
              <CardTitle>企業情報入力</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* モード選択 */}
              <div className="space-y-4">
                <div className="flex space-x-4">
                  <Button
                    variant={companyMode === 'new' ? 'default' : 'outline'}
                    onClick={() => setCompanyMode('new')}
                  >
                    新規企業追加
                  </Button>
                  <Button
                    variant={companyMode === 'update' ? 'default' : 'outline'}
                    onClick={() => setCompanyMode('update')}
                  >
                    既存企業更新
                  </Button>
                </div>
                
                {companyMode === 'update' && (
                  <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
                    <h4 className="font-semibold">既存企業を検索</h4>
                    <div className="flex space-x-2">
                      <Input
                        placeholder="企業名またはティッカーで検索..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearchCompanies()}
                      />
                      <Button 
                        onClick={handleSearchCompanies}
                        disabled={isSearching || !searchQuery.trim()}
                      >
                        {isSearching ? '検索中...' : '検索'}
                      </Button>
                    </div>
                    
                    {searchResults.length > 0 && (
                      <div className="space-y-2">
                        <h5 className="font-medium">検索結果:</h5>
                        <div className="max-h-40 overflow-y-auto space-y-1">
                          {searchResults.map((company, index) => (
                            <div
                              key={index}
                              className="p-2 border rounded cursor-pointer hover:bg-blue-50"
                              onClick={() => handleSelectCompany(company)}
                            >
                              <div className="font-medium">{company.company_name}</div>
                              <div className="text-sm text-gray-600">
                                {company.ticker && `ティッカー: ${company.ticker}`}
                                {company.sector && ` | 業種: ${company.sector}`}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 基本情報 */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">基本情報</h3>
                  
                  <div className="space-y-2">
                    <Label htmlFor="ticker">証券コード（任意）</Label>
                    <Input
                      id="ticker"
                      value={companyForm.ticker}
                      onChange={(e) => handleInputChange('ticker', e.target.value)}
                      placeholder="例: 7203"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="company_name">企業名 *</Label>
                    <Input
                      id="company_name"
                      value={companyForm.company_name}
                      onChange={(e) => handleInputChange('company_name', e.target.value)}
                      placeholder="例: トヨタ自動車"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sector">業種</Label>
                    <Input
                      id="sector"
                      value={companyForm.sector}
                      onChange={(e) => handleInputChange('sector', e.target.value)}
                      placeholder="例: 輸送用機器"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="industry">業界</Label>
                    <Input
                      id="industry"
                      value={companyForm.industry}
                      onChange={(e) => handleInputChange('industry', e.target.value)}
                      placeholder="例: 自動車"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="country">国</Label>
                    <Select value={companyForm.country} onValueChange={(value) => handleInputChange('country', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="JP">日本</SelectItem>
                        <SelectItem value="US">アメリカ</SelectItem>
                        <SelectItem value="CN">中国</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="market">市場</Label>
                    <Select value={companyForm.market} onValueChange={(value) => handleInputChange('market', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="JP">日本</SelectItem>
                        <SelectItem value="US">NASDAQ</SelectItem>
                        <SelectItem value="NYSE">NYSE</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="website">ウェブサイト</Label>
                    <Input
                      id="website"
                      value={companyForm.website}
                      onChange={(e) => handleInputChange('website', e.target.value)}
                      placeholder="例: https://global.toyota/"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="company_type">企業タイプ</Label>
                    <Select value={companyForm.company_type} onValueChange={(value) => handleInputChange('company_type', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="LISTED">上場企業</SelectItem>
                        <SelectItem value="STARTUP">スタートアップ</SelectItem>
                        <SelectItem value="PRIVATE">非上場企業</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ceo">代表者</Label>
                    <Input
                      id="ceo"
                      value={companyForm.ceo}
                      onChange={(e) => handleInputChange('ceo', e.target.value)}
                      placeholder="例: 佐藤恒治"
                    />
                  </div>
                </div>

                {/* 財務情報 */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">財務情報</h3>
                  
                  <div className="space-y-2">
                    <Label htmlFor="market_cap">時価総額</Label>
                    <Input
                      id="market_cap"
                      type="number"
                      value={companyForm.market_cap}
                      onChange={(e) => handleInputChange('market_cap', e.target.value)}
                      placeholder="例: 30000000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="current_price">現在株価</Label>
                    <Input
                      id="current_price"
                      type="number"
                      step="0.01"
                      value={companyForm.current_price}
                      onChange={(e) => handleInputChange('current_price', e.target.value)}
                      placeholder="例: 2500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="employees">従業員数</Label>
                    <Input
                      id="employees"
                      type="number"
                      value={companyForm.employees}
                      onChange={(e) => handleInputChange('employees', e.target.value)}
                      placeholder="例: 372817"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="shares_outstanding">発行済株式数</Label>
                    <Input
                      id="shares_outstanding"
                      type="number"
                      value={companyForm.shares_outstanding}
                      onChange={(e) => handleInputChange('shares_outstanding', e.target.value)}
                      placeholder="例: 12000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="volume">出来高</Label>
                    <Input
                      id="volume"
                      type="number"
                      value={companyForm.volume}
                      onChange={(e) => handleInputChange('volume', e.target.value)}
                      placeholder="例: 1000000"
                    />
                  </div>
                </div>
              </div>

              {/* 財務指標 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">財務指標</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="per">PER</Label>
                    <Input
                      id="per"
                      type="number"
                      step="0.01"
                      value={companyForm.per}
                      onChange={(e) => handleInputChange('per', e.target.value)}
                      placeholder="例: 10.0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="pbr">PBR</Label>
                    <Input
                      id="pbr"
                      type="number"
                      step="0.01"
                      value={companyForm.pbr}
                      onChange={(e) => handleInputChange('pbr', e.target.value)}
                      placeholder="例: 1.2"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="eps">EPS</Label>
                    <Input
                      id="eps"
                      type="number"
                      step="0.01"
                      value={companyForm.eps}
                      onChange={(e) => handleInputChange('eps', e.target.value)}
                      placeholder="例: 250.0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="bps">BPS</Label>
                    <Input
                      id="bps"
                      type="number"
                      step="0.01"
                      value={companyForm.bps}
                      onChange={(e) => handleInputChange('bps', e.target.value)}
                      placeholder="例: 2000.0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="roe">ROE</Label>
                    <Input
                      id="roe"
                      type="number"
                      step="0.01"
                      value={companyForm.roe}
                      onChange={(e) => handleInputChange('roe', e.target.value)}
                      placeholder="例: 12.0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="roa">ROA</Label>
                    <Input
                      id="roa"
                      type="number"
                      step="0.01"
                      value={companyForm.roa}
                      onChange={(e) => handleInputChange('roa', e.target.value)}
                      placeholder="例: 5.0"
                    />
                  </div>
                </div>
              </div>

              {/* 損益計算書 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">損益計算書</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="revenue">売上高</Label>
                    <Input
                      id="revenue"
                      type="number"
                      value={companyForm.revenue}
                      onChange={(e) => handleInputChange('revenue', e.target.value)}
                      placeholder="例: 45000000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="operating_profit">営業利益</Label>
                    <Input
                      id="operating_profit"
                      type="number"
                      value={companyForm.operating_profit}
                      onChange={(e) => handleInputChange('operating_profit', e.target.value)}
                      placeholder="例: 5000000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="net_profit">純利益</Label>
                    <Input
                      id="net_profit"
                      type="number"
                      value={companyForm.net_profit}
                      onChange={(e) => handleInputChange('net_profit', e.target.value)}
                      placeholder="例: 4000000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="operating_margin">営業利益率</Label>
                    <Input
                      id="operating_margin"
                      type="number"
                      step="0.01"
                      value={companyForm.operating_margin}
                      onChange={(e) => handleInputChange('operating_margin', e.target.value)}
                      placeholder="例: 11.1"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="net_margin">純利益率</Label>
                    <Input
                      id="net_margin"
                      type="number"
                      step="0.01"
                      value={companyForm.net_margin}
                      onChange={(e) => handleInputChange('net_margin', e.target.value)}
                      placeholder="例: 8.9"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dividend_yield">配当利回り</Label>
                    <Input
                      id="dividend_yield"
                      type="number"
                      step="0.01"
                      value={companyForm.dividend_yield}
                      onChange={(e) => handleInputChange('dividend_yield', e.target.value)}
                      placeholder="例: 2.5"
                    />
                  </div>
                </div>
              </div>

              {/* 貸借対照表 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">貸借対照表</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="total_assets">総資産</Label>
                    <Input
                      id="total_assets"
                      type="number"
                      value={companyForm.total_assets}
                      onChange={(e) => handleInputChange('total_assets', e.target.value)}
                      placeholder="例: 80000000000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="equity">純資産</Label>
                    <Input
                      id="equity"
                      type="number"
                      value={companyForm.equity}
                      onChange={(e) => handleInputChange('equity', e.target.value)}
                      placeholder="例: 30000000000000"
                    />
                  </div>
                </div>
              </div>

              {/* 企業説明 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">企業説明</h3>
                <div className="space-y-2">
                  <Label htmlFor="business_description">事業内容</Label>
                  <Textarea
                    id="business_description"
                    value={companyForm.business_description}
                    onChange={(e) => handleInputChange('business_description', e.target.value)}
                    placeholder="企業の事業内容を入力してください"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">詳細説明</Label>
                  <Textarea
                    id="description"
                    value={companyForm.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="企業の詳細な説明を入力してください"
                    rows={4}
                  />
                </div>
              </div>

              {/* 送信ボタン */}
              <div className="flex justify-end space-x-4">
                <Button
                  onClick={handleSubmitCompany}
                  disabled={isSubmitting || !companyForm.company_name}
                  className="min-w-[120px]"
                >
                  {isSubmitting ? '送信中...' : companyMode === 'new' ? '新規企業を追加' : '企業情報を更新'}
                </Button>
              </div>

              {/* メッセージ表示 */}
              {submitMessage && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-green-800">{submitMessage}</p>
                </div>
              )}

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-800">{error}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-collect">
          <Card>
            <CardHeader>
              <CardTitle>AI企業情報収集</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-sm text-gray-500 mb-4">
                AIが企業名とウェブサイトから自動的に企業情報を収集し、データベースに保存します。
                収集される情報：業種、業界、事業内容、従業員数、財務情報など
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="ai-company-name">企業名 *</Label>
                    <Input
                      id="ai-company-name"
                      value={aiForm.company_name}
                      onChange={(e) => handleAiInputChange('company_name', e.target.value)}
                      placeholder="例: トヨタ自動車株式会社"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ai-ticker">TICKER（任意）</Label>
                    <Input
                      id="ai-ticker"
                      value={aiForm.ticker}
                      onChange={(e) => handleAiInputChange('ticker', e.target.value)}
                      placeholder="例: 7203（日本）またはAAPL（アメリカ）"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ai-website-url">ウェブサイトURL *</Label>
                    <Input
                      id="ai-website-url"
                      value={aiForm.website_url}
                      onChange={(e) => handleAiInputChange('website_url', e.target.value)}
                      placeholder="例: https://global.toyota/"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ai-country">国</Label>
                    <Select value={aiForm.country} onValueChange={(value) => handleAiInputChange('country', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="JP">日本</SelectItem>
                        <SelectItem value="US">アメリカ</SelectItem>
                        <SelectItem value="CN">中国</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button
                    onClick={handleAiCollectCompany}
                    disabled={isAiCollecting || !aiForm.company_name || !aiForm.website_url}
                    className="w-full"
                  >
                    {isAiCollecting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        AI収集中...
                      </>
                    ) : (
                      'AIで企業情報を収集'
                    )}
                  </Button>
                </div>

                {/* 収集結果表示エリア */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">収集結果</h3>
                  
                  {aiResult && (
                    <div className="space-y-4 p-4 bg-gray-900 rounded-lg">
                      <div className="space-y-2">
                        <Label className="font-semibold">収集された情報:</Label>
                        <div className="text-sm space-y-1">
                          <div><strong>企業名:</strong> {aiForm.company_name}</div>
                          <div><strong>業種:</strong> {aiResult.company_info.sector || 'N/A'}</div>
                          <div><strong>業界:</strong> {aiResult.company_info.industry || 'N/A'}</div>
                          <div><strong>企業タイプ:</strong> {aiResult.company_info.company_type || 'N/A'}</div>
                          <div><strong>代表者:</strong> {aiResult.company_info.ceo || 'N/A'}</div>
                          <div><strong>従業員数:</strong> {aiResult.company_info.estimated_employees || 'N/A'}</div>
                          <div><strong>推定時価総額:</strong> {aiResult.company_info.estimated_market_cap ? `${aiResult.company_info.estimated_market_cap.toLocaleString()}円` : 'N/A'}</div>
                          <div><strong>推定売上高:</strong> {aiResult.company_info.estimated_revenue ? `${aiResult.company_info.estimated_revenue.toLocaleString()}円` : 'N/A'}</div>
                        </div>
                      </div>
                      
                      {aiResult.company_info.business_description && (
                        <div className="space-y-2">
                          <Label className="font-semibold">事業内容:</Label>
                          <div className="text-sm bg-gray-800 p-2 rounded border">
                            {aiResult.company_info.business_description}
                          </div>
                        </div>
                      )}
                      
                      {aiResult.company_info.description && (
                        <div className="space-y-2">
                          <Label className="font-semibold">詳細説明:</Label>
                          <div className="text-sm bg-gray-800 p-2 rounded border">
                            {aiResult.company_info.description}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {!aiResult && !isAiCollecting && (
                    <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg">
                      企業名とウェブサイトURLを入力して「AIで企業情報を収集」ボタンをクリックしてください。
                    </div>
                  )}
                </div>
              </div>

              {/* メッセージ表示 */}
              {submitMessage && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-green-800">{submitMessage}</p>
                </div>
              )}

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-800">{error}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="financial-reports">
          <Card>
            <CardHeader>
              <CardTitle>決算資料収集</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-500 mb-4">
                EDINET、TDnet、企業サイトから決算資料を収集します。
                収集した資料はGoogle Cloud Storageに保存され、アプリ内で閲覧できるようになります。
              </div>
              <Button 
                onClick={handleCollectReports} 
                disabled={isLoading}
              >
                {isLoading ? '収集中...' : '決算資料を収集'}
              </Button>

              {isLoading && (
                <div className="space-y-2">
                  <Progress value={progress} className="w-full" />
                  <p className="text-sm text-muted-foreground">{status}</p>
                </div>
              )}

              {error && (
                <p className="text-red-500 mt-2">{error}</p>
              )}

              {/* ログ表示エリア */}
              {logs.length > 0 && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle>処理ログ</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                      {logs.map((log, index) => (
                        <div
                          key={index}
                          className={`text-sm ${
                            log.startsWith('エラー') ? 'text-red-500' : 'text-gray-700'
                          } mb-1`}
                        >
                          {log}
                        </div>
                      ))}
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DataCollectionPage;
