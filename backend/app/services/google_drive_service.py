#!/usr/bin/env python3
"""
Google Drive API サービス（サービスアカウント認証）
"""

import os
import json
from typing import Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import logging

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Google Drive APIサービスを初期化"""
        try:
            print("Initializing Google Drive service...")
            # サービスアカウントキーファイルのパス
            service_account_file = "/Users/ookubo/ookuboc5399/perpetualtraveler/BizLens/backend/roadtoentrepreneur-045990358137.json"
            
            print(f"Checking service account file: {service_account_file}")
            if not os.path.exists(service_account_file):
                print(f"Service account file not found: {service_account_file}")
                logger.error(f"Service account file not found: {service_account_file}")
                return
            
            print("Service account file exists, loading credentials...")
            # スコープを設定（Google Drive API用）
            scopes = ['https://www.googleapis.com/auth/drive']
            
            # サービスアカウント認証情報を作成
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            print("Credentials loaded successfully")
            
            # Google Drive APIサービスを構築
            print("Building Google Drive API service...")
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Google Sheets APIサービスも構築
            print("Building Google Sheets API service...")
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            
            print("Google Drive and Sheets API services initialized successfully")
            logger.info("Google Drive and Sheets API services initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize Google Drive service: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            self.service = None
    
    def normalize_company_name(self, company_name: str) -> str:
        """企業名を正規化（フォルダ名用）"""
        normalization_map = {
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
        }
        
        if company_name in normalization_map:
            return normalization_map[company_name]
        
        # 一般的な正規化ルール
        normalized = company_name
        normalized = normalized.replace(' Inc.', '').replace(' Corporation', '').replace(' Corp.', '')
        normalized = normalized.replace(' Company', '').replace(' Co.', '').replace(' Ltd.', '')
        normalized = normalized.replace(' Limited', '').replace(' LLC', '').replace(' LP', '')
        normalized = normalized.replace(' LLP', '').strip()
        
        return normalized
    
    def find_or_create_company_folder(self, company_name: str, parent_folder_id: str = "1qH-kGP8Hn2setbwAHWcRXNEr2pd-hvMg") -> Optional[str]:
        """企業フォルダを検索または作成"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            normalized_name = self.normalize_company_name(company_name)
            logger.info(f"Searching for company folder: '{normalized_name}' (original: '{company_name}')")
            
            # 親フォルダIDが指定されていない場合は、デフォルトのフォルダを使用
            if parent_folder_id is None:
                parent_folder_id = "1qH-kGP8Hn2setbwAHWcRXNEr2pd-hvMg"
            
            # 既存のフォルダを検索
            query = f"name='{normalized_name}' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                logger.info(f"Found existing folder: {folders[0]['name']} (ID: {folder_id})")
                return folder_id
            
            # フォルダが存在しない場合は作成
            logger.info(f"Creating new folder: '{normalized_name}'")
            
            folder_metadata = {
                'name': normalized_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id, name'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created new folder: {folder.get('name')} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            logger.error(f"Error finding or creating company folder: {str(e)}")
            return None
    
    def upload_file_to_company_folder(self, company_name: str, file_name: str, file_content: str, 
                                    mime_type: str = 'text/html', parent_folder_id: str = "1qH-kGP8Hn2setbwAHWcRXNEr2pd-hvMg", use_shared_drive: bool = True) -> Optional[str]:
        """ファイルを企業フォルダにアップロード"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            # 企業フォルダを取得または作成
            company_folder_id = self.find_or_create_company_folder(company_name, parent_folder_id)
            
            if not company_folder_id:
                logger.error("Failed to get company folder ID")
                return None
            
            logger.info(f"Uploading file '{file_name}' to folder ID: {company_folder_id}")
            
            # ファイルメタデータを作成
            file_metadata = {
                'name': file_name,
                'parents': [company_folder_id]
            }
            
            # ファイル内容をメモリに読み込み
            file_content_bytes = file_content.encode('utf-8')
            media = MediaIoBaseUpload(
                io.BytesIO(file_content_bytes),
                mimetype=mime_type,
                resumable=True
            )
            
            # ファイルをアップロード（共有ドライブ対応）
            if use_shared_drive:
                # 共有ドライブを使用する場合
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink',
                    supportsAllDrives=True
                ).execute()
            else:
                # 通常のドライブを使用する場合
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink'
                ).execute()
            
            file_id = file.get('id')
            logger.info(f"File uploaded successfully: {file.get('name')} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file to company folder: {str(e)}")
            return None
    
    def get_folder_info(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """フォルダ情報を取得"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields='id, name, mimeType, createdTime, modifiedTime, webViewLink'
            ).execute()
            
            return folder
            
        except Exception as e:
            logger.error(f"Error getting folder info: {str(e)}")
            return None
    
    def list_files_in_folder(self, folder_id: str) -> list:
        """フォルダ内のファイル一覧を取得"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            results = self.service.files().list(
                q=f"parents in '{folder_id}' and trashed=false",
                fields="files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Error listing files in folder: {str(e)}")
            return []

    def get_file_content(self, file_id: str) -> str:
        """Google Driveからファイルの内容を取得"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            # ファイルの内容をダウンロード
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            # バイト列を文字列に変換
            if isinstance(file_content, bytes):
                return file_content.decode('utf-8')
            else:
                return str(file_content)
                
        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            return None

    def get_spreadsheet_data(self, spreadsheet_id: str, range_name: str = None, sheet_name: str = None) -> dict:
        """Google Sheetsからデータを取得"""
        if not self.sheets_service:
            logger.error("Google Sheets service not initialized")
            return None
        
        try:
            print(f"Getting spreadsheet data for ID: {spreadsheet_id}")
            
            # スプレッドシートのメタデータを取得
            spreadsheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            print(f"Spreadsheet title: {spreadsheet_metadata.get('properties', {}).get('title', 'Unknown')}")
            
            # シート名の一覧を取得
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_metadata.get('sheets', [])]
            print(f"Available sheets: {sheet_names}")
            
            # データを取得（範囲が指定されていない場合は指定されたシートまたは最初のシート全体）
            if not range_name:
                target_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0] if sheet_names else "Sheet1"
                range_name = f"{target_sheet}!A:Z"
            
            print(f"Getting data from range: {range_name}")
            
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            print(f"Retrieved {len(values)} rows of data")
            
            # データの構造を分析
            if values:
                headers = values[0] if values else []
                print(f"Headers: {headers}")
                
                # 最初の数行を表示
                for i, row in enumerate(values[:5]):
                    print(f"Row {i+1}: {row}")
            
            return {
                'title': spreadsheet_metadata.get('properties', {}).get('title', 'Unknown'),
                'sheets': sheet_names,
                'headers': values[0] if values else [],
                'data': values,
                'range': range_name
            }
            
        except Exception as e:
            logger.error(f"Error getting spreadsheet data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_all_sheets_data(self, spreadsheet_id: str) -> dict:
        """スプレッドシートのすべてのシートのデータを取得"""
        if not self.sheets_service:
            logger.error("Google Sheets service not initialized")
            return None
        
        try:
            print(f"Getting all sheets data for ID: {spreadsheet_id}")
            
            # スプレッドシートのメタデータを取得
            spreadsheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            print(f"Spreadsheet title: {spreadsheet_metadata.get('properties', {}).get('title', 'Unknown')}")
            
            # シート名の一覧を取得
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_metadata.get('sheets', [])]
            print(f"Available sheets: {sheet_names}")
            
            all_sheets_data = {}
            
            # 各シートのデータを取得
            for sheet_name in sheet_names:
                print(f"Getting data from sheet: {sheet_name}")
                range_name = f"{sheet_name}!A:Z"
                
                result = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                print(f"Retrieved {len(values)} rows from {sheet_name}")
                
                all_sheets_data[sheet_name] = {
                    'headers': values[0] if values else [],
                    'data': values,
                    'range': range_name
                }
            
            return {
                'title': spreadsheet_metadata.get('properties', {}).get('title', 'Unknown'),
                'sheets': sheet_names,
                'sheets_data': all_sheets_data
            }
            
        except Exception as e:
            logger.error(f"Error getting all sheets data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def search_company_folders(self, query: str, parent_folder_id: str = "1uragZmOuCVZYJ_9Wcyxe6R9-dnyI8-fi") -> list:
        """Google Driveで企業フォルダとファイルを検索"""
        logger.info(f"Google Drive service initialized: {self.service is not None}")
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            print(f"Starting Google Drive search for query: '{query}' in folder: {parent_folder_id}")
            logger.info(f"Starting Google Drive search for query: '{query}' in folder: {parent_folder_id}")
            
            # まず、指定されたフォルダ内のすべてのアイテムを取得してテスト
            print("Testing folder access...")
            test_query = f"parents in '{parent_folder_id}' and trashed=false"
            test_results = self.service.files().list(
                q=test_query,
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            test_items = test_results.get('files', [])
            print(f"Found {len(test_items)} items in folder {parent_folder_id}")
            for item in test_items:
                print(f"  - {item.get('name', 'Unknown')} ({item.get('mimeType', 'Unknown')})")
            
            # 企業名でフォルダとスプレッドシートファイルを検索
            search_query = f"name contains '{query}' and parents in '{parent_folder_id}' and (mimeType='application/vnd.google-apps.folder' or mimeType='application/vnd.google-apps.spreadsheet') and trashed=false"
            
            print(f"Executing search query: {search_query}")
            logger.info(f"Executing search query: {search_query}")
            
            results = self.service.files().list(
                q=search_query,
                fields="files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
                pageSize=50
            ).execute()
            
            items = results.get('files', [])
            logger.info(f"Raw API response: {results}")
            logger.info(f"Found {len(items)} company items (folders/files) matching '{query}'")
            logger.info(f"Search query used: {search_query}")
            logger.info(f"Items found: {[item.get('name', 'Unknown') for item in items]}")
            
            # 各アイテムの詳細をログ出力
            for i, item in enumerate(items):
                logger.info(f"Item {i+1}: {item}")
            
            # フォルダとファイルを区別して処理
            processed_items = []
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # フォルダの場合
                    processed_items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'mimeType': item['mimeType'],
                        'createdTime': item.get('createdTime', ''),
                        'modifiedTime': item.get('modifiedTime', ''),
                        'webViewLink': item.get('webViewLink', ''),
                        'type': 'folder'
                    })
                elif item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                    # スプレッドシートファイルの場合
                    processed_items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'mimeType': item['mimeType'],
                        'createdTime': item.get('createdTime', ''),
                        'modifiedTime': item.get('modifiedTime', ''),
                        'webViewLink': item.get('webViewLink', ''),
                        'type': 'spreadsheet'
                    })
            
            return processed_items
            
        except Exception as e:
            logger.error(f"Error searching company folders: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_company_folder_files(self, folder_id: str) -> list:
        """企業フォルダ内のファイル一覧を取得"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            results = self.service.files().list(
                q=f"parents in '{folder_id}' and trashed=false",
                fields="files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink, webContentLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Error getting company folder files: {str(e)}")
            return []
