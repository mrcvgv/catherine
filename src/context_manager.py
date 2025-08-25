"""
コンテキスト管理システム - Firebase履歴管理の拡張
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
import logging
import json

logger = logging.getLogger(__name__)

class ContextManager:
    """会話コンテキストと履歴を管理"""
    
    def __init__(self):
        try:
            from firebase_config import firebase_manager
            self.db = firebase_manager.get_db()
            if not self.db:
                logger.error("Firebase not available for ContextManager")
        except ImportError:
            logger.error("Firebase config not available")
            self.db = None
    
    async def save_user_preference(self, user_id: str, preference_key: str, preference_value: Any) -> bool:
        """ユーザーの好みを保存"""
        try:
            if not self.db:
                return False
            
            doc_ref = self.db.collection('user_preferences').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                # 既存の設定を更新
                doc_ref.update({
                    preference_key: preference_value,
                    'updated_at': datetime.now(pytz.UTC)
                })
            else:
                # 新規作成
                doc_ref.set({
                    preference_key: preference_value,
                    'created_at': datetime.now(pytz.UTC),
                    'updated_at': datetime.now(pytz.UTC)
                })
            
            logger.info(f"Saved preference for user {user_id}: {preference_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user preference: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """ユーザーの好みを取得"""
        try:
            if not self.db:
                return {}
            
            doc_ref = self.db.collection('user_preferences').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                preferences = doc.to_dict()
                # タイムスタンプを除外
                preferences.pop('created_at', None)
                preferences.pop('updated_at', None)
                return preferences
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def save_important_context(self, user_id: str, context_type: str, context_data: Dict[str, Any]) -> bool:
        """重要なコンテキストを保存"""
        try:
            if not self.db:
                return False
            
            context_entry = {
                'user_id': user_id,
                'context_type': context_type,
                'data': context_data,
                'timestamp': datetime.now(pytz.UTC),
                'expires_at': datetime.now(pytz.UTC) + timedelta(days=30)  # 30日後に期限切れ
            }
            
            self.db.collection('important_contexts').add(context_entry)
            logger.info(f"Saved important context for user {user_id}: {context_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save important context: {e}")
            return False
    
    async def get_recent_context(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """最近の重要コンテキストを取得"""
        try:
            if not self.db:
                return []
            
            now = datetime.now(pytz.UTC)
            
            # 期限切れでない最近のコンテキストを取得
            query = (self.db.collection('important_contexts')
                    .where('user_id', '==', user_id)
                    .where('expires_at', '>', now)
                    .order_by('timestamp', direction='DESCENDING')
                    .limit(limit))
            
            contexts = []
            for doc in query.stream():
                context = doc.to_dict()
                contexts.append({
                    'type': context.get('context_type'),
                    'data': context.get('data'),
                    'timestamp': context.get('timestamp')
                })
            
            return contexts
            
        except Exception as e:
            logger.error(f"Failed to get recent context: {e}")
            return []
    
    async def save_conversation_summary(self, user_id: str, channel_id: str, summary: str, key_points: List[str]) -> bool:
        """会話の要約を保存"""
        try:
            if not self.db:
                return False
            
            summary_entry = {
                'user_id': user_id,
                'channel_id': channel_id,
                'summary': summary,
                'key_points': key_points,
                'timestamp': datetime.now(pytz.UTC),
                'expires_at': datetime.now(pytz.UTC) + timedelta(days=7)  # 7日後に期限切れ
            }
            
            self.db.collection('conversation_summaries').add(summary_entry)
            logger.info(f"Saved conversation summary for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation summary: {e}")
            return False
    
    async def get_recent_summaries(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """最近の会話要約を取得"""
        try:
            if not self.db:
                return []
            
            now = datetime.now(pytz.UTC)
            
            query = (self.db.collection('conversation_summaries')
                    .where('user_id', '==', user_id)
                    .where('expires_at', '>', now)
                    .order_by('timestamp', direction='DESCENDING')
                    .limit(limit))
            
            summaries = []
            for doc in query.stream():
                summary = doc.to_dict()
                summaries.append({
                    'summary': summary.get('summary'),
                    'key_points': summary.get('key_points', []),
                    'timestamp': summary.get('timestamp')
                })
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to get recent summaries: {e}")
            return []
    
    async def build_context_prompt(self, user_id: str) -> str:
        """ユーザーのコンテキストからプロンプトを構築"""
        try:
            # ユーザーの好みを取得
            preferences = await self.get_user_preferences(user_id)
            
            # 最近の重要コンテキストを取得
            recent_contexts = await self.get_recent_context(user_id)
            
            # 最近の会話要約を取得
            recent_summaries = await self.get_recent_summaries(user_id)
            
            context_parts = []
            
            # ユーザーの好みを追加
            if preferences:
                pref_str = "ユーザーの設定: " + ", ".join([f"{k}={v}" for k, v in preferences.items()])
                context_parts.append(pref_str)
            
            # 重要なコンテキストを追加
            if recent_contexts:
                for ctx in recent_contexts[:3]:  # 最大3つ
                    context_parts.append(f"重要事項({ctx['type']}): {json.dumps(ctx['data'], ensure_ascii=False)}")
            
            # 会話要約を追加
            if recent_summaries and recent_summaries[0]:
                latest_summary = recent_summaries[0]
                context_parts.append(f"前回の会話: {latest_summary['summary']}")
                if latest_summary['key_points']:
                    context_parts.append("要点: " + ", ".join(latest_summary['key_points']))
            
            if context_parts:
                return "\n[コンテキスト]\n" + "\n".join(context_parts) + "\n"
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to build context prompt: {e}")
            return ""
    
    async def learn_from_interaction(self, user_id: str, message: str, response: str) -> None:
        """対話から学習して重要な情報を抽出"""
        try:
            # 特定のパターンを検出して好みを保存
            message_lower = message.lower()
            
            # 呼び方の好みを検出
            if "呼んで" in message_lower or "名前" in message_lower:
                if "さん" in message:
                    await self.save_user_preference(user_id, "preferred_honorific", "さん")
                elif "ちゃん" in message:
                    await self.save_user_preference(user_id, "preferred_honorific", "ちゃん")
                elif "くん" in message:
                    await self.save_user_preference(user_id, "preferred_honorific", "くん")
            
            # 作業時間の好みを検出
            if "朝" in message_lower and ("作業" in message_lower or "仕事" in message_lower):
                await self.save_user_preference(user_id, "work_time", "morning")
            elif "夜" in message_lower and ("作業" in message_lower or "仕事" in message_lower):
                await self.save_user_preference(user_id, "work_time", "night")
            
            # プロジェクト名や重要な固有名詞を検出
            if "プロジェクト" in message_lower or "案件" in message_lower:
                await self.save_important_context(user_id, "project_mention", {
                    "message": message,
                    "timestamp": datetime.now(pytz.UTC).isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to learn from interaction: {e}")

# グローバルインスタンス
context_manager = ContextManager()