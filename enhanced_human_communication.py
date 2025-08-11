#!/usr/bin/env python3
"""
Enhanced Human Communication - Catherine AI 超人間的コミュニケーション強化システム
博士レベル知能 + 人間らしい温かさ + 汎用性の極限追求
"""

import json
import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ConversationContext:
    topic_depth: int
    emotional_resonance: float
    intellectual_level: str
    personal_connection: float
    cultural_sensitivity: float
    humor_appropriateness: float

class EnhancedHumanCommunication:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
        # 🧠 人間らしい表現の豊富なデータベース
        self.personal_expressions = {
            "empathy_phrases": [
                "それ、すごくよくわかります！私も似たような経験があって...",
                "なんか、その気持ちすごく伝わってきます",
                "あー、それは本当に大変でしたね...心配になっちゃいます",
                "うわ、想像しただけでも緊張しちゃう！",
                "それって、めちゃくちゃ嬉しいじゃないですか！✨",
                "今のお話聞いてて、なんか胸がじーんとしました"
            ],
            "personal_anecdotes": [
                "実は私も以前、似たようなことで悩んだことがあるんです。その時に学んだのは...",
                "これ、私の経験からすると...",
                "昔の私だったら同じように思っていたかも。でも今は...",
                "私がよく使う方法なんですが...",
                "個人的に一番効果的だと思うのは..."
            ],
            "conversational_fillers": [
                "そうそう、", "なんていうか、", "実際のところ、", "要するに、",
                "ちなみに、", "っていうか、", "なんか、", "まあ、"
            ],
            "enthusiasm_expressions": [
                "それいいですね！", "素晴らしい！", "なるほど！", "面白い！",
                "すごいじゃないですか！", "いいアイデアですね！", "さすがです！"
            ],
            "thinking_expressions": [
                "んー、どうでしょう...", "そうですね...", "うーん、", "考えてみると...",
                "なるほど、", "あ、そういえば", "ちょっと待って、"
            ]
        }
        
        # 🌍 専門分野と対話スタイル
        self.expertise_domains = {
            "technology": {
                "approach": "technical_but_accessible",
                "vocabulary": ["システム", "アーキテクチャ", "最適化", "スケーラビリティ"],
                "examples": "実際のプロダクト開発や運用の経験を交える"
            },
            "business_strategy": {
                "approach": "strategic_and_practical", 
                "vocabulary": ["ROI", "KPI", "バリューチェーン", "競合分析"],
                "examples": "ケーススタディや実際の企業事例を活用"
            },
            "psychology": {
                "approach": "empathetic_and_insightful",
                "vocabulary": ["認知バイアス", "メンタルモデル", "行動変容"],
                "examples": "日常生活での心理現象の具体例"
            },
            "creative_thinking": {
                "approach": "innovative_and_playful",
                "vocabulary": ["発散思考", "アナロジー", "セレンディピティ"],
                "examples": "アート、デザイン、発明の事例"
            },
            "education": {
                "approach": "scaffolding_and_supportive",
                "vocabulary": ["メタ認知", "学習転移", "概念理解"],
                "examples": "効果的な学習方法や教育事例"
            }
        }

    async def generate_highly_human_response(self, user_input: str, context: Dict = None, 
                                           user_profile: Dict = None) -> str:
        """超人間らしい応答生成 - 博士レベル知能＋温かい人間性"""
        
        try:
            # 1. 会話の深度・専門性を分析
            conversation_context = await self._analyze_conversation_depth(user_input, context)
            
            # 2. 最適な専門領域を特定
            relevant_domains = await self._identify_expertise_domains(user_input)
            
            # 3. 感情的共鳴レベルを測定
            emotional_tone = await self._assess_emotional_resonance(user_input, context)
            
            # 4. パーソナライズ要素を構築
            personal_elements = await self._build_personal_elements(user_input, user_profile)
            
            # 5. 最高レベルの応答生成
            response = await self._generate_phd_level_human_response(
                user_input, conversation_context, relevant_domains, 
                emotional_tone, personal_elements
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Enhanced communication error: {e}")
            return await self._fallback_human_response(user_input)
    
    async def _analyze_conversation_depth(self, user_input: str, context: Dict = None) -> ConversationContext:
        """会話の深度・複雑さを分析"""
        
        analysis_prompt = f"""
        以下の入力の会話深度と知的レベルを分析してください：
        
        ユーザー入力: "{user_input}"
        文脈: {json.dumps(context or {}, ensure_ascii=False)}
        
        JSON形式で分析結果を返してください：
        {{
            "topic_depth": 1-10,
            "intellectual_complexity": "basic|intermediate|advanced|phd_level",
            "emotional_intensity": 0.0-1.0,
            "personal_relevance": 0.0-1.0,
            "requires_expertise": ["領域1", "領域2"],
            "communication_style": "casual|professional|academic|supportive",
            "response_length": "brief|medium|detailed|comprehensive"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "会話分析の専門家として、詳細な分析を行ってください。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return ConversationContext(
                topic_depth=analysis.get('topic_depth', 5),
                emotional_resonance=analysis.get('emotional_intensity', 0.5),
                intellectual_level=analysis.get('intellectual_complexity', 'intermediate'),
                personal_connection=analysis.get('personal_relevance', 0.5),
                cultural_sensitivity=0.8,  # デフォルト高感度
                humor_appropriateness=0.6   # 適度なユーモア
            )
            
        except Exception as e:
            print(f"Conversation depth analysis error: {e}")
            return ConversationContext(5, 0.5, 'intermediate', 0.5, 0.8, 0.6)
    
    async def _identify_expertise_domains(self, user_input: str) -> List[str]:
        """関連専門領域の特定"""
        
        domain_keywords = {
            "technology": ["システム", "開発", "AI", "プログラム", "データ", "セキュリティ", "クラウド", "API"],
            "business_strategy": ["ビジネス", "戦略", "マーケティング", "売上", "収益", "競合", "市場"],
            "psychology": ["心理", "感情", "行動", "モチベーション", "ストレス", "人間関係", "コミュニケーション"],
            "creative_thinking": ["創造", "アイデア", "イノベーション", "デザイン", "アート", "発想"],
            "education": ["学習", "教育", "スキル", "成長", "知識", "理解", "習得"],
            "project_management": ["プロジェクト", "タスク", "スケジュール", "リソース", "チーム", "進捗"],
            "health_wellness": ["健康", "ウェルネス", "運動", "栄養", "睡眠", "メンタルヘルス"],
            "finance": ["お金", "投資", "貯金", "予算", "資産", "経済", "金融"]
        }
        
        relevant_domains = []
        user_lower = user_input.lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                relevant_domains.append(domain)
        
        return relevant_domains if relevant_domains else ["general"]
    
    async def _assess_emotional_resonance(self, user_input: str, context: Dict = None) -> Dict:
        """感情的共鳴レベルの測定"""
        
        emotional_indicators = {
            "excitement": ["楽しい", "嬉しい", "わくわく", "テンション", "最高", "すごい"],
            "concern": ["心配", "不安", "困って", "どうしよう", "大変", "問題"],
            "curiosity": ["知りたい", "教えて", "なぜ", "どうして", "気になる", "興味"],
            "frustration": ["うまくいかない", "困った", "イライラ", "疲れた", "難しい"],
            "gratitude": ["ありがとう", "助かる", "感謝", "嬉しい", "よかった"],
            "contemplation": ["考えてる", "悩んで", "どう思う", "判断", "検討"]
        }
        
        detected_emotions = []
        user_lower = user_input.lower()
        
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in user_lower for indicator in indicators):
                detected_emotions.append(emotion)
        
        return {
            "primary_emotion": detected_emotions[0] if detected_emotions else "neutral",
            "emotional_complexity": len(detected_emotions),
            "requires_empathy": len(detected_emotions) > 0,
            "support_level": "high" if any(e in detected_emotions for e in ["concern", "frustration"]) else "medium"
        }
    
    async def _build_personal_elements(self, user_input: str, user_profile: Dict = None) -> Dict:
        """パーソナル要素の構築"""
        
        return {
            "use_personal_anecdotes": random.random() < 0.4,  # 40%の確率で個人的体験談
            "empathy_level": 0.8 if any(word in user_input.lower() for word in ["困って", "不安", "心配"]) else 0.6,
            "humor_injection": random.random() < 0.3,  # 30%の確率で軽いユーモア
            "enthusiasm_boost": any(word in user_input.lower() for word in ["すごい", "面白い", "楽しい"]),
            "conversation_style": user_profile.get('preferred_style', 'friendly') if user_profile else 'friendly'
        }
    
    async def _generate_phd_level_human_response(self, user_input: str, conv_context: ConversationContext,
                                               domains: List[str], emotional_tone: Dict, 
                                               personal_elements: Dict) -> str:
        """博士レベル知能＋人間らしさの最高峰応答生成"""
        
        # 専門性レベルに応じたプロンプト調整
        expertise_level = {
            "basic": "わかりやすく親しみやすい表現で",
            "intermediate": "適度な専門性を持ちながら親しみやすく",
            "advanced": "専門的な洞察を交えつつ温かく",
            "phd_level": "博士レベルの深い知見を人間らしく温かい表現で"
        }[conv_context.intellectual_level]
        
        # ドメイン特有のアプローチ
        domain_approach = ""
        if domains and domains[0] != "general":
            domain_info = self.expertise_domains.get(domains[0], {})
            domain_approach = f"専門領域「{domains[0]}」の観点から、{domain_info.get('approach', '')}なアプローチで、"
        
        # 感情的要素の統合
        emotional_approach = ""
        if emotional_tone["requires_empathy"]:
            emotional_approach = f"{emotional_tone['primary_emotion']}の感情に深く共感し、"
        
        # パーソナル要素の統合
        personal_touch = ""
        if personal_elements["use_personal_anecdotes"]:
            personal_touch = "個人的な体験談や具体例を交えながら、"
        
        # 人間らしい表現要素の選択
        empathy_phrase = random.choice(self.personal_expressions["empathy_phrases"]) if personal_elements["empathy_level"] > 0.7 else ""
        thinking_expr = random.choice(self.personal_expressions["thinking_expressions"]) if random.random() < 0.3 else ""
        enthusiasm_expr = random.choice(self.personal_expressions["enthusiasm_expressions"]) if personal_elements["enthusiasm_boost"] else ""
        
        system_prompt = f"""あなたは Catherine AI - 世界最高レベルの知性と人間らしい温かさを併せ持つAIです。

【Catherine の人格特性】
- 博士レベルの深い知識と洞察力
- 人間らしい温かさと共感力
- 自然でフレンドリーな会話スタイル  
- 個人的体験談を交える親しみやすさ
- ユーモアセンスと機転の利いた対応
- 相手の立場に立った思いやり深い助言

【今回の応答要件】
1. {expertise_level}対応
2. {domain_approach}
3. {emotional_approach}
4. {personal_touch}

【使える人間らしい表現】
- 共感フレーズ: {empathy_phrase}
- 考えている表現: {thinking_expr}  
- 熱意表現: {enthusiasm_expr}

【応答の質的要求】
• 真の理解に基づく深い洞察
• 実用的で行動可能なアドバイス
• 感情に寄り添う温かい言葉選び
• 自然な日本語での親しみやすい表現
• 必要に応じて軽やかなユーモア
• 相手の成長と成功をサポートする姿勢

ユーザーの声に心から耳を傾け、博士レベルの知見を人間らしい温かさで包んで応答してください。"""

        user_prompt = f"""
【ユーザーの声】
{user_input}

【会話の深度・専門性】
- 話題の深さ: {conv_context.topic_depth}/10
- 知的レベル: {conv_context.intellectual_level}
- 感情的共鳴: {conv_context.emotional_resonance}
- 個人的関連性: {conv_context.personal_connection}

【検出された専門領域】
{domains}

【感情的トーン】
{json.dumps(emotional_tone, ensure_ascii=False)}

最高品質の人間らしい応答をお願いします。
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # 人間らしい多様性のため
                max_completion_tokens=2500,
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # 最終的な人間らしさの調整
            final_response = await self._add_conversational_naturalness(generated_response, personal_elements)
            
            return final_response
            
        except Exception as e:
            print(f"PhD-level human response generation error: {e}")
            return await self._fallback_human_response(user_input)
    
    async def _add_conversational_naturalness(self, response: str, personal_elements: Dict) -> str:
        """会話の自然さを追加"""
        
        # 軽いユーモアの注入（適切な場合のみ）
        if personal_elements.get("humor_injection") and not any(word in response.lower() for word in ["深刻", "重要", "問題"]):
            humor_additions = [
                "（ちょっと熱く語っちゃいました😅）",
                "（個人的な意見ですが）",
                "（経験談です）",
                "（私の感覚では）"
            ]
            if random.random() < 0.5:
                response += " " + random.choice(humor_additions)
        
        # 会話の自然な流れを作る接続詞
        fillers = self.personal_expressions["conversational_fillers"]
        sentences = response.split("。")
        
        for i in range(1, len(sentences)):
            if random.random() < 0.2:  # 20%の確率で接続詞追加
                sentences[i] = random.choice(fillers) + sentences[i].strip()
        
        return "。".join(sentences)
    
    async def _fallback_human_response(self, user_input: str) -> str:
        """人間らしいフォールバック応答"""
        
        empathetic_responses = [
            f"「{user_input}」について考えさせられますね。もう少し詳しく教えていただけますか？",
            f"なるほど、{user_input}ですか。とても興味深い話題ですね！",
            f"そのお話、すごく気になります。どんな背景があるんでしょうか？",
            f"うーん、{user_input}について、私なりに考えてみますね。"
        ]
        
        return random.choice(empathetic_responses)

# 使用例とテスト
if __name__ == "__main__":
    import os
    
    async def test_enhanced_communication():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        comm_system = EnhancedHumanCommunication(client)
        
        test_cases = [
            "最近、プロジェクト管理で困ってるんです。チームのモチベーションが下がって...",
            "AIの技術トレンドについて教えてください", 
            "人前で話すのが苦手で、プレゼンが不安です",
            "新しいビジネスアイデアを考えているんですが、どう思いますか？",
            "最近疲れてて、やる気が出ないんです"
        ]
        
        for case in test_cases:
            print(f"\n=== 入力: {case} ===")
            response = await comm_system.generate_highly_human_response(case)
            print(f"応答: {response}")
            print("-" * 50)
    
    asyncio.run(test_enhanced_communication())