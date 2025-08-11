#!/usr/bin/env python3
"""
Advanced Context Engine - Catherine AI 高度文脈理解システム
暗示・行間・文化的背景・長期記憶・関係性の完全理解
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass, field
from collections import defaultdict, deque
import numpy as np

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ContextLayer:
    layer_name: str
    content: Dict[str, Any]
    confidence: float
    relevance_score: float
    temporal_weight: float

@dataclass
class RelationshipDynamics:
    user_id: str
    relationship_type: str  # professional, casual, mentor, peer
    trust_level: float
    interaction_history: List[Dict]
    communication_patterns: Dict[str, Any]
    shared_context: Dict[str, Any]
    emotional_bond: float

@dataclass
class CulturalContext:
    cultural_markers: List[str]
    communication_norms: Dict[str, Any]
    social_expectations: List[str]
    taboos_sensitivities: List[str]
    context_specific_knowledge: Dict[str, Any]

@dataclass
class ImplicitMeaning:
    surface_text: str
    implicit_content: List[str]
    emotional_subtext: Dict[str, float]
    social_implications: List[str]
    intended_actions: List[str]
    confidence: float

class AdvancedContextEngine:
    def __init__(self, openai_client: OpenAI, firebase_manager):
        self.client = openai_client
        self.db = firebase_manager.get_db()
        self.context_layers = {}
        self.relationship_dynamics = {}
        self.cultural_contexts = {}
        self.long_term_memory = defaultdict(deque)
        self.context_decay_rate = 0.1  # 文脈の減衰率
        
    async def analyze_deep_context(self, user_id: str, current_input: str, 
                                 conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """深層文脈分析"""
        try:
            # 1. 多層文脈分析
            context_layers = await self._analyze_multi_layer_context(user_id, current_input, conversation_history)
            
            # 2. 暗示・行間の意味抽出
            implicit_meanings = await self._extract_implicit_meanings(current_input, context_layers)
            
            # 3. 関係性ダイナミクス分析
            relationship = await self._analyze_relationship_dynamics(user_id, current_input, conversation_history)
            
            # 4. 文化的・社会的文脈
            cultural_context = await self._analyze_cultural_context(current_input, relationship)
            
            # 5. 長期記憶・パターン認識
            long_term_patterns = await self._analyze_long_term_patterns(user_id, current_input)
            
            # 6. 文脈統合・重要度評価
            integrated_context = await self._integrate_context_layers(
                context_layers, implicit_meanings, relationship, cultural_context, long_term_patterns
            )
            
            # 7. 文脈更新・記憶
            await self._update_context_memory(user_id, integrated_context, current_input)
            
            return {
                'context_layers': context_layers,
                'implicit_meanings': implicit_meanings,
                'relationship_dynamics': relationship,
                'cultural_context': cultural_context,
                'long_term_patterns': long_term_patterns,
                'integrated_context': integrated_context,
                'context_confidence': self._calculate_context_confidence(integrated_context)
            }
            
        except Exception as e:
            print(f"❌ Deep context analysis error: {e}")
            return self._fallback_context_analysis(user_id, current_input)
    
    async def _analyze_multi_layer_context(self, user_id: str, current_input: str, 
                                         conversation_history: List[Dict] = None) -> List[ContextLayer]:
        """多層文脈分析"""
        layers_prompt = f"""
以下のメッセージを多層的に分析してください：

現在の入力: "{current_input}"
会話履歴: {json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)}

以下の7つの層で分析し、JSON形式で返してください：

