"""
Catherine 自己学習システム - 魔女コメントの学習・改善
"""
import json
from datetime import datetime
from typing import Dict, List, Any
import pytz
from firebase_config import firebase_manager
import logging
import random

logger = logging.getLogger(__name__)

class CatherineLearningSystem:
    """Catherine の発言学習システム"""
    
    def __init__(self):
        self.db = firebase_manager.get_db()
        
    async def record_response_feedback(self, user_id: str, message_type: str, 
                                     catherine_response: str, user_reaction: str):
        """ユーザーの反応を記録して学習データに追加"""
        try:
            feedback_data = {
                'user_id': user_id,
                'message_type': message_type,  # 'todo_create', 'todo_delete', etc.
                'catherine_response': catherine_response,
                'user_reaction': user_reaction,  # 'positive', 'negative', 'neutral'
                'timestamp': datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC),
                'hour': datetime.now(pytz.timezone('Asia/Tokyo')).hour
            }
            
            # Firebaseに保存
            self.db.collection('catherine_learning').add(feedback_data)
            logger.info(f"Recorded feedback for {message_type}: {user_reaction}")
            
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
    
    async def get_learned_responses(self, message_type: str, hour: int = None) -> List[str]:
        """学習データから最適な返答候補を取得"""
        try:
            # 基本的な魔女コメント（フォールバック）
            default_responses = {
                'todo_create': [
                    "よくできました、偉いねぇ",
                    "また一つ増えちゃったね",
                    "ちゃんと覚えておいたからね"
                ],
                'todo_list': [
                    "さあ、今日も頑張るんだよ",
                    "一つずつ片付けていきな",
                    "やることが山積みだねぇ"
                ],
                'todo_delete': [
                    "まあ、あんたの判断に任せるよ",
                    "思い切りがいいじゃないか",
                    "後悔しないようにね"
                ]
            }
            
            # 学習データがある場合は取得
            if self.db:
                query = (self.db.collection('catherine_learning')
                        .where('message_type', '==', message_type)
                        .where('user_reaction', '==', 'positive')
                        .limit(10))
                
                learned_responses = []
                for doc in query.stream():
                    data = doc.to_dict()
                    learned_responses.append(data['catherine_response'])
                
                if learned_responses:
                    # 学習した好評な返答を50%の確率で使用
                    if random.random() < 0.5:
                        return learned_responses
            
            # デフォルト返答を返す
            return default_responses.get(message_type, ["ふふ、そうですねぇ"])
            
        except Exception as e:
            logger.error(f"Failed to get learned responses: {e}")
            return default_responses.get(message_type, ["ふふ、そうですねぇ"])
    
    async def generate_adaptive_response(self, message_type: str, context: Dict[str, Any]) -> str:
        """文脈に応じた適応的な返答を生成"""
        try:
            hour = datetime.now(pytz.timezone('Asia/Tokyo')).hour
            
            # 時間帯による調整
            if 5 <= hour < 10:
                time_modifier = ["朝から", "早起きして", "今日も"]
            elif 12 <= hour < 15:
                time_modifier = ["お昼に", "午後も", ""]
            elif 18 <= hour < 22:
                time_modifier = ["夜に", "お疲れ様、", "一日の終わりに"]
            else:
                time_modifier = ["こんな時間に", "夜更かしして", ""]
            
            # 学習した返答を取得
            responses = await self.get_learned_responses(message_type, hour)
            base_response = random.choice(responses)
            
            # 時間帯修飾子を追加（30%の確率）
            if random.random() < 0.3 and time_modifier:
                modifier = random.choice(time_modifier)
                if modifier:
                    base_response = f"{modifier}{base_response}"
            
            return base_response
            
        except Exception as e:
            logger.error(f"Failed to generate adaptive response: {e}")
            return "ふふ、そうですねぇ"
    
    async def learn_from_conversation(self, user_id: str, user_message: str, 
                                    catherine_response: str):
        """対話から自動学習（簡易版）"""
        try:
            # ポジティブな単語が含まれていれば好評と判定
            positive_words = ['ありがとう', 'いいね', '素晴らしい', '最高', 'かわいい', '面白い']
            negative_words = ['つまらない', 'だめ', '嫌い', 'うざい', 'やめて']
            
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in positive_words):
                reaction = 'positive'
            elif any(word in user_message_lower for word in negative_words):
                reaction = 'negative'
            else:
                reaction = 'neutral'
            
            # 自動フィードバック記録
            await self.record_response_feedback(
                user_id, 'conversation', catherine_response, reaction
            )
            
        except Exception as e:
            logger.error(f"Failed to learn from conversation: {e}")

# グローバルインスタンス
catherine_learning = CatherineLearningSystem()