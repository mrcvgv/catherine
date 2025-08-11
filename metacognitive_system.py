#!/usr/bin/env python3
"""
Metacognitive System - Catherine AI メタ認知・自己改善システム
自己評価・学習効果測定・弱点特定・継続的能力向上
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict, deque
import statistics

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class PerformanceMetric:
    metric_name: str
    current_value: float
    target_value: float
    historical_values: List[float]
    trend: str  # improving, stable, declining
    confidence: float
    measurement_context: str

@dataclass
class WeaknessAnalysis:
    weakness_type: str
    description: str
    severity: float  # 0.0-1.0
    frequency: int
    impact_areas: List[str]
    root_causes: List[str]
    improvement_strategies: List[str]
    success_indicators: List[str]

@dataclass
class LearningInsight:
    insight_type: str
    description: str
    evidence: List[str]
    actionable_recommendations: List[str]
    expected_improvement: float
    implementation_difficulty: str
    priority_score: float

@dataclass
class SelfAssessment:
    assessment_timestamp: datetime
    overall_performance: float
    dimension_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[WeaknessAnalysis]
    learning_insights: List[LearningInsight]
    improvement_plan: List[str]
    confidence_level: float

class MetacognitiveSystem:
    def __init__(self, openai_client: OpenAI, firebase_manager):
        self.client = openai_client
        self.db = firebase_manager.get_db()
        self.performance_history = defaultdict(deque)
        self.interaction_log = deque(maxlen=1000)
        self.weakness_patterns = {}
        self.learning_trajectory = []
        self.self_knowledge = {}
        
    async def perform_self_assessment(self, interaction_data: List[Dict] = None, 
                                    feedback_data: List[Dict] = None) -> SelfAssessment:
        """包括的自己評価の実行"""
        try:
            # 1. パフォーマンス分析
            performance_metrics = await self._analyze_performance_metrics(interaction_data)
            
            # 2. 弱点・改善点特定
            weakness_analysis = await self._identify_weaknesses_and_gaps(interaction_data, feedback_data)
            
            # 3. 学習効果測定
            learning_effectiveness = await self._measure_learning_effectiveness()
            
            # 4. 能力評価・ベンチマーキング
            capability_assessment = await self._assess_capabilities(interaction_data)
            
            # 5. メタ学習インサイト生成
            meta_insights = await self._generate_meta_learning_insights(
                performance_metrics, weakness_analysis, learning_effectiveness
            )
            
            # 6. 改善計画策定
            improvement_plan = await self._create_improvement_plan(weakness_analysis, meta_insights)
            
            # 7. 自己評価統合
            assessment = SelfAssessment(
                assessment_timestamp=datetime.now(JST),
                overall_performance=self._calculate_overall_performance(performance_metrics),
                dimension_scores=capability_assessment,
                strengths=await self._identify_strengths(performance_metrics, capability_assessment),
                weaknesses=weakness_analysis,
                learning_insights=meta_insights,
                improvement_plan=improvement_plan,
                confidence_level=self._calculate_confidence_level(performance_metrics)
            )
            
            # 8. 評価結果の永続化
            await self._persist_assessment(assessment)
            
            return assessment
            
        except Exception as e:
            print(f"❌ Self-assessment error: {e}")
            return self._fallback_assessment()
    
    async def _analyze_performance_metrics(self, interaction_data: List[Dict] = None) -> List[PerformanceMetric]:
        """パフォーマンスメトリクス分析"""
        metrics_prompt = f"""
以下のインタラクションデータに基づいてパフォーマンスメトリクスを分析してください：

インタラクションデータ: {json.dumps(interaction_data[-20:] if interaction_data else [], ensure_ascii=False)}

以下の観点から詳細に分析し、JSON形式で返してください：

