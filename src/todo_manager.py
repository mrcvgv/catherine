"""
TODO管理システム - AI秘書Catherine用
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pytz
from firebase_config import firebase_manager
from google.cloud.firestore_v1.base_query import FieldFilter
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
                'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC),
                'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC),
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
            query = self.db.collection('todos').where(filter=FieldFilter('user_id', '==', user_id))
            
            if status:
                query = query.where(filter=FieldFilter('status', '==', status))
            elif not include_completed:
                query = query.where(filter=FieldFilter('status', 'in', ['pending', 'in_progress']))
            
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
            updates['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            
            # 完了処理
            if updates.get('status') == 'completed':
                updates['completed_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            
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
    
    async def delete_todos_by_numbers(self, todo_numbers: List[int], user_id: str) -> Dict[str, Any]:
        """番号指定で複数のTODOを削除"""
        try:
            # ユーザーのTODOリストを取得
            todos = await self.get_todos(user_id)
            
            if not todos:
                return {'success': False, 'message': 'TODOリストが空です'}
            
            # 番号を1ベースから0ベースに変換
            deleted_count = 0
            failed_numbers = []
            deleted_titles = []
            
            for number in todo_numbers:
                if 1 <= number <= len(todos):
                    todo_to_delete = todos[number - 1]
                    if await self.delete_todo(todo_to_delete['id'], user_id):
                        deleted_count += 1
                        deleted_titles.append(todo_to_delete.get('title', ''))
                    else:
                        failed_numbers.append(number)
                else:
                    failed_numbers.append(number)
            
            result = {
                'success': deleted_count > 0,
                'deleted_count': deleted_count,
                'deleted_titles': deleted_titles,
                'failed_numbers': failed_numbers
            }
            
            if deleted_count > 0:
                result['message'] = f'{deleted_count}個のTODOを削除しました'
            if failed_numbers:
                result['message'] += f' (番号 {failed_numbers} は削除できませんでした)'
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete multiple TODOs: {e}")
            return {'success': False, 'message': 'TODOの削除に失敗しました'}
    
    async def update_todo_priority_by_number(self, todo_number: int, user_id: str, new_priority: str) -> Dict[str, Any]:
        """番号指定でTODOの優先度を更新"""
        try:
            # ユーザーのTODOリストを取得
            todos = await self.get_todos(user_id)
            
            if not todos:
                return {'success': False, 'message': 'TODOリストが空です'}
            
            # 番号の有効性をチェック（1ベース）
            if not (1 <= todo_number <= len(todos)):
                return {'success': False, 'message': f'番号 {todo_number} は存在しません（1-{len(todos)}の範囲で指定してください）'}
            
            # 更新対象のTODOを取得
            todo_to_update = todos[todo_number - 1]
            old_priority = todo_to_update.get('priority', 'normal')
            
            # 優先度を更新
            success = await self.update_todo(todo_to_update['id'], user_id, priority=new_priority)
            
            priority_names = {
                'urgent': '激高',
                'high': '高',
                'normal': '普通',
                'low': '低'
            }
            
            if success:
                return {
                    'success': True,
                    'message': f'TODO {todo_number} の優先度を{priority_names.get(new_priority, new_priority)}に変更しました',
                    'old_priority': old_priority,
                    'new_priority': new_priority
                }
            else:
                return {'success': False, 'message': 'TODOの優先度更新に失敗しました'}
            
        except Exception as e:
            logger.error(f"Failed to update TODO priority by number: {e}")
            return {'success': False, 'message': 'TODOの優先度更新に失敗しました'}
    
    async def update_todo_by_number(self, todo_number: int, user_id: str, new_title: str) -> Dict[str, Any]:
        """番号指定でTODOのタイトルを更新"""
        try:
            # ユーザーのTODOリストを取得
            todos = await self.get_todos(user_id)
            
            if not todos:
                return {'success': False, 'message': 'TODOリストが空です'}
            
            # 番号の有効性をチェック（1ベース）
            if not (1 <= todo_number <= len(todos)):
                return {'success': False, 'message': f'番号 {todo_number} は存在しません（1-{len(todos)}の範囲で指定してください）'}
            
            # 更新対象のTODOを取得
            todo_to_update = todos[todo_number - 1]
            old_title = todo_to_update.get('title', '')
            
            # タイトルを更新
            success = await self.update_todo(todo_to_update['id'], user_id, title=new_title)
            
            if success:
                return {
                    'success': True,
                    'message': f'TODO {todo_number} の名前を変更しました',
                    'old_title': old_title,
                    'new_title': new_title
                }
            else:
                return {'success': False, 'message': 'TODOの更新に失敗しました'}
            
        except Exception as e:
            logger.error(f"Failed to update TODO by number: {e}")
            return {'success': False, 'message': 'TODOの更新に失敗しました'}
    
    async def set_reminder_by_number(self, todo_number: int, user_id: str, remind_time: datetime, remind_type: str = 'custom', mention_target: str = 'everyone', channel_target: str = 'todo') -> Dict[str, Any]:
        """番号指定でTODOにリマインダーを設定"""
        try:
            # ユーザーのTODOリストを取得
            todos = await self.get_todos(user_id)
            
            if not todos:
                return {'success': False, 'message': 'TODOリストが空です'}
            
            # 番号の有効性をチェック（1ベース）
            if not (1 <= todo_number <= len(todos)):
                return {'success': False, 'message': f'番号 {todo_number} は存在しません（1-{len(todos)}の範囲で指定してください）'}
            
            # 更新対象のTODOを取得
            todo_to_update = todos[todo_number - 1]
            title = todo_to_update.get('title', '')
            
            # リマインダー情報を更新
            success = await self.update_todo(
                todo_to_update['id'], 
                user_id, 
                remind_time=remind_time,
                remind_type=remind_type,
                reminder_enabled=True,
                mention_target=mention_target,
                channel_target=channel_target
            )
            
            if success:
                if remind_type == 'immediate':
                    # 即座にリマインダーを送信
                    return {
                        'success': True,
                        'message': f'TODO {todo_number} 「{title}」のリマインダーを今すぐ送信しました！',
                        'immediate': True,
                        'mention_target': mention_target,
                        'channel_target': channel_target,
                        'todo_title': title
                    }
                else:
                    # JSTで表示
                    time_jst = remind_time.astimezone(pytz.timezone('Asia/Tokyo')) if remind_time else None
                    time_str = time_jst.strftime('%Y-%m-%d %H:%M JST') if time_jst else '指定時間'
                    mention_str = f'@{mention_target}' if mention_target != 'everyone' else '@everyone'
                    channel_str = f'#{channel_target}チャンネル'
                    return {
                        'success': True,
                        'message': f'TODO {todo_number} 「{title}」のリマインダーを{time_str}に{channel_str}で{mention_str}宛に設定しました',
                        'todo_title': title,
                        'remind_time': remind_time,
                        'mention_target': mention_target,
                        'channel_target': channel_target
                    }
            else:
                return {'success': False, 'message': 'リマインダーの設定に失敗しました'}
            
        except Exception as e:
            logger.error(f"Failed to set reminder by number: {e}")
            return {'success': False, 'message': 'リマインダーの設定に失敗しました'}
    
    async def complete_todo(self, todo_id: str, user_id: str) -> bool:
        """TODOを完了にする"""
        return await self.update_todo(todo_id, user_id, status='completed')
    
    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """リマインダーが必要なTODOを取得"""
        try:
            now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            
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
        
        # 優先度アイコン定義（激高、高、普通、低）
        priority_icons = {
            'urgent': '⚫',   # 激高
            'high': '🔴',     # 高
            'normal': '🟡',   # 普通
            'low': '🟢'       # 低い
        }
        
        formatted = "📋 **TODOリスト**\n\n"
        
        for i, todo in enumerate(todos, 1):
            # 優先度アイコンを先頭に、番号とタイトルを表示
            priority = todo.get('priority', 'normal')
            priority_icon = priority_icons.get(priority, '🟡')
            formatted += f"{priority_icon} {i}. {todo['title']}\n"
            
            if todo.get('description'):
                formatted += f"   📝 {todo['description']}\n"
            
            if todo.get('due_date'):
                due_date = todo['due_date']
                if isinstance(due_date, datetime):
                    # JSTで期限を表示
                    due_date_jst = due_date.astimezone(pytz.timezone('Asia/Tokyo'))
                    formatted += f"   📅 期限: {due_date_jst.strftime('%Y-%m-%d %H:%M')}\n"
            
            formatted += "\n"
        
        return formatted

# グローバルインスタンス
todo_manager = TodoManager()