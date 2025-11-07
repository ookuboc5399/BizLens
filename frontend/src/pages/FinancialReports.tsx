'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { googleDriveService, DriveFolder, DriveFile } from '../services/googleDriveService';
import { Folder, Search, FileText, ArrowLeft, Eye, FileCode } from 'lucide-react';
import HTMLViewer from '../components/HTMLViewer';

function FinancialReports() {
  const [searchParams] = useSearchParams();
  const companyName = searchParams.get('company');
  const ticker = searchParams.get('ticker');
  
  const [searchTerm, setSearchTerm] = useState('');
  const [folders, setFolders] = useState<DriveFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentFolder, setCurrentFolder] = useState<DriveFolder | null>(null);
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [htmlViewer, setHtmlViewer] = useState<{
    isOpen: boolean;
    htmlContent: string;
    fileName: string;
  }>({
    isOpen: false,
    htmlContent: '',
    fileName: ''
  });

  useEffect(() => {
    // 企業名またはティッカーが指定されている場合は自動検索
    if (companyName || ticker) {
      const searchQuery = companyName || ticker || '';
      setSearchTerm(searchQuery);
      handleAutoSearch(searchQuery);
    } else {
      loadFolders();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyName, ticker]);

  const loadFolders = async () => {
    try {
      setLoading(true);
      setError(null);
      const folderData = await googleDriveService.getFolders();
      setFolders(folderData);
    } catch (err) {
      setError('フォルダの読み込みに失敗しました');
      console.error('フォルダ読み込みエラー:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = async (folder: DriveFolder) => {
    try {
      setCurrentFolder(folder);
      setLoadingFiles(true);
      setError(null);
      
      console.log('フォルダをクリック:', folder.name);
      console.log('フォルダID:', folder.id);
      
      const folderFiles = await googleDriveService.getFilesInFolder(folder.id);
      console.log('取得したファイル:', folderFiles);
      setFiles(folderFiles);
      
      console.log('フォルダ内ファイル数:', folderFiles.length);
    } catch (err) {
      setError('ファイルの読み込みに失敗しました');
      console.error('ファイル読み込みエラー:', err);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleBackToFolders = () => {
    setCurrentFolder(null);
    setFiles([]);
    setError(null);
  };

  const handleAutoSearch = async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      const searchResults = await googleDriveService.searchFolders(query);
      setFolders(searchResults);
      
      // 検索結果が1つだけの場合は自動的にそのフォルダを開く
      if (searchResults.length === 1) {
        await handleFolderClick(searchResults[0]);
      }
    } catch (err) {
      setError('検索に失敗しました');
      console.error('検索エラー:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    const term = searchTerm.trim();
    if (!term) {
      await loadFolders();
      return;
    }
    try {
      setIsSearching(true);
      setError(null);
      const searchResults = await googleDriveService.searchFolders(term);
      setFolders(searchResults);
    } catch (err) {
      setError('検索に失敗しました');
      console.error('検索エラー:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString('ja-JP');

  const formatFileSize = (size: string) => {
    const bytes = parseInt(size);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const isHtmlFile = (fileName: string): boolean => {
    return fileName.toLowerCase().endsWith('.html') || fileName.toLowerCase().endsWith('.htm');
  };

  const isPdfFile = (fileName: string): boolean => {
    return fileName.toLowerCase().endsWith('.pdf');
  };

  const handleFileClick = async (file: DriveFile) => {
    if (isHtmlFile(file.name)) {
      try {
        // SEC EDGARファイルかどうかを判定
        const isSecEdgarFile = file.name.includes('_10K') || file.name.includes('_10-Q') || file.name.includes('_8-K');
        
        if (isSecEdgarFile) {
          // SEC EDGARファイルの場合はバックエンドから取得
          const companyName = file.name.split('_')[0];
          const response = await fetch(`http://localhost:8000/api/admin/sec-edgar/view-file/${file.name}`);
          
          if (response.ok) {
            const htmlContent = await response.text();
            setHtmlViewer({
              isOpen: true,
              htmlContent,
              fileName: file.name
            });
          } else {
            throw new Error('Failed to fetch SEC EDGAR file');
          }
        } else {
          // 通常のHTMLファイルの場合はバックエンド経由で取得
          // Google Driveから直接取得するとCORSエラーが発生する可能性があるため
          const response = await fetch(`http://localhost:8000/api/admin/google-drive/get-file-content/${file.id}`);
          
          if (response.ok) {
            const htmlContent = await response.text();
            setHtmlViewer({
              isOpen: true,
              htmlContent,
              fileName: file.name
            });
          } else {
            throw new Error('Failed to fetch HTML file content');
          }
        }
      } catch (error) {
        console.error('HTMLファイルの読み込みに失敗:', error);
        // エラーの場合はアラートを表示して、Google Driveのビューは開かない
        alert('HTMLファイルの読み込みに失敗しました。ファイルが正しくアップロードされているか確認してください。');
      }
    } else {
      // PDFやその他のファイルは通常通り開く
      window.open(file.webViewLink, '_blank');
    }
  };

  const closeHtmlViewer = () => {
    setHtmlViewer({
      isOpen: false,
      htmlContent: '',
      fileName: ''
    });
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <div className="flex items-center justify-center h-64">
          <div className="space-y-4 text-center">
            <Progress value={30} className="w-64" />
            <p className="text-sm text-gray-500">読み込み中...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <div className="text-center p-8">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={loadFolders}>再試行</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>
            {currentFolder ? (
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleBackToFolders}
                  variant="ghost"
                  size="sm"
                  className="p-1"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                決算資料 - {currentFolder.name}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span>決算資料</span>
                {(companyName || ticker) && (
                  <span className="text-sm text-gray-500 font-normal">
                    - {companyName || ticker} の検索結果
                  </span>
                )}
              </div>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 検索バー（フォルダ一覧時のみ表示） */}
          {!currentFolder && (
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="フォルダ名で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Button onClick={handleSearch} disabled={isSearching}>
                <Search className="h-4 w-4 mr-2" />
                {isSearching ? '検索中...' : '検索'}
              </Button>
              {searchTerm && (
                <Button
                  onClick={() => {
                    setSearchTerm('');
                    loadFolders();
                  }}
                  variant="outline"
                >
                  クリア
                </Button>
              )}
            </div>
          )}

          {/* フォルダ一覧またはファイル一覧 */}
          {!currentFolder ? (
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                {searchTerm
                  ? `検索結果: ${folders.length}件`
                  : `最新のフォルダ: ${folders.length}件`}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {folders.map((folder) => (
                  <Card
                    key={folder.id}
                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => handleFolderClick(folder)}
                  >
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center space-y-3">
                        <Folder className="h-12 w-12 text-blue-500" />
                        <div>
                          <h3
                            className="font-semibold text-sm truncate w-full"
                            title={folder.name}
                          >
                            {folder.name}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            更新日: {formatDate(folder.modifiedTime)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {folders.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  {searchTerm
                    ? '検索結果が見つかりませんでした'
                    : 'フォルダがありません'}
                </div>
              )}
            </div>
          ) : (
            /* ファイル一覧 */
            <div className="space-y-4">
              {loadingFiles ? (
                <div className="flex items-center justify-center h-32">
                  <div className="space-y-4 text-center">
                    <Progress value={30} className="w-64" />
                    <p className="text-sm text-gray-500">ファイルを読み込み中...</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="text-sm text-gray-600">
                    ファイル数: {files.length}件
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {files.map((file) => (
                      <Card
                        key={file.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => handleFileClick(file)}
                      >
                        <CardContent className="p-6">
                          <div className="flex flex-col items-center text-center space-y-3">
                            {isHtmlFile(file.name) ? (
                              <FileCode className="h-12 w-12 text-green-500" />
                            ) : isPdfFile(file.name) ? (
                              <FileText className="h-12 w-12 text-red-500" />
                            ) : (
                              <FileText className="h-12 w-12 text-gray-500" />
                            )}
                            <div>
                              <h3
                                className="font-semibold text-sm truncate w-full"
                                title={file.name}
                              >
                                {file.name}
                              </h3>
                              <p className="text-xs text-gray-500 mt-1">
                                サイズ: {formatFileSize(file.size)}
                              </p>
                              <p className="text-xs text-gray-500">
                                更新日: {formatDate(file.modifiedTime)}
                              </p>
                              {isHtmlFile(file.name) && (
                                <div className="flex items-center justify-center mt-2">
                                  <Eye className="h-3 w-3 text-green-500 mr-1" />
                                  <span className="text-xs text-green-600">
                                    {(file.name.includes('_10K') || file.name.includes('_10-Q') || file.name.includes('_8-K')) 
                                      ? 'SEC EDGAR表示可能' 
                                      : 'HTML表示可能'}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {files.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      ファイルがありません
                    </div>
                  )}
                </>
              )}
            </div>
          )}

        </CardContent>
      </Card>

      {/* HTML Viewer Modal */}
      {htmlViewer.isOpen && (
        <HTMLViewer
          htmlContent={htmlViewer.htmlContent}
          fileName={htmlViewer.fileName}
          onClose={closeHtmlViewer}
        />
      )}
    </div>
  );
}

export default FinancialReports;