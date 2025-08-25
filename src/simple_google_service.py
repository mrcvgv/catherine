"""
シンプルなGoogle APIサービス - サービスアカウント使用
"""

import json
import logging
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class SimpleGoogleService:
    def __init__(self):
        self.credentials = None
        self.gmail_service = None
        self.tasks_service = None
        self.calendar_service = None
        
    def initialize(self):
        """サービスアカウントで初期化"""
        try:
            # 環境変数からサービスアカウント情報を取得
            service_account_info = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
            if not service_account_info:
                logger.warning("GOOGLE_SERVICE_ACCOUNT_KEY not found")
                return False
            
            # JSONをパース
            service_account_dict = json.loads(service_account_info)
            
            # スコープ設定
            scopes = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/tasks',
                'https://www.googleapis.com/auth/calendar'
            ]
            
            # 認証情報作成
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_dict, scopes=scopes
            )
            
            # サービス構築
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            self.tasks_service = build('tasks', 'v1', credentials=self.credentials)
            self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
            
            logger.info("Google services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Google service initialization failed: {e}")
            return False
    
    def get_unread_emails(self):
        """未読メールを取得"""
        try:
            if not self.gmail_service:
                return []
            
            results = self.gmail_service.users().messages().list(
                userId='me', q='is:unread', maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for msg in messages:
                msg_detail = self.gmail_service.users().messages().get(
                    userId='me', id=msg['id']
                ).execute()
                
                headers = msg_detail['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                email_list.append({
                    'subject': subject,
                    'from': sender,
                    'snippet': msg_detail.get('snippet', '')
                })
            
            return email_list
            
        except Exception as e:
            logger.error(f"Failed to get emails: {e}")
            return []
    
    def create_task(self, title, notes=""):
        """タスクを作成"""
        try:
            if not self.tasks_service:
                return False
            
            task = {
                'title': title,
                'notes': notes
            }
            
            result = self.tasks_service.tasks().insert(
                tasklist='@default', body=task
            ).execute()
            
            logger.info(f"Task created: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return False
    
    def get_tasks(self):
        """タスクを取得"""
        try:
            if not self.tasks_service:
                return []
            
            results = self.tasks_service.tasks().list(tasklist='@default').execute()
            tasks = results.get('items', [])
            
            task_list = []
            for task in tasks:
                if task.get('status') != 'completed':
                    task_list.append({
                        'title': task.get('title', 'No Title'),
                        'notes': task.get('notes', ''),
                        'status': task.get('status', 'needsAction')
                    })
            
            return task_list
            
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

# グローバルインスタンス
google_service = SimpleGoogleService()