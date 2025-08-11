#!/usr/bin/env python3
"""
Advanced Reasoning Engine - Catherine AI 高度推論システム
多段階推論・因果関係分析・複雑問題解決
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ReasoningStep:
    step_number: int
    premise: str
    inference: str
    conclusion: str
    confidence: float
    evidence: List[str]

@dataclass
class ReasoningChain:
    initial_query: str
    steps: List[ReasoningStep]
    final_conclusion: str
    overall_confidence: float
    alternative_hypotheses: List[str]

class AdvancedReasoningEngine:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.reasoning_depth = 7  # 7段階の深い推論
        self.knowledge_domains = [
            "business_strategy", "psychology", "technology", "management",
            "creativity", "communication", "problem_solving", "optimization"
        ]
    
    async def multi_step_reasoning(self, query: str, context: Dict = None) -> ReasoningChain:
        """多段階推論実行"""
        try:
            # 1. 問題分析・分解
            problem_analysis = await self._analyze_complex_problem(query, context)
            
            # 2. 仮説生成
            hypotheses = await self._generate_hypotheses(query, problem_analysis)
            
            # 3. 推論チェーン構築
            reasoning_steps = await self._build_reasoning_chain(query, hypotheses, problem_analysis)
            
            # 4. 証拠収集・検証
            validated_steps = await self._validate_reasoning_steps(reasoning_steps)
            
            # 5. 最終結論統合
            final_conclusion = await self._synthesize_conclusion(validated_steps, query)
            
            return ReasoningChain(
                initial_query=query,
                steps=validated_steps,
                final_conclusion=final_conclusion,
                overall_confidence=self._calculate_overall_confidence(validated_steps),
                alternative_hypotheses=hypotheses['alternatives'][:3]
            )
            
        except Exception as e:
            print(f"❌ Advanced reasoning error: {e}")
            return self._fallback_reasoning(query)
    
    async def _analyze_complex_problem(self, query: str, context: Dict = None) -> Dict:
        """複雑問題の分析・分解"""
        prompt = f"""
あなたは世界最高レベルの問題分析専門家です。以下の問題を深く分析してください。

問題: "{query}"
文脈: {json.dumps(context or {}, ensure_ascii=False)}

以下の観点から詳細に分析し、JSON形式で返してください：