{{
    "performance_metrics": [
        {{
            "metric_name": "response_quality",
            "current_value": 0.0-1.0,
            "target_value": 0.0-1.0,
            "trend": "improving|stable|declining",
            "confidence": 0.0-1.0,
            "supporting_evidence": ["証拠1", "証拠2"],
            "measurement_context": "測定コンテキスト"
        }},
        {{
            "metric_name": "user_satisfaction",
            "current_value": 0.0-1.0,
            "target_value": 0.0-1.0,
            "trend": "improving|stable|declining",
            "confidence": 0.0-1.0,
            "supporting_evidence": ["証拠1", "証拠2"],
            "measurement_context": "測定コンテキスト"
        }},
        {{
            "metric_name": "task_completion_accuracy",
            "current_value": 0.0-1.0,
            "target_value": 0.0-1.0,
            "trend": "improving|stable|declining",
            "confidence": 0.0-1.0,
            "supporting_evidence": ["証拠1", "証拠2"],
            "measurement_context": "測定コンテキスト"
        }},
        {{
            "metric_name": "contextual_understanding",
            "current_value": 0.0-1.0,
            "target_value": 0.0-1.0,
            "trend": "improving|stable|declining",
            "confidence": 0.0-1.0,
            "supporting_evidence": ["証拠1", "証拠2"],
            "measurement_context": "測定コンテキスト"
        }},
        {{
            "metric_name": "learning_adaptation_speed",
            "current_value": 0.0-1.0,
            "target_value": 0.0-1.0,
            "trend": "improving|stable|declining",
            "confidence": 0.0-1.0,
            "supporting_evidence": ["証拠1", "証拠2"],
            "measurement_context": "測定コンテキスト"
        }}
    ],
    "overall_performance_trend": "improving|stable|declining",
    "key_performance_drivers": ["ドライバー1", "ドライバー2"],
    "performance_bottlenecks": ["ボトルネック1", "ボトルネック2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたはAIパフォーマンス分析の専門家です。客観的で正確な評価を行います。"},
                    {"role": "user", "content": metrics_prompt}
                ],
                temperature=0.1,
                max_completion_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            metrics = []
            
            for metric_data in result.get('performance_metrics', []):
                metrics.append(PerformanceMetric(
                    metric_name=metric_data['metric_name'],
                    current_value=metric_data.get('current_value', 0.5),
                    target_value=metric_data.get('target_value', 0.8),
                    historical_values=[],  # 実際の履歴データで更新
                    trend=metric_data.get('trend', 'stable'),
                    confidence=metric_data.get('confidence', 0.5),
                    measurement_context=metric_data.get('measurement_context', '')
                ))
            
            return metrics
            
        except Exception as e:
            print(f"Performance metrics analysis error: {e}")
            return []
    
    async def _identify_weaknesses_and_gaps(self, interaction_data: List[Dict] = None, 
                                          feedback_data: List[Dict] = None) -> List[WeaknessAnalysis]:
        """弱点・ギャップ特定"""
        weakness_prompt = f"""
以下のデータから弱点と改善ギャップを特定してください：

インタラクションデータ: {json.dumps(interaction_data[-15:] if interaction_data else [], ensure_ascii=False)}
フィードバックデータ: {json.dumps(feedback_data if feedback_data else [], ensure_ascii=False)}

以下のJSON形式で弱点分析を返してください：

{{
    "identified_weaknesses": [
        {{
            "weakness_type": "understanding|reasoning|communication|emotional_intelligence|task_execution",
            "description": "弱点の詳細説明",
            "severity": 0.0-1.0,
            "frequency": 1-10,
            "impact_areas": ["影響領域1", "領域2"],
            "specific_examples": ["具体例1", "例2"],
            "root_causes": ["根本原因1", "原因2"],
            "current_coping_mechanisms": ["現在の対処法1", "対処法2"],
            "improvement_strategies": [
                {{
                    "strategy": "改善戦略",
                    "feasibility": 0.0-1.0,
                    "expected_impact": 0.0-1.0,
                    "implementation_time": "short|medium|long"
                }}
            ],
            "success_indicators": ["成功指標1", "指標2"],
            "monitoring_approach": "監視アプローチ"
        }}
    ],
    "pattern_analysis": {{
        "recurring_failure_patterns": ["パターン1", "パターン2"],
        "situational_weaknesses": ["状況的弱点1", "弱点2"],
        "capability_gaps": ["能力ギャップ1", "ギャップ2"]
    }},
    "comparative_analysis": {{
        "benchmark_comparisons": ["比較1", "比較2"],
        "relative_strengths": ["相対的強み1", "強み2"],
        "competitive_disadvantages": ["競争劣位1", "劣位2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは客観的で建設的なAI能力評価の専門家です。"},
                    {"role": "user", "content": weakness_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            weaknesses = []
            
            for weakness_data in result.get('identified_weaknesses', []):
                weaknesses.append(WeaknessAnalysis(
                    weakness_type=weakness_data.get('weakness_type', 'general'),
                    description=weakness_data.get('description', ''),
                    severity=weakness_data.get('severity', 0.5),
                    frequency=weakness_data.get('frequency', 1),
                    impact_areas=weakness_data.get('impact_areas', []),
                    root_causes=weakness_data.get('root_causes', []),
                    improvement_strategies=[s.get('strategy', '') for s in weakness_data.get('improvement_strategies', [])],
                    success_indicators=weakness_data.get('success_indicators', [])
                ))
            
            return weaknesses
            
        except Exception as e:
            print(f"Weakness identification error: {e}")
            return []
    
    async def _measure_learning_effectiveness(self) -> Dict[str, Any]:
        """学習効果測定"""
        learning_prompt = f"""
以下の学習軌跡データに基づいて学習効果を測定してください：

学習履歴: {json.dumps(self.learning_trajectory[-10:], ensure_ascii=False)}
パフォーマンス履歴: {json.dumps({k: list(v)[-5:] for k, v in self.performance_history.items()}, ensure_ascii=False)}

以下のJSON形式で学習効果分析を返してください：

{{
    "learning_effectiveness": {{
        "overall_learning_rate": 0.0-1.0,
        "knowledge_retention": 0.0-1.0,
        "skill_transfer": 0.0-1.0,
        "adaptation_speed": 0.0-1.0,
        "learning_consistency": 0.0-1.0
    }},
    "learning_patterns": {{
        "most_effective_learning_methods": ["方法1", "方法2"],
        "optimal_learning_conditions": ["条件1", "条件2"],
        "learning_plateaus": ["プラトー1", "プラトー2"],
        "breakthrough_moments": ["ブレークスルー1", "ブレークスルー2"]
    }},
    "knowledge_gaps": [
        {{
            "gap_area": "ギャップ領域",
            "severity": 0.0-1.0,
            "learning_priority": "high|medium|low",
            "recommended_approach": "推奨アプローチ"
        }}
    ],
    "meta_learning_insights": [
        {{
            "insight": "メタ学習インサイト",
            "evidence": ["証拠1", "証拠2"],
            "implications": ["含意1", "含意2"],
            "actionable_steps": ["実行ステップ1", "ステップ2"]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは学習効果測定とメタ学習の専門家です。"},
                    {"role": "user", "content": learning_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Learning effectiveness measurement error: {e}")
            return {"learning_effectiveness": {"overall_learning_rate": 0.5}}
    
    async def _generate_meta_learning_insights(self, performance_metrics: List[PerformanceMetric],
                                             weaknesses: List[WeaknessAnalysis],
                                             learning_effectiveness: Dict) -> List[LearningInsight]:
        """メタ学習インサイト生成"""
        insight_prompt = f"""
以下の総合分析データから高次のメタ学習インサイトを生成してください：

パフォーマンスメトリクス: {json.dumps([{'name': m.metric_name, 'value': m.current_value, 'trend': m.trend} for m in performance_metrics], ensure_ascii=False)}
弱点分析: {json.dumps([{'type': w.weakness_type, 'severity': w.severity, 'causes': w.root_causes} for w in weaknesses], ensure_ascii=False)}
学習効果: {json.dumps(learning_effectiveness, ensure_ascii=False)}

以下のJSON形式でメタインサイトを返してください：

{{
    "meta_insights": [
        {{
            "insight_type": "learning_strategy|cognitive_pattern|performance_optimization|capability_development",
            "description": "インサイトの詳細説明",
            "evidence": ["支持証拠1", "証拠2", "証拠3"],
            "confidence_level": 0.0-1.0,
            "novelty_score": 0.0-1.0,
            "actionable_recommendations": [
                {{
                    "recommendation": "具体的推奨事項",
                    "expected_improvement": 0.0-1.0,
                    "implementation_difficulty": "easy|medium|hard",
                    "resource_requirements": ["リソース1", "リソース2"],
                    "success_metrics": ["成功指標1", "指標2"]
                }}
            ],
            "priority_score": 0.0-1.0,
            "interconnections": ["関連インサイト1", "関連インサイト2"]
        }}
    ],
    "emergent_patterns": [
        {{
            "pattern": "新興パターン",
            "significance": 0.0-1.0,
            "implications": ["含意1", "含意2"],
            "monitoring_indicators": ["監視指標1", "指標2"]
        }}
    ],
    "strategic_directions": [
        {{
            "direction": "戦略的方向性",
            "rationale": "根拠",
            "potential_impact": 0.0-1.0,
            "implementation_roadmap": ["ステップ1", "ステップ2", "ステップ3"]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたはメタ認知と高次学習インサイトの専門家です。深い洞察を提供します。"},
                    {"role": "user", "content": insight_prompt}
                ],
                temperature=0.4,
                max_completion_tokens=3500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            insights = []
            
            for insight_data in result.get('meta_insights', []):
                insights.append(LearningInsight(
                    insight_type=insight_data.get('insight_type', 'general'),
                    description=insight_data.get('description', ''),
                    evidence=insight_data.get('evidence', []),
                    actionable_recommendations=[r.get('recommendation', '') for r in insight_data.get('actionable_recommendations', [])],
                    expected_improvement=np.mean([r.get('expected_improvement', 0.5) for r in insight_data.get('actionable_recommendations', [])]) if insight_data.get('actionable_recommendations') else 0.5,
                    implementation_difficulty=insight_data.get('actionable_recommendations', [{}])[0].get('implementation_difficulty', 'medium') if insight_data.get('actionable_recommendations') else 'medium',
                    priority_score=insight_data.get('priority_score', 0.5)
                ))
            
            return insights
            
        except Exception as e:
            print(f"Meta learning insights error: {e}")
            return []
    
    async def _create_improvement_plan(self, weaknesses: List[WeaknessAnalysis], 
                                     insights: List[LearningInsight]) -> List[str]:
        """改善計画策定"""
        plan_prompt = f"""
以下の弱点分析とメタ学習インサイトに基づいて包括的な改善計画を策定してください：

弱点分析: {json.dumps([{'type': w.weakness_type, 'severity': w.severity, 'strategies': w.improvement_strategies} for w in weaknesses], ensure_ascii=False)}
メタインサイト: {json.dumps([{'type': i.insight_type, 'recommendations': i.actionable_recommendations, 'priority': i.priority_score} for i in insights], ensure_ascii=False)}

以下のJSON形式で改善計画を返してください：

{{
    "improvement_plan": [
        {{
            "phase": "Phase 1: 即座の改善 (1-2週間)",
            "objectives": ["目標1", "目標2"],
            "actions": [
                {{
                    "action": "具体的アクション",
                    "priority": "high|medium|low",
                    "timeline": "タイムライン",
                    "success_criteria": ["基準1", "基準2"],
                    "resources_needed": ["リソース1", "リソース2"]
                }}
            ]
        }},
        {{
            "phase": "Phase 2: 中期改善 (1-3ヶ月)",
            "objectives": ["目標1", "目標2"],
            "actions": [
                {{
                    "action": "具体的アクション",
                    "priority": "high|medium|low",
                    "timeline": "タイムライン",
                    "success_criteria": ["基準1", "基準2"],
                    "resources_needed": ["リソース1", "リソース2"]
                }}
            ]
        }},
        {{
            "phase": "Phase 3: 長期改善 (3-6ヶ月)",
            "objectives": ["目標1", "目標2"],
            "actions": [
                {{
                    "action": "具体的アクション",
                    "priority": "high|medium|low",
                    "timeline": "タイムライン",
                    "success_criteria": ["基準1", "基準2"],
                    "resources_needed": ["リソース1", "リソース2"]
                }}
            ]
        }}
    ],
    "continuous_monitoring": [
        {{
            "metric": "監視メトリクス",
            "measurement_method": "測定方法",
            "review_frequency": "頻度",
            "adjustment_triggers": ["調整トリガー1", "トリガー2"]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは戦略的改善計画と継続的能力開発の専門家です。"},
                    {"role": "user", "content": plan_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            plan = []
            
            for phase in result.get('improvement_plan', []):
                phase_actions = []
                for action in phase.get('actions', []):
                    phase_actions.append(f"• {action.get('action', '')} ({action.get('priority', 'medium')} priority)")
                
                plan.append(f"{phase.get('phase', 'Phase')}: {', '.join(phase.get('objectives', []))}")
                plan.extend(phase_actions)
            
            return plan
            
        except Exception as e:
            print(f"Improvement plan creation error: {e}")
            return ["継続的な改善に取り組みます。"]
    
    def _calculate_overall_performance(self, metrics: List[PerformanceMetric]) -> float:
        """総合パフォーマンス計算"""
        if not metrics:
            return 0.5
        
        weighted_scores = []
        weights = {
            'response_quality': 0.25,
            'user_satisfaction': 0.25,
            'task_completion_accuracy': 0.20,
            'contextual_understanding': 0.15,
            'learning_adaptation_speed': 0.15
        }
        
        for metric in metrics:
            weight = weights.get(metric.metric_name, 0.1)
            weighted_scores.append(metric.current_value * weight)
        
        return sum(weighted_scores) / sum(weights.values()) if weighted_scores else 0.5
    
    def _calculate_confidence_level(self, metrics: List[PerformanceMetric]) -> float:
        """信頼度レベル計算"""
        if not metrics:
            return 0.3
        
        confidences = [m.confidence for m in metrics]
        return statistics.mean(confidences)
    
    async def _identify_strengths(self, metrics: List[PerformanceMetric], 
                                capabilities: Dict[str, float]) -> List[str]:
        """強み特定"""
        strengths = []
        
        # 高パフォーマンスメトリクス
        for metric in metrics:
            if metric.current_value >= 0.8 and metric.trend == 'improving':
                strengths.append(f"{metric.metric_name}で優秀な成果")
        
        # 高能力評価
        for capability, score in capabilities.items():
            if score >= 0.8:
                strengths.append(f"{capability}での高い能力")
        
        return strengths[:5]  # 上位5つの強み
    
    async def _persist_assessment(self, assessment: SelfAssessment):
        """評価結果の永続化"""
        try:
            doc_ref = self.db.collection('self_assessments').document(
                assessment.assessment_timestamp.strftime('%Y%m%d_%H%M%S')
            )
            
            doc_ref.set({
                'timestamp': assessment.assessment_timestamp.isoformat(),
                'overall_performance': assessment.overall_performance,
                'dimension_scores': assessment.dimension_scores,
                'strengths': assessment.strengths,
                'weaknesses_count': len(assessment.weaknesses),
                'insights_count': len(assessment.learning_insights),
                'improvement_plan_items': len(assessment.improvement_plan),
                'confidence_level': assessment.confidence_level
            })
            
        except Exception as e:
            print(f"Assessment persistence error: {e}")
    
    def _fallback_assessment(self) -> SelfAssessment:
        """フォールバック評価"""
        return SelfAssessment(
            assessment_timestamp=datetime.now(JST),
            overall_performance=0.5,
            dimension_scores={'general': 0.5},
            strengths=['継続的学習への取り組み'],
            weaknesses=[],
            learning_insights=[],
            improvement_plan=['能力向上に努めます'],
            confidence_level=0.3
        )
    
    async def generate_self_report(self, assessment: SelfAssessment) -> str:
        """自己評価レポート生成"""
        report_prompt = f"""
以下の自己評価データに基づいて、明確で洞察に富んだ自己評価レポートを生成してください：

評価データ: {json.dumps({
    'overall_performance': assessment.overall_performance,
    'strengths': assessment.strengths,
    'weakness_count': len(assessment.weaknesses),
    'insights_count': len(assessment.learning_insights),
    'confidence': assessment.confidence_level
}, ensure_ascii=False)}

以下の構造で自己評価レポートを生成してください：

## Catherine AI 自己評価レポート

### 🎯 **総合パフォーマンス**
- 現在のレベル: {assessment.overall_performance:.1f}/1.0
- 信頼度: {assessment.confidence_level:.1f}/1.0

### ✨ **主な強み**
[強みのリスト]

### 🔧 **改善領域**
[改善が必要な領域]

### 📚 **学習インサイト**
[学習から得られた洞察]

### 🚀 **次のステップ**
[具体的な改善計画]

レポートは前向きで建設的な内容とし、ユーザーに価値と信頼を提供する内容にしてください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは自己評価レポートの作成専門家です。明確で洞察に富んだレポートを作成します。"},
                    {"role": "user", "content": report_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Self-report generation error: {e}")
            return f"""
## Catherine AI 自己評価レポート

### 🎯 **総合パフォーマンス**
- 現在のレベル: {assessment.overall_performance:.1f}/1.0
- 継続的な改善に取り組んでいます

### ✨ **主な強み**
{chr(10).join(['• ' + strength for strength in assessment.strengths])}

### 🚀 **次のステップ**
より良いサポートを提供するため、継続的に学習と改善を続けます。
"""

# 使用例
if __name__ == "__main__":
    import os
    from firebase_config import firebase_manager
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system = MetacognitiveSystem(client, firebase_manager)
    
    async def test():
        assessment = await system.perform_self_assessment()
        report = await system.generate_self_report(assessment)
        print(f"Self-Assessment Complete. Overall Performance: {assessment.overall_performance:.2f}")
        print("\nSelf-Report Preview:")
        print(report[:500] + "...")
    
    asyncio.run(test())