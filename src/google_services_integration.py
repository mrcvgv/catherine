"""
Google Workspace統合システム - OAuth認証を使った実際のAPI統合
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pytz
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httpx

logger = logging.getLogger(__name__)

class GoogleServicesIntegration:
    """Google Workspace サービス統合"""
    
    def __init__(self):
        self.credentials = None
        self.gmail_service = None
        self.tasks_service = None
        self.docs_service = None
        self.sheets_service = None
        self.drive_service = None
        self.calendar_service = None
        
        # OAuth設定
        self.client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        self.refresh_token = os.getenv('GOOGLE_FULL_REFRESH_TOKEN')
        
        self._initialize_credentials()

    def _initialize_credentials(self):
        """OAuth認証情報の初期化"""
        try:
            if not all([self.client_id, self.client_secret, self.refresh_token]):
                logger.warning("Google OAuth credentials not fully configured")
                return
                
            self.credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/tasks',
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/calendar'
                ]
            )
            
            # トークンを更新
            self.credentials.refresh(Request())
            logger.info("Google OAuth credentials initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google credentials: {e}")
            self.credentials = None

    def _get_service(self, service_name: str, version: str):
        """Googleサービスのクライアントを取得"""
        if not self.credentials:
            raise Exception("Google credentials not initialized")
            
        if not self.credentials.valid:
            self.credentials.refresh(Request())
            
        return build(service_name, version, credentials=self.credentials)

    async def check_gmail(self, count_limit: int = 5) -> Dict[str, Any]:
        """Gmail確認"""
        try:
            if not self.gmail_service:
                self.gmail_service = self._get_service('gmail', 'v1')
            
            # 最新のメールを取得
            results = self.gmail_service.users().messages().list(
                userId='me', maxResults=count_limit, q='in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            
            email_list = []
            for message in messages:
                msg_detail = self.gmail_service.users().messages().get(
                    userId='me', id=message['id'], format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_detail['payload']['headers']}
                
                email_list.append({
                    'subject': headers.get('Subject', 'No Subject'),
                    'from': headers.get('From', 'Unknown'),
                    'date': headers.get('Date', 'Unknown'),
                    'snippet': msg_detail.get('snippet', '')[:100] + '...'
                })
            
            return {
                'success': True,
                'count': len(email_list),
                'emails': email_list
            }
            
        except Exception as e:
            logger.error(f"Failed to check Gmail: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Gmailの確認に失敗しました'
            }

    async def search_gmail(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Gmail検索"""
        try:
            if not self.gmail_service:
                self.gmail_service = self._get_service('gmail', 'v1')
            
            results = self.gmail_service.users().messages().list(
                userId='me', maxResults=max_results, q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            search_results = []
            for message in messages[:max_results]:
                msg_detail = self.gmail_service.users().messages().get(
                    userId='me', id=message['id'], format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_detail['payload']['headers']}
                
                search_results.append({
                    'subject': headers.get('Subject', 'No Subject'),
                    'from': headers.get('From', 'Unknown'),
                    'date': headers.get('Date', 'Unknown'),
                    'snippet': msg_detail.get('snippet', '')[:100] + '...'
                })
            
            return {
                'success': True,
                'query': query,
                'count': len(search_results),
                'results': search_results
            }
            
        except Exception as e:
            logger.error(f"Failed to search Gmail: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Gmail検索に失敗しました'
            }

    async def create_google_task(self, title: str, notes: str = "", due_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Googleタスク作成"""
        try:
            if not self.tasks_service:
                self.tasks_service = self._get_service('tasks', 'v1')
            
            # タスクリストを取得（デフォルトリスト）
            tasklists = self.tasks_service.tasklists().list().execute()
            tasklist_id = tasklists['items'][0]['id']
            
            # タスク作成
            task = {
                'title': title,
                'notes': notes
            }
            
            if due_date:
                # RFC 3339形式に変換
                task['due'] = due_date.isoformat()
            
            result = self.tasks_service.tasks().insert(
                tasklist=tasklist_id,
                body=task
            ).execute()
            
            return {
                'success': True,
                'task_id': result['id'],
                'title': result['title'],
                'message': f'Googleタスク「{title}」を作成しました'
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google task: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Googleタスクの作成に失敗しました'
            }

    async def list_google_tasks(self) -> Dict[str, Any]:
        """Googleタスク一覧"""
        try:
            if not self.tasks_service:
                self.tasks_service = self._get_service('tasks', 'v1')
            
            # タスクリストを取得
            tasklists = self.tasks_service.tasklists().list().execute()
            tasklist_id = tasklists['items'][0]['id']
            
            # タスクを取得
            results = self.tasks_service.tasks().list(
                tasklist=tasklist_id,
                showCompleted=False
            ).execute()
            
            tasks = results.get('items', [])
            
            task_list = []
            for task in tasks:
                task_info = {
                    'id': task['id'],
                    'title': task['title'],
                    'notes': task.get('notes', ''),
                    'status': task['status']
                }
                
                if 'due' in task:
                    task_info['due'] = task['due']
                
                task_list.append(task_info)
            
            return {
                'success': True,
                'count': len(task_list),
                'tasks': task_list
            }
            
        except Exception as e:
            logger.error(f"Failed to list Google tasks: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Googleタスクの取得に失敗しました'
            }

    async def create_google_doc(self, title: str, content: str = "") -> Dict[str, Any]:
        """Googleドキュメント作成"""
        try:
            if not self.docs_service:
                self.docs_service = self._get_service('docs', 'v1')
            
            # ドキュメント作成
            document = {
                'title': title
            }
            
            result = self.docs_service.documents().create(body=document).execute()
            document_id = result['documentId']
            
            # コンテンツを追加
            if content:
                requests = [{
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }]
                
                self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            
            # ドキュメントのURLを生成
            doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
            
            return {
                'success': True,
                'document_id': document_id,
                'title': title,
                'url': doc_url,
                'message': f'Googleドキュメント「{title}」を作成しました'
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google doc: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Googleドキュメントの作成に失敗しました'
            }

    async def create_google_sheet(self, title: str, data: Optional[List[List[Any]]] = None) -> Dict[str, Any]:
        """Googleスプレッドシート作成"""
        try:
            if not self.sheets_service:
                self.sheets_service = self._get_service('sheets', 'v4')
            
            # スプレッドシート作成
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result['spreadsheetId']
            
            # データを追加
            if data:
                body = {
                    'values': data
                }
                
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='A1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
            
            # スプレッドシートのURLを生成
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            
            return {
                'success': True,
                'spreadsheet_id': spreadsheet_id,
                'title': title,
                'url': sheet_url,
                'message': f'Googleスプレッドシート「{title}」を作成しました'
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google sheet: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Googleスプレッドシートの作成に失敗しました'
            }

    async def create_calendar_event(self, title: str, start_time: datetime, end_time: Optional[datetime] = None, 
                                   description: str = "") -> Dict[str, Any]:
        """Googleカレンダーイベント作成"""
        try:
            if not self.calendar_service:
                self.calendar_service = self._get_service('calendar', 'v3')
            
            if not end_time:
                end_time = start_time + timedelta(hours=1)  # デフォルト1時間
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
            }
            
            result = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': result['id'],
                'title': title,
                'start_time': start_time.isoformat(),
                'url': result.get('htmlLink', ''),
                'message': f'カレンダーイベント「{title}」を作成しました'
            }
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'カレンダーイベントの作成に失敗しました'
            }

# グローバルインスタンス
google_services = GoogleServicesIntegration()