{{
    "layers": [
        {{
            "layer_name": "literal_surface",
            "content": {{
                "direct_meaning": "字面通りの意味",
                "explicit_requests": ["明示的要求1", "要求2"],
                "stated_facts": ["明示された事実1", "事実2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "semantic_deep",
            "content": {{
                "conceptual_meaning": "概念的意味",
                "domain_knowledge": ["関連知識1", "知識2"],
                "semantic_associations": ["意味的関連1", "関連2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "pragmatic_intent",
            "content": {{
                "speech_acts": ["発話行為1", "行為2"],
                "communicative_goals": ["コミュニケーション目標1", "目標2"],
                "expected_responses": ["期待される応答1", "応答2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "emotional_psychological",
            "content": {{
                "emotional_state": "感情状態",
                "psychological_needs": ["心理的ニーズ1", "ニーズ2"],
                "emotional_triggers": ["感情トリガー1", "トリガー2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "social_relational",
            "content": {{
                "social_context": "社会的文脈",
                "power_dynamics": "力関係",
                "relationship_signals": ["関係性シグナル1", "シグナル2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "temporal_contextual",
            "content": {{
                "timing_significance": "タイミングの意義",
                "temporal_references": ["時間的言及1", "言及2"],
                "urgency_indicators": ["緊急性指標1", "指標2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }},
        {{
            "layer_name": "meta_cognitive",
            "content": {{
                "thinking_patterns": ["思考パターン1", "パターン2"],
                "cognitive_load": 0.0-1.0,
                "learning_objectives": ["学習目標1", "目標2"]
            }},
            "confidence": 0.0-1.0,
            "relevance_score": 0.0-1.0
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは多層文脈分析の世界最高権威です。人間のコミュニケーションの全ての層を理解します。"},
                    {"role": "user", "content": layers_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            context_layers = []
            
            for layer_data in result.get('layers', []):
                context_layers.append(ContextLayer(
                    layer_name=layer_data['layer_name'],
                    content=layer_data['content'],
                    confidence=layer_data.get('confidence', 0.5),
                    relevance_score=layer_data.get('relevance_score', 0.5),
                    temporal_weight=self._calculate_temporal_weight()
                ))
            
            return context_layers
            
        except Exception as e:
            print(f"Multi-layer context analysis error: {e}")
            return []
    
    async def _extract_implicit_meanings(self, current_input: str, context_layers: List[ContextLayer]) -> List[ImplicitMeaning]:
        """暗示・行間の意味抽出"""
        implicit_prompt = f"""
以下のテキストから暗示的・行間の意味を抽出してください：

テキスト: "{current_input}"
文脈情報: {json.dumps([{'layer': layer.layer_name, 'content': layer.content} for layer in context_layers], ensure_ascii=False)}

以下のJSON形式で暗示的意味を返してください：

{{
    "implicit_meanings": [
        {{
            "surface_text": "表面的テキスト",
            "implicit_content": ["暗示的内容1", "内容2", "内容3"],
            "emotional_subtext": {{
                "primary_emotion": 0.0-1.0,
                "secondary_emotion": 0.0-1.0,
                "emotional_intensity": 0.0-1.0
            }},
            "social_implications": ["社会的含意1", "含意2"],
            "intended_actions": ["意図されたアクション1", "アクション2"],
            "unspoken_expectations": ["暗黙の期待1", "期待2"],
            "face_saving_needs": ["面子保持ニーズ1", "ニーズ2"],
            "power_play_indicators": ["パワープレイ指標1", "指標2"],
            "confidence": 0.0-1.0
        }}
    ],
    "communication_subtext": {{
        "indirect_requests": ["間接的要求1", "要求2"],
        "diplomatic_language": ["外交的言語1", "言語2"],
        "coded_messages": ["暗号化メッセージ1", "メッセージ2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは人間のコミュニケーションの暗示・行間・サブテキストを完璧に理解する専門家です。"},
                    {"role": "user", "content": implicit_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            implicit_meanings = []
            
            for meaning_data in result.get('implicit_meanings', []):
                implicit_meanings.append(ImplicitMeaning(
                    surface_text=meaning_data.get('surface_text', current_input),
                    implicit_content=meaning_data.get('implicit_content', []),
                    emotional_subtext=meaning_data.get('emotional_subtext', {}),
                    social_implications=meaning_data.get('social_implications', []),
                    intended_actions=meaning_data.get('intended_actions', []),
                    confidence=meaning_data.get('confidence', 0.5)
                ))
            
            return implicit_meanings
            
        except Exception as e:
            print(f"Implicit meaning extraction error: {e}")
            return []
    
    async def _analyze_relationship_dynamics(self, user_id: str, current_input: str, 
                                           conversation_history: List[Dict] = None) -> RelationshipDynamics:
        """関係性ダイナミクス分析"""
        # 既存の関係性データ取得
        existing_relationship = self.relationship_dynamics.get(user_id)
        
        relationship_prompt = f"""
以下の情報から関係性ダイナミクスを分析してください：

現在の入力: "{current_input}"
会話履歴: {json.dumps(conversation_history[-5:] if conversation_history else [], ensure_ascii=False)}
既存の関係性: {json.dumps(existing_relationship.__dict__ if existing_relationship else {}, ensure_ascii=False, default=str)}

JSON形式で関係性分析を返してください：

{{
    "relationship_analysis": {{
        "relationship_type": "professional|casual|mentor|peer|friend|formal",
        "trust_level": 0.0-1.0,
        "formality_level": 0.0-1.0,
        "emotional_closeness": 0.0-1.0,
        "power_balance": "equal|user_higher|ai_higher|neutral",
        "communication_comfort": 0.0-1.0
    }},
    "interaction_patterns": {{
        "preferred_communication_style": "direct|indirect|supportive|analytical",
        "response_expectations": ["期待1", "期待2"],
        "boundary_preferences": ["境界1", "境界2"],
        "topics_of_interest": ["関心トピック1", "トピック2"]
    }},
    "shared_context": {{
        "common_references": ["共通参照1", "参照2"],
        "inside_jokes": ["内輪ジョーク1", "ジョーク2"],
        "shared_experiences": ["共有体験1", "体験2"],
        "ongoing_projects": ["進行プロジェクト1", "プロジェクト2"]
    }},
    "evolution_indicators": {{
        "relationship_trajectory": "strengthening|stable|weakening",
        "trust_changes": "increasing|stable|decreasing",
        "intimacy_changes": "closer|stable|more_distant"
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは人間関係とコミュニケーションダイナミクスの専門家です。"},
                    {"role": "user", "content": relationship_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            analysis = result.get('relationship_analysis', {})
            
            # 既存の関係性を更新
            if existing_relationship:
                # 段階的更新
                learning_rate = 0.2
                existing_relationship.trust_level = (existing_relationship.trust_level * (1 - learning_rate) + 
                                                   analysis.get('trust_level', 0.5) * learning_rate)
                existing_relationship.emotional_bond = (existing_relationship.emotional_bond * (1 - learning_rate) + 
                                                      analysis.get('emotional_closeness', 0.5) * learning_rate)
                return existing_relationship
            else:
                # 新規関係性作成
                new_relationship = RelationshipDynamics(
                    user_id=user_id,
                    relationship_type=analysis.get('relationship_type', 'casual'),
                    trust_level=analysis.get('trust_level', 0.5),
                    interaction_history=[],
                    communication_patterns=result.get('interaction_patterns', {}),
                    shared_context=result.get('shared_context', {}),
                    emotional_bond=analysis.get('emotional_closeness', 0.3)
                )
                self.relationship_dynamics[user_id] = new_relationship
                return new_relationship
            
        except Exception as e:
            print(f"Relationship dynamics analysis error: {e}")
            return RelationshipDynamics(
                user_id=user_id,
                relationship_type='casual',
                trust_level=0.5,
                interaction_history=[],
                communication_patterns={},
                shared_context={},
                emotional_bond=0.3
            )
    
    async def _analyze_cultural_context(self, current_input: str, relationship: RelationshipDynamics) -> CulturalContext:
        """文化的・社会的文脈分析"""
        cultural_prompt = f"""
以下のテキストから文化的・社会的文脈を分析してください：

テキスト: "{current_input}"
関係性タイプ: {relationship.relationship_type}
信頼レベル: {relationship.trust_level}

JSON形式で文化的文脈を返してください：

{{
    "cultural_analysis": {{
        "cultural_markers": ["文化的マーカー1", "マーカー2"],
        "language_formality": "very_formal|formal|neutral|casual|very_casual",
        "social_norms": ["社会規範1", "規範2"],
        "communication_style": "high_context|low_context|mixed",
        "cultural_values": ["価値観1", "価値観2"]
    }},
    "communication_norms": {{
        "directness_expectation": 0.0-1.0,
        "hierarchy_awareness": 0.0-1.0,
        "face_saving_importance": 0.0-1.0,
        "group_vs_individual": 0.0-1.0
    }},
    "social_expectations": ["社会的期待1", "期待2", "期待3"],
    "taboos_sensitivities": ["タブー1", "センシティブ話題1"],
    "context_specific_knowledge": {{
        "domain_expertise": ["専門分野1", "分野2"],
        "cultural_references": ["文化的参照1", "参照2"],
        "generational_markers": ["世代マーカー1", "マーカー2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは文化人類学と異文化コミュニケーションの専門家です。"},
                    {"role": "user", "content": cultural_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            analysis = result.get('cultural_analysis', {})
            
            return CulturalContext(
                cultural_markers=analysis.get('cultural_markers', []),
                communication_norms=result.get('communication_norms', {}),
                social_expectations=result.get('social_expectations', []),
                taboos_sensitivities=result.get('taboos_sensitivities', []),
                context_specific_knowledge=result.get('context_specific_knowledge', {})
            )
            
        except Exception as e:
            print(f"Cultural context analysis error: {e}")
            return CulturalContext([], {}, [], [], {})
    
    async def _analyze_long_term_patterns(self, user_id: str, current_input: str) -> Dict[str, Any]:
        """長期パターン・記憶分析"""
        # 長期記憶から関連パターンを取得
        memory_data = list(self.long_term_memory[user_id])
        
        if not memory_data:
            return {'patterns': [], 'insights': [], 'predictions': []}
        
        pattern_prompt = f"""
以下の長期記憶データから現在の入力に関連するパターンを分析してください：

現在の入力: "{current_input}"
長期記憶: {json.dumps(memory_data[-10:], ensure_ascii=False, default=str)}

JSON形式でパターン分析を返してください：

{{
    "behavioral_patterns": [
        {{
            "pattern_type": "communication|preference|cognitive|temporal",
            "pattern_description": "パターンの説明",
            "frequency": 1-10,
            "confidence": 0.0-1.0,
            "trend": "increasing|stable|decreasing"
        }}
    ],
    "recurring_themes": ["テーマ1", "テーマ2", "テーマ3"],
    "preference_evolution": {{
        "past_preferences": ["過去の好み1", "好み2"],
        "current_preferences": ["現在の好み1", "好み2"],
        "predicted_preferences": ["予想される好み1", "好み2"]
    }},
    "interaction_insights": [
        {{
            "insight": "インサイト",
            "supporting_evidence": ["証拠1", "証拠2"],
            "implications": ["含意1", "含意2"]
        }}
    ],
    "predictive_indicators": ["予測指標1", "指標2", "指標3"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは長期的行動パターンと予測分析の専門家です。"},
                    {"role": "user", "content": pattern_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Long-term pattern analysis error: {e}")
            return {'patterns': [], 'insights': [], 'predictions': []}
    
    async def _integrate_context_layers(self, context_layers: List[ContextLayer], 
                                      implicit_meanings: List[ImplicitMeaning],
                                      relationship: RelationshipDynamics,
                                      cultural_context: CulturalContext,
                                      long_term_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """文脈レイヤーの統合"""
        integration_prompt = f"""
以下の多層文脈情報を統合して、最適な理解と応答戦略を生成してください：

文脈レイヤー: {json.dumps([{'layer': layer.layer_name, 'content': layer.content, 'confidence': layer.confidence} for layer in context_layers], ensure_ascii=False)}
暗示的意味: {json.dumps([{'implicit': meaning.implicit_content, 'emotions': meaning.emotional_subtext} for meaning in implicit_meanings], ensure_ascii=False)}
関係性: {json.dumps({'type': relationship.relationship_type, 'trust': relationship.trust_level, 'patterns': relationship.communication_patterns}, ensure_ascii=False)}
文化的文脈: {json.dumps({'markers': cultural_context.cultural_markers, 'norms': cultural_context.communication_norms}, ensure_ascii=False)}
長期パターン: {json.dumps(long_term_patterns, ensure_ascii=False)}

以下のJSON形式で統合結果を返してください：

{{
    "integrated_understanding": {{
        "primary_interpretation": "主要解釈",
        "alternative_interpretations": ["代替解釈1", "解釈2"],
        "confidence_level": 0.0-1.0,
        "ambiguity_areas": ["曖昧な領域1", "領域2"]
    }},
    "response_strategy": {{
        "optimal_approach": "最適なアプローチ",
        "tone_recommendation": "推奨トーン",
        "content_focus": ["コンテンツ焦点1", "焦点2"],
        "interaction_style": "インタラクションスタイル",
        "personalization_elements": ["個人化要素1", "要素2"]
    }},
    "risk_mitigation": {{
        "potential_misunderstandings": ["誤解の可能性1", "可能性2"],
        "cultural_sensitivities": ["文化的配慮1", "配慮2"],
        "relationship_risks": ["関係リスク1", "リスク2"],
        "mitigation_strategies": ["軽減戦略1", "戦略2"]
    }},
    "success_predictors": {{
        "key_success_factors": ["成功要因1", "要因2"],
        "expected_outcomes": ["期待される結果1", "結果2"],
        "success_probability": 0.0-1.0
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは複雑な文脈情報を統合して最適な理解と戦略を生成する専門家です。"},
                    {"role": "user", "content": integration_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Context integration error: {e}")
            return {
                'integrated_understanding': {'primary_interpretation': 'Basic understanding', 'confidence_level': 0.5},
                'response_strategy': {'optimal_approach': 'balanced', 'tone_recommendation': 'friendly'},
                'risk_mitigation': {},
                'success_predictors': {}
            }
    
    async def _update_context_memory(self, user_id: str, integrated_context: Dict[str, Any], current_input: str):
        """文脈記憶の更新"""
        memory_entry = {
            'input': current_input,
            'timestamp': datetime.now(JST),
            'context_summary': integrated_context.get('integrated_understanding', {}),
            'relationship_state': self.relationship_dynamics.get(user_id, {}).__dict__ if user_id in self.relationship_dynamics else {},
            'success_prediction': integrated_context.get('success_predictors', {}).get('success_probability', 0.5)
        }
        
        # 長期記憶に追加
        self.long_term_memory[user_id].append(memory_entry)
        
        # メモリサイズ制限（最新100件保持）
        if len(self.long_term_memory[user_id]) > 100:
            self.long_term_memory[user_id].popleft()
        
        # データベース永続化
        try:
            doc_ref = self.db.collection('context_memory').document(user_id)
            doc_ref.set({
                'memory_entries': [
                    {
                        'input': entry['input'],
                        'timestamp': entry['timestamp'].isoformat(),
                        'context_summary': entry['context_summary'],
                        'success_prediction': entry['success_prediction']
                    }
                    for entry in list(self.long_term_memory[user_id])[-20:]  # 最新20件のみ保存
                ],
                'last_updated': datetime.now(JST).isoformat()
            })
        except Exception as e:
            print(f"Context memory persistence error: {e}")
    
    def _calculate_temporal_weight(self) -> float:
        """時間的重み計算"""
        return 1.0  # 現在は固定、将来的に時間減衰を実装
    
    def _calculate_context_confidence(self, integrated_context: Dict[str, Any]) -> float:
        """文脈信頼度計算"""
        understanding = integrated_context.get('integrated_understanding', {})
        return understanding.get('confidence_level', 0.5)
    
    def _fallback_context_analysis(self, user_id: str, current_input: str) -> Dict[str, Any]:
        """フォールバック文脈分析"""
        return {
            'context_layers': [],
            'implicit_meanings': [],
            'relationship_dynamics': RelationshipDynamics(
                user_id=user_id, relationship_type='casual', trust_level=0.5,
                interaction_history=[], communication_patterns={},
                shared_context={}, emotional_bond=0.3
            ),
            'cultural_context': CulturalContext([], {}, [], [], {}),
            'long_term_patterns': {},
            'integrated_context': {
                'integrated_understanding': {'primary_interpretation': current_input, 'confidence_level': 0.3},
                'response_strategy': {'optimal_approach': 'balanced'}
            },
            'context_confidence': 0.3
        }

# 使用例
if __name__ == "__main__":
    import os
    from firebase_config import firebase_manager
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    engine = AdvancedContextEngine(client, firebase_manager)
    
    async def test():
        result = await engine.analyze_deep_context(
            user_id="test_user",
            current_input="最近、チームとのコミュニケーションがうまくいかなくて...",
            conversation_history=[]
        )
        print(f"Context Analysis: {result['context_confidence']}")
        print(f"Primary Interpretation: {result['integrated_context']['integrated_understanding']['primary_interpretation']}")
    
    asyncio.run(test())