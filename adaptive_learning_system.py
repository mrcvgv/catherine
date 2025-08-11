#!/usr/bin/env python3
"""
Adaptive Learning System - 会話を通じて成長する自己学習システム
会話パターン、ユーザー好み、成功/失敗から継続的に学習
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from firebase_config import firebase_manager
from openai import OpenAI
import numpy as np

JST = pytz.timezone('Asia/Tokyo')

class AdaptiveLearningSystem:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        
        # 学習パラメータ
        self.learning_rate = 0.1
        self.memory_decay = 0.95  # 記憶の減衰率
        self.success_threshold = 0.7
        
        # 学習データストア
        self.conversation_patterns = {}  # パターン認識
        self.user_preferences = {}       # ユーザー好み
        self.response_effectiveness = {} # 応答効果
        self.personality_evolution = {}  # 性格進化
        
    async def learn_from_conversation(self, user_id: str, message: str, 
                                     response: str, user_reaction: Optional[Dict] = None) -> Dict:
        """会話から学習"""
        try:
            # 会話パターン解析
            pattern = await self._analyze_conversation_pattern(message, response)
            
            # ユーザーの好み学習
            preferences = await self._learn_user_preferences(user_id, message, response, user_reaction)
            
            # 応答効果測定
            effectiveness = await self._measure_response_effectiveness(
                user_id, message, response, user_reaction
            )
            
            # 学習データ更新
            learning_data = {
                'user_id': user_id,
                'timestamp': datetime.now(JST),
                'message': message,
                'response': response,
                'pattern': pattern,
                'preferences': preferences,
                'effectiveness': effectiveness,
                'reaction': user_reaction
            }
            
            # Firestoreに保存
            await self._save_learning_data(user_id, learning_data)
            
            # モデル更新
            await self._update_conversation_model(user_id, learning_data)
            
            # 性格進化
            await self._evolve_personality(user_id, effectiveness)
            
            return {
                'learned': True,
                'pattern': pattern,
                'effectiveness': effectiveness,
                'growth_level': await self._get_growth_level(user_id)
            }
            
        except Exception as e:
            print(f"❌ Learning error: {e}")
            return {'learned': False}
    
    async def _analyze_conversation_pattern(self, message: str, response: str) -> Dict:
        """会話パターン解析"""
        try:
            prompt = f"""
            以下の会話を分析してパターンを抽出してください：
            
            ユーザー: {message}
            AI応答: {response}
            
            以下のJSONで返してください：
            {{
                "topic_category": "仕事/雑談/質問/感情表現/その他",
                "user_intent": "具体的な意図",
                "communication_style": "フォーマル/カジュアル/フレンドリー",
                "emotional_tone": "ポジティブ/ネガティブ/ニュートラル",
                "complexity": 0.0-1.0,
                "key_phrases": ["重要フレーズ1", "重要フレーズ2"],
                "response_appropriateness": 0.0-1.0
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "会話パターン分析の専門家として正確に分析してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Pattern analysis error: {e}")
            return {}
    
    async def _learn_user_preferences(self, user_id: str, message: str, 
                                     response: str, user_reaction: Optional[Dict]) -> Dict:
        """ユーザー好み学習"""
        try:
            # 既存の好みデータ取得
            existing_prefs = await self._get_user_preferences(user_id)
            
            # 新しい好み要素を抽出
            new_preferences = {
                'communication_style': {},
                'topics_of_interest': {},
                'response_length': {},
                'humor_level': {},
                'formality': {},
                'emoji_usage': {}
            }
            
            # メッセージから好みを推測
            if len(message) > 100:
                new_preferences['response_length']['prefers_detailed'] = 1.0
            else:
                new_preferences['response_length']['prefers_concise'] = 1.0
            
            # 絵文字使用の好み
            if any(char in message for char in '😀😃😄😁😆😊🙂🙃☺️😉'):
                new_preferences['emoji_usage']['likes_emoji'] = 1.0
            
            # ユーザー反応から学習
            if user_reaction:
                reaction_score = user_reaction.get('score', 0.5)
                
                # 応答スタイルの好み更新
                if 'です' in response or 'ます' in response:
                    new_preferences['formality']['formal'] = reaction_score
                else:
                    new_preferences['formality']['casual'] = reaction_score
            
            # 既存の好みと統合（指数移動平均）
            merged_preferences = self._merge_preferences(existing_prefs, new_preferences)
            
            return merged_preferences
            
        except Exception as e:
            print(f"❌ Preference learning error: {e}")
            return {}
    
    async def _measure_response_effectiveness(self, user_id: str, message: str, 
                                             response: str, user_reaction: Optional[Dict]) -> float:
        """応答効果測定"""
        try:
            effectiveness = 0.5  # ベースライン
            
            # ユーザー反応から効果測定
            if user_reaction:
                # リアクション絵文字から効果判定
                positive_reactions = ['👍', '😄', '❤️', '✨', '🎉']
                negative_reactions = ['👎', '😢', '😡', '❌', '🤔']
                
                reaction_emoji = user_reaction.get('emoji', '')
                if reaction_emoji in positive_reactions:
                    effectiveness = 0.9
                elif reaction_emoji in negative_reactions:
                    effectiveness = 0.2
                
                # 返信速度から関心度を測定
                response_time = user_reaction.get('response_time', 60)
                if response_time < 10:  # 10秒以内の返信は高関心
                    effectiveness += 0.1
            
            # 会話継続性から効果測定
            if user_reaction and user_reaction.get('continued_conversation', False):
                effectiveness += 0.2
            
            # 正規化
            effectiveness = min(1.0, max(0.0, effectiveness))
            
            return effectiveness
            
        except Exception as e:
            print(f"❌ Effectiveness measurement error: {e}")
            return 0.5
    
    async def _evolve_personality(self, user_id: str, effectiveness: float):
        """性格進化"""
        try:
            # 現在の性格パラメータ取得
            personality = await self._get_personality_params(user_id)
            
            # 効果に基づいて性格調整
            if effectiveness > 0.7:
                # 成功した応答スタイルを強化
                personality['confidence'] = min(1.0, personality.get('confidence', 0.5) + 0.05)
                personality['friendliness'] = min(1.0, personality.get('friendliness', 0.7) + 0.03)
            elif effectiveness < 0.3:
                # 失敗した応答スタイルを調整
                personality['formality'] = min(1.0, personality.get('formality', 0.5) + 0.05)
                personality['cautiousness'] = min(1.0, personality.get('cautiousness', 0.5) + 0.05)
            
            # ユーザー別性格パラメータ保存
            doc_ref = self.db.collection('personality_evolution').document(user_id)
            doc_ref.set({
                'user_id': user_id,
                'personality': personality,
                'updated_at': datetime.now(JST),
                'evolution_stage': await self._calculate_evolution_stage(personality)
            }, merge=True)
            
        except Exception as e:
            print(f"❌ Personality evolution error: {e}")
    
    async def _update_conversation_model(self, user_id: str, learning_data: Dict):
        """会話モデル更新"""
        try:
            # パターン頻度更新
            pattern = learning_data['pattern']
            topic = pattern.get('topic_category', 'その他')
            
            if user_id not in self.conversation_patterns:
                self.conversation_patterns[user_id] = {}
            
            if topic not in self.conversation_patterns[user_id]:
                self.conversation_patterns[user_id][topic] = {
                    'count': 0,
                    'success_rate': 0.5,
                    'preferred_style': None
                }
            
            # カウント更新
            self.conversation_patterns[user_id][topic]['count'] += 1
            
            # 成功率更新（指数移動平均）
            current_success = self.conversation_patterns[user_id][topic]['success_rate']
            effectiveness = learning_data['effectiveness']
            new_success = current_success * 0.9 + effectiveness * 0.1
            self.conversation_patterns[user_id][topic]['success_rate'] = new_success
            
            # Firestoreに保存
            doc_ref = self.db.collection('conversation_models').document(user_id)
            doc_ref.set({
                'patterns': self.conversation_patterns[user_id],
                'updated_at': datetime.now(JST)
            }, merge=True)
            
        except Exception as e:
            print(f"❌ Model update error: {e}")
    
    async def get_adapted_response_style(self, user_id: str, context: Dict) -> Dict:
        """学習済みの応答スタイルを取得"""
        try:
            # ユーザー好み取得
            preferences = await self._get_user_preferences(user_id)
            
            # 性格パラメータ取得
            personality = await self._get_personality_params(user_id)
            
            # 会話パターン取得
            patterns = self.conversation_patterns.get(user_id, {})
            
            # 最適な応答スタイル決定
            response_style = {
                'tone': self._determine_tone(preferences, personality),
                'length': self._determine_length(preferences),
                'formality': self._determine_formality(preferences, personality),
                'humor_level': self._determine_humor(preferences, personality),
                'emoji_usage': preferences.get('emoji_usage', {}).get('likes_emoji', 0.3) > 0.5,
                'confidence_level': personality.get('confidence', 0.7),
                'learning_insights': await self._get_learning_insights(user_id)
            }
            
            return response_style
            
        except Exception as e:
            print(f"❌ Style adaptation error: {e}")
            return self._get_default_style()
    
    async def _get_growth_level(self, user_id: str) -> Dict:
        """成長レベル取得"""
        try:
            # 会話回数
            conv_count = sum(
                pattern.get('count', 0) 
                for pattern in self.conversation_patterns.get(user_id, {}).values()
            )
            
            # 平均成功率
            success_rates = [
                pattern.get('success_rate', 0.5) 
                for pattern in self.conversation_patterns.get(user_id, {}).values()
            ]
            avg_success = np.mean(success_rates) if success_rates else 0.5
            
            # 成長レベル計算
            growth_level = min(100, conv_count * 0.5 + avg_success * 50)
            
            # 成長段階
            if growth_level < 20:
                stage = "初心者"
            elif growth_level < 40:
                stage = "学習中"
            elif growth_level < 60:
                stage = "習熟"
            elif growth_level < 80:
                stage = "熟練"
            else:
                stage = "マスター"
            
            return {
                'level': growth_level,
                'stage': stage,
                'conversations': conv_count,
                'success_rate': avg_success,
                'next_milestone': self._get_next_milestone(growth_level)
            }
            
        except Exception as e:
            print(f"❌ Growth level error: {e}")
            return {'level': 0, 'stage': '初心者'}
    
    async def _save_learning_data(self, user_id: str, data: Dict):
        """学習データ保存"""
        try:
            doc_ref = self.db.collection('learning_history').document()
            doc_ref.set(data)
            
            # 統計更新
            stats_ref = self.db.collection('learning_stats').document(user_id)
            stats_ref.set({
                'total_conversations': self.db._firestore.FieldValue.increment(1),
                'last_learning': datetime.now(JST),
                'updated_at': datetime.now(JST)
            }, merge=True)
            
        except Exception as e:
            print(f"❌ Save learning data error: {e}")
    
    async def _get_user_preferences(self, user_id: str) -> Dict:
        """ユーザー好み取得"""
        try:
            doc = self.db.collection('user_preferences').document(user_id).get()
            if doc.exists:
                return doc.to_dict().get('preferences', {})
            return {}
        except Exception as e:
            print(f"❌ Get preferences error: {e}")
            return {}
    
    async def _get_personality_params(self, user_id: str) -> Dict:
        """性格パラメータ取得"""
        try:
            doc = self.db.collection('personality_evolution').document(user_id).get()
            if doc.exists:
                return doc.to_dict().get('personality', self._get_default_personality())
            return self._get_default_personality()
        except Exception as e:
            print(f"❌ Get personality error: {e}")
            return self._get_default_personality()
    
    def _get_default_personality(self) -> Dict:
        """デフォルト性格"""
        return {
            'confidence': 0.7,
            'friendliness': 0.8,
            'formality': 0.5,
            'cautiousness': 0.4,
            'humor': 0.6,
            'empathy': 0.8
        }
    
    def _merge_preferences(self, existing: Dict, new: Dict) -> Dict:
        """好みデータ統合"""
        merged = existing.copy()
        
        for category, values in new.items():
            if category not in merged:
                merged[category] = {}
            
            for key, value in values.items():
                if key in merged[category]:
                    # 指数移動平均で更新
                    merged[category][key] = merged[category][key] * 0.8 + value * 0.2
                else:
                    merged[category][key] = value
        
        return merged
    
    def _determine_tone(self, preferences: Dict, personality: Dict) -> str:
        """トーン決定"""
        friendliness = personality.get('friendliness', 0.7)
        formality = personality.get('formality', 0.5)
        
        if friendliness > 0.7 and formality < 0.4:
            return "casual_friendly"
        elif friendliness > 0.7 and formality > 0.6:
            return "polite_friendly"
        elif formality > 0.7:
            return "formal"
        else:
            return "balanced"
    
    def _determine_length(self, preferences: Dict) -> str:
        """応答長決定"""
        length_pref = preferences.get('response_length', {})
        if length_pref.get('prefers_detailed', 0) > 0.6:
            return "detailed"
        elif length_pref.get('prefers_concise', 0) > 0.6:
            return "concise"
        else:
            return "moderate"
    
    def _determine_formality(self, preferences: Dict, personality: Dict) -> float:
        """フォーマル度決定"""
        pref_formal = preferences.get('formality', {}).get('formal', 0.5)
        pers_formal = personality.get('formality', 0.5)
        return (pref_formal + pers_formal) / 2
    
    def _determine_humor(self, preferences: Dict, personality: Dict) -> float:
        """ユーモアレベル決定"""
        pref_humor = preferences.get('humor_level', {}).get('likes_humor', 0.5)
        pers_humor = personality.get('humor', 0.6)
        return (pref_humor + pers_humor) / 2
    
    async def _get_learning_insights(self, user_id: str) -> List[str]:
        """学習洞察取得"""
        insights = []
        
        patterns = self.conversation_patterns.get(user_id, {})
        if patterns:
            # 最も多い話題
            most_common = max(patterns.items(), key=lambda x: x[1]['count'])[0]
            insights.append(f"よく{most_common}について話します")
            
            # 成功率が高い話題
            best_topic = max(patterns.items(), key=lambda x: x[1]['success_rate'])[0]
            insights.append(f"{best_topic}の話が得意です")
        
        return insights
    
    def _calculate_evolution_stage(self, personality: Dict) -> str:
        """進化段階計算"""
        total_score = sum(personality.values()) / len(personality)
        
        if total_score < 0.3:
            return "学習初期"
        elif total_score < 0.5:
            return "成長期"
        elif total_score < 0.7:
            return "発展期"
        elif total_score < 0.85:
            return "成熟期"
        else:
            return "完成期"
    
    def _get_next_milestone(self, current_level: float) -> str:
        """次のマイルストーン"""
        milestones = [
            (20, "基本パターン習得"),
            (40, "好み理解"),
            (60, "性格最適化"),
            (80, "完全適応"),
            (100, "マスター到達")
        ]
        
        for level, milestone in milestones:
            if current_level < level:
                return f"レベル{level}: {milestone}"
        
        return "最高レベル達成！"
    
    def _get_default_style(self) -> Dict:
        """デフォルトスタイル"""
        return {
            'tone': 'balanced',
            'length': 'moderate',
            'formality': 0.5,
            'humor_level': 0.5,
            'emoji_usage': False,
            'confidence_level': 0.7,
            'learning_insights': []
        }