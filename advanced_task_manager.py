#!/usr/bin/env python3
"""
Advanced Task Manager - プロアクティブ・インテリジェントタスク管理
超優秀秘書の高度なタスク処理・優先度判断・自動化システム
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class AdvancedTaskManager:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 高度な管理機能
        self.task_dependencies = {}
        self.automated_workflows = {}
        self.intelligent_scheduling = {}
    
    async def analyze_task_complexity(self, user_id: str, task_title: str, description: str = "") -> Dict:
        """タスクの複雑度とリソース要件を分析"""
        try:
            analysis_prompt = f"""
            以下のタスクを詳細分析し、最適な実行プランを策定してください：
            
            【タスク】
            タイトル: {task_title}
            説明: {description}
            
            以下のJSONで詳細分析を返してください：
            {{
                "complexity_score": 1-10,
                "estimated_duration": "具体的な所要時間",
                "skill_requirements": ["必要スキル1", "必要スキル2"],
                "resource_needs": ["必要リソース1", "必要リソース2"],
                "subtasks": [
                    {{
                        "title": "サブタスク1",
                        "duration": "所要時間",
                        "priority": 1-5,
                        "dependencies": ["依存タスク"]
                    }}
                ],
                "optimal_timing": "最適実行タイミング",
                "potential_blockers": ["潜在的な障害"],
                "success_metrics": ["成功指標"],
                "automated_opportunities": ["自動化可能部分"],
                "delegation_candidates": ["委任候補部分"],
                "risk_factors": ["リスク要因"],
                "preparation_steps": ["事前準備"],
                "follow_up_actions": ["フォローアップ"],
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは世界最高レベルのタスク分析・プロジェクト管理専門家です。あらゆるタスクを完璧に分解し、最適化されたプランを提供してください。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(content)
            
            # 分析結果を保存
            await self._save_task_analysis(user_id, task_title, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Task complexity analysis error: {e}")
            return {"confidence": 0.0}
    
    async def create_intelligent_schedule(self, user_id: str, tasks: List[Dict]) -> Dict:
        """AIによる最適スケジューリング"""
        try:
            # ユーザーの作業パターンを取得
            work_patterns = await self._get_work_patterns(user_id)
            
            scheduling_prompt = f"""
            以下のタスクリストを最適にスケジューリングしてください：
            
            【タスクリスト】
            {tasks}
            
            【ユーザーの作業パターン】
            {work_patterns}
            
            以下を考慮して最適スケジュールをJSONで返してください：
            - タスクの優先度と複雑度
            - 依存関係と前提条件
            - ユーザーの生産性パターン
            - エネルギーレベルの変動
            - 締切日とバッファ時間
            - 集中作業時間の確保
            
            {{
                "daily_schedule": {{
                    "2024-01-01": [
                        {{
                            "time": "09:00-11:00",
                            "task": "タスク名",
                            "reasoning": "この時間帯を選んだ理由",
                            "preparation": ["事前準備"],
                            "energy_match": "high/medium/low"
                        }}
                    ]
                }},
                "optimization_strategy": "スケジューリング戦略",
                "productivity_tips": ["生産性向上のコツ"],
                "risk_mitigation": ["リスク軽減策"],
                "flexibility_points": ["調整可能ポイント"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは時間管理とスケジューリングの天才です。個人の特性を考慮した完璧なスケジュールを作成してください。"},
                    {"role": "user", "content": scheduling_prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            schedule = json.loads(content)
            
            # スケジュールを保存
            await self._save_intelligent_schedule(user_id, schedule)
            
            return schedule
            
        except Exception as e:
            print(f"❌ Intelligent scheduling error: {e}")
            return {}
    
    async def identify_automation_opportunities(self, user_id: str) -> List[Dict]:
        """自動化可能なタスクを特定"""
        try:
            # ユーザーの過去のタスクを分析
            past_tasks = await self._get_user_task_history(user_id, days=90)
            
            automation_prompt = f"""
            以下のタスク履歴から自動化・効率化の機会を特定してください：
            
            【過去のタスク履歴】
            {past_tasks[:20]}  # 最新20件
            
            以下の観点で分析し、JSONで返してください：
            {{
                "automation_opportunities": [
                    {{
                        "task_pattern": "繰り返しパターン",
                        "frequency": "頻度",
                        "automation_method": "自動化方法",
                        "time_savings": "時間節約効果",
                        "implementation_difficulty": 1-5,
                        "roi_estimate": "投資対効果",
                        "tools_needed": ["必要ツール"],
                        "setup_steps": ["設定手順"]
                    }}
                ],
                "workflow_optimizations": [
                    {{
                        "current_workflow": "現在のフロー",
                        "optimized_workflow": "最適化後のフロー",
                        "improvement": "改善効果"
                    }}
                ],
                "elimination_candidates": ["削除候補タスク"],
                "delegation_opportunities": ["委任可能タスク"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは業務効率化とオートメーションの専門家です。最大限の効率化を実現する提案をしてください。"},
                    {"role": "user", "content": automation_prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            automation = json.loads(content)
            return automation.get('automation_opportunities', [])
            
        except Exception as e:
            print(f"❌ Automation analysis error: {e}")
            return []
    
    async def smart_task_prioritization(self, user_id: str, context: str = "") -> List[Dict]:
        """AIによる動的優先度調整"""
        try:
            # 現在のタスクを取得
            current_tasks = await self._get_current_tasks(user_id)
            # ユーザーの目標と状況を分析
            user_context = await self._analyze_user_context(user_id, context)
            
            prioritization_prompt = f"""
            現在の状況とコンテキストに基づいて、タスクの優先度を動的に再調整してください：
            
            【現在のタスク】
            {current_tasks}
            
            【ユーザーコンテキスト】
            {user_context}
            
            【追加情報】
            {context}
            
            以下の要因を考慮して優先度を調整し、JSONで返してください：
            - 締切の切迫度
            - ビジネス・個人的重要性
            - 他タスクへの影響度
            - 現在のエネルギー/状況適合性
            - 長期目標への貢献度
            - リスクとコスト
            
            {{
                "prioritized_tasks": [
                    {{
                        "task_id": "ID",
                        "new_priority": 1-10,
                        "reasoning": "優先度変更理由",
                        "urgency_factor": 0.0-1.0,
                        "importance_factor": 0.0-1.0,
                        "context_match": 0.0-1.0,
                        "recommended_action": "next_action",
                        "timing": "immediate/today/this_week/later"
                    }}
                ],
                "priority_shift_summary": "全体的な変更サマリー",
                "context_insights": "状況に基づく洞察",
                "recommendations": ["アクション推奨事項"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは戦略的思考を持つ優秀なエグゼクティブアシスタントです。状況に応じた最適な優先度判断を行ってください。"},
                    {"role": "user", "content": prioritization_prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            prioritization = json.loads(content)
            
            # 優先度の更新を実行
            await self._update_task_priorities(user_id, prioritization['prioritized_tasks'])
            
            return prioritization['prioritized_tasks']
            
        except Exception as e:
            print(f"❌ Smart prioritization error: {e}")
            return []
    
    async def generate_task_insights(self, user_id: str) -> Dict:
        """タスク管理の洞察とレポート生成"""
        try:
            # データ収集
            task_history = await self._get_user_task_history(user_id, days=30)
            completion_patterns = await self._analyze_completion_patterns(user_id)
            productivity_metrics = await self._calculate_productivity_metrics(user_id)
            
            insights_prompt = f"""
            以下のデータからタスク管理の洞察とレポートを生成してください：
            
            【タスク履歴（30日間）】
            {task_history[:15]}
            
            【完了パターン】
            {completion_patterns}
            
            【生産性指標】
            {productivity_metrics}
            
            包括的なレポートをJSONで返してください：
            {{
                "performance_summary": "パフォーマンス要約",
                "strengths": ["強み"],
                "improvement_areas": ["改善ポイント"],
                "productivity_trends": "生産性トレンド",
                "time_management_score": 1-10,
                "task_completion_rate": "完了率",
                "average_task_duration": "平均所要時間",
                "peak_productivity_times": ["最高効率時間帯"],
                "procrastination_patterns": ["先延ばしパターン"],
                "success_strategies": ["成功戦略"],
                "recommended_improvements": [
                    {{
                        "area": "改善分野",
                        "suggestion": "具体的提案",
                        "expected_impact": "期待効果",
                        "implementation": "実装方法"
                    }}
                ],
                "next_month_goals": ["来月の目標"],
                "motivation_boosters": ["モチベーション向上策"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "あなたは生産性とパフォーマンス分析の専門家です。データから深い洞察を抽出し、実用的な改善提案をしてください。"},
                    {"role": "user", "content": insights_prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            insights = json.loads(content)
            
            # 洞察を保存
            await self._save_task_insights(user_id, insights)
            
            return insights
            
        except Exception as e:
            print(f"❌ Task insights generation error: {e}")
            return {}
    
    # Helper methods
    async def _save_task_analysis(self, user_id: str, task_title: str, analysis: Dict):
        """タスク分析結果を保存"""
        try:
            doc = {
                'user_id': user_id,
                'task_title': task_title,
                'analysis': analysis,
                'created_at': datetime.now(self.jst)
            }
            self.db.collection('task_analyses').document().set(doc)
        except Exception as e:
            print(f"❌ Save task analysis error: {e}")
    
    async def _get_work_patterns(self, user_id: str) -> Dict:
        """ユーザーの作業パターンを取得"""
        try:
            # 簡略化：実際の実装ではより詳細な分析
            return {
                "peak_hours": ["09:00-11:00", "14:00-16:00"],
                "low_energy_times": ["13:00-14:00", "16:00-17:00"],
                "preferred_task_types": {
                    "morning": "creative_work",
                    "afternoon": "administrative",
                    "evening": "planning"
                },
                "break_patterns": "25min_work_5min_break",
                "focus_duration": "90_minutes_max"
            }
        except Exception as e:
            print(f"❌ Get work patterns error: {e}")
            return {}
    
    async def _save_intelligent_schedule(self, user_id: str, schedule: Dict):
        """インテリジェントスケジュールを保存"""
        try:
            doc = {
                'user_id': user_id,
                'schedule': schedule,
                'created_at': datetime.now(self.jst),
                'status': 'active'
            }
            self.db.collection('intelligent_schedules').document().set(doc)
        except Exception as e:
            print(f"❌ Save schedule error: {e}")
    
    async def _get_user_task_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """ユーザーのタスク履歴を取得"""
        try:
            start_date = datetime.now(self.jst) - timedelta(days=days)
            query = self.db.collection('todos').where('user_id', '==', user_id)
            
            docs = query.get()
            tasks = []
            
            for doc in docs:
                data = doc.to_dict()
                if data.get('created_at') and data['created_at'] >= start_date:
                    tasks.append(data)
            
            return sorted(tasks, key=lambda x: x.get('created_at', datetime.min), reverse=True)
            
        except Exception as e:
            print(f"❌ Get task history error: {e}")
            return []
    
    async def _get_current_tasks(self, user_id: str) -> List[Dict]:
        """現在のタスクを取得"""
        try:
            query = self.db.collection('todos')\
                          .where('user_id', '==', user_id)\
                          .where('status', '==', 'pending')
            
            docs = query.get()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            print(f"❌ Get current tasks error: {e}")
            return []
    
    async def _analyze_user_context(self, user_id: str, context: str) -> Dict:
        """ユーザーコンテキストを分析"""
        try:
            # 簡略化：実際はより複雑な分析
            return {
                "current_focus": context,
                "stress_level": "medium",
                "available_time": "normal",
                "energy_level": "high",
                "goals_alignment": "high"
            }
        except Exception as e:
            print(f"❌ Context analysis error: {e}")
            return {}
    
    async def _update_task_priorities(self, user_id: str, prioritized_tasks: List[Dict]):
        """タスクの優先度を更新"""
        try:
            for task in prioritized_tasks:
                task_id = task.get('task_id')
                new_priority = task.get('new_priority')
                
                if task_id and new_priority:
                    self.db.collection('todos').document(task_id).update({
                        'priority': new_priority,
                        'updated_at': datetime.now(self.jst),
                        'priority_reasoning': task.get('reasoning', '')
                    })
        except Exception as e:
            print(f"❌ Update priorities error: {e}")
    
    async def _analyze_completion_patterns(self, user_id: str) -> Dict:
        """完了パターンを分析"""
        try:
            # 簡略化：実際の実装はより詳細
            return {
                "average_completion_time": "2_days",
                "peak_completion_days": ["Tuesday", "Thursday"],
                "success_rate": 0.75,
                "common_delays": ["scope_creep", "interruptions"]
            }
        except Exception as e:
            print(f"❌ Completion patterns error: {e}")
            return {}
    
    async def _calculate_productivity_metrics(self, user_id: str) -> Dict:
        """生産性指標を計算"""
        try:
            # 簡略化：実際の実装はより詳細
            return {
                "tasks_per_week": 8.5,
                "completion_rate": 0.78,
                "average_priority": 3.2,
                "time_to_completion": "1.8_days",
                "quality_score": 4.2
            }
        except Exception as e:
            print(f"❌ Productivity metrics error: {e}")
            return {}
    
    async def _save_task_insights(self, user_id: str, insights: Dict):
        """タスク洞察を保存"""
        try:
            doc = {
                'user_id': user_id,
                'insights': insights,
                'generated_at': datetime.now(self.jst),
                'period': '30_days'
            }
            self.db.collection('task_insights').document().set(doc)
        except Exception as e:
            print(f"❌ Save insights error: {e}")