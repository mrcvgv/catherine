#!/usr/bin/env python3
"""
Dynamic Learning System - Catherine AI 動的学習システム
リアルタイム適応・パターン学習・自己改善
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class InteractionPattern:
    user_id: str
    pattern_type: str
    frequency: int
    success_rate: float
    context: Dict
    timestamp: datetime
    confidence: float

@dataclass 
class LearningInsight:
    insight_type: str
    description: str
    evidence: List[str]
    actionable_recommendations: List[str]
    confidence: float
    impact_score: float

@dataclass
class PersonalityProfile:
    user_id: str
    traits: Dict[str, float]  # Big Five + custom traits
    preferences: Dict[str, Any]
    communication_style: str
    emotional_patterns: Dict[str, float]
    cognitive_style: str
    interaction_history: List[Dict]
    last_updated: datetime

class DynamicLearningSystem:
    def __init__(self, openai_client: OpenAI, firebase_manager):
        self.client = openai_client
        self.db = firebase_manager.get_db()
        self.interaction_patterns = defaultdict(list)
        self.personality_profiles = {}
        self.learning_insights = []
        self.adaptation_rules = {}
        
    async def learn_from_interaction(self, user_id: str, user_input: str, 
                                   bot_response: str, user_reaction: Optional[str] = None,
                                   success_metrics: Dict = None) -> Dict:
        """インタラクションからの動的学習"""
        try:
            # 1. インタラクションパターン抽出
            patterns = await self._extract_interaction_patterns(user_id, user_input, bot_response, user_reaction)
            
            # 2. 成功度評価
            success_score = await self._evaluate_interaction_success(user_input, bot_response, user_reaction, success_metrics)
            
            # 3. パーソナリティプロファイル更新
            await self._update_personality_profile(user_id, user_input, bot_response, success_score)
            
            # 4. 学習インサイト生成
            insights = await self._generate_learning_insights(user_id, patterns, success_score)
            
            # 5. 適応ルール更新
            await self._update_adaptation_rules(user_id, insights, success_score)
            
            # 6. データ永続化
            await self._persist_learning_data(user_id, patterns, insights)
            
            return {
                'patterns_learned': len(patterns),
                'success_score': success_score,
                'insights_generated': len(insights),
                'profile_updated': True,
                'adaptation_level': self._calculate_adaptation_level(user_id)
            }
            
        except Exception as e:
            print(f"❌ Dynamic learning error: {e}")
            return {'error': str(e), 'patterns_learned': 0}
    
    async def _extract_interaction_patterns(self, user_id: str, user_input: str, 
                                          bot_response: str, user_reaction: Optional[str]) -> List[InteractionPattern]:
        """インタラクションパターンの抽出"""
        prompt = f"""
以下のインタラクションから学習可能なパターンを抽出してください：

ユーザー入力: "{user_input}"
ボット応答: "{bot_response}"
ユーザー反応: "{user_reaction or '不明'}"

以下のJSON形式でパターンを返してください：

