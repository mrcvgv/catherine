#!/usr/bin/env python3
"""
Intelligent Automation System - Catherine AI 知的タスク自動化システム
プロジェクト戦略立案・依存関係分析・リソース最適化・予測的問題解決
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re
from dataclasses import dataclass, field
import networkx as nx
from collections import defaultdict
import numpy as np

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: int
    estimated_duration: timedelta
    dependencies: List[str]
    required_resources: List[str]
    skills_required: List[str]
    status: str
    assigned_to: Optional[str] = None
    deadline: Optional[datetime] = None
    complexity_score: float = 0.5

@dataclass
class Project:
    id: str
    name: str
    description: str
    tasks: List[Task]
    timeline: Dict[str, datetime]
    resources: Dict[str, Any]
    risks: List[Dict[str, Any]]
    success_metrics: List[str]
    stakeholders: List[str]

@dataclass
class ResourceOptimization:
    resource_type: str
    current_allocation: Dict[str, float]
    optimal_allocation: Dict[str, float]
    efficiency_gain: float
    implementation_steps: List[str]
    risk_factors: List[str]

@dataclass
class PredictiveInsight:
    prediction_type: str
    description: str
    probability: float
    impact_score: float
    timeline: str
    mitigation_strategies: List[str]
    monitoring_indicators: List[str]

class IntelligentAutomationSystem:
    def __init__(self, openai_client: OpenAI, firebase_manager):
        self.client = openai_client
        self.db = firebase_manager.get_db()
        self.projects = {}
        self.task_graphs = {}
        self.optimization_history = []
        self.prediction_models = {}
        
    async def create_strategic_plan(self, project_description: str, constraints: Dict = None, 
                                  stakeholders: List[str] = None) -> Dict[str, Any]:
        """戦略的プロジェクト計画の作成"""
        try:
            # 1. プロジェクト分析・分解
            project_analysis = await self._analyze_project_scope(project_description, constraints)
            
            # 2. タスク自動生成・構造化
            tasks = await self._generate_structured_tasks(project_analysis)
            
            # 3. 依存関係分析・グラフ構築
            dependency_graph = await self._build_dependency_graph(tasks)
            
            # 4. リソース要件分析
            resource_requirements = await self._analyze_resource_requirements(tasks, constraints)
            
            # 5. リスク分析・軽減戦略
            risk_analysis = await self._perform_risk_analysis(project_analysis, tasks)
            
            # 6. 最適化・スケジューリング
            optimized_schedule = await self._optimize_project_schedule(tasks, dependency_graph, resource_requirements)
            
            # 7. 成功指標・監視システム
            success_framework = await self._create_success_framework(project_analysis, tasks)
            
            # 8. プロジェクト統合
            project = await self._integrate_project_plan(
                project_analysis, tasks, dependency_graph, resource_requirements,
                risk_analysis, optimized_schedule, success_framework
            )
            
            return {
                'project': project,
                'strategic_insights': await self._generate_strategic_insights(project),
                'automation_opportunities': await self._identify_automation_opportunities(project),
                'success_probability': self._calculate_success_probability(project)
            }
            
        except Exception as e:
            print(f"❌ Strategic planning error: {e}")
            return self._fallback_strategic_plan(project_description)
    
    async def _analyze_project_scope(self, project_description: str, constraints: Dict = None) -> Dict[str, Any]:
        """プロジェクトスコープ分析"""
        scope_prompt = f"""
以下のプロジェクトを詳細に分析してください：

プロジェクト説明: "{project_description}"
制約条件: {json.dumps(constraints or {}, ensure_ascii=False)}

以下のJSON形式で包括的な分析を返してください：