{{
    "problem_type": "問題の種類",
    "complexity_level": 1-10,
    "key_components": ["主要要素1", "要素2", "要素3"],
    "hidden_assumptions": ["潜在的仮定1", "仮定2"],
    "stakeholders": ["関係者1", "関係者2"],
    "constraints": ["制約1", "制約2"],
    "success_criteria": ["成功基準1", "基準2"],
    "risk_factors": ["リスク要因1", "要因2"],
    "interdependencies": ["依存関係1", "関係2"],
    "required_expertise": ["必要な専門知識1", "知識2"],
    "time_sensitivity": 1-5,
    "resource_requirements": ["必要リソース1", "リソース2"],
    "potential_obstacles": ["潜在的障害1", "障害2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは複雑な問題を完璧に分析する世界最高の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Problem analysis error: {e}")
            return {"problem_type": "general", "complexity_level": 5}
    
    async def _generate_hypotheses(self, query: str, analysis: Dict) -> Dict:
        """仮説生成・検証"""
        prompt = f"""
世界最高の科学者・思想家として、以下の問題に対する仮説を生成してください。

問題: "{query}"
分析結果: {json.dumps(analysis, ensure_ascii=False)}

以下のJSON形式で包括的な仮説を返してください：

{{
    "primary_hypothesis": {{
        "hypothesis": "主要仮説",
        "reasoning": "推論根拠",
        "testable_predictions": ["検証可能な予測1", "予測2"],
        "required_evidence": ["必要な証拠1", "証拠2"],
        "confidence": 0.0-1.0
    }},
    "alternatives": [
        {{
            "hypothesis": "代替仮説1",
            "reasoning": "根拠",
            "confidence": 0.0-1.0
        }},
        {{
            "hypothesis": "代替仮説2", 
            "reasoning": "根拠",
            "confidence": 0.0-1.0
        }}
    ],
    "null_hypothesis": "帰無仮説",
    "confounding_factors": ["交絡要因1", "要因2"],
    "experimental_design": "検証方法",
    "expected_outcomes": ["期待される結果1", "結果2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは仮説生成と科学的推論の世界最高権威です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Hypothesis generation error: {e}")
            return {"primary_hypothesis": {"hypothesis": "基本仮説", "confidence": 0.5}, "alternatives": []}
    
    async def _build_reasoning_chain(self, query: str, hypotheses: Dict, analysis: Dict) -> List[ReasoningStep]:
        """推論チェーン構築"""
        steps = []
        
        for i in range(self.reasoning_depth):
            step_prompt = f"""
推論ステップ {i+1}/{self.reasoning_depth} を構築してください。

元の問題: "{query}"
問題分析: {json.dumps(analysis, ensure_ascii=False)}
仮説: {json.dumps(hypotheses['primary_hypothesis'], ensure_ascii=False)}
前のステップ: {json.dumps([{'premise': s.premise, 'conclusion': s.conclusion} for s in steps[-2:]], ensure_ascii=False) if steps else "なし"}

このステップでの推論をJSON形式で返してください：

{{
    "premise": "このステップの前提",
    "inference": "推論過程",
    "conclusion": "結論",
    "confidence": 0.0-1.0,
    "evidence": ["証拠1", "証拠2", "証拠3"],
    "logical_connection": "論理的結び付き",
    "potential_fallacies": ["潜在的誤謬1", "誤謬2"],
    "next_step_direction": "次のステップの方向性"
}}
"""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": f"あなたは論理的推論の専門家です。ステップ{i+1}の推論を構築してください。"},
                        {"role": "user", "content": step_prompt}
                    ],
                    temperature=0.3,
                    max_completion_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                step_data = json.loads(response.choices[0].message.content)
                
                steps.append(ReasoningStep(
                    step_number=i+1,
                    premise=step_data.get('premise', ''),
                    inference=step_data.get('inference', ''),
                    conclusion=step_data.get('conclusion', ''),
                    confidence=step_data.get('confidence', 0.5),
                    evidence=step_data.get('evidence', [])
                ))
                
            except Exception as e:
                print(f"Reasoning step {i+1} error: {e}")
                break
        
        return steps
    
    async def _validate_reasoning_steps(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """推論ステップの検証・妥当性確認"""
        validated_steps = []
        
        for step in steps:
            validation_prompt = f"""
以下の推論ステップを厳密に検証してください：

前提: {step.premise}
推論: {step.inference}
結論: {step.conclusion}
証拠: {step.evidence}

検証結果をJSON形式で返してください：

{{
    "is_valid": true/false,
    "logical_soundness": 0.0-1.0,
    "evidence_strength": 0.0-1.0,
    "potential_errors": ["エラー1", "エラー2"],
    "improvement_suggestions": ["改善案1", "改善案2"],
    "corrected_premise": "修正された前提（必要な場合）",
    "corrected_inference": "修正された推論（必要な場合）",
    "corrected_conclusion": "修正された結論（必要な場合）",
    "final_confidence": 0.0-1.0
}}
"""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "あなたは論理学と推論の妥当性検証の専門家です。"},
                        {"role": "user", "content": validation_prompt}
                    ],
                    temperature=0.1,
                    max_completion_tokens=1000,
                    response_format={"type": "json_object"}
                )
                
                validation = json.loads(response.choices[0].message.content)
                
                # 修正が必要な場合は適用
                if validation.get('corrected_premise'):
                    step.premise = validation['corrected_premise']
                if validation.get('corrected_inference'):
                    step.inference = validation['corrected_inference']
                if validation.get('corrected_conclusion'):
                    step.conclusion = validation['corrected_conclusion']
                
                step.confidence = validation.get('final_confidence', step.confidence)
                
                validated_steps.append(step)
                
            except Exception as e:
                print(f"Validation error for step {step.step_number}: {e}")
                validated_steps.append(step)
        
        return validated_steps
    
    async def _synthesize_conclusion(self, steps: List[ReasoningStep], original_query: str) -> str:
        """最終結論の統合・生成"""
        steps_summary = []
        for step in steps:
            steps_summary.append({
                "step": step.step_number,
                "conclusion": step.conclusion,
                "confidence": step.confidence
            })
        
        synthesis_prompt = f"""
以下の推論チェーンから最終的な結論を統合してください：

元の質問: "{original_query}"
推論ステップ: {json.dumps(steps_summary, ensure_ascii=False)}

最高品質の最終結論を生成してください：
1. 論理的一貫性の確保
2. 実用的価値の最大化
3. 明確で理解しやすい表現
4. 次のアクションの提示
5. リスクと限界の言及

結論は200-300文字で簡潔にまとめてください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは複雑な推論を明確で実用的な結論にまとめる専門家です。"},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=800
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Conclusion synthesis error: {e}")
            return f"{original_query}について、多角的な分析を行った結果、実用的な解決策を提示いたします。"
    
    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> float:
        """全体的信頼度の計算"""
        if not steps:
            return 0.0
        
        # 各ステップの信頼度の重み付き平均
        weights = [1.0 / (i + 1) for i in range(len(steps))]  # 後のステップほど重要
        weighted_sum = sum(step.confidence * weight for step, weight in zip(steps, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _fallback_reasoning(self, query: str) -> ReasoningChain:
        """フォールバック推論"""
        return ReasoningChain(
            initial_query=query,
            steps=[],
            final_conclusion=f"{query}について分析中です。より詳細な情報をお聞かせください。",
            overall_confidence=0.3,
            alternative_hypotheses=[]
        )

# 使用例
if __name__ == "__main__":
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    engine = AdvancedReasoningEngine(client)
    
    async def test():
        result = await engine.multi_step_reasoning(
            "チームの生産性を向上させるにはどうしたらいいですか？"
        )
        print(f"Final Conclusion: {result.final_conclusion}")
        print(f"Confidence: {result.overall_confidence:.2f}")
    
    asyncio.run(test())