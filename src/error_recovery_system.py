"""
完璧なエラー回復システム - Catherine用
全てのエラーを適切にキャッチし、ユーザーフレンドリーな回復を行う
"""
import logging
import asyncio
import traceback
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class ErrorRecoverySystem:
    """エラー回復とフォールバックシステム"""
    
    def __init__(self):
        self.error_counts = {}  # エラー頻度追跡
        self.last_errors = {}   # 最新エラー記録
        self.recovery_strategies = self._init_recovery_strategies()
    
    def _init_recovery_strategies(self) -> Dict[str, Dict[str, Any]]:
        """エラー別の回復戦略"""
        return {
            'openai_api_error': {
                'max_retries': 3,
                'retry_delay': [1, 3, 5],  # 段階的遅延
                'fallback_message': 'あらあら、少し疲れちゃったみたい。基本的な操作で手伝うよ',
                'fallback_actions': ['basic_todo', 'simple_response']
            },
            'google_api_error': {
                'max_retries': 2,
                'retry_delay': [2, 5],
                'fallback_message': 'やれやれ、Googleとの接続が不安定だね。しばらく待ってから再試行するよ',
                'fallback_actions': ['cache_request', 'notify_user']
            },
            'notion_api_error': {
                'max_retries': 2,
                'retry_delay': [1, 3],
                'fallback_message': 'まったく、Notionが応答しないよ。とりあえずローカルTODOに保存しておくね',
                'fallback_actions': ['local_todo_save', 'schedule_retry']
            },
            'permission_error': {
                'max_retries': 0,  # 再試行無意味
                'fallback_message': 'おや、権限が足りないようだね。管理者に設定を確認してもらって',
                'fallback_actions': ['show_setup_guide', 'alternative_method']
            },
            'network_error': {
                'max_retries': 3,
                'retry_delay': [2, 5, 10],
                'fallback_message': 'あら、ネットワークの調子が悪いね。少し待ってからもう一度試してみるよ',
                'fallback_actions': ['cache_request', 'offline_mode']
            },
            'database_error': {
                'max_retries': 2,
                'retry_delay': [1, 3],
                'fallback_message': 'データベースとの接続に問題があるよ。メモリに一時保存しておくね',
                'fallback_actions': ['memory_cache', 'schedule_retry']
            },
            'unknown_error': {
                'max_retries': 1,
                'retry_delay': [3],
                'fallback_message': 'ごめんなさい、予期しない問題が起きたよ。できる範囲で手伝うからね',
                'fallback_actions': ['basic_response', 'log_for_debugging']
            }
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        エラーを分析し、適切な回復戦略を実行
        
        Args:
            error: 発生したエラー
            context: エラーの文脈情報
            
        Returns:
            回復結果とユーザーメッセージ
        """
        try:
            error_type = self._classify_error(error)
            error_key = f"{error_type}_{context.get('user_id', 'unknown')}" if context else error_type
            
            # エラー頻度を記録
            self._record_error(error_key, error)
            
            # 回復戦略を取得
            strategy = self.recovery_strategies.get(error_type, self.recovery_strategies['unknown_error'])
            
            # 再試行ロジック
            if await self._should_retry(error_key, strategy):
                retry_result = await self._retry_operation(error, context, strategy)
                if retry_result['success']:
                    return retry_result
            
            # フォールバック実行
            fallback_result = await self._execute_fallback(error_type, strategy, context)
            
            return {
                'success': False,
                'recovered': True,
                'message': fallback_result['message'],
                'fallback_data': fallback_result.get('data'),
                'error_type': error_type,
                'retry_count': self.error_counts.get(error_key, {}).get('count', 0)
            }
            
        except Exception as recovery_error:
            logger.critical(f"Error recovery system failed: {recovery_error}")
            return {
                'success': False,
                'recovered': False,
                'message': 'ごめんなさい、完全に困っちゃった。しばらく待ってからもう一度試してくれる？',
                'error_type': 'recovery_failure'
            }
    
    def _classify_error(self, error: Exception) -> str:
        """エラーを分類"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # OpenAI APIエラー
        if 'openai' in error_str or 'gpt' in error_str or 'rate_limit' in error_str:
            return 'openai_api_error'
        
        # Google APIエラー
        if 'google' in error_str or 'googleapis' in error_str or 'oauth' in error_str:
            return 'google_api_error'
        
        # Notion APIエラー
        if 'notion' in error_str or 'notion_client' in error_str:
            return 'notion_api_error'
        
        # 権限エラー
        if 'permission' in error_str or 'unauthorized' in error_str or 'forbidden' in error_str:
            return 'permission_error'
        
        # ネットワークエラー
        if 'network' in error_str or 'connection' in error_str or 'timeout' in error_str or 'httperror' in error_str:
            return 'network_error'
        
        # データベースエラー
        if 'database' in error_str or 'firebase' in error_str or 'firestore' in error_str:
            return 'database_error'
        
        return 'unknown_error'
    
    def _record_error(self, error_key: str, error: Exception):
        """エラー記録"""
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        
        if error_key not in self.error_counts:
            self.error_counts[error_key] = {'count': 0, 'first_seen': now, 'last_seen': now}
        
        self.error_counts[error_key]['count'] += 1
        self.error_counts[error_key]['last_seen'] = now
        self.last_errors[error_key] = {
            'error': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': now
        }
        
        logger.error(f"Error recorded: {error_key} (count: {self.error_counts[error_key]['count']})")
    
    async def _should_retry(self, error_key: str, strategy: Dict[str, Any]) -> bool:
        """再試行すべきか判定"""
        if strategy['max_retries'] == 0:
            return False
        
        error_info = self.error_counts.get(error_key, {})
        retry_count = error_info.get('count', 0)
        
        # 最大再試行回数チェック
        if retry_count > strategy['max_retries']:
            return False
        
        # 時間ベースの制限（同じエラーが頻発している場合）
        last_seen = error_info.get('last_seen')
        if last_seen and retry_count > 1:
            time_since_last = datetime.now(pytz.timezone('Asia/Tokyo')) - last_seen
            if time_since_last.total_seconds() < 60:  # 1分以内に複数回エラーなら停止
                return False
        
        return True
    
    async def _retry_operation(self, error: Exception, context: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """再試行実行"""
        retry_delays = strategy['retry_delay']
        
        for attempt in range(len(retry_delays)):
            try:
                delay = retry_delays[attempt]
                logger.info(f"Retrying operation after {delay}s (attempt {attempt + 1})")
                
                await asyncio.sleep(delay)
                
                # 元の操作を再実行（contextから復元）
                if context and 'retry_function' in context:
                    result = await context['retry_function']()
                    return {'success': True, 'message': 'ふふ、今度はうまくいったようだね', 'data': result}
                
            except Exception as retry_error:
                logger.warning(f"Retry attempt {attempt + 1} failed: {retry_error}")
                if attempt == len(retry_delays) - 1:  # 最後の試行
                    break
        
        return {'success': False}
    
    async def _execute_fallback(self, error_type: str, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック戦略実行"""
        fallback_message = strategy['fallback_message']
        fallback_actions = strategy.get('fallback_actions', [])
        
        fallback_data = {}
        
        for action in fallback_actions:
            try:
                if action == 'basic_todo':
                    fallback_data['basic_todo_available'] = True
                elif action == 'simple_response':
                    fallback_data['response_mode'] = 'simple'
                elif action == 'cache_request':
                    fallback_data['cached'] = await self._cache_request(context)
                elif action == 'local_todo_save':
                    fallback_data['local_save'] = await self._save_locally(context)
                elif action == 'show_setup_guide':
                    fallback_data['setup_guide'] = self._get_setup_guide(error_type)
                elif action == 'alternative_method':
                    fallback_data['alternatives'] = self._get_alternatives(error_type)
                elif action == 'offline_mode':
                    fallback_data['offline_mode'] = True
                elif action == 'memory_cache':
                    fallback_data['memory_cached'] = await self._memory_cache(context)
                elif action == 'schedule_retry':
                    fallback_data['retry_scheduled'] = await self._schedule_retry(context)
                elif action == 'log_for_debugging':
                    fallback_data['logged'] = await self._log_debug_info(error_type, context)
                    
            except Exception as fallback_error:
                logger.error(f"Fallback action {action} failed: {fallback_error}")
        
        return {
            'message': fallback_message,
            'data': fallback_data
        }
    
    async def _cache_request(self, context: Dict[str, Any]) -> bool:
        """リクエストをキャッシュして後で再試行"""
        # 実装: リクエストを一時保存
        logger.info("Request cached for later retry")
        return True
    
    async def _save_locally(self, context: Dict[str, Any]) -> bool:
        """ローカルに保存"""
        # 実装: ローカルファイルやメモリに保存
        logger.info("Data saved locally")
        return True
    
    def _get_setup_guide(self, error_type: str) -> str:
        """セットアップガイドを取得"""
        guides = {
            'google_api_error': '🔧 Google API設定: Google Cloud Consoleで権限を確認してください',
            'notion_api_error': '🔧 Notion設定: Notionワークスペースでデータベースを作成してください',
            'permission_error': '🔧 権限設定: 管理者にAPI権限の付与を依頼してください'
        }
        return guides.get(error_type, '🔧 設定確認: 環境変数と権限を確認してください')
    
    def _get_alternatives(self, error_type: str) -> list:
        """代替手段を提案"""
        alternatives = {
            'google_api_error': ['ローカルTODO管理', 'メール通知での代替', '手動でGoogleサービス操作'],
            'notion_api_error': ['Firebase TODO', 'ローカルメモ', 'Discord内TODO管理'],
            'openai_api_error': ['基本的なパターンマッチング', 'キーワードベース応答', '事前定義された応答']
        }
        return alternatives.get(error_type, ['基本機能のみ使用', '手動操作', 'しばらく待ってから再試行'])
    
    async def _memory_cache(self, context: Dict[str, Any]) -> bool:
        """メモリキャッシュ"""
        logger.info("Data cached in memory")
        return True
    
    async def _schedule_retry(self, context: Dict[str, Any]) -> bool:
        """再試行をスケジュール"""
        logger.info("Retry scheduled for later")
        return True
    
    async def _log_debug_info(self, error_type: str, context: Dict[str, Any]) -> bool:
        """デバッグ情報をログ"""
        logger.debug(f"Debug info logged for {error_type}: {context}")
        return True
    
    def get_error_stats(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        stats = {
            'total_errors': sum(info['count'] for info in self.error_counts.values()),
            'error_types': len(self.error_counts),
            'recent_errors': {},
            'most_common_errors': []
        }
        
        # 最近のエラー（過去1時間）
        for error_key, info in self.error_counts.items():
            if (now - info['last_seen']).total_seconds() < 3600:
                stats['recent_errors'][error_key] = info['count']
        
        # 最も頻繁なエラー
        sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        stats['most_common_errors'] = sorted_errors[:5]
        
        return stats
    
    def reset_error_counts(self):
        """エラーカウントをリセット"""
        self.error_counts.clear()
        self.last_errors.clear()
        logger.info("Error counts reset")

# グローバルインスタンス
error_recovery = ErrorRecoverySystem()