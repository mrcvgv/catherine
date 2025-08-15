"""
TODO管理システム - AI秘書Catherine用
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pytz
from firebase_config import firebase_manager
import logging

logger = logging.getLogger(__name__)

class TodoManager:
    """TODO管理クラス"""
    
    def __init__(self):
        self.db = firebase_manager.get_db()
        if not self.db:
            logger.error("Firebase not available for TodoManager")
    
    async def create_todo(self, user_id: str, title: str, description: str = "", 
                         due_date: Optional[datetime] = None, priority: str = "normal") -> Dict[str, Any]:
        """TODOを作成"""
        try:
            todo_data = {
                'user_id': user_id,
                'title': title,
                'description': description,
                'created_at': datetime.now(pytz.UTC),
                'updated_at': datetime.now(pytz.UTC),
                'due_date': due_date,
                'priority': priority,  # low, normal, high, urgent
                'status': 'pending',  # pending, in_progress, completed, cancelled
                'completed_at': None,
                'reminder_sent': False,
                'tags': []
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('todos').add(todo_data)
            todo_id = doc_ref[1].id
            
            logger.info(f"Created TODO {todo_id} for user {user_id}: {title}")
            return {'id': todo_id, **todo_data}
            
        except Exception as e:
            logger.error(f"Failed to create TODO: {e}")
            raise
    
    async def get_todos(self, user_id: str, status: Optional[str] = None, 
                        include_completed: bool = False) -> List[Dict[str, Any]]:
        """ユーザーのTODOリストを取得"""
        try:
            query = self.db.collection('todos').where('user_id', '==', user_id)
            
            if status:
                query = query.where('status', '==', status)
            elif not include_completed:
                query = query.where('status', 'in', ['pending', 'in_progress'])
            
            # 優先度と期限でソート（インデックス作成後に有効化）
            # query = query.order_by('priority', direction='DESCENDING')
            # query = query.order_by('due_date')
            
            todos = []
            for doc in query.stream():
                todo_data = doc.to_dict()
                todo_data['id'] = doc.id
                todos.append(todo_data)
            
            return todos
            
        except Exception as e:
            logger.error(f"Failed to get TODOs: {e}")
            return []
    
    async def update_todo(self, todo_id: str, user_id: str, **updates) -> bool:
        """TODOを更新"""
        try:
            doc_ref = self.db.collection('todos').document(todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"TODO {todo_id} not found")
                return False
            
            # 所有者チェック
            if doc.to_dict().get('user_id') != user_id:
                logger.warning(f"User {user_id} not authorized to update TODO {todo_id}")
                return False
            
            # 更新日時を追加
            updates['updated_at'] = datetime.now(pytz.UTC)
            
            # 完了処理
            if updates.get('status') == 'completed':
                updates['completed_at'] = datetime.now(pytz.UTC)
            
            doc_ref.update(updates)
            logger.info(f"Updated TODO {todo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update TODO: {e}")
            return False
    
    async def delete_todo(self, todo_id: str, user_id: str) -> bool:
        """TODOを削除"""
        try:
            doc_ref = self.db.collection('todos').document(todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            # 所有者チェック
            if doc.to_dict().get('user_id') != user_id:
                logger.warning(f"User {user_id} not authorized to delete TODO {todo_id}")
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted TODO {todo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete TODO: {e}")
            return False
    
    async def complete_todo(self, todo_id: str, user_id: str) -> bool:
        """TODOを完了にする"""
        return await self.update_todo(todo_id, user_id, status='completed')
    
    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """リマインダーが必要なTODOを取得"""
        try:
            now = datetime.now(pytz.UTC)
            
            # 期限が近づいているTODOを取得
            query = (self.db.collection('todos')
                    .where('status', 'in', ['pending', 'in_progress'])
                    .where('reminder_sent', '==', False)
                    .where('due_date', '!=', None)
                    .where('due_date', '<=', now + timedelta(hours=24)))
            
            todos = []
            for doc in query.stream():
                todo_data = doc.to_dict()
                todo_data['id'] = doc.id
                todos.append(todo_data)
            
            return todos
            
        except Exception as e:
            logger.error(f"Failed to get pending reminders: {e}")
            return []
    
    async def mark_reminder_sent(self, todo_id: str) -> bool:
        """リマインダー送信済みにマーク"""
        try:
            doc_ref = self.db.collection('todos').document(todo_id)
            doc_ref.update({'reminder_sent': True})
            return True
        except Exception as e:
            logger.error(f"Failed to mark reminder sent: {e}")
            return False
    
    async def search_todos(self, user_id: str, query_text: str) -> List[Dict[str, Any]]:
        """TODOを検索"""
        try:
            # 全てのTODOを取得して検索（Firestoreのテキスト検索は制限があるため）
            all_todos = await self.get_todos(user_id, include_completed=True)
            
            query_lower = query_text.lower()
            matched_todos = []
            
            for todo in all_todos:
                title_match = query_lower in todo.get('title', '').lower()
                desc_match = query_lower in todo.get('description', '').lower()
                tag_match = any(query_lower in tag.lower() for tag in todo.get('tags', []))
                
                if title_match or desc_match or tag_match:
                    matched_todos.append(todo)
            
            return matched_todos
            
        except Exception as e:
            logger.error(f"Failed to search TODOs: {e}")
            return []
    
    def format_todo_list(self, todos: List[Dict[str, Any]]) -> str:
        """TODOリストを読みやすい形式にフォーマット"""
        if not todos:
            return "📝 TODOリストは空です。"
        
        priority_icons = {
            'urgent': '🔴',
            'high': '🟠',
            'normal': '🟡',
            'low': '🟢'
        }
        
        status_icons = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        formatted = "📋 **TODOリスト**\n\n"
        
        for i, todo in enumerate(todos, 1):
            priority = todo.get('priority', 'normal')
            status = todo.get('status', 'pending')
            
            formatted += f"{i}. {priority_icons.get(priority, '')} {status_icons.get(status, '')} **{todo['title']}**\n"
            
            if todo.get('description'):
                formatted += f"   📝 {todo['description']}\n"
            
            if todo.get('due_date'):
                due_date = todo['due_date']
                if isinstance(due_date, datetime):
                    formatted += f"   📅 期限: {due_date.strftime('%Y-%m-%d %H:%M')}\n"
            
            formatted += "\n"
        
        return formatted

# グローバルインスタンス
todo_manager = TodoManager()