{{
    "patterns": [
        {{
            "pattern_type": "communication_style|content_preference|emotional_response|task_approach",
            "pattern_description": "パターンの説明",
            "triggers": ["トリガー1", "トリガー2"],
            "preferences": ["好み1", "好み2"],
            "success_indicators": ["成功指標1", "指標2"],
            "failure_indicators": ["失敗指標1", "指標2"],
            "confidence": 0.0-1.0,
            "generalizability": 0.0-1.0,
            "actionable_insights": ["洞察1", "洞察2"]
        }}
    ],
    "meta_patterns": [
        {{
            "pattern": "メタパターン",
            "evidence": ["証拠1", "証拠2"],
            "implications": ["含意1", "含意2"]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは人間行動とコミュニケーションパターンの分析専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            patterns = []
            
            for p in result.get('patterns', []):
                patterns.append(InteractionPattern(
                    user_id=user_id,
                    pattern_type=p.get('pattern_type', 'general'),
                    frequency=1,  # 初回は1
                    success_rate=p.get('confidence', 0.5),
                    context={
                        'triggers': p.get('triggers', []),
                        'preferences': p.get('preferences', []),
                        'insights': p.get('actionable_insights', [])
                    },
                    timestamp=datetime.now(JST),
                    confidence=p.get('confidence', 0.5)
                ))
            
            return patterns
            
        except Exception as e:
            print(f"Pattern extraction error: {e}")
            return []
    
    async def _evaluate_interaction_success(self, user_input: str, bot_response: str, 
                                          user_reaction: Optional[str], metrics: Dict = None) -> float:
        """インタラクション成功度の評価"""
        prompt = f"""
以下のインタラクションの成功度を0.0-1.0で評価してください：

ユーザー入力: "{user_input}"
ボット応答: "{bot_response}"
ユーザー反応: "{user_reaction or '反応なし'}"
追加メトリクス: {json.dumps(metrics or {}, ensure_ascii=False)}

評価基準：
- 応答の適切性・関連性
- ユーザーのニーズ満足度
- 会話の自然さ・流れ
- 実用的価値の提供
- 感情的満足度
- 問題解決度

JSON形式で詳細な評価を返してください：

{{
    "overall_success_score": 0.0-1.0,
    "dimension_scores": {{
        "relevance": 0.0-1.0,
        "satisfaction": 0.0-1.0,
        "naturalness": 0.0-1.0,
        "utility": 0.0-1.0,
        "emotional_resonance": 0.0-1.0,
        "problem_solving": 0.0-1.0
    }},
    "success_indicators": ["指標1", "指標2"],
    "improvement_areas": ["改善点1", "改善点2"],
    "user_sentiment": "positive|neutral|negative",
    "engagement_level": 0.0-1.0,
    "learning_value": 0.0-1.0
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはAIインタラクションの品質評価専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_completion_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('overall_success_score', 0.5)
            
        except Exception as e:
            print(f"Success evaluation error: {e}")
            return 0.5
    
    async def _update_personality_profile(self, user_id: str, user_input: str, 
                                        bot_response: str, success_score: float):
        """パーソナリティプロファイルの更新"""
        if user_id not in self.personality_profiles:
            self.personality_profiles[user_id] = PersonalityProfile(
                user_id=user_id,
                traits={
                    'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5,
                    'agreeableness': 0.5, 'neuroticism': 0.5,
                    'analytical_thinking': 0.5, 'creativity': 0.5, 'pragmatism': 0.5
                },
                preferences={},
                communication_style='balanced',
                emotional_patterns={},
                cognitive_style='balanced',
                interaction_history=[],
                last_updated=datetime.now(JST)
            )
        
        profile = self.personality_profiles[user_id]
        
        # AI分析による特性更新
        analysis_prompt = f"""
以下のインタラクションからユーザーの性格特性を分析してください：

ユーザー入力: "{user_input}"
成功スコア: {success_score}
現在の特性: {json.dumps(profile.traits, ensure_ascii=False)}

更新された特性をJSON形式で返してください：

{{
    "updated_traits": {{
        "openness": 0.0-1.0,
        "conscientiousness": 0.0-1.0,
        "extraversion": 0.0-1.0,
        "agreeableness": 0.0-1.0,
        "neuroticism": 0.0-1.0,
        "analytical_thinking": 0.0-1.0,
        "creativity": 0.0-1.0,
        "pragmatism": 0.0-1.0
    }},
    "communication_style": "formal|casual|technical|emotional|balanced",
    "cognitive_style": "analytical|intuitive|creative|practical|balanced",
    "preferences": {{
        "response_length": "short|medium|long",
        "detail_level": "summary|balanced|detailed",
        "tone": "professional|friendly|enthusiastic|calm"
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは心理学・性格分析の専門家です。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 特性の段階的更新（急激な変化を避ける）
            learning_rate = 0.1
            for trait, new_value in result.get('updated_traits', {}).items():
                if trait in profile.traits:
                    profile.traits[trait] = profile.traits[trait] * (1 - learning_rate) + new_value * learning_rate
            
            # その他の特性更新
            if result.get('communication_style'):
                profile.communication_style = result['communication_style']
            if result.get('cognitive_style'):
                profile.cognitive_style = result['cognitive_style']
            if result.get('preferences'):
                profile.preferences.update(result['preferences'])
            
            profile.last_updated = datetime.now(JST)
            
            # インタラクション履歴追加
            profile.interaction_history.append({
                'input': user_input[:100],  # 最初の100文字
                'success_score': success_score,
                'timestamp': datetime.now(JST).isoformat(),
                'traits_snapshot': profile.traits.copy()
            })
            
            # 履歴のサイズ制限
            if len(profile.interaction_history) > 50:
                profile.interaction_history = profile.interaction_history[-50:]
            
        except Exception as e:
            print(f"Personality profile update error: {e}")
    
    async def _generate_learning_insights(self, user_id: str, patterns: List[InteractionPattern], 
                                        success_score: float) -> List[LearningInsight]:
        """学習インサイトの生成"""
        profile = self.personality_profiles.get(user_id)
        if not profile:
            return []
        
        insight_prompt = f"""
以下の情報から実用的な学習インサイトを生成してください：

パーソナリティプロファイル: {json.dumps(profile.traits, ensure_ascii=False)}
インタラクションパターン: {[p.pattern_type for p in patterns]}
最新成功スコア: {success_score}
コミュニケーションスタイル: {profile.communication_style}

以下のJSON形式でインサイトを返してください：

{{
    "insights": [
        {{
            "insight_type": "communication|personalization|content|timing",
            "description": "インサイトの説明",
            "evidence": ["証拠1", "証拠2"],
            "actionable_recommendations": ["推奨アクション1", "アクション2"],
            "confidence": 0.0-1.0,
            "impact_score": 0.0-1.0,
            "implementation_priority": "high|medium|low"
        }}
    ],
    "meta_insights": [
        {{
            "insight": "メタレベルのインサイト",
            "strategic_implications": ["戦略的含意1", "含意2"]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはAI学習とパーソナライゼーションの専門家です。"},
                    {"role": "user", "content": insight_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            insights = []
            
            for insight_data in result.get('insights', []):
                insights.append(LearningInsight(
                    insight_type=insight_data.get('insight_type', 'general'),
                    description=insight_data.get('description', ''),
                    evidence=insight_data.get('evidence', []),
                    actionable_recommendations=insight_data.get('actionable_recommendations', []),
                    confidence=insight_data.get('confidence', 0.5),
                    impact_score=insight_data.get('impact_score', 0.5)
                ))
            
            return insights
            
        except Exception as e:
            print(f"Insight generation error: {e}")
            return []
    
    async def _update_adaptation_rules(self, user_id: str, insights: List[LearningInsight], success_score: float):
        """適応ルールの更新"""
        if user_id not in self.adaptation_rules:
            self.adaptation_rules[user_id] = {
                'response_style': 'balanced',
                'content_depth': 'medium',
                'interaction_frequency': 'normal',
                'personalization_level': 'medium',
                'learning_rate': 0.1
            }
        
        rules = self.adaptation_rules[user_id]
        
        # 成功スコアに基づく学習率調整
        if success_score > 0.8:
            rules['learning_rate'] *= 0.9  # 成功時は変化を控えめに
        elif success_score < 0.4:
            rules['learning_rate'] *= 1.2  # 失敗時は積極的に学習
        
        # インサイトに基づくルール更新
        for insight in insights:
            if insight.impact_score > 0.7:
                for recommendation in insight.actionable_recommendations:
                    if 'formal' in recommendation.lower():
                        rules['response_style'] = 'formal'
                    elif 'casual' in recommendation.lower():
                        rules['response_style'] = 'casual'
                    elif 'detailed' in recommendation.lower():
                        rules['content_depth'] = 'high'
                    elif 'concise' in recommendation.lower():
                        rules['content_depth'] = 'low'
        
        # ルールの永続化
        try:
            doc_ref = self.db.collection('adaptation_rules').document(user_id)
            doc_ref.set({
                'rules': rules,
                'last_updated': datetime.now(JST).isoformat(),
                'success_score': success_score
            })
        except Exception as e:
            print(f"Rules persistence error: {e}")
    
    async def _persist_learning_data(self, user_id: str, patterns: List[InteractionPattern], insights: List[LearningInsight]):
        """学習データの永続化"""
        try:
            # パターンデータ保存
            patterns_data = []
            for pattern in patterns:
                patterns_data.append({
                    'pattern_type': pattern.pattern_type,
                    'frequency': pattern.frequency,
                    'success_rate': pattern.success_rate,
                    'context': pattern.context,
                    'timestamp': pattern.timestamp.isoformat(),
                    'confidence': pattern.confidence
                })
            
            # インサイトデータ保存
            insights_data = []
            for insight in insights:
                insights_data.append({
                    'insight_type': insight.insight_type,
                    'description': insight.description,
                    'evidence': insight.evidence,
                    'recommendations': insight.actionable_recommendations,
                    'confidence': insight.confidence,
                    'impact_score': insight.impact_score
                })
            
            # Firestore保存
            doc_ref = self.db.collection('learning_data').document(user_id)
            doc_ref.set({
                'patterns': patterns_data,
                'insights': insights_data,
                'personality_profile': {
                    'traits': self.personality_profiles.get(user_id, {}).traits if user_id in self.personality_profiles else {},
                    'communication_style': self.personality_profiles.get(user_id, {}).communication_style if user_id in self.personality_profiles else 'balanced',
                    'last_updated': datetime.now(JST).isoformat()
                },
                'timestamp': datetime.now(JST).isoformat()
            }, merge=True)
            
        except Exception as e:
            print(f"Learning data persistence error: {e}")
    
    def _calculate_adaptation_level(self, user_id: str) -> float:
        """適応レベルの計算"""
        if user_id not in self.personality_profiles:
            return 0.0
        
        profile = self.personality_profiles[user_id]
        interaction_count = len(profile.interaction_history)
        
        # インタラクション数、成功率、特性の確信度に基づく計算
        base_level = min(interaction_count / 20.0, 1.0)  # 20回で最大
        
        if interaction_count > 0:
            avg_success = np.mean([h['success_score'] for h in profile.interaction_history])
            success_factor = avg_success
        else:
            success_factor = 0.5
        
        return base_level * success_factor
    
    async def get_adaptive_response_strategy(self, user_id: str, query: str) -> Dict:
        """適応的応答戦略の取得"""
        profile = self.personality_profiles.get(user_id)
        rules = self.adaptation_rules.get(user_id, {})
        
        if not profile:
            return {'strategy': 'default', 'confidence': 0.3}
        
        strategy_prompt = f"""
以下のユーザー情報に基づいて最適な応答戦略を提案してください：

クエリ: "{query}"
パーソナリティ特性: {json.dumps(profile.traits, ensure_ascii=False)}
コミュニケーションスタイル: {profile.communication_style}
適応ルール: {json.dumps(rules, ensure_ascii=False)}

JSON形式で戦略を返してください：

{{
    "response_strategy": {{
        "tone": "professional|friendly|enthusiastic|calm",
        "length": "short|medium|long",
        "detail_level": "summary|balanced|comprehensive",
        "interaction_style": "direct|supportive|collaborative|analytical",
        "personalization_elements": ["要素1", "要素2"]
    }},
    "confidence": 0.0-1.0,
    "rationale": "戦略の根拠",
    "expected_effectiveness": 0.0-1.0
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは個人適応型コミュニケーション戦略の専門家です。"},
                    {"role": "user", "content": strategy_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Adaptive strategy error: {e}")
            return {'strategy': 'default', 'confidence': 0.3}

# 使用例
if __name__ == "__main__":
    import os
    from firebase_config import firebase_manager
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system = DynamicLearningSystem(client, firebase_manager)
    
    async def test():
        result = await system.learn_from_interaction(
            user_id="test_user",
            user_input="プロジェクト管理について教えて",
            bot_response="プロジェクト管理の基本原則をご説明します...",
            user_reaction="とても参考になりました"
        )
        print(f"Learning Result: {result}")
    
    asyncio.run(test())