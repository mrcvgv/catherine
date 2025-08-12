#!/usr/bin/env python3
"""
Error Handler - Catherine AI 統合エラーハンドリングシステム
全システムでの例外処理、ロギング、フォールバック機能
"""

import logging
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
from dataclasses import dataclass
import pytz

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    function_name: Optional[str] = None
    traceback_info: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False

class CatherineErrorHandler:
    """Catherine AI 統合エラーハンドラー"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.error_count = 0
        self.recent_errors = []
        self.recovery_strategies = {
            'firebase_connection': self._recover_firebase,
            'openai_api': self._recover_openai,
            'discord_api': self._recover_discord,
            'intent_detection': self._recover_intent_detection,
            'reminder_system': self._recover_reminder_system
        }
        
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger('catherine_ai')
        logger.setLevel(logging.INFO)
        
        # ハンドラーが既に存在する場合は追加しない
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def with_error_handling(self, 
                          error_type: str = 'general',
                          user_message: str = "処理中にエラーが発生しました",
                          recovery_strategy: Optional[str] = None,
                          fallback_response: Any = None):
        """デコレータ：エラーハンドリング付き関数実行"""
        
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    return await self._handle_error(
                        error=e,
                        error_type=error_type,
                        function_name=func.__name__,
                        user_message=user_message,
                        recovery_strategy=recovery_strategy,
                        fallback_response=fallback_response,
                        args=args,
                        kwargs=kwargs
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 同期関数の場合は簡易処理
                    self._log_error(e, func.__name__, error_type)
                    return fallback_response
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    async def _handle_error(self, 
                          error: Exception,
                          error_type: str,
                          function_name: str,
                          user_message: str,
                          recovery_strategy: Optional[str],
                          fallback_response: Any,
                          args: tuple,
                          kwargs: dict) -> Any:
        """エラー処理メイン"""
        
        # エラーコンテキスト作成
        error_context = ErrorContext(
            error_id=f"{error_type}_{datetime.now(JST).strftime('%Y%m%d_%H%M%S')}_{self.error_count}",
            timestamp=datetime.now(JST),
            error_type=error_type,
            error_message=str(error),
            function_name=function_name,
            traceback_info=traceback.format_exc()
        )
        
        # ユーザー情報抽出（可能な場合）
        try:
            if args and hasattr(args[0], 'author'):  # Discord message object
                error_context.user_id = str(args[0].author.id)
                error_context.channel_id = str(args[0].channel.id)
            elif 'user_id' in kwargs:
                error_context.user_id = kwargs['user_id']
                error_context.channel_id = kwargs.get('channel_id')
        except:
            pass
        
        # ログ記録
        self._log_error_context(error_context)
        
        # 復旧試行
        recovery_result = None
        if recovery_strategy and recovery_strategy in self.recovery_strategies:
            try:
                recovery_result = await self.recovery_strategies[recovery_strategy](
                    error_context, args, kwargs
                )
                error_context.recovery_attempted = True
                error_context.recovery_successful = recovery_result is not None
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for {recovery_strategy}: {recovery_error}")
        
        # 復旧成功時は結果を返す
        if recovery_result is not None:
            return recovery_result
        
        # フォールバック応答
        if error_type == 'discord_command':
            return await self._create_error_response(error_context, user_message)
        
        return fallback_response
    
    def _log_error_context(self, context: ErrorContext):
        """エラーコンテキストログ記録"""
        self.error_count += 1
        self.recent_errors.append(context)
        
        # 最新50件のみ保持
        if len(self.recent_errors) > 50:
            self.recent_errors = self.recent_errors[-50:]
        
        log_message = f"""
Error ID: {context.error_id}
Type: {context.error_type}
Function: {context.function_name}
Message: {context.error_message}
User: {context.user_id or 'Unknown'}
Channel: {context.channel_id or 'Unknown'}
Recovery: {'Attempted' if context.recovery_attempted else 'Not attempted'}
Success: {'Yes' if context.recovery_successful else 'No'}
"""
        
        self.logger.error(log_message.strip())
        
        if context.traceback_info:
            self.logger.debug(f"Traceback for {context.error_id}:\n{context.traceback_info}")
    
    def _log_error(self, error: Exception, function_name: str, error_type: str):
        """簡易エラーログ"""
        self.logger.error(f"{error_type} in {function_name}: {error}")
    
    async def _create_error_response(self, context: ErrorContext, user_message: str) -> Dict[str, Any]:
        """ユーザー向けエラーレスポンス作成"""
        
        # エラータイプ別のカスタムメッセージ
        custom_messages = {
            'firebase_connection': 'データベース接続エラーです。しばらく待ってから再試行してください。',
            'openai_api': 'AI処理でエラーが発生しました。別の表現で試してみてください。',
            'intent_detection': '理解できませんでした。より具体的に教えてください。',
            'reminder_system': 'リマインド設定でエラーが発生しました。時刻と内容を確認してください。',
            'todo_operation': 'TODO操作でエラーが発生しました。番号を確認してください。'
        }
        
        final_message = custom_messages.get(context.error_type, user_message)
        
        return {
            'success': False,
            'error': True,
            'message': final_message,
            'error_id': context.error_id,
            'timestamp': context.timestamp.isoformat(),
            'suggestions': self._get_error_suggestions(context.error_type)
        }
    
    def _get_error_suggestions(self, error_type: str) -> list:
        """エラータイプ別の提案"""
        suggestions = {
            'firebase_connection': [
                '少し時間をおいてから再試行してください',
                '他のコマンドを試してみてください'
            ],
            'openai_api': [
                'より簡潔な表現で試してください',
                '具体的な内容を教えてください'
            ],
            'intent_detection': [
                '「リスト」「追加」「削除」など明確な動詞を使ってください',
                '例：「タスク追加：会議の準備」'
            ],
            'reminder_system': [
                '時刻形式を確認してください（例：15:30）',
                'リマインド内容を明確にしてください'
            ],
            'todo_operation': [
                'TODOの番号を確認してください',
                'まず「リスト」でTODOを確認してください'
            ]
        }
        
        return suggestions.get(error_type, ['しばらく待ってから再試行してください'])
    
    # 復旧戦略実装
    async def _recover_firebase(self, context: ErrorContext, args: tuple, kwargs: dict) -> Optional[Any]:
        """Firebase接続復旧"""
        try:
            from firebase_config import firebase_manager
            firebase_manager.initialize_firebase()
            if firebase_manager.is_available():
                self.logger.info(f"Firebase recovery successful for {context.error_id}")
                return {'success': True, 'recovered': True}
        except Exception as e:
            self.logger.error(f"Firebase recovery failed: {e}")
        return None
    
    async def _recover_openai(self, context: ErrorContext, args: tuple, kwargs: dict) -> Optional[Any]:
        """OpenAI API復旧"""
        try:
            import time
            time.sleep(1)  # Rate limit対応
            return {'success': False, 'message': 'AI処理を再試行してください', 'retry_suggested': True}
        except Exception:
            return None
    
    async def _recover_discord(self, context: ErrorContext, args: tuple, kwargs: dict) -> Optional[Any]:
        """Discord API復旧"""
        try:
            return {'success': False, 'message': 'Discord接続エラーです。管理者に連絡してください'}
        except Exception:
            return None
    
    async def _recover_intent_detection(self, context: ErrorContext, args: tuple, kwargs: dict) -> Optional[Any]:
        """意図検出復旧"""
        return {
            'success': False,
            'message': '理解できませんでした。以下から選んでください：\n① TODO追加 ② TODO削除 ③ TODO完了 ④ TODO一覧 ⑤ リマインド設定',
            'fallback_options': ['todo.add', 'todo.delete', 'todo.complete', 'todo.list', 'remind.create']
        }
    
    async def _recover_reminder_system(self, context: ErrorContext, args: tuple, kwargs: dict) -> Optional[Any]:
        """リマインドシステム復旧"""
        return {
            'success': False,
            'message': 'リマインド設定でエラーが発生しました。\n形式：「内容を時刻にリマインド」（例：会議を15:30にリマインド）',
            'example': '会議の準備を明日10:00にリマインド'
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計取得"""
        if not self.recent_errors:
            return {'total_errors': 0, 'error_types': {}, 'recovery_rate': 0}
        
        error_types = {}
        recovery_count = 0
        
        for error in self.recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            if error.recovery_successful:
                recovery_count += 1
        
        return {
            'total_errors': len(self.recent_errors),
            'error_types': error_types,
            'recovery_rate': recovery_count / len(self.recent_errors) if self.recent_errors else 0,
            'last_error': self.recent_errors[-1].timestamp.isoformat() if self.recent_errors else None
        }

# グローバルエラーハンドラーインスタンス
error_handler = CatherineErrorHandler()

# デコレータのエイリアス（使いやすくするため）
handle_errors = error_handler.with_error_handling

# 使用例とテスト
if __name__ == "__main__":
    async def test_error_handling():
        """エラーハンドリングテスト"""
        
        @handle_errors(
            error_type='test_error',
            user_message='テストエラーが発生しました',
            fallback_response={'test': 'fallback'}
        )
        async def test_function_with_error():
            raise ValueError("テストエラー")
        
        @handle_errors(error_type='test_success')
        async def test_function_success():
            return {'success': True, 'message': 'テスト成功'}
        
        print("Catherine AI Error Handler Test")
        print("=" * 40)
        
        # エラー発生テスト
        error_result = await test_function_with_error()
        print(f"Error test result: {error_result}")
        
        # 成功テスト
        success_result = await test_function_success()
        print(f"Success test result: {success_result}")
        
        # 統計情報
        stats = error_handler.get_error_statistics()
        print(f"Error statistics: {stats}")
    
    print("Catherine AI Error Handler")
    print("Features:")
    print("  - Decorator-based error handling")
    print("  - Automatic recovery strategies")
    print("  - User-friendly error messages")
    print("  - Error logging and statistics")
    print("  - Context-aware error responses")
    
    asyncio.run(test_error_handling())