#!/usr/bin/env python3
"""
Emotional Intelligence Module - 高度な感情知能システム
超優秀秘書の感情理解・適応的コミュニケーション機能
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class EmotionalIntelligence:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 感情プロファイル
        self.emotion_profiles = {}
        self.communication_adaptations = {}
        
    async def analyze_emotional_state(self, user_id: str, text: str, context: str = "") -> Dict:
        """高度な感情状態分析"""
        try:
            # 過去の感情履歴を取得
            emotion_history = await self._get_emotion_history(user_id, days=7)
            
            analysis_prompt = f"""
            以下のテキストと文脈から、ユーザーの詳細な感情状態を分析してください：
            
            【現在のメッセージ】
            {text}
            
            【文脈】
            {context}
            
            【過去7日間の感情履歴】
            {emotion_history}
            
            以下のJSONで詳細分析を返してください：
            {{
                "primary_emotion": "主要感情",
                "secondary_emotions": ["副次感情1", "副次感情2"],
                "emotion_intensity": 0.0-1.0,
                "emotional_stability": 0.0-1.0,
                "stress_level": 0.0-1.0,
                "energy_level": 0.0-1.0,
                "confidence_level": 0.0-1.0,
                "openness_to_feedback": 0.0-1.0,
                "decision_readiness": 0.0-1.0,
                "social_need": 0.0-1.0,
                "support_need": 0.0-1.0,
                "emotional_triggers": ["トリガー1", "トリガー2"],
                "recommended_approach": "推奨アプローチ",
                "communication_style": "formal/friendly/supportive/energetic/calm",
                "timing_sensitivity": "immediate/flexible/delayed",
                "emotional_trajectory": "improving/stable/declining/volatile",
                "intervention_needed": true/false,
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは世界最高レベルの感情分析心理学者です。微細な感情変化も正確に読み取り、最適なサポート方法を提案してください。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            emotion_analysis = json.loads(content)
            
            # 分析結果を保存
            await self._save_emotion_analysis(user_id, emotion_analysis, text)
            
            return emotion_analysis
            
        except Exception as e:
            print(f"❌ Emotional analysis error: {e}")
            return {"confidence": 0.0, "primary_emotion": "neutral"}
    
    async def adapt_communication_style(self, user_id: str, emotion_state: Dict, base_response: str) -> str:
        """感情状態に基づいてコミュニケーションスタイルを適応"""
        try:
            if emotion_state.get('confidence', 0) < 0.7:
                return base_response  # 低信頼度の場合は変更しない
            
            adaptation_prompt = f"""
            以下の感情分析結果に基づいて、応答を最適化してください：
            
            【感情分析】
            {emotion_state}
            
            【元の応答】
            {base_response}
            
            以下の点を考慮して応答を調整してください：
            1. 推奨コミュニケーションスタイル: {emotion_state.get('communication_style', 'friendly')}
            2. ストレスレベル: {emotion_state.get('stress_level', 0.5)}
            3. サポート必要度: {emotion_state.get('support_need', 0.5)}
            4. エネルギーレベル: {emotion_state.get('energy_level', 0.5)}
            5. 意思決定準備度: {emotion_state.get('decision_readiness', 0.5)}
            
            感情に寄り添った適切な応答を生成してください。
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは感情に配慮した高度なコミュニケーション専門家です。相手の心理状態に完璧に適応した応答を生成してください。"},
                    {"role": "user", "content": adaptation_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            adapted_response = response.choices[0].message.content
            
            # 適応ログを保存
            await self._log_communication_adaptation(user_id, emotion_state, base_response, adapted_response)
            
            return adapted_response
            
        except Exception as e:
            print(f"❌ Communication adaptation error: {e}")
            return base_response
    
    async def detect_emotional_crisis(self, user_id: str, emotion_state: Dict) -> Optional[Dict]:
        """感情的危機状況の検出"""
        try:
            crisis_indicators = {
                'high_stress': emotion_state.get('stress_level', 0) > 0.8,
                'low_stability': emotion_state.get('emotional_stability', 1) < 0.3,
                'intervention_needed': emotion_state.get('intervention_needed', False),
                'declining_trajectory': emotion_state.get('emotional_trajectory') == 'declining',
                'volatile_state': emotion_state.get('emotional_trajectory') == 'volatile'
            }
            
            crisis_count = sum(crisis_indicators.values())
            
            if crisis_count >= 2:  # 2つ以上の危機指標
                crisis_response = await self._generate_crisis_support(user_id, emotion_state, crisis_indicators)
                
                # 危機ログを保存
                crisis_log = {
                    'user_id': user_id,
                    'detected_at': datetime.now(self.jst),
                    'indicators': crisis_indicators,
                    'emotion_state': emotion_state,
                    'support_provided': crisis_response,
                    'severity': 'high' if crisis_count >= 4 else 'medium'
                }
                
                self.db.collection('emotional_crises').document().set(crisis_log)
                
                return crisis_response
            
            return None
            
        except Exception as e:
            print(f"❌ Crisis detection error: {e}")
            return None
    
    async def build_emotional_rapport(self, user_id: str) -> Dict:
        """感情的ラポート構築"""
        try:
            # 感情履歴分析
            emotion_patterns = await self._analyze_emotion_patterns(user_id)
            
            rapport_strategies = {
                'preferred_communication': emotion_patterns.get('preferred_style', 'friendly'),
                'emotional_triggers': emotion_patterns.get('triggers', []),
                'comfort_topics': emotion_patterns.get('comfort_topics', []),
                'stress_relievers': emotion_patterns.get('stress_relievers', []),
                'motivation_patterns': emotion_patterns.get('motivations', []),
                'trust_building_methods': emotion_patterns.get('trust_methods', [])
            }
            
            return rapport_strategies
            
        except Exception as e:
            print(f"❌ Rapport building error: {e}")
            return {}
    
    async def provide_emotional_support(self, user_id: str, emotion_state: Dict) -> str:
        """感情サポートの提供"""
        try:
            support_type = self._determine_support_type(emotion_state)
            
            support_prompts = {
                'validation': "感情を受け入れ、共感的な支援",
                'encouragement': "励ましと前向きなエネルギー",
                'practical': "具体的な解決策とアクション",
                'listening': "傾聴と理解の表現",
                'distraction': "気分転換と軽やかさ",
                'professional': "専門的で客観的な助言"
            }
            
            support_prompt = f"""
            ユーザーの感情状態に基づいて、{support_type}の支援メッセージを生成してください：
            
            【感情分析】
            {emotion_state}
            
            【支援タイプ】{support_prompts.get(support_type, '総合的支援')}
            
            温かく、誠実で、適切な支援メッセージを作成してください。
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは感情に深く共感し、的確な支援を提供する心理カウンセラーです。"},
                    {"role": "user", "content": support_prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Emotional support error: {e}")
            return "心配事があるようですね。お話を聞かせてください。"
    
    def _determine_support_type(self, emotion_state: Dict) -> str:
        """必要な支援タイプを決定"""
        stress = emotion_state.get('stress_level', 0.5)
        energy = emotion_state.get('energy_level', 0.5)
        confidence = emotion_state.get('confidence_level', 0.5)
        support_need = emotion_state.get('support_need', 0.5)
        
        if stress > 0.7 and support_need > 0.6:
            return 'validation'
        elif confidence < 0.4:
            return 'encouragement'
        elif energy < 0.3:
            return 'distraction'
        elif support_need > 0.7:
            return 'listening'
        elif emotion_state.get('decision_readiness', 0.5) > 0.7:
            return 'practical'
        else:
            return 'professional'
    
    async def _get_emotion_history(self, user_id: str, days: int = 7) -> str:
        """感情履歴を取得"""
        try:
            start_date = datetime.now(self.jst) - timedelta(days=days)
            
            # シンプルなクエリ（インデックス不要）
            query = self.db.collection('emotion_analyses').where('user_id', '==', user_id)
            
            docs = query.get()
            
            emotions = []
            for doc in docs:
                data = doc.to_dict()
                if data.get('analyzed_at') and data['analyzed_at'] >= start_date:
                    emotions.append({
                        'emotion': data.get('primary_emotion'),
                        'intensity': data.get('emotion_intensity', 0.5),
                        'date': data['analyzed_at'].strftime('%Y-%m-%d')
                    })
            
            # 日付でソート（新しい順）
            emotions = sorted(emotions, key=lambda x: x.get('date', ''), reverse=True)
            
            if not emotions:
                return "感情履歴なし"
            
            return f"過去の感情: {emotions[:5]}"
            
        except Exception as e:
            print(f"❌ Get emotion history error: {e}")
            return "感情履歴取得エラー"
    
    async def _save_emotion_analysis(self, user_id: str, analysis: Dict, original_text: str):
        """感情分析結果を保存"""
        try:
            emotion_doc = {
                'user_id': user_id,
                'analyzed_at': datetime.now(self.jst),
                'original_text': original_text,
                **analysis
            }
            
            self.db.collection('emotion_analyses').document().set(emotion_doc)
            
        except Exception as e:
            print(f"❌ Save emotion analysis error: {e}")
    
    async def _log_communication_adaptation(self, user_id: str, emotion_state: Dict, 
                                          original: str, adapted: str):
        """コミュニケーション適応ログ"""
        try:
            adaptation_log = {
                'user_id': user_id,
                'adapted_at': datetime.now(self.jst),
                'emotion_state': emotion_state,
                'original_response': original,
                'adapted_response': adapted,
                'adaptation_reason': emotion_state.get('recommended_approach', 'general')
            }
            
            self.db.collection('communication_adaptations').document().set(adaptation_log)
            
        except Exception as e:
            print(f"❌ Log adaptation error: {e}")
    
    async def _generate_crisis_support(self, user_id: str, emotion_state: Dict, 
                                     crisis_indicators: Dict) -> Dict:
        """危機状況への支援生成"""
        try:
            crisis_prompt = f"""
            ユーザーが感情的危機状態にあります。以下の状況に対する適切な支援を提案してください：
            
            【危機指標】
            {crisis_indicators}
            
            【感情状態】
            {emotion_state}
            
            以下のJSONで支援プランを返してください：
            {{
                "immediate_support": "即座に提供すべき支援",
                "follow_up_actions": ["フォローアップアクション"],
                "referral_needed": true/false,
                "monitoring_frequency": "継続監視の頻度",
                "safety_concerns": true/false
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは危機介入の専門家です。安全で効果的な支援を提供してください。"},
                    {"role": "user", "content": crisis_prompt}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Crisis support generation error: {e}")
            return {"immediate_support": "専門的な支援が必要かもしれません。お話を聞かせてください。"}
    
    async def _analyze_emotion_patterns(self, user_id: str) -> Dict:
        """感情パターン分析"""
        try:
            # 過去30日間の感情データを取得
            start_date = datetime.now(self.jst) - timedelta(days=30)
            
            query = self.db.collection('emotion_analyses').where('user_id', '==', user_id)
            docs = query.get()
            
            emotions = []
            for doc in docs:
                data = doc.to_dict()
                if data.get('analyzed_at') and data['analyzed_at'] >= start_date:
                    emotions.append(data)
            
            if not emotions:
                return {}
            
            # パターン分析をAIに依頼
            pattern_prompt = f"""
            以下の感情分析データからユーザーの感情パターンを抽出してください：
            
            【感情データ】
            {emotions[:10]}  # 最新10件
            
            パターン分析結果をJSONで返してください：
            {{
                "preferred_style": "好まれるコミュニケーションスタイル",
                "triggers": ["感情トリガー"],
                "comfort_topics": ["安心できる話題"],
                "stress_relievers": ["ストレス軽減方法"],
                "motivations": ["モチベーション要因"],
                "trust_methods": ["信頼構築方法"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "感情パターン分析の専門家として、深いインサイトを提供してください。"},
                    {"role": "user", "content": pattern_prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Emotion pattern analysis error: {e}")
            return {}