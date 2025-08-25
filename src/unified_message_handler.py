"""
統合メッセージハンドラー - 高度NLUとGoogle統合を組み合わせたシステム
"""
import logging
from typing import Dict, Any, Optional
import discord
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class UnifiedMessageHandler:
    """統合メッセージ処理システム"""
    
    def __init__(self):
        self.advanced_nlu = None
        self.google_services = None
        self.todo_manager = None
        self.notion_integration = None
        self.initialized = False

    async def initialize(self):
        """システムの初期化"""
        try:
            from src.advanced_nlu_system import advanced_nlu
            from src.google_services_integration import google_services
            from src.todo_manager import todo_manager
            
            self.advanced_nlu = advanced_nlu
            self.google_services = google_services
            self.todo_manager = todo_manager
            
            # Notion統合（オプション）
            try:
                from src.notion_integration import notion_integration
                self.notion_integration = notion_integration
            except ImportError:
                logger.info("Notion integration not available")
                
            self.initialized = True
            logger.info("Unified message handler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize unified message handler: {e}")
            self.initialized = False

    async def handle_message(self, message: discord.Message) -> str:
        """メッセージを処理して返答を生成"""
        if not self.initialized:
            await self.initialize()
            
        user = message.author
        content = message.content
        
        try:
            # ユーザーコンテキストの構築
            user_context = {
                "user_id": str(user.id),
                "username": user.name,
                "channel": message.channel.name if hasattr(message.channel, 'name') else 'DM',
                "timestamp": datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            }
            
            # 意図理解
            intent_result = await self.advanced_nlu.understand_intent(content, user_context)
            
            logger.info(f"Intent analysis: action={intent_result.get('action')}, confidence={intent_result.get('confidence')}")
            
            action = intent_result.get('action')
            parameters = intent_result.get('parameters', {})
            confidence = intent_result.get('confidence', 0)
            
            # アクション実行（エラー回復システムと統合）
            execution_result = await self._execute_action_with_recovery(action, parameters, str(user.id))
            
            # 返答生成
            if execution_result:
                response = await self.advanced_nlu.generate_response(intent_result, execution_result)
            else:
                response = await self.advanced_nlu.generate_response(intent_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # エラー回復システムを使用
            from src.error_recovery_system import error_recovery
            recovery_result = await error_recovery.handle_error(e, {
                'user_id': str(user.id),
                'message': content,
                'action': 'message_handling'
            })
            
            if recovery_result.get('recovered'):
                return recovery_result.get('message', "あらあら、何かうまくいかなかったようだね。")
            else:
                return "ごめんなさい、完全に困っちゃった。しばらく待ってからもう一度試してくれる？"

    async def _execute_action_with_recovery(self, action: str, parameters: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """エラー回復システムを統合したアクション実行"""
        try:
            # まず通常の実行を試行
            return await self._execute_action(action, parameters, user_id)
            
        except Exception as e:
            logger.error(f"Action execution failed: {action}, error: {e}")
            
            # エラー回復システムを使用
            from src.error_recovery_system import error_recovery
            
            # 再試行可能な関数を定義
            async def retry_function():
                return await self._execute_action(action, parameters, user_id)
            
            # エラー回復を実行
            recovery_result = await error_recovery.handle_error(e, {
                'user_id': user_id,
                'action': action,
                'parameters': parameters,
                'retry_function': retry_function
            })
            
            # 回復結果を適切な形式で返す
            if recovery_result.get('success'):
                return recovery_result.get('data')
            elif recovery_result.get('recovered'):
                # フォールバックデータを返す
                return {
                    'success': False,
                    'recovered': True,
                    'message': recovery_result.get('message'),
                    'fallback_data': recovery_result.get('fallback_data')
                }
            else:
                # 完全な失敗
                return {
                    'success': False,
                    'recovered': False,
                    'error': recovery_result.get('message', 'Unknown error')
                }

    async def _execute_action(self, action: str, parameters: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """アクションを実行"""
        try:
            # TODO関連アクション
            if action == 'create':
                return await self._handle_todo_create(parameters, user_id)
            elif action == 'list':
                return await self._handle_todo_list(parameters, user_id)
            elif action == 'complete':
                return await self._handle_todo_complete(parameters, user_id)
            elif action == 'delete':
                return await self._handle_todo_delete(parameters, user_id)
            elif action == 'update':
                return await self._handle_todo_update(parameters, user_id)
            elif action == 'priority':
                return await self._handle_todo_priority(parameters, user_id)
            elif action == 'remind':
                return await self._handle_todo_remind(parameters, user_id)
                
            # Google Workspace関連アクション
            elif action == 'gmail_check':
                return await self._handle_gmail_check(parameters)
            elif action == 'gmail_search':
                return await self._handle_gmail_search(parameters)
            elif action == 'tasks_create':
                return await self._handle_google_tasks_create(parameters)
            elif action == 'tasks_list':
                return await self._handle_google_tasks_list(parameters)
            elif action == 'docs_create':
                return await self._handle_google_docs_create(parameters)
            elif action == 'sheets_create':
                return await self._handle_google_sheets_create(parameters)
            elif action == 'calendar_create_event':
                return await self._handle_calendar_create_event(parameters)
                
            # 通常の会話
            elif action == 'chat':
                return {'success': True, 'type': 'chat', 'message': parameters.get('message', '')}
            
            else:
                logger.warning(f"Unknown action: {action}")
                return {'success': False, 'error': f'Unknown action: {action}'}
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {'success': False, 'error': str(e)}

    # TODO関連メソッド
    async def _handle_todo_create(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO作成"""
        title = parameters.get('title', 'New TODO')
        priority = parameters.get('priority', 'normal')
        due_date = parameters.get('due_date')
        
        result = await self.todo_manager.create_todo(
            user_id=user_id,
            title=title,
            priority=priority,
            due_date=due_date
        )
        
        return result

    async def _handle_todo_list(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO一覧"""
        include_completed = parameters.get('include_completed', False)
        
        todos = await self.todo_manager.get_todos(
            user_id=user_id,
            include_completed=include_completed
        )
        
        if todos:
            formatted_list = self.todo_manager.format_todo_list(todos)
            return {
                'success': True,
                'count': len(todos),
                'formatted_list': formatted_list,
                'todos': todos
            }
        else:
            return {
                'success': True,
                'count': 0,
                'message': 'TODOはありません'
            }

    async def _handle_todo_complete(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO完了"""
        todo_number = parameters.get('todo_number')
        title_keywords = parameters.get('title_keywords')
        
        if todo_number:
            return await self.todo_manager.complete_todo_by_number(todo_number, user_id)
        elif title_keywords:
            return await self.todo_manager.complete_todo_by_title(title_keywords, user_id)
        else:
            return {'success': False, 'error': 'TODO番号またはタイトルが必要です'}

    async def _handle_todo_delete(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO削除"""
        todo_numbers = parameters.get('todo_numbers', [])
        todo_number = parameters.get('todo_number')
        
        if todo_number:
            todo_numbers = [todo_number]
        
        if todo_numbers:
            return await self.todo_manager.delete_todos_by_numbers(todo_numbers, user_id)
        else:
            return {'success': False, 'error': 'TODO番号が必要です'}

    async def _handle_todo_update(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO更新"""
        todo_number = parameters.get('todo_number')
        new_content = parameters.get('new_content')
        
        if todo_number and new_content:
            return await self.todo_manager.update_todo_by_number(todo_number, user_id, new_content)
        else:
            return {'success': False, 'error': 'TODO番号と新しい内容が必要です'}

    async def _handle_todo_priority(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO優先度変更"""
        todo_number = parameters.get('todo_number')
        new_priority = parameters.get('new_priority')
        
        if todo_number and new_priority:
            return await self.todo_manager.change_todo_priority(todo_number, user_id, new_priority)
        else:
            return {'success': False, 'error': 'TODO番号と新しい優先度が必要です'}

    async def _handle_todo_remind(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """リマインダー設定"""
        # 既存のリマインダーシステムを使用
        try:
            from src.reminder_system import reminder_system
            
            todo_number = parameters.get('todo_number')
            remind_time = parameters.get('remind_time')
            custom_message = parameters.get('custom_message')
            
            if remind_time:
                await reminder_system.schedule_reminder(
                    user_id=user_id,
                    todo_number=todo_number,
                    remind_time=remind_time,
                    custom_message=custom_message
                )
                return {'success': True, 'message': 'リマインダーを設定しました'}
            else:
                return {'success': False, 'error': '時間指定が必要です'}
                
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return {'success': False, 'error': str(e)}

    # Google Workspace関連メソッド
    async def _handle_gmail_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Gmail確認"""
        count_limit = parameters.get('count_limit', 5)
        return await self.google_services.check_gmail(count_limit)

    async def _handle_gmail_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Gmail検索"""
        query = parameters.get('query', '')
        max_results = parameters.get('max_results', 10)
        return await self.google_services.search_gmail(query, max_results)

    async def _handle_google_tasks_create(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Googleタスク作成"""
        title = parameters.get('title', 'New Task')
        notes = parameters.get('notes', '')
        due_date = parameters.get('due_date')
        return await self.google_services.create_google_task(title, notes, due_date)

    async def _handle_google_tasks_list(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Googleタスク一覧"""
        return await self.google_services.list_google_tasks()

    async def _handle_google_docs_create(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Googleドキュメント作成"""
        title = parameters.get('title', 'New Document')
        content = parameters.get('content', '')
        return await self.google_services.create_google_doc(title, content)

    async def _handle_google_sheets_create(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Googleスプレッドシート作成"""
        title = parameters.get('title', 'New Spreadsheet')
        data = parameters.get('data', None)
        return await self.google_services.create_google_sheet(title, data)

    async def _handle_calendar_create_event(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """カレンダーイベント作成"""
        title = parameters.get('title', 'New Event')
        start_time = parameters.get('start_time')
        end_time = parameters.get('end_time')
        description = parameters.get('description', '')
        
        if start_time:
            return await self.google_services.create_calendar_event(title, start_time, end_time, description)
        else:
            return {'success': False, 'error': '開始時間が必要です'}

# グローバルインスタンス
unified_handler = UnifiedMessageHandler()