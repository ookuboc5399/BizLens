import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { googleDriveService, DriveFolder } from '../services/googleDriveService';
import { Folder, Search } from 'lucide-react';



function FinancialReports() {

  const [searchTerm, setSearchTerm] = useState('');
  const [folders, setFolders] = useState<DriveFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFolders();
  }, []);

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

  const handleFolderClick = (folder: DriveFolder) => {
    // フォルダをクリックした時の処理（必要に応じて実装）
    console.log('フォルダをクリック:', folder.name);
  };

  const handleSearch = () => {
    // 検索機能の実装（必要に応じて）
    console.log('検索:', searchTerm);
  };

  const filteredFolders = folders.filter(folder =>
    folder.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-4">
        <div className="flex items-center justify-center h-64">
          <div className="space-y-4 text-center">
            <Progress value={undefined} className="w-64" />
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
          <CardTitle>決算資料</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 検索バー */}
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="フォルダ名で検索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              検索
            </Button>
          </div>

          {/* フォルダ一覧 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredFolders.map((folder) => (
              <Card
                key={folder.id}
                className="cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleFolderClick(folder)}
              >
                <CardContent className="p-6">
                  <div className="flex flex-col items-center text-center space-y-3">
                    <Folder className="h-12 w-12 text-blue-500" />
                    <div>
                      <h3 className="font-semibold text-sm truncate w-full" title={folder.name}>
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

          {filteredFolders.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              {searchTerm ? '検索結果が見つかりませんでした' : 'フォルダがありません'}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancialReports;
