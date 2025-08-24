// Google Drive API サービス
const GOOGLE_DRIVE_API_KEY = import.meta.env.VITE_GOOGLE_DRIVE_API_KEY || '';
const GOOGLE_DRIVE_FOLDER_ID = import.meta.env.VITE_GOOGLE_DRIVE_FOLDER_ID || '';

console.log('Google Drive API設定:', {
  API_KEY: GOOGLE_DRIVE_API_KEY ? '設定済み' : '未設定',
  FOLDER_ID: GOOGLE_DRIVE_FOLDER_ID ? '設定済み' : '未設定',
  FOLDER_ID_VALUE: GOOGLE_DRIVE_FOLDER_ID
});

export interface DriveFolder {
  id: string;
  name: string;
  mimeType: string;
  createdTime: string;
  modifiedTime: string;
  size?: string;
}

export interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  createdTime: string;
  modifiedTime: string;
  size: string;
  webViewLink: string;
  webContentLink: string;
}

export interface DriveItem {
  id: string;
  name: string;
  mimeType: string;
  createdTime: string;
  modifiedTime: string;
  size?: string;
  webViewLink?: string;
  webContentLink?: string;
  isFolder: boolean;
}

export const googleDriveService = {
  // フォルダ一覧を取得
  async getFolders(): Promise<DriveFolder[]> {
    try {
      console.log('getFolders開始 - API_KEY:', GOOGLE_DRIVE_API_KEY ? '設定済み' : '未設定');
      console.log('getFolders開始 - FOLDER_ID:', GOOGLE_DRIVE_FOLDER_ID);
      
      if (!GOOGLE_DRIVE_API_KEY || !GOOGLE_DRIVE_FOLDER_ID) {
        console.warn('Google Drive API設定が不完全です');
        console.warn('API_KEY:', GOOGLE_DRIVE_API_KEY ? '設定済み' : '未設定');
        console.warn('FOLDER_ID:', GOOGLE_DRIVE_FOLDER_ID);
        return this.getMockFolders();
      }

      // 共有ドライブ対応のクエリ
      const url = `https://www.googleapis.com/drive/v3/files?` +
        `q='${GOOGLE_DRIVE_FOLDER_ID}'+in+parents+and+mimeType='application/vnd.google-apps.folder'&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name,mimeType,createdTime,modifiedTime)&` +
        `supportsAllDrives=true&` +
        `includeItemsFromAllDrives=true`;
      
      console.log('API URL:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      console.log('API Response status:', response.status);
      console.log('API Response ok:', response.ok);
      console.log('API Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Google Drive API error response:', errorText);
        
        // エラーの種類を判定
        if (response.status === 403) {
          console.error('権限エラー: Google Drive APIが有効になっていないか、APIキーに権限がありません');
          console.error('共有ドライブの場合は、OAuth認証が必要な場合があります');
        } else if (response.status === 400) {
          console.error('リクエストエラー: フォルダIDが無効か、クエリパラメータが間違っています');
        } else if (response.status === 0) {
          console.error('CORSエラー: ブラウザがAPIリクエストをブロックしています');
        }
        
        throw new Error(`Google Drive API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);
      
      const files = data.files || [];
      console.log('取得されたフォルダ数:', files.length);
      
      if (files.length === 0) {
        console.warn('フォルダが見つかりませんでした。以下を確認してください:');
        console.warn('1. フォルダIDが正しいか');
        console.warn('2. フォルダが共有設定されているか');
        console.warn('3. APIキーに適切な権限があるか');
        console.warn('4. 共有ドライブの場合は、OAuth認証が必要な場合があります');
        console.warn('5. マイドライブにフォルダを移動してみてください');
      }
      
      return files;
    } catch (error) {
      console.error('フォルダ取得エラー:', error);
      
      // ネットワークエラーの場合
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('ネットワークエラー: CORS設定またはネットワーク接続を確認してください');
      }
      
      return this.getMockFolders();
    }
  },

  // フォルダ内のファイル一覧を取得
  async getFilesInFolder(folderId: string): Promise<DriveFile[]> {
    try {
      if (!GOOGLE_DRIVE_API_KEY) {
        console.warn('Google Drive API設定が不完全です');
        return this.getMockFiles();
      }

      const response = await fetch(
        `https://www.googleapis.com/drive/v3/files?` +
        `q='${folderId}'+in+parents+and+mimeType='application/pdf'&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name,mimeType,createdTime,modifiedTime,size,webViewLink,webContentLink)`
      );

      if (!response.ok) {
        throw new Error(`Google Drive API error: ${response.status}`);
      }

      const data = await response.json();
      return data.files || [];
    } catch (error) {
      console.error('ファイル取得エラー:', error);
      return this.getMockFiles();
    }
  },

  // フォルダとファイルの統合リストを取得
  async getFolderContents(folderId?: string): Promise<DriveItem[]> {
    try {
      if (!folderId) {
        // ルートフォルダの場合はフォルダ一覧を取得
        const folders = await this.getFolders();
        return folders.map(folder => ({
          ...folder,
          isFolder: true
        }));
      } else {
        // 特定フォルダ内のファイルを取得
        const files = await this.getFilesInFolder(folderId);
        return files.map(file => ({
          ...file,
          isFolder: false
        }));
      }
    } catch (error) {
      console.error('フォルダ内容取得エラー:', error);
      return [];
    }
  },

  // PDFファイルのプレビューURLを取得
  getPdfPreviewUrl(fileId: string): string {
    return `https://drive.google.com/file/d/${fileId}/preview`;
  },

  // PDFファイルのダウンロードURLを取得
  getPdfDownloadUrl(fileId: string): string {
    return `https://drive.google.com/uc?export=download&id=${fileId}`;
  },

  // モックフォルダデータ
  getMockFolders(): DriveFolder[] {
    return [
      {
        id: 'folder1',
        name: '決算報告書 2024年度',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2024-01-01T00:00:00.000Z',
        modifiedTime: '2024-01-15T00:00:00.000Z'
      },
      {
        id: 'folder2',
        name: '決算報告書 2023年度',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2023-01-01T00:00:00.000Z',
        modifiedTime: '2023-12-31T00:00:00.000Z'
      },
      {
        id: 'folder3',
        name: '有価証券報告書',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2024-01-01T00:00:00.000Z',
        modifiedTime: '2024-01-20T00:00:00.000Z'
      },
      {
        id: 'folder4',
        name: '四半期報告書',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2024-01-01T00:00:00.000Z',
        modifiedTime: '2024-01-25T00:00:00.000Z'
      }
    ];
  },

  // モックファイルデータ
  getMockFiles(): DriveFile[] {
    return [
      {
        id: 'file1',
        name: 'トヨタ自動車_決算報告書_2024Q3.pdf',
        mimeType: 'application/pdf',
        createdTime: '2024-01-15T00:00:00.000Z',
        modifiedTime: '2024-01-15T00:00:00.000Z',
        size: '2.5MB',
        webViewLink: 'https://drive.google.com/file/d/file1/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file1'
      },
      {
        id: 'file2',
        name: 'ソニーグループ_決算報告書_2024Q3.pdf',
        mimeType: 'application/pdf',
        createdTime: '2024-01-16T00:00:00.000Z',
        modifiedTime: '2024-01-16T00:00:00.000Z',
        size: '3.1MB',
        webViewLink: 'https://drive.google.com/file/d/file2/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file2'
      },
      {
        id: 'file3',
        name: 'ソフトバンクグループ_決算報告書_2024Q3.pdf',
        mimeType: 'application/pdf',
        createdTime: '2024-01-17T00:00:00.000Z',
        modifiedTime: '2024-01-17T00:00:00.000Z',
        size: '1.8MB',
        webViewLink: 'https://drive.google.com/file/d/file3/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file3'
      }
    ];
  }
};
