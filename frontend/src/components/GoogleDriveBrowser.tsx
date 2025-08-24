import React, { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Progress } from './ui/progress';
import { googleDriveService, DriveItem } from '../services/googleDriveService';
import { Folder, FileText, ArrowLeft, Download, Eye, Search } from 'lucide-react';

interface GoogleDriveBrowserProps {
  onFileSelect?: (file: DriveItem) => void;
}

export const GoogleDriveBrowser: React.FC<GoogleDriveBrowserProps> = ({ onFileSelect }) => {
  const [items, setItems] = useState<DriveItem[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [folderPath, setFolderPath] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState<DriveItem | null>(null);

  useEffect(() => {
    loadFolderContents();
  }, [currentFolderId]);

  const loadFolderContents = async () => {
    try {
      setLoading(true);
      setError(null);
      const contents = await googleDriveService.getFolderContents(currentFolderId);
      setItems(contents);
    } catch (err) {
      setError('フォルダの読み込みに失敗しました');
      console.error('フォルダ読み込みエラー:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = (folder: DriveItem) => {
    setCurrentFolderId(folder.id);
    setFolderPath([...folderPath, folder.name]);
  };

  const handleFileClick = (file: DriveItem) => {
    setSelectedFile(file);
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleBackClick = () => {
    if (folderPath.length > 0) {
      const newPath = folderPath.slice(0, -1);
      setFolderPath(newPath);
      
      // ルートフォルダに戻る場合
      if (newPath.length === 0) {
        setCurrentFolderId(undefined);
      } else {
        // 実際の実装では、フォルダIDの履歴を管理する必要があります
        // ここでは簡易的にルートに戻します
        setCurrentFolderId(undefined);
        setFolderPath([]);
      }
    }
  };

  const handleSearch = () => {
    // 検索機能の実装（必要に応じて）
    console.log('検索:', searchTerm);
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const formatFileSize = (size?: string) => {
    if (!size) return '';
    return size;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="space-y-4 text-center">
          <Progress value={undefined} className="w-64" />
          <p className="text-sm text-gray-500">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <p className="text-red-500 mb-4">{error}</p>
        <Button onClick={loadFolderContents}>再試行</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {folderPath.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackClick}
              className="flex items-center space-x-1"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>戻る</span>
            </Button>
          )}
          <h2 className="text-lg font-semibold">
            {folderPath.length > 0 ? folderPath[folderPath.length - 1] : '決算資料'}
          </h2>
        </div>
        
        <div className="flex items-center space-x-2">
          <Input
            type="text"
            placeholder="ファイル名で検索..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />
          <Button size="sm" onClick={handleSearch}>
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* パンくずリスト */}
      {folderPath.length > 0 && (
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span>決算資料</span>
          {folderPath.map((path, index) => (
            <React.Fragment key={index}>
              <span>/</span>
              <span>{path}</span>
            </React.Fragment>
          ))}
        </div>
      )}

      {/* ファイル・フォルダ一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredItems.map((item) => (
          <Card
            key={item.id}
            className={`cursor-pointer hover:bg-gray-50 transition-colors ${
              selectedFile?.id === item.id ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => item.isFolder ? handleFolderClick(item) : handleFileClick(item)}
          >
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {item.isFolder ? (
                    <Folder className="h-8 w-8 text-blue-500" />
                  ) : (
                    <FileText className="h-8 w-8 text-red-500" />
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm truncate" title={item.name}>
                    {item.name}
                  </h3>
                  
                  <div className="text-xs text-gray-500 mt-1">
                    <div>更新日: {formatDate(item.modifiedTime)}</div>
                    {!item.isFolder && item.size && (
                      <div>サイズ: {formatFileSize(item.size)}</div>
                    )}
                  </div>
                </div>
              </div>

              {/* ファイルの場合のアクションボタン */}
              {!item.isFolder && (
                <div className="flex space-x-2 mt-3">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(googleDriveService.getPdfPreviewUrl(item.id), '_blank');
                    }}
                    className="flex-1"
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    プレビュー
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(googleDriveService.getPdfDownloadUrl(item.id), '_blank');
                    }}
                    className="flex-1"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    ダウンロード
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          {searchTerm ? '検索結果が見つかりませんでした' : 'フォルダが空です'}
        </div>
      )}
    </div>
  );
};
