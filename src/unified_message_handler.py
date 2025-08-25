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
            # Import with fallback handling
            try:
                from src.advanced_nlu_system import advanced_nlu
                self.advanced_nlu = advanced_nlu
                logger.info("Advanced NLU system loaded successfully")
            except Exception as e:
                logger.warning(f"Advanced NLU system not available: {e}")
                self.advanced_nlu = None
            
            try:
                from src.google_services_integration import google_services
                self.google_services = google_services
                logger.info("Google services integration loaded successfully")
            except Exception as e:
                logger.warning(f"Google services integration not available: {e}")
                self.google_services = None
            
            try:
                from src.todo_manager import todo_manager
                self.todo_manager = todo_manager
                logger.info("TODO manager loaded successfully")
            except Exception as e:
                logger.warning(f"TODO manager not available: {e}")
                self.todo_manager = None
            
            # Notion統合（オプション）
            try:
                from src.notion_integration import notion_integration
                self.notion_integration = notion_integration
                logger.info("Notion integration loaded successfully")
            except ImportError:
                logger.info("Notion integration not available")
                self.notion_integration = None
                
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
            if self.advanced_nlu:
                intent_result = await self.advanced_nlu.understand_intent(content, user_context)
                logger.info(f"Intent analysis: action={intent_result.get('action')}, confidence={intent_result.get('confidence')}")
            else:
                # Fallback: Simple keyword-based intent recognition
                intent_result = await self._simple_intent_understanding(content)
                logger.info(f"Simple intent analysis: action={intent_result.get('action')}")
            
            action = intent_result.get('action')
            parameters = intent_result.get('parameters', {})
            confidence = intent_result.get('confidence', 0)
            
            # アクション実行（エラー回復システムと統合）
            execution_result = await self._execute_action_with_recovery(action, parameters, str(user.id))
            
            # 返答生成
            if self.advanced_nlu:
                if execution_result:
                    response = await self.advanced_nlu.generate_response(intent_result, execution_result)
                else:
                    response = await self.advanced_nlu.generate_response(intent_result)
            else:
                # Fallback response generation
                response = await self._simple_response_generation(intent_result, execution_result)
            
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
        """TODO作成 - 統合TODOマネージャーを使用（スマートルーティング）"""
        try:
            from src.unified_todo_manager import unified_todo_manager
            
            title = parameters.get('title', 'New TODO')
            priority = parameters.get('priority', 'normal')
            due_date = parameters.get('due_date')
            description = parameters.get('description', '')
            
            result = await unified_todo_manager.create_todo(
                title=title,
                user_id=user_id,
                priority=priority,
                due_date=due_date,
                description=description
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Unified TODO manager failed: {e}")
            return {'success': False, 'error': f'TODO作成に失敗しました: {str(e)}'}

    async def _handle_todo_list(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO一覧 - 統合TODOマネージャーを使用（全サービス統合表示）"""
        try:
            from src.unified_todo_manager import unified_todo_manager
            
            include_completed = parameters.get('include_completed', False)
            
            result = await unified_todo_manager.list_todos(
                user_id=user_id,
                include_completed=include_completed
            )
            
            if result.get('success') and result.get('todos'):
                formatted_list = unified_todo_manager.format_todo_list(result['todos'])
                result['formatted_list'] = formatted_list
                
            return result
            
        except Exception as e:
            logger.error(f"Unified TODO manager failed: {e}")
            return {'success': False, 'error': f'TODO一覧取得に失敗しました: {str(e)}'}

    async def _handle_todo_complete(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO完了 - 統合TODOマネージャーを使用"""
        try:
            from src.unified_todo_manager import unified_todo_manager
            
            todo_number = parameters.get('todo_number')
            
            if todo_number:
                return await unified_todo_manager.complete_todo_by_number(todo_number, user_id)
            else:
                return {'success': False, 'error': 'TODO番号が必要です'}
                
        except Exception as e:
            logger.error(f"Unified TODO manager failed: {e}")
            return {'success': False, 'error': f'TODO完了に失敗しました: {str(e)}'}

    async def _handle_todo_delete(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO削除 - 安全のため無効化（完了機能を使用）"""
        return {
            'success': False, 
            'error': 'TODO削除は安全のため無効化されています。代わりに「完了」機能を使用してください。'
        }

    async def _handle_todo_update(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO更新 - 複雑すぎるため無効化（削除&作成を推奨）"""
        return {
            'success': False,
            'error': 'TODO更新は複雑すぎるため無効化されています。完了して新しく作成してください。'
        }

    async def _handle_todo_priority(self, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """TODO優先度変更 - 複雑すぎるため無効化"""
        return {
            'success': False,
            'error': 'TODO優先度変更は複雑すぎるため無効化されています。作成時に適切な優先度を設定してください。'
        }

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

    async def _simple_intent_understanding(self, content: str) -> Dict[str, Any]:
        """簡単なキーワードベースの意図理解（フォールバック）"""
        content_lower = content.lower()
        
        # TODOリスト関連
        if any(word in content_lower for word in ['リスト', 'list', '一覧', '全部', '全リスト']):
            return {
                "action": "list",
                "confidence": 0.7,
                "parameters": {"include_completed": False},
                "reasoning": "キーワードベース: リスト表示"
            }
        
        # TODO作成関連
        elif any(word in content_lower for word in ['追加', 'add', '作成', 'create', 'を', 'やる', 'する']):
            return {
                "action": "create",
                "confidence": 0.6,
                "parameters": {"title": content, "priority": "normal"},
                "reasoning": "キーワードベース: TODO作成"
            }
        
        # TODO完了関連  
        elif any(word in content_lower for word in ['完了', 'done', '終了', 'complete', '済み']):
            # 番号を抽出
            import re
            numbers = re.findall(r'\d+', content)
            if numbers:
                return {
                    "action": "complete",
                    "confidence": 0.7,
                    "parameters": {"todo_number": int(numbers[0])},
                    "reasoning": "キーワードベース: TODO完了"
                }
        
        # TODO削除関連
        elif any(word in content_lower for word in ['削除', 'delete', '消す', '消去']):
            import re
            numbers = re.findall(r'\d+', content)
            if numbers:
                return {
                    "action": "delete", 
                    "confidence": 0.7,
                    "parameters": {"todo_number": int(numbers[0])},
                    "reasoning": "キーワードベース: TODO削除"
                }
        
        # デフォルト: 会話として処理
        return {
            "action": "chat",
            "confidence": 0.5,
            "parameters": {"message": content},
            "reasoning": "キーワードベース: 一般会話"
        }
    
    async def _simple_response_generation(self, intent_result: Dict, execution_result: Optional[Dict] = None) -> str:
        """簡単な返答生成（フォールバック）"""
        action = intent_result.get('action')
        
        # 魔女風の返答パターン
        witch_responses = {
            'create_success': [
                "ふふ、新しいTODOを追加したよ",
                "あらあら、また一つ増えちゃったね", 
                "やれやれ、追加完了だよ",
                "まったく、忙しくなるねぇ"
            ],
            'list_success': [
                "ふふ、TODOリストを見せてあげるよ",
                "あらあら、やることがいろいろあるねぇ",
                "やれやれ、リストはこんな感じだよ"
            ],
            'complete_success': [
                "ふふ、お疲れさま。一つ片付いたね",
                "あらあら、よくできました",
                "やれやれ、完了したよ"
            ],
            'delete_success': [
                "ふふ、削除したよ",
                "あらあら、消しちゃったね",
                "やれやれ、なくなったよ"
            ],
            'error': [
                "あらあら、うまくいかなかったねぇ",
                "やれやれ、困ったことになったよ", 
                "ごめんなさい、何かおかしいようだね"
            ],
            'chat': [
                "ふふ、そうですねぇ",
                "あらあら、なるほどねぇ",
                "やれやれ、そういうことかい"
            ]
        }
        
        import random
        
        if execution_result and execution_result.get('success'):
            response_key = f"{action}_success"
            base_response = random.choice(witch_responses.get(response_key, witch_responses['chat']))
            
            # 結果に応じて詳細を追加
            if action == 'list' and execution_result.get('formatted_list'):
                return base_response + "\n\n" + execution_result['formatted_list']
            elif execution_result.get('message'):
                return base_response + "\n" + execution_result['message']
            else:
                return base_response
        
        elif execution_result and not execution_result.get('success'):
            base_response = random.choice(witch_responses['error'])
            error_msg = execution_result.get('error', '不明なエラー')
            return f"{base_response}\n{error_msg}"
        
        else:
            return random.choice(witch_responses['chat'])

# グローバルインスタンス
unified_handler = UnifiedMessageHandler()