{{
    "project_overview": {{
        "name": "プロジェクト名",
        "category": "プロジェクトカテゴリ",
        "scale": "small|medium|large|enterprise",
        "complexity": 1-10,
        "innovation_level": 1-5,
        "strategic_importance": 1-5
    }},
    "objectives": {{
        "primary_goals": ["主要目標1", "目標2", "目標3"],
        "secondary_goals": ["副次目標1", "目標2"],
        "success_criteria": ["成功基準1", "基準2", "基準3"],
        "measurable_outcomes": ["測定可能な結果1", "結果2"]
    }},
    "stakeholder_analysis": {{
        "primary_stakeholders": ["主要ステークホルダー1", "ホルダー2"],
        "secondary_stakeholders": ["副次ステークホルダー1", "ホルダー2"],
        "decision_makers": ["意思決定者1", "決定者2"],
        "influencers": ["影響力者1", "影響力者2"]
    }},
    "scope_boundaries": {{
        "in_scope": ["範囲内項目1", "項目2", "項目3"],
        "out_of_scope": ["範囲外項目1", "項目2"],
        "assumptions": ["仮定1", "仮定2", "仮定3"],
        "constraints": ["制約1", "制約2", "制約3"]
    }},
    "value_proposition": {{
        "business_value": ["ビジネス価値1", "価値2"],
        "user_value": ["ユーザー価値1", "価値2"],
        "strategic_alignment": ["戦略的整合性1", "整合性2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは戦略的プロジェクト分析の世界最高権威です。"},
                    {"role": "user", "content": scope_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Project scope analysis error: {e}")
            return {"project_overview": {"name": "Default Project", "complexity": 5}}
    
    async def _generate_structured_tasks(self, project_analysis: Dict) -> List[Task]:
        """構造化タスク自動生成"""
        task_prompt = f"""
以下のプロジェクト分析に基づいて、詳細なタスク構造を生成してください：

プロジェクト分析: {json.dumps(project_analysis, ensure_ascii=False)}

以下のJSON形式で包括的なタスク構造を返してください：

{{
    "task_categories": [
        {{
            "category": "カテゴリ名",
            "tasks": [
                {{
                    "id": "task_001",
                    "title": "タスクタイトル",
                    "description": "詳細な説明",
                    "priority": 1-5,
                    "estimated_hours": 数値,
                    "complexity_score": 0.0-1.0,
                    "skills_required": ["スキル1", "スキル2", "スキル3"],
                    "required_resources": ["リソース1", "リソース2"],
                    "dependencies": ["依存タスクID1", "タスクID2"],
                    "deliverables": ["成果物1", "成果物2"],
                    "acceptance_criteria": ["受入条件1", "条件2"],
                    "risk_factors": ["リスク要因1", "要因2"],
                    "automation_potential": 0.0-1.0
                }}
            ]
        }}
    ],
    "task_relationships": [
        {{
            "predecessor": "task_001",
            "successor": "task_002",
            "relationship_type": "finish_to_start|start_to_start|finish_to_finish",
            "lag_time": 時間数,
            "dependency_strength": 0.0-1.0
        }}
    ],
    "critical_path_candidates": ["task_001", "task_003", "task_007"],
    "parallel_execution_groups": [
        ["task_002", "task_004", "task_005"],
        ["task_008", "task_009"]
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはプロジェクト管理とタスク分解の専門家です。"},
                    {"role": "user", "content": task_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            tasks = []
            
            for category in result.get('task_categories', []):
                for task_data in category.get('tasks', []):
                    tasks.append(Task(
                        id=task_data['id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        priority=task_data.get('priority', 3),
                        estimated_duration=timedelta(hours=task_data.get('estimated_hours', 8)),
                        dependencies=task_data.get('dependencies', []),
                        required_resources=task_data.get('required_resources', []),
                        skills_required=task_data.get('skills_required', []),
                        status='planned',
                        complexity_score=task_data.get('complexity_score', 0.5)
                    ))
            
            return tasks
            
        except Exception as e:
            print(f"Task generation error: {e}")
            return []
    
    async def _build_dependency_graph(self, tasks: List[Task]) -> nx.DiGraph:
        """依存関係グラフ構築"""
        graph = nx.DiGraph()
        
        # ノード追加
        for task in tasks:
            graph.add_node(task.id, 
                          title=task.title,
                          duration=task.estimated_duration.total_seconds() / 3600,  # hours
                          priority=task.priority,
                          complexity=task.complexity_score)
        
        # エッジ追加
        for task in tasks:
            for dep_id in task.dependencies:
                if graph.has_node(dep_id):
                    graph.add_edge(dep_id, task.id, weight=1.0)
        
        # 循環依存チェック
        if not nx.is_directed_acyclic_graph(graph):
            print("⚠️ Warning: Circular dependencies detected")
            # 循環を検出して解消
            cycles = list(nx.simple_cycles(graph))
            for cycle in cycles:
                # 最も重要度の低いエッジを削除
                edges_in_cycle = [(cycle[i], cycle[(i+1) % len(cycle)]) for i in range(len(cycle))]
                min_priority_edge = min(edges_in_cycle, 
                                      key=lambda e: graph.nodes[e[0]].get('priority', 3))
                graph.remove_edge(min_priority_edge[0], min_priority_edge[1])
        
        return graph
    
    async def _analyze_resource_requirements(self, tasks: List[Task], constraints: Dict = None) -> Dict[str, Any]:
        """リソース要件分析"""
        resource_prompt = f"""
以下のタスクリストからリソース要件を分析してください：

タスク情報: {json.dumps([{'id': t.id, 'title': t.title, 'resources': t.required_resources, 'skills': t.skills_required, 'duration': t.estimated_duration.total_seconds()/3600} for t in tasks], ensure_ascii=False)}
制約条件: {json.dumps(constraints or {}, ensure_ascii=False)}

以下のJSON形式でリソース分析を返してください：

{{
    "resource_categories": {{
        "human_resources": {{
            "roles_needed": [
                {{
                    "role": "役割名",
                    "skills": ["スキル1", "スキル2"],
                    "experience_level": "junior|mid|senior|expert",
                    "allocation_percentage": 0.0-1.0,
                    "critical_periods": ["期間1", "期間2"]
                }}
            ],
            "total_person_hours": 数値,
            "peak_capacity_requirements": 数値
        }},
        "technical_resources": {{
            "software_tools": ["ツール1", "ツール2"],
            "hardware_requirements": ["要件1", "要件2"],
            "infrastructure": ["インフラ1", "インフラ2"],
            "licenses_subscriptions": ["ライセンス1", "サブスク1"]
        }},
        "financial_resources": {{
            "budget_categories": [
                {{
                    "category": "カテゴリ",
                    "estimated_cost": 金額,
                    "confidence": 0.0-1.0,
                    "cost_drivers": ["要因1", "要因2"]
                }}
            ],
            "total_estimated_budget": 金額,
            "contingency_percentage": パーセンテージ
        }}
    }},
    "resource_optimization": {{
        "bottlenecks": ["ボトルネック1", "ボトルネック2"],
        "optimization_opportunities": ["最適化機会1", "機会2"],
        "resource_sharing_potential": ["共有可能リソース1", "リソース2"],
        "outsourcing_candidates": ["外注候補1", "候補2"]
    }},
    "capacity_planning": {{
        "resource_timeline": [
            {{
                "period": "期間",
                "resource_demand": {{
                    "developers": 数値,
                    "designers": 数値,
                    "managers": 数値
                }},
                "utilization_rate": 0.0-1.0
            }}
        ],
        "scaling_requirements": ["スケーリング要件1", "要件2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはリソース管理と容量計画の専門家です。"},
                    {"role": "user", "content": resource_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Resource analysis error: {e}")
            return {"resource_categories": {}, "resource_optimization": {}}
    
    async def _perform_risk_analysis(self, project_analysis: Dict, tasks: List[Task]) -> Dict[str, Any]:
        """リスク分析・軽減戦略"""
        risk_prompt = f"""
以下のプロジェクト情報に基づいて包括的なリスク分析を実行してください：

プロジェクト分析: {json.dumps(project_analysis, ensure_ascii=False)}
タスク概要: {json.dumps([{'id': t.id, 'title': t.title, 'complexity': t.complexity_score, 'dependencies': len(t.dependencies)} for t in tasks], ensure_ascii=False)}

以下のJSON形式でリスク分析を返してください：

{{
    "risk_categories": [
        {{
            "category": "technical|operational|financial|strategic|external",
            "risks": [
                {{
                    "risk_id": "RISK_001",
                    "description": "リスクの説明",
                    "probability": 0.0-1.0,
                    "impact": 0.0-1.0,
                    "risk_score": 0.0-1.0,
                    "triggers": ["トリガー1", "トリガー2"],
                    "indicators": ["早期警告指標1", "指標2"],
                    "affected_areas": ["影響領域1", "領域2"],
                    "mitigation_strategies": [
                        {{
                            "strategy": "軽減戦略",
                            "effectiveness": 0.0-1.0,
                            "cost": "low|medium|high",
                            "timeline": "short|medium|long"
                        }}
                    ],
                    "contingency_plans": ["代替計画1", "計画2"],
                    "responsible_party": "責任者",
                    "review_frequency": "weekly|bi-weekly|monthly"
                }}
            ]
        }}
    ],
    "risk_matrix": {{
        "high_impact_high_probability": ["RISK_001"],
        "high_impact_low_probability": ["RISK_002"],
        "low_impact_high_probability": ["RISK_003"],
        "low_impact_low_probability": ["RISK_004"]
    }},
    "overall_risk_assessment": {{
        "project_risk_level": "low|medium|high|critical",
        "key_risk_factors": ["要因1", "要因2", "要因3"],
        "risk_tolerance_recommendations": ["推奨1", "推奨2"],
        "monitoring_framework": ["監視フレームワーク1", "フレームワーク2"]
    }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはリスク管理と予防戦略の専門家です。"},
                    {"role": "user", "content": risk_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Risk analysis error: {e}")
            return {"risk_categories": [], "overall_risk_assessment": {"project_risk_level": "medium"}}
    
    async def optimize_resource_allocation(self, project: Project, constraints: Dict = None) -> ResourceOptimization:
        """リソース配分最適化"""
        try:
            optimization_prompt = f"""
以下のプロジェクト情報に基づいてリソース配分を最適化してください：

プロジェクト: {project.name}
タスク数: {len(project.tasks)}
制約条件: {json.dumps(constraints or {}, ensure_ascii=False)}
現在のリソース: {json.dumps(project.resources, ensure_ascii=False)}

最適化目標:
1. 全体効率の最大化
2. リソース利用率の向上
3. ボトルネックの解消
4. コスト効果の最大化

JSON形式で最適化結果を返してください：

{{
    "optimization_results": {{
        "current_efficiency": 0.0-1.0,
        "optimized_efficiency": 0.0-1.0,
        "efficiency_gain": 0.0-1.0,
        "cost_reduction": 0.0-1.0
    }},
    "resource_reallocation": [
        {{
            "resource_type": "リソースタイプ",
            "current_allocation": {{"task1": 0.3, "task2": 0.7}},
            "optimal_allocation": {{"task1": 0.5, "task2": 0.5}},
            "improvement_rationale": "改善の根拠"
        }}
    ],
    "implementation_plan": [
        {{
            "step": 1,
            "action": "実行アクション",
            "timeline": "タイムライン",
            "resources_needed": ["必要リソース1", "リソース2"],
            "success_metrics": ["成功指標1", "指標2"]
        }}
    ],
    "risk_mitigation": [
        {{
            "risk": "リスク",
            "mitigation": "軽減策",
            "monitoring": "監視方法"
        }}
    ]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたはリソース最適化とオペレーションズリサーチの専門家です。"},
                    {"role": "user", "content": optimization_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return ResourceOptimization(
                resource_type="mixed",
                current_allocation={},
                optimal_allocation={},
                efficiency_gain=result.get('optimization_results', {}).get('efficiency_gain', 0.0),
                implementation_steps=[step['action'] for step in result.get('implementation_plan', [])],
                risk_factors=[risk['risk'] for risk in result.get('risk_mitigation', [])]
            )
            
        except Exception as e:
            print(f"Resource optimization error: {e}")
            return ResourceOptimization("default", {}, {}, 0.0, [], [])
    
    async def generate_predictive_insights(self, project: Project, historical_data: List[Dict] = None) -> List[PredictiveInsight]:
        """予測的インサイト生成"""
        prediction_prompt = f"""
以下の情報に基づいて予測的インサイトを生成してください：

プロジェクト情報: {json.dumps({'name': project.name, 'task_count': len(project.tasks), 'timeline': {k: v.isoformat() if isinstance(v, datetime) else str(v) for k, v in project.timeline.items()}}, ensure_ascii=False)}
履歴データ: {json.dumps(historical_data or [], ensure_ascii=False)}

以下のJSON形式で予測インサイトを返してください：

{{
    "predictive_insights": [
        {{
            "prediction_type": "schedule|budget|quality|risk|resource",
            "description": "予測の説明",
            "probability": 0.0-1.0,
            "impact_score": 0.0-1.0,
            "timeline": "1week|1month|3months|6months",
            "confidence_level": 0.0-1.0,
            "supporting_indicators": ["指標1", "指標2"],
            "potential_outcomes": ["結果1", "結果2", "結果3"],
            "mitigation_strategies": [
                {{
                    "strategy": "軽減戦略",
                    "effectiveness": 0.0-1.0,
                    "implementation_difficulty": "easy|medium|hard"
                }}
            ],
            "monitoring_recommendations": ["監視推奨1", "推奨2"]
        }}
    ],
    "trend_analysis": {{
        "positive_trends": ["ポジティブトレンド1", "トレンド2"],
        "negative_trends": ["ネガティブトレンド1", "トレンド2"],
        "emerging_patterns": ["新興パターン1", "パターン2"]
    }},
    "strategic_recommendations": [
        {{
            "recommendation": "戦略的推奨",
            "rationale": "根拠",
            "expected_benefit": "期待される利益",
            "implementation_complexity": "low|medium|high"
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは予測分析と戦略的洞察の専門家です。"},
                    {"role": "user", "content": prediction_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=3500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            insights = []
            
            for insight_data in result.get('predictive_insights', []):
                insights.append(PredictiveInsight(
                    prediction_type=insight_data.get('prediction_type', 'general'),
                    description=insight_data.get('description', ''),
                    probability=insight_data.get('probability', 0.5),
                    impact_score=insight_data.get('impact_score', 0.5),
                    timeline=insight_data.get('timeline', '1month'),
                    mitigation_strategies=[s.get('strategy', '') for s in insight_data.get('mitigation_strategies', [])],
                    monitoring_indicators=insight_data.get('monitoring_recommendations', [])
                ))
            
            return insights
            
        except Exception as e:
            print(f"Predictive insights error: {e}")
            return []
    
    def _calculate_success_probability(self, project: Project) -> float:
        """成功確率計算"""
        # 複雑性、リスク、リソース要件に基づく簡易計算
        base_probability = 0.7
        
        # タスク複雑性による調整
        avg_complexity = np.mean([task.complexity_score for task in project.tasks]) if project.tasks else 0.5
        complexity_factor = 1.0 - (avg_complexity * 0.3)
        
        # タスク数による調整
        task_count_factor = max(0.5, 1.0 - (len(project.tasks) / 100) * 0.2)
        
        return min(1.0, base_probability * complexity_factor * task_count_factor)
    
    def _fallback_strategic_plan(self, project_description: str) -> Dict[str, Any]:
        """フォールバック戦略計画"""
        return {
            'project': {
                'name': 'Basic Project',
                'description': project_description,
                'tasks': [],
                'success_probability': 0.5
            },
            'strategic_insights': [],
            'automation_opportunities': [],
            'success_probability': 0.5
        }

# 使用例とテスト
if __name__ == "__main__":
    import os
    from firebase_config import firebase_manager
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system = IntelligentAutomationSystem(client, firebase_manager)
    
    async def test():
        result = await system.create_strategic_plan(
            "新しいウェブアプリケーションの開発プロジェクト",
            constraints={"budget": 1000000, "timeline": "3months"},
            stakeholders=["開発チーム", "マーケティング", "経営陣"]
        )
        print(f"Success Probability: {result['success_probability']:.2f}")
        print(f"Tasks Generated: {len(result['project'].get('tasks', []))}")
    
    asyncio.run(test())