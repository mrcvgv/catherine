#!/usr/bin/env python3
"""
Master Communicator - Catherine AI 超高度コミュニケーション術システム
世界最高レベルの説明力・質問技術・対話マネジメント
"""

import json
import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from openai import OpenAI
import re
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CommunicationContext:
    audience_level: str          # beginner, intermediate, expert, mixed
    communication_goal: str      # inform, persuade, engage, support, teach
    emotional_state: str         # receptive, defensive, confused, excited, neutral
    time_constraints: str        # urgent, normal, relaxed, none
    relationship_stage: str      # new, developing, established, deep
    cultural_context: str        # formal, casual, business, academic, personal

@dataclass
class ExplanationStrategy:
    approach: str
    structure: List[str]
    examples_needed: int
    visual_aids: bool
    interaction_points: List[str]
    complexity_gradation: List[str]

class MasterCommunicator:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
        # 🎯 説明技術のマスターリスト
        self.explanation_techniques = {
            "layered_explanation": {
                "description": "段階的詳細化による説明",
                "structure": ["概要", "詳細1", "詳細2", "統合"],
                "use_cases": ["複雑な概念", "技術的内容", "段階的理解"]
            },
            "analogy_method": {
                "description": "類推・比喩による説明",
                "structure": ["馴染みある例", "類似点", "相違点", "応用"],
                "use_cases": ["抽象概念", "新しい技術", "理解促進"]
            },
            "story_narrative": {
                "description": "物語形式による説明",
                "structure": ["設定", "課題", "解決過程", "結論"],
                "use_cases": ["感情移入", "記憶定着", "興味喚起"]
            },
            "problem_solution": {
                "description": "問題解決型説明",
                "structure": ["問題提示", "分析", "解決策", "効果"],
                "use_cases": ["実践的内容", "課題解決", "動機付け"]
            },
            "socratic_dialogue": {
                "description": "対話型説明",
                "structure": ["質問", "思考誘導", "気づき", "確認"],
                "use_cases": ["能動的学習", "批判的思考", "深い理解"]
            }
        }
        
        # 🤔 質問技術のマスターツール
        self.questioning_techniques = {
            "clarifying_questions": {
                "purpose": "理解の明確化",
                "examples": [
                    "つまり、{}ということでしょうか？",
                    "{}について、もう少し詳しく教えていただけますか？",
                    "それは{}という意味で捉えて良いですか？"
                ]
            },
            "probing_questions": {
                "purpose": "深い探求",
                "examples": [
                    "それはなぜだと思いますか？",
                    "他にどんな可能性が考えられでしょう？",
                    "もしそうでないとしたら、どうなりますか？"
                ]
            },
            "hypothetical_questions": {
                "purpose": "思考拡張",
                "examples": [
                    "もし{}だったら、どうしますか？",
                    "理想的な状況では、何が起こるでしょう？",
                    "逆の立場だったら、どう考えますか？"
                ]
            },
            "reflective_questions": {
                "purpose": "内省促進",
                "examples": [
                    "これまでの経験から、どう感じますか？",
                    "あなたにとって最も重要なのは何ですか？",
                    "この件について、どんな感情を抱いていますか？"
                ]
            },
            "strategic_questions": {
                "purpose": "戦略的思考",
                "examples": [
                    "長期的に見ると、どんな影響がありそうですか？",
                    "この決定のリスクとメリットは何でしょう？",
                    "他のステークホルダーはどう反応するでしょう？"
                ]
            }
        }
        
        # 💬 対話マネジメント技術
        self.dialogue_management = {
            "active_listening": {
                "techniques": ["要約・確認", "感情の反映", "非言語情報の読取り"],
                "responses": ["そうおっしゃるのは", "つまりお気持ちとしては", "ということは"]
            },
            "rapport_building": {
                "techniques": ["共通点発見", "適切な自己開示", "ペーシング・マッチング"],
                "responses": ["私も同じような経験が", "それすごくわかります", "なるほど、確かに"]
            },
            "conflict_resolution": {
                "techniques": ["双方の立場理解", "共通目標の確認", "win-winソリューション"],
                "responses": ["両方の視点で見ると", "共通の目標は", "どちらにとっても良い方法は"]
            },
            "influence_persuasion": {
                "techniques": ["論理的根拠", "感情的アピール", "権威・信頼性", "社会的証明"],
                "responses": ["データから見ると", "お気持ちを考えると", "専門家によると", "多くの方が"]
            }
        }
    
    async def analyze_communication_context(self, user_input: str, conversation_history: List[Dict] = None,
                                          user_profile: Dict = None) -> CommunicationContext:
        """コミュニケーション文脈の詳細分析"""
        
        context_prompt = f"""
        以下の情報からコミュニケーション文脈を詳細に分析してください：
        
        【ユーザー入力】{user_input}
        【会話履歴】{json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)}
        【ユーザープロファイル】{json.dumps(user_profile or {}, ensure_ascii=False)}
        
        以下のJSON形式で文脈分析を返してください：
        
        {{
            "audience_level": "beginner|intermediate|expert|mixed",
            "communication_goal": "inform|persuade|engage|support|teach|explore",
            "emotional_state": "receptive|defensive|confused|excited|frustrated|curious|neutral",
            "urgency_level": "immediate|high|normal|low",
            "relationship_stage": "new|developing|established|deep",
            "formality_level": "very_formal|formal|semi_formal|casual|very_casual",
            "cultural_sensitivity": 0.0-1.0,
            "information_density": "high|medium|low",
            "interaction_preference": "dialogue|explanation|guidance|exploration",
            "attention_span": "short|medium|long|variable",
            "learning_style": "visual|auditory|kinesthetic|reading|multimodal",
            "decision_readiness": 0.0-1.0,
            "trust_level": 0.0-1.0,
            "expertise_areas": ["領域1", "領域2"],
            "communication_barriers": ["障壁1", "障壁2"],
            "optimal_approach": "推奨アプローチ"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたはコミュニケーション分析の専門家です。文脈を詳細に分析してください。"},
                    {"role": "user", "content": context_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return CommunicationContext(
                audience_level=analysis.get('audience_level', 'intermediate'),
                communication_goal=analysis.get('communication_goal', 'inform'),
                emotional_state=analysis.get('emotional_state', 'neutral'),
                time_constraints=analysis.get('urgency_level', 'normal'),
                relationship_stage=analysis.get('relationship_stage', 'developing'),
                cultural_context=analysis.get('formality_level', 'semi_formal')
            )
            
        except Exception as e:
            print(f"Communication context analysis error: {e}")
            return CommunicationContext('intermediate', 'inform', 'neutral', 'normal', 'developing', 'semi_formal')
    
    async def design_optimal_explanation(self, topic: str, context: CommunicationContext,
                                       complexity_level: int = 5) -> ExplanationStrategy:
        """最適説明戦略の設計"""
        
        # 文脈に基づく説明技術の選択
        if context.audience_level == 'beginner':
            primary_technique = 'analogy_method'
        elif context.communication_goal == 'engage':
            primary_technique = 'story_narrative'
        elif context.emotional_state in ['confused', 'frustrated']:
            primary_technique = 'layered_explanation'
        elif context.audience_level == 'expert':
            primary_technique = 'problem_solution'
        else:
            primary_technique = 'socratic_dialogue'
        
        technique_info = self.explanation_techniques[primary_technique]
        
        strategy_prompt = f"""
        以下の条件に基づいて、最適な説明戦略を設計してください：
        
        【トピック】{topic}
        【選択技術】{primary_technique}: {technique_info['description']}
        【コミュニケーション文脈】{context.__dict__}
        【複雑度】{complexity_level}/10
        
        以下のJSON形式で詳細戦略を返してください：
        
        {{
            "explanation_structure": [
                {{
                    "section": "セクション名",
                    "content_type": "概念|例示|比較|実演|質問",
                    "duration_estimate": "時間見積もり",
                    "interaction_points": ["インタラクション1", "インタラクション2"],
                    "difficulty_level": 1-10
                }}
            ],
            "examples_strategy": {{
                "analogy_examples": ["類推例1", "類推例2"],
                "concrete_examples": ["具体例1", "具体例2"],
                "counter_examples": ["反例1", "反例2"]
            }},
            "visual_aids": {{
                "diagrams_needed": ["図表1", "図表2"],
                "metaphors": ["比喩1", "比喩2"],
                "storytelling_elements": ["要素1", "要素2"]
            }},
            "interaction_design": {{
                "check_points": ["チェックポイント1", "ポイント2"],
                "questions_to_ask": ["質問1", "質問2"],
                "activities": ["活動1", "活動2"]
            }},
            "adaptation_triggers": {{
                "confusion_signals": ["混乱サイン1", "サイン2"],
                "engagement_drop": ["関心低下サイン1", "サイン2"],
                "comprehension_check": ["理解確認方法1", "方法2"]
            }}
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは説明設計の専門家です。最適で効果的な説明戦略を設計してください。"},
                    {"role": "user", "content": strategy_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            strategy_data = json.loads(response.choices[0].message.content)
            
            return ExplanationStrategy(
                approach=primary_technique,
                structure=[section.get('section', '') for section in strategy_data.get('explanation_structure', [])],
                examples_needed=len(strategy_data.get('examples_strategy', {}).get('concrete_examples', [])),
                visual_aids=len(strategy_data.get('visual_aids', {}).get('diagrams_needed', [])) > 0,
                interaction_points=strategy_data.get('interaction_design', {}).get('questions_to_ask', []),
                complexity_gradation=[str(section.get('difficulty_level', 5)) for section in strategy_data.get('explanation_structure', [])]
            )
            
        except Exception as e:
            print(f"Explanation strategy design error: {e}")
            return ExplanationStrategy('layered_explanation', ['概要', '詳細', '統合'], 2, False, ['理解度確認'], ['5'])
    
    async def generate_strategic_questions(self, topic: str, context: CommunicationContext,
                                         conversation_stage: str = 'exploration') -> List[str]:
        """戦略的質問の生成"""
        
        # 会話段階と目標に基づく質問タイプの選択
        if conversation_stage == 'exploration':
            primary_types = ['clarifying_questions', 'probing_questions']
        elif conversation_stage == 'deepening':
            primary_types = ['probing_questions', 'reflective_questions']
        elif conversation_stage == 'decision':
            primary_types = ['strategic_questions', 'hypothetical_questions']
        else:
            primary_types = ['clarifying_questions', 'strategic_questions']
        
        questions_prompt = f"""
        以下の文脈で最も効果的な質問を生成してください：
        
        【トピック】{topic}
        【コミュニケーション文脈】{context.__dict__}
        【会話段階】{conversation_stage}
        【優先質問タイプ】{primary_types}
        
        以下のカテゴリで質問を生成し、JSON形式で返してください：
        
        {{
            "opening_questions": [
                {{
                    "question": "導入質問",
                    "purpose": "目的",
                    "expected_response": "期待される応答タイプ"
                }}
            ],
            "deepening_questions": [
                {{
                    "question": "深掘り質問", 
                    "purpose": "目的",
                    "follow_up": "フォローアップ質問"
                }}
            ],
            "clarifying_questions": [
                {{
                    "question": "明確化質問",
                    "trigger": "使用タイミング",
                    "variation": "バリエーション"
                }}
            ],
            "reflective_questions": [
                {{
                    "question": "内省質問",
                    "purpose": "目的", 
                    "emotional_tone": "感情的トーン"
                }}
            ],
            "strategic_questions": [
                {{
                    "question": "戦略的質問",
                    "scope": "思考範囲",
                    "decision_support": "意思決定支援レベル"
                }}
            ],
            "closing_questions": [
                {{
                    "question": "締めくくり質問",
                    "purpose": "目的",
                    "next_action": "次のアクション"
                }}
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは質問技術のエキスパートです。効果的で戦略的な質問を生成してください。"},
                    {"role": "user", "content": questions_prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            questions_data = json.loads(response.choices[0].message.content)
            
            # 全カテゴリから質問を抽出
            all_questions = []
            for category, questions in questions_data.items():
                for q in questions:
                    all_questions.append(q.get('question', ''))
            
            return all_questions[:10]  # 上位10個の質問
            
        except Exception as e:
            print(f"Strategic questions generation error: {e}")
            return [
                f"{topic}について、どのような経験をお持ちですか？",
                f"最も重要だと思う点は何でしょうか？",
                f"理想的な結果はどのようなものでしょう？"
            ]
    
    async def apply_advanced_dialogue_management(self, user_input: str, context: CommunicationContext,
                                               dialogue_history: List[Dict] = None) -> Dict:
        """高度対話マネジメントの適用"""
        
        management_prompt = f"""
        高度な対話マネジメント技術を適用して、以下の会話を分析・最適化してください：
        
        【ユーザー入力】{user_input}
        【コミュニケーション文脈】{context.__dict__}
        【対話履歴】{json.dumps(dialogue_history[-5:] if dialogue_history else [], ensure_ascii=False)}
        
        以下のJSON形式で対話マネジメント戦略を返してください：
        
        {{
            "active_listening": {{
                "key_points_identified": ["ポイント1", "ポイント2"],
                "emotions_detected": ["感情1", "感情2"],
                "unstated_concerns": ["懸念1", "懸念2"],
                "reflection_response": "反映応答"
            }},
            "rapport_building": {{
                "connection_opportunities": ["機会1", "機会2"],
                "shared_experiences": ["共通体験1", "体験2"],
                "trust_building_actions": ["行動1", "行動2"],
                "rapport_indicators": ["指標1", "指標2"]
            }},
            "influence_strategy": {{
                "primary_approach": "logic|emotion|authority|social_proof",
                "supporting_evidence": ["根拠1", "根拠2"],
                "persuasion_sequence": ["ステップ1", "ステップ2"],
                "resistance_handling": ["対処法1", "対処法2"]
            }},
            "engagement_optimization": {{
                "attention_maintainers": ["要素1", "要素2"],
                "curiosity_generators": ["要素1", "要素2"],
                "participation_encouragers": ["方法1", "方法2"],
                "energy_level_adjustments": ["調整1", "調整2"]
            }},
            "conversation_steering": {{
                "current_direction": "現在の方向性",
                "optimal_direction": "最適な方向性",
                "transition_strategy": "転換戦略",
                "milestone_checkpoints": ["チェックポイント1", "ポイント2"]
            }}
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは対話マネジメントの専門家です。高度な技術を駆使して効果的な対話戦略を提案してください。"},
                    {"role": "user", "content": management_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Dialogue management error: {e}")
            return {"error": "Advanced dialogue management unavailable"}
    
    async def generate_master_communication_response(self, user_input: str, context: CommunicationContext,
                                                   explanation_strategy: ExplanationStrategy,
                                                   strategic_questions: List[str],
                                                   dialogue_management: Dict) -> str:
        """マスターコミュニケーター統合応答生成"""
        
        master_prompt = f"""
        世界最高レベルのコミュニケーションマスターとして、統合的な応答を生成してください：
        
        【ユーザー入力】{user_input}
        【コミュニケーション文脈】{context.__dict__}
        【説明戦略】{explanation_strategy.__dict__}
        【戦略的質問】{strategic_questions[:3]}
        【対話マネジメント】{dialogue_management}
        
        以下の要素を統合した最高品質の応答を生成：
        
        1. 【アクティブリスニング】- 深い理解と共感の表現
        2. 【最適説明】- 文脈に応じた理解しやすい説明
        3. 【戦略的質問】- 思考を深める効果的な問いかけ
        4. 【ラポート構築】- 信頼関係の強化
        5. 【エンゲージメント】- 興味と参加を促進
        6. 【影響力行使】- 適切で建設的な説得
        7. 【会話誘導】- 目標に向けた自然な流れ
        8. 【感情配慮】- 感情状態への適切な対応
        
        応答構造（必要に応じて調整）：
        
        ## 🤝 **理解と共感**
        [ユーザーの状況・感情への深い共感と理解]
        
        ## 💡 **洞察と説明**
        [最適化された説明・洞察の提供]
        
        ## 🔍 **探求の質問**
        [思考を深める戦略的質問]
        
        ## 🚀 **行動への誘導**
        [具体的で実行しやすい次のステップ]
        
        最高レベルのコミュニケーション術を駆使した応答をお願いします。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは世界最高レベルのコミュニケーションマスター Catherine AI です。全ての技術を統合した完璧な応答を生成してください。"},
                    {"role": "user", "content": master_prompt}
                ],
                temperature=0.6,
                max_completion_tokens=2500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Master communication response error: {e}")
            return self._fallback_communication_response(user_input, context)
    
    def _fallback_communication_response(self, user_input: str, context: CommunicationContext) -> str:
        """フォールバック コミュニケーション応答"""
        
        empathy_phrases = [
            "おっしゃること、本当によくわかります。",
            "そのお気持ち、すごく理解できます。", 
            "なるほど、そういう状況なんですね。"
        ]
        
        questions = [
            f"もう少し詳しく教えていただけませんか？",
            f"どのような結果を期待されていますか？",
            f"一番大切にしたい点は何でしょうか？"
        ]
        
        empathy = random.choice(empathy_phrases)
        question = random.choice(questions)
        
        return f"{empathy}\n\n{user_input}について、{question}"

# 使用例
if __name__ == "__main__":
    import os
    
    async def test_master_communication():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        communicator = MasterCommunicator(client)
        
        user_input = "プロジェクトの進捗が遅れていて、チームのモチベーションも下がっています。どうしたらいいでしょうか？"
        
        # 文脈分析
        context = await communicator.analyze_communication_context(user_input)
        print(f"コミュニケーション文脈: {context}")
        
        # 説明戦略設計  
        strategy = await communicator.design_optimal_explanation("プロジェクト管理とチーム動機付け", context, 6)
        print(f"説明戦略: {strategy.approach}")
        
        # 戦略的質問生成
        questions = await communicator.generate_strategic_questions("プロジェクト改善", context, "exploration")
        print(f"戦略的質問: {questions[:3]}")
        
        # 対話マネジメント
        dialogue_mgmt = await communicator.apply_advanced_dialogue_management(user_input, context)
        
        # 統合応答生成
        response = await communicator.generate_master_communication_response(
            user_input, context, strategy, questions, dialogue_mgmt
        )
        
        print(f"\n=== マスターコミュニケーター応答 ===")
        print(response)
    
    asyncio.run(test_master_communication())