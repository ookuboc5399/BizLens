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

      // APIキーを使用したクエリ（最新12個のフォルダを取得）
      const url = `https://www.googleapis.com/drive/v3/files?` +
        `q='${GOOGLE_DRIVE_FOLDER_ID}'+in+parents+and+mimeType='application/vnd.google-apps.folder'&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name,mimeType,createdTime,modifiedTime)&` +
        `orderBy=modifiedTime desc&` +
        `pageSize=12`;
      
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

  // フォルダを検索
  async searchFolders(query: string): Promise<DriveFolder[]> {
    try {
      console.log('searchFolders開始 - 検索クエリ:', query);
      
      if (!GOOGLE_DRIVE_API_KEY || !GOOGLE_DRIVE_FOLDER_ID) {
        console.warn('Google Drive API設定が不完全です');
        return [];
      }

      // 検索クエリを使用したAPIリクエスト
      const url = `https://www.googleapis.com/drive/v3/files?` +
        `q='${GOOGLE_DRIVE_FOLDER_ID}'+in+parents+and+mimeType='application/vnd.google-apps.folder'and+name+contains+'${query}'&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name,mimeType,createdTime,modifiedTime)&` +
        `orderBy=modifiedTime desc`;
      
      console.log('検索API URL:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      console.log('検索API Response status:', response.status);
      console.log('検索API Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Google Drive API error response:', errorText);
        throw new Error(`Google Drive API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('検索API Response data:', data);
      
      const files = data.files || [];
      console.log('検索で見つかったフォルダ数:', files.length);
      
      return files;
    } catch (error) {
      console.error('フォルダ検索エラー:', error);
      return [];
    }
  },

  // フォルダ内のファイル一覧を取得
  async getFilesInFolder(folderId: string): Promise<DriveFile[]> {
    try {
      console.log('getFilesInFolder開始 - フォルダID:', folderId);
      
      if (!GOOGLE_DRIVE_API_KEY) {
        console.warn('Google Drive API設定が不完全です');
        return this.getMockFiles();
      }

      // PDFとHTMLファイルの両方を取得
      const response = await fetch(
        `https://www.googleapis.com/drive/v3/files?` +
        `q='${folderId}'+in+parents+and+(mimeType='application/pdf'+or+mimeType='text/html')&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name,mimeType,createdTime,modifiedTime,size,webViewLink,webContentLink)`
      );

      console.log('ファイル取得API Response status:', response.status);
      console.log('ファイル取得API Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Google Drive API error response:', errorText);
        throw new Error(`Google Drive API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('ファイル取得API Response data:', data);
      
      const files = data.files || [];
      console.log('取得されたファイル数:', files.length);
      console.log('取得されたファイル一覧:', files.map(f => ({ name: f.name, mimeType: f.mimeType })));
      
      return files;
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

  // 企業名を正規化（フォルダ名用）
  normalizeCompanyName(companyName: string): string {
    // 一般的な企業名の正規化ルール
    const normalizationMap: { [key: string]: string } = {
      'Apple Inc.': 'Apple',
      'Microsoft Corporation': 'Microsoft',
      'Amazon.com Inc.': 'Amazon',
      'Alphabet Inc.': 'Alphabet',
      'Tesla Inc.': 'Tesla',
      'Meta Platforms Inc.': 'Meta',
      'NVIDIA Corporation': 'NVIDIA',
      'Netflix Inc.': 'Netflix',
      'Salesforce Inc.': 'Salesforce',
      'Adobe Inc.': 'Adobe',
      'Intel Corporation': 'Intel',
      'HP Inc.': 'HP',
      'Nike Inc.': 'Nike',
      'FedEx Corporation': 'FedEx',
      'Marriott International Inc.': 'Marriott International',
      'Southwest Airlines Co.': 'Southwest Airlines',
      'ServiceNow Inc.': 'Service Now',
      'Teach For America': 'Teach For America',
      'Amgen Inc.': 'Amgen',
      'Pixar Animation Studios': 'Pixar',
      'L.L.Bean Inc.': 'L.L.Bean'
    };

    // マッピングに存在する場合は正規化された名前を返す
    if (normalizationMap[companyName]) {
      return normalizationMap[companyName];
    }

    // 一般的な正規化ルール
    let normalized = companyName
      .replace(/\s+(Inc\.?|Corporation|Corp\.?|Company|Co\.?|Ltd\.?|Limited|LLC|LP|LLP)$/i, '')
      .replace(/\s+/g, ' ')
      .trim();

    return normalized;
  },

  // 企業フォルダを検索または作成
  async findOrCreateCompanyFolder(companyName: string): Promise<string> {
    try {
      const normalizedName = this.normalizeCompanyName(companyName);
      console.log(`Searching for company folder: "${normalizedName}" (original: "${companyName}")`);

      if (!GOOGLE_DRIVE_API_KEY || !GOOGLE_DRIVE_FOLDER_ID) {
        console.warn('Google Drive API設定が不完全です');
        return '';
      }

      // 既存のフォルダを検索
      const searchUrl = `https://www.googleapis.com/drive/v3/files?` +
        `q='${GOOGLE_DRIVE_FOLDER_ID}'+in+parents+and+mimeType='application/vnd.google-apps.folder'and+name='${encodeURIComponent(normalizedName)}'&` +
        `key=${GOOGLE_DRIVE_API_KEY}&` +
        `fields=files(id,name)`;

      console.log('Searching for existing folder:', searchUrl);

      const searchResponse = await fetch(searchUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (searchResponse.ok) {
        const searchData = await searchResponse.json();
        const existingFolders = searchData.files || [];

        if (existingFolders.length > 0) {
          console.log(`Found existing folder: ${existingFolders[0].name} (ID: ${existingFolders[0].id})`);
          return existingFolders[0].id;
        }
      }

      // フォルダが存在しない場合は作成
      console.log(`Creating new folder: "${normalizedName}"`);
      
      const createUrl = `https://www.googleapis.com/drive/v3/files?key=${GOOGLE_DRIVE_API_KEY}`;
      
      const folderMetadata = {
        name: normalizedName,
        mimeType: 'application/vnd.google-apps.folder',
        parents: [GOOGLE_DRIVE_FOLDER_ID]
      };

      const createResponse = await fetch(createUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(folderMetadata)
      });

      if (createResponse.ok) {
        const createData = await createResponse.json();
        console.log(`Created new folder: ${createData.name} (ID: ${createData.id})`);
        return createData.id;
      } else {
        const errorText = await createResponse.text();
        console.error('Failed to create folder:', errorText);
        throw new Error(`Failed to create folder: ${createResponse.status} - ${errorText}`);
      }

    } catch (error) {
      console.error('Error finding or creating company folder:', error);
      throw error;
    }
  },

  // ファイルを企業フォルダにアップロード
  async uploadFileToCompanyFolder(companyName: string, fileName: string, fileContent: string | Blob, mimeType: string = 'text/html'): Promise<string> {
    try {
      const folderId = await this.findOrCreateCompanyFolder(companyName);
      
      if (!folderId) {
        throw new Error('Failed to get company folder ID');
      }

      console.log(`Uploading file "${fileName}" to folder ID: ${folderId}`);

      if (!GOOGLE_DRIVE_API_KEY) {
        console.warn('Google Drive API設定が不完全です');
        return '';
      }

      // ファイルメタデータを作成
      const metadata = {
        name: fileName,
        parents: [folderId]
      };

      // FormDataを作成
      const formData = new FormData();
      formData.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
      formData.append('file', new Blob([fileContent], { type: mimeType }));

      const uploadUrl = `https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&key=${GOOGLE_DRIVE_API_KEY}`;

      const uploadResponse = await fetch(uploadUrl, {
        method: 'POST',
        body: formData
      });

      if (uploadResponse.ok) {
        const uploadData = await uploadResponse.json();
        console.log(`File uploaded successfully: ${uploadData.name} (ID: ${uploadData.id})`);
        return uploadData.id;
      } else {
        const errorText = await uploadResponse.text();
        console.error('Failed to upload file:', errorText);
        throw new Error(`Failed to upload file: ${uploadResponse.status} - ${errorText}`);
      }

    } catch (error) {
      console.error('Error uploading file to company folder:', error);
      throw error;
    }
  },

  // モックフォルダデータ
  getMockFolders(): DriveFolder[] {
    return [
      {
        id: 'folder1',
        name: 'Apple',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2024-01-01T00:00:00.000Z',
        modifiedTime: '2024-01-15T00:00:00.000Z'
      },
      {
        id: 'folder2',
        name: 'Amazon',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2023-01-01T00:00:00.000Z',
        modifiedTime: '2023-12-31T00:00:00.000Z'
      },
      {
        id: 'folder3',
        name: 'Microsoft',
        mimeType: 'application/vnd.google-apps.folder',
        createdTime: '2024-01-01T00:00:00.000Z',
        modifiedTime: '2024-01-20T00:00:00.000Z'
      },
      {
        id: 'folder4',
        name: 'Google',
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
        name: 'Apple_Inc._aapl-20240928.htm',
        mimeType: 'text/html',
        createdTime: '2024-01-15T00:00:00.000Z',
        modifiedTime: '2024-01-15T00:00:00.000Z',
        size: '1.5MB',
        webViewLink: 'https://drive.google.com/file/d/file1/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file1'
      },
      {
        id: 'file2',
        name: 'Amazon.com_Inc._amzn-20241231.htm',
        mimeType: 'text/html',
        createdTime: '2024-01-16T00:00:00.000Z',
        modifiedTime: '2024-01-16T00:00:00.000Z',
        size: '1.9MB',
        webViewLink: 'https://drive.google.com/file/d/file2/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file2'
      },
      {
        id: 'file3',
        name: 'Microsoft_Corporation_10K_2024.pdf',
        mimeType: 'application/pdf',
        createdTime: '2024-01-17T00:00:00.000Z',
        modifiedTime: '2024-01-17T00:00:00.000Z',
        size: '2.1MB',
        webViewLink: 'https://drive.google.com/file/d/file3/preview',
        webContentLink: 'https://drive.google.com/uc?export=download&id=file3'
      }
    ];
  }
};
