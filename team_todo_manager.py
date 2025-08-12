#!/usr/bin/env python3
"""
Team ToDo Management System
チーム全体のToDo管理と担当者割り当てシステム
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class TeamTodoManager:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # チームメンバーの定義
        self.team_members = {
            'mrc': {
                'name': 'MRC',
                'skills': ['開発', 'デザイン', 'フロントエンド'],
                'capacity': 10,  # 同時に処理できるタスク数
                'discord_id': None
            },
            'supy': {
                'name': 'Supy',
                'skills': ['バックエンド', 'インフラ', 'データベース'],
                'capacity': 10,
                'discord_id': None
            },
            'unassigned': {
                'name': '未割り当て',
                'skills': [],
                'capacity': 999,
                'discord_id': None
            }
        }
        
        # タスクステータス
        self.task_statuses = {
            'pending': '未着手',
            'in_progress': '進行中',
            'review': 'レビュー待ち',
            'blocked': 'ブロック中',
            'completed': '完了',
            'cancelled': 'キャンセル'
        }
        
        # プロジェクトカテゴリ
        self.project_categories = {
            'development': '開発',
            'design': 'デザイン',
            'infrastructure': 'インフラ',
            'documentation': 'ドキュメント',
            'testing': 'テスト',
            'meeting': 'ミーティング',
            'research': 'リサーチ',
            'other': 'その他'
        }
    
    async def create_team_todo(self, creator_id: str, title: str, 
                              description: str = "",
                              assignee: str = "unassigned",
                              project: str = "general",
                              category: str = "other",
                              priority: int = 3,
                              due_date: Optional[datetime] = None,
                              dependencies: List[str] = None,
                              tags: List[str] = None) -> Dict:
        """チームToDo作成"""
        try:
            # AI分析でタスクを解析
            analysis = await self._analyze_task(title, description)
            
            # 自動割り当て提案
            if assignee == "unassigned":
                suggested_assignee = await self._suggest_assignee(analysis)
                assignee = suggested_assignee
            
            team_todo = {
                'todo_id': str(uuid.uuid4()),
                'creator_id': creator_id,
                'title': title,
                'description': description,
                'assignee': assignee,
                'project': project,
                'category': category if category in self.project_categories else analysis.get('category', 'other'),
                'priority': priority,
                'estimated_hours': analysis.get('estimated_hours', 1),
                'due_date': due_date,
                'dependencies': dependencies or [],
                'tags': tags or analysis.get('tags', []),
                'status': 'pending',
                'created_at': datetime.now(self.jst),
                'updated_at': datetime.now(self.jst),
                'completed_at': None,
                'comments': [],
                'attachments': [],
                'subtasks': [],
                'metadata': {
                    'auto_assigned': assignee == suggested_assignee,
                    'complexity': analysis.get('complexity', 'medium'),
                    'skills_required': analysis.get('skills_required', [])
                }
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('team_todos').document(team_todo['todo_id'])
            doc_ref.set(team_todo)
            
            # 担当者の負荷を更新
            await self._update_member_workload(assignee, 1)
            
            print(f"✅ Team ToDo created: {title} -> {assignee}")
            return team_todo
            
        except Exception as e:
            print(f"❌ Team ToDo creation error: {e}")
            return {}
    
    async def get_team_todos(self, filters: Dict = None) -> List[Dict]:
        """チームToDoリスト取得"""
        try:
            query = self.db.collection('team_todos')
            
            if filters:
                if 'assignee' in filters:
                    query = query.where('assignee', '==', filters['assignee'])
                if 'status' in filters:
                    query = query.where('status', '==', filters['status'])
                if 'project' in filters:
                    query = query.where('project', '==', filters['project'])
                if 'category' in filters:
                    query = query.where('category', '==', filters['category'])
            else:
                # デフォルトで削除されたTODOを除外
                query = query.where('status', '!=', 'deleted')
            
            # 優先度と締切日でソート
            todos = []
            for doc in query.stream():
                todo = doc.to_dict()
                todo['id'] = doc.id  # Add document ID
                # 追加の安全チェック：削除済みTODOを除外
                if todo.get('status') != 'deleted':
                    todos.append(todo)
            
            # カスタムソート（優先度高い順、締切日近い順）
            todos.sort(key=lambda x: (
                -x.get('priority', 0),
                x.get('due_date') or datetime.max.replace(tzinfo=self.jst)
            ))
            
            return todos
            
        except Exception as e:
            print(f"❌ Team ToDo retrieval error: {e}")
            return []
    
    async def get_team_dashboard(self) -> Dict:
        """チームダッシュボード情報取得"""
        try:
            todos = await self.get_team_todos()
            
            dashboard = {
                'total_tasks': len(todos),
                'by_status': {},
                'by_assignee': {},
                'by_category': {},
                'by_priority': {},
                'overdue_tasks': [],
                'upcoming_deadlines': [],
                'blocked_tasks': [],
                'team_velocity': 0,
                'workload_distribution': {}
            }
            
            now = datetime.now(self.jst)
            
            for todo in todos:
                # ステータス別集計
                status = todo.get('status', 'pending')
                dashboard['by_status'][status] = dashboard['by_status'].get(status, 0) + 1
                
                # 担当者別集計
                assignee = todo.get('assignee', 'unassigned')
                if assignee not in dashboard['by_assignee']:
                    dashboard['by_assignee'][assignee] = {
                        'total': 0,
                        'pending': 0,
                        'in_progress': 0,
                        'completed': 0
                    }
                dashboard['by_assignee'][assignee]['total'] += 1
                dashboard['by_assignee'][assignee][status] = dashboard['by_assignee'][assignee].get(status, 0) + 1
                
                # カテゴリ別集計
                category = todo.get('category', 'other')
                dashboard['by_category'][category] = dashboard['by_category'].get(category, 0) + 1
                
                # 優先度別集計
                priority = todo.get('priority', 3)
                dashboard['by_priority'][priority] = dashboard['by_priority'].get(priority, 0) + 1
                
                # 期限超過タスク
                if todo.get('due_date') and todo['due_date'] < now and status != 'completed':
                    dashboard['overdue_tasks'].append({
                        'title': todo['title'],
                        'assignee': assignee,
                        'days_overdue': (now - todo['due_date']).days
                    })
                
                # 直近の締切（7日以内）
                if todo.get('due_date'):
                    days_until = (todo['due_date'] - now).days
                    if 0 <= days_until <= 7 and status != 'completed':
                        dashboard['upcoming_deadlines'].append({
                            'title': todo['title'],
                            'assignee': assignee,
                            'due_date': todo['due_date'],
                            'days_remaining': days_until
                        })
                
                # ブロック中のタスク
                if status == 'blocked':
                    dashboard['blocked_tasks'].append({
                        'title': todo['title'],
                        'assignee': assignee,
                        'blocked_since': todo.get('updated_at')
                    })
            
            # チーム速度（過去7日間の完了タスク数）
            week_ago = now - timedelta(days=7)
            completed_this_week = sum(
                1 for todo in todos 
                if todo.get('status') == 'completed' 
                and todo.get('completed_at', datetime.min.replace(tzinfo=self.jst)) > week_ago
            )
            dashboard['team_velocity'] = completed_this_week / 7  # 1日あたりの完了タスク数
            
            # ワークロード分布
            for member_id, member_data in self.team_members.items():
                if member_id in dashboard['by_assignee']:
                    active_tasks = (
                        dashboard['by_assignee'][member_id].get('pending', 0) +
                        dashboard['by_assignee'][member_id].get('in_progress', 0)
                    )
                    dashboard['workload_distribution'][member_id] = {
                        'name': member_data['name'],
                        'active_tasks': active_tasks,
                        'capacity': member_data['capacity'],
                        'utilization': (active_tasks / member_data['capacity']) * 100 if member_data['capacity'] > 0 else 0
                    }
            
            return dashboard
            
        except Exception as e:
            print(f"❌ Dashboard generation error: {e}")
            return {}
    
    async def assign_todo(self, todo_id: str, new_assignee: str, 
                         reassign_reason: str = "") -> bool:
        """ToDo担当者変更"""
        try:
            doc_ref = self.db.collection('team_todos').document(todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            todo = doc.to_dict()
            old_assignee = todo.get('assignee', 'unassigned')
            
            # 更新
            update_data = {
                'assignee': new_assignee,
                'updated_at': datetime.now(self.jst)
            }
            
            # 再割り当て履歴を追加
            if 'assignment_history' not in todo:
                todo['assignment_history'] = []
            
            todo['assignment_history'].append({
                'from': old_assignee,
                'to': new_assignee,
                'timestamp': datetime.now(self.jst),
                'reason': reassign_reason
            })
            
            update_data['assignment_history'] = todo['assignment_history']
            
            doc_ref.update(update_data)
            
            # ワークロード更新
            await self._update_member_workload(old_assignee, -1)
            await self._update_member_workload(new_assignee, 1)
            
            return True
            
        except Exception as e:
            print(f"❌ Assignment error: {e}")
            return False
    
    async def update_todo_status(self, todo_id: str, new_status: str, 
                                comment: str = "") -> bool:
        """ToDoステータス更新"""
        try:
            doc_ref = self.db.collection('team_todos').document(todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            todo = doc.to_dict()
            
            update_data = {
                'status': new_status,
                'updated_at': datetime.now(self.jst)
            }
            
            # 完了時の処理
            if new_status == 'completed':
                update_data['completed_at'] = datetime.now(self.jst)
                # ワークロード更新
                await self._update_member_workload(todo.get('assignee', 'unassigned'), -1)
            
            # コメント追加
            if comment:
                if 'comments' not in todo:
                    todo['comments'] = []
                todo['comments'].append({
                    'text': comment,
                    'timestamp': datetime.now(self.jst),
                    'type': 'status_change',
                    'old_status': todo.get('status'),
                    'new_status': new_status
                })
                update_data['comments'] = todo['comments']
            
            doc_ref.update(update_data)
            return True
            
        except Exception as e:
            print(f"❌ Status update error: {e}")
            return False
    
    async def update_todo_title(self, todo_id: str, new_title: str, 
                               comment: str = "") -> bool:
        """ToDoタイトル更新"""
        try:
            doc_ref = self.db.collection('team_todos').document(todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            todo = doc.to_dict()
            old_title = todo.get('title', '')
            
            update_data = {
                'title': new_title,
                'updated_at': datetime.now(self.jst)
            }
            
            # コメント追加
            if comment or old_title != new_title:
                if 'comments' not in todo:
                    todo['comments'] = []
                todo['comments'].append({
                    'text': comment or f'タイトル変更: "{old_title}" → "{new_title}"',
                    'timestamp': datetime.now(self.jst),
                    'type': 'title_change',
                    'old_title': old_title,
                    'new_title': new_title
                })
                update_data['comments'] = todo['comments']
            
            doc_ref.update(update_data)
            return True
            
        except Exception as e:
            print(f"❌ Title update error: {e}")
            return False
    
    async def add_subtask(self, parent_todo_id: str, subtask_title: str) -> bool:
        """サブタスク追加"""
        try:
            doc_ref = self.db.collection('team_todos').document(parent_todo_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            todo = doc.to_dict()
            
            if 'subtasks' not in todo:
                todo['subtasks'] = []
            
            subtask = {
                'subtask_id': str(uuid.uuid4()),
                'title': subtask_title,
                'completed': False,
                'created_at': datetime.now(self.jst)
            }
            
            todo['subtasks'].append(subtask)
            
            doc_ref.update({
                'subtasks': todo['subtasks'],
                'updated_at': datetime.now(self.jst)
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Subtask addition error: {e}")
            return False
    
    async def _analyze_task(self, title: str, description: str) -> Dict:
        """AIでタスクを分析"""
        try:
            prompt = f"""
以下のタスクを分析してください：

タイトル: {title}
説明: {description}

以下の情報をJSON形式で返してください：
{{
    "category": "development/design/infrastructure/documentation/testing/meeting/research/other",
    "estimated_hours": 推定作業時間（数値）,
    "complexity": "low/medium/high",
    "skills_required": ["必要なスキルのリスト"],
    "tags": ["関連タグのリスト"],
    "suggested_assignee": "mrc/supy/unassigned",
    "urgency": 1-5の緊急度
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Task analysis error: {e}")
            return {
                'category': 'other',
                'estimated_hours': 1,
                'complexity': 'medium',
                'skills_required': [],
                'tags': [],
                'suggested_assignee': 'unassigned',
                'urgency': 3
            }
    
    async def _suggest_assignee(self, task_analysis: Dict) -> str:
        """タスクに最適な担当者を提案"""
        try:
            skills_required = task_analysis.get('skills_required', [])
            
            # スキルマッチング
            best_match = 'unassigned'
            best_score = 0
            
            for member_id, member_data in self.team_members.items():
                if member_id == 'unassigned':
                    continue
                
                # スキルの一致度を計算
                matching_skills = set(skills_required) & set(member_data['skills'])
                score = len(matching_skills)
                
                # 現在のワークロードを考慮
                workload = await self._get_member_workload(member_id)
                if workload < member_data['capacity']:
                    score += (member_data['capacity'] - workload) / member_data['capacity']
                
                if score > best_score:
                    best_score = score
                    best_match = member_id
            
            return best_match
            
        except Exception as e:
            print(f"❌ Assignee suggestion error: {e}")
            return 'unassigned'
    
    async def _get_member_workload(self, member_id: str) -> int:
        """メンバーの現在のワークロード取得"""
        try:
            query = self.db.collection('team_todos').where('assignee', '==', member_id).where('status', 'in', ['pending', 'in_progress'])
            
            count = 0
            for doc in query.stream():
                count += 1
            
            return count
            
        except Exception as e:
            print(f"❌ Workload retrieval error: {e}")
            return 0
    
    async def _update_member_workload(self, member_id: str, delta: int) -> None:
        """メンバーのワークロード更新（キャッシュ用）"""
        # 実装は必要に応じて追加
        pass
    
    async def generate_team_report(self) -> str:
        """チームレポート生成"""
        try:
            dashboard = await self.get_team_dashboard()
            
            report = "📊 **チームToDoレポート**\n\n"
            
            # サマリー
            report += f"**総タスク数**: {dashboard['total_tasks']}\n"
            report += f"**チーム速度**: {dashboard['team_velocity']:.1f} タスク/日\n\n"
            
            # ステータス別
            report += "**📈 ステータス別**\n"
            for status, count in dashboard['by_status'].items():
                status_name = self.task_statuses.get(status, status)
                report += f"  {status_name}: {count}\n"
            report += "\n"
            
            # 担当者別
            report += "**👥 担当者別ワークロード**\n"
            for member_id, data in dashboard['workload_distribution'].items():
                report += f"  {data['name']}: {data['active_tasks']}/{data['capacity']} "
                report += f"({data['utilization']:.0f}%)\n"
            report += "\n"
            
            # 期限超過
            if dashboard['overdue_tasks']:
                report += "**⚠️ 期限超過タスク**\n"
                for task in dashboard['overdue_tasks'][:5]:
                    report += f"  • {task['title']} ({task['assignee']}) - {task['days_overdue']}日超過\n"
                report += "\n"
            
            # 直近の締切
            if dashboard['upcoming_deadlines']:
                report += "**📅 直近の締切**\n"
                for task in dashboard['upcoming_deadlines'][:5]:
                    report += f"  • {task['title']} ({task['assignee']}) - {task['days_remaining']}日後\n"
                report += "\n"
            
            # ブロック中
            if dashboard['blocked_tasks']:
                report += "**🚫 ブロック中のタスク**\n"
                for task in dashboard['blocked_tasks'][:5]:
                    report += f"  • {task['title']} ({task['assignee']})\n"
            
            return report
            
        except Exception as e:
            print(f"❌ Report generation error: {e}")
            return "レポート生成に失敗しました。"