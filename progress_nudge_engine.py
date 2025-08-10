#!/usr/bin/env python3
"""
Progress Nudge Engine
進捗ヌッジ：停滞検知 + 5分でできるサブタスク提案
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pytz
from openai import OpenAI
from firebase_config import firebase_manager

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class NudgeAction:
    title: str
    description: str
    estimated_minutes: int
    confidence: float
    category: str  # "research", "organize", "communicate", "create"

@dataclass
class TaskNudge:
    task_id: str
    task_title: str
    stalled_hours: int
    last_activity: datetime
    nudge_message: str
    micro_steps: List[NudgeAction]
    urgency_level: int  # 1-5
    suggested_next_step: NudgeAction

class ProgressNudgeEngine:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
        
        # 停滞の定義（時間）
        self.stall_thresholds = {
            'high_priority': 4,    # 4時間で停滞
            'medium_priority': 12, # 12時間で停滞
            'low_priority': 24,    # 24時間で停滞
            'default': 24
        }
    
    async def check_stalled_tasks(self) -> List[TaskNudge]:
        """停滞タスクをチェック"""
        try:
            now = datetime.now(JST)
            stalled_tasks = []
            
            # チームToDoをチェック
            team_tasks = await self._get_potentially_stalled_team_tasks(now)
            for task in team_tasks:
                nudge = await self._create_task_nudge(task, now)
                if nudge:
                    stalled_tasks.append(nudge)
            
            # 個人ToDoもチェック（実装は環境に応じて）
            # personal_tasks = await self._get_potentially_stalled_personal_tasks(now)
            
            # 緊急度でソート
            stalled_tasks.sort(key=lambda x: -x.urgency_level)
            
            return stalled_tasks
            
        except Exception as e:
            print(f"❌ Stalled task check error: {e}")
            return []
    
    async def _get_potentially_stalled_team_tasks(self, now: datetime) -> List[Dict]:
        """停滞の可能性があるチームタスクを取得"""
        try:
            # 未完了でupdated_atが古いタスクを取得
            query = self.db.collection('team_todos')\
                .where('status', 'in', ['pending', 'in_progress'])\
                .limit(50)
            
            potentially_stalled = []
            
            for doc in query.stream():
                task = doc.to_dict()
                
                # 最終更新時刻を確認
                last_update = task.get('updated_at', task.get('created_at'))
                if not last_update:
                    continue
                
                hours_since_update = (now - last_update).total_seconds() / 3600
                
                # 優先度に応じた停滞判定
                priority = task.get('priority', 3)
                threshold_key = 'high_priority' if priority >= 4 else \
                               'medium_priority' if priority >= 3 else 'low_priority'
                threshold = self.stall_thresholds[threshold_key]
                
                if hours_since_update > threshold:
                    potentially_stalled.append({
                        **task,
                        'hours_stalled': hours_since_update,
                        'last_activity': last_update
                    })
            
            return potentially_stalled
            
        except Exception as e:
            print(f"❌ Stalled team tasks retrieval error: {e}")
            return []
    
    async def _create_task_nudge(self, task: Dict, now: datetime) -> Optional[TaskNudge]:
        """タスクのナッジを作成"""
        try:
            # マイクロステップ生成
            micro_steps = await self._generate_micro_steps(task)
            
            if not micro_steps:
                return None
            
            # ナッジメッセージ生成
            nudge_message = await self._generate_nudge_message(task, micro_steps)
            
            # 緊急度計算
            urgency = self._calculate_urgency(task)
            
            # 推奨次ステップ（最も実行しやすいもの）
            suggested_step = min(micro_steps, key=lambda x: x.estimated_minutes)
            
            return TaskNudge(
                task_id=task['todo_id'],
                task_title=task['title'],
                stalled_hours=int(task['hours_stalled']),
                last_activity=task['last_activity'],
                nudge_message=nudge_message,
                micro_steps=micro_steps,
                urgency_level=urgency,
                suggested_next_step=suggested_step
            )
            
        except Exception as e:
            print(f"❌ Nudge creation error: {e}")
            return None
    
    async def _generate_micro_steps(self, task: Dict) -> List[NudgeAction]:
        """5分以内でできるマイクロステップを生成"""
        try:
            prompt = f"""
以下のタスクが停滞しています。5分以内でできる小さな次の一歩を3つ提案してください：

タスク: {task['title']}
説明: {task.get('description', '')}
カテゴリ: {task.get('category', '')}
担当者: {task.get('assignee', 'unassigned')}

各ステップは以下の条件を満たすこと：
- 5分以内で完了可能
- 具体的で実行しやすい
- タスク進行に寄与する
- モチベーションを維持できる

JSON形式で回答：
{{
    "steps": [
        {{
            "title": "ステップ名（20字以内）",
            "description": "具体的な行動（50字以内）",
            "estimated_minutes": 推定分数（1-5）,
            "category": "research/organize/communicate/create",
            "confidence": 0.0-1.0の実行しやすさ
        }}
    ]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            micro_steps = []
            for step_data in result.get('steps', []):
                step = NudgeAction(
                    title=step_data['title'],
                    description=step_data['description'],
                    estimated_minutes=step_data['estimated_minutes'],
                    confidence=step_data['confidence'],
                    category=step_data['category']
                )
                micro_steps.append(step)
            
            return micro_steps
            
        except Exception as e:
            print(f"❌ Micro steps generation error: {e}")
            return self._get_fallback_micro_steps(task)
    
    def _get_fallback_micro_steps(self, task: Dict) -> List[NudgeAction]:
        """フォールバックのマイクロステップ"""
        return [
            NudgeAction(
                title="現状を整理",
                description="タスクの現在の状況を3行で書き出す",
                estimated_minutes=3,
                confidence=0.9,
                category="organize"
            ),
            NudgeAction(
                title="次の障害を特定",
                description="なぜ進まないかの理由を1つ明確にする",
                estimated_minutes=2,
                confidence=0.8,
                category="research"
            ),
            NudgeAction(
                title="関係者に相談",
                description="困っていることを誰かに相談する",
                estimated_minutes=5,
                confidence=0.7,
                category="communicate"
            )
        ]
    
    async def _generate_nudge_message(self, task: Dict, 
                                     micro_steps: List[NudgeAction]) -> str:
        """ナッジメッセージ生成"""
        try:
            stalled_hours = int(task['hours_stalled'])
            
            # 停滞時間に応じたトーン
            if stalled_hours >= 48:
                tone = "優しく心配する"
            elif stalled_hours >= 24:
                tone = "励ましの"
            else:
                tone = "軽やかな"
            
            prompt = f"""
{tone}トーンで、以下のタスクの進捗を促すナッジメッセージを生成してください：

タスク: {task['title']}
停滞時間: {stalled_hours}時間
最良のマイクロステップ: {micro_steps[0].title} - {micro_steps[0].description}

要件:
- 40字以内
- 責めない、プレッシャーを与えない
- 具体的な次のアクションを含む
- やる気を起こさせる

例: "「API設計」お疲れ様！まずは現状を3行で整理してみませんか？✨"
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.6,
                max_tokens=60
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Nudge message generation error: {e}")
            return f"「{task['title']}」の件、一歩ずつ進めていきましょう！"
    
    def _calculate_urgency(self, task: Dict) -> int:
        """緊急度を計算（1-5）"""
        urgency = 1
        
        # 優先度による加算
        priority = task.get('priority', 3)
        if priority >= 5: urgency += 2
        elif priority >= 4: urgency += 1
        
        # 期限による加算
        due_date = task.get('due_date')
        if due_date:
            now = datetime.now(JST)
            days_until_due = (due_date - now).days
            if days_until_due < 0: urgency += 2  # 期限超過
            elif days_until_due == 0: urgency += 2  # 今日期限
            elif days_until_due == 1: urgency += 1  # 明日期限
        
        # 停滞時間による加算
        stalled_hours = task.get('hours_stalled', 0)
        if stalled_hours >= 72: urgency += 1  # 3日以上
        elif stalled_hours >= 48: urgency += 1  # 2日以上
        
        return min(5, urgency)
    
    async def create_micro_todo(self, parent_task_id: str, micro_step: NudgeAction,
                               user_id: str) -> bool:
        """マイクロステップをToDoとして登録"""
        try:
            from team_todo_manager import TeamTodoManager
            
            # 親タスクの情報取得
            parent_doc = self.db.collection('team_todos').document(parent_task_id).get()
            if not parent_doc.exists:
                return False
            
            parent_task = parent_doc.to_dict()
            
            # マイクロToDo作成
            micro_todo = {
                'todo_id': f"micro_{parent_task_id}_{int(datetime.now().timestamp())}",
                'creator_id': user_id,
                'title': f"[micro] {micro_step.title}",
                'description': micro_step.description,
                'assignee': parent_task.get('assignee', 'unassigned'),
                'project': parent_task.get('project', 'general'),
                'category': 'micro_task',
                'priority': 2,  # 低優先度
                'estimated_hours': micro_step.estimated_minutes / 60,
                'parent_task_id': parent_task_id,
                'status': 'pending',
                'created_at': datetime.now(JST),
                'updated_at': datetime.now(JST),
                'metadata': {
                    'is_micro_step': True,
                    'original_category': micro_step.category,
                    'confidence': micro_step.confidence
                }
            }
            
            # 保存
            doc_ref = self.db.collection('team_todos').document(micro_todo['todo_id'])
            doc_ref.set(micro_todo)
            
            return True
            
        except Exception as e:
            print(f"❌ Micro todo creation error: {e}")
            return False
    
    def format_nudge_message(self, nudge: TaskNudge, include_actions: bool = True) -> str:
        """ナッジメッセージのフォーマット"""
        urgency_emoji = {1: "📌", 2: "⚡", 3: "🔥", 4: "💥", 5: "🚨"}
        
        message = f"{urgency_emoji.get(nudge.urgency_level, '📌')} **進捗ナッジ**\n\n"
        message += f"📋 **タスク**: {nudge.task_title}\n"
        message += f"⏰ **停滞時間**: {nudge.stalled_hours}時間\n\n"
        message += f"💬 {nudge.nudge_message}\n\n"
        
        if include_actions:
            message += f"⚡ **すぐできる次の一歩** ({nudge.suggested_next_step.estimated_minutes}分):\n"
            message += f"▶️ {nudge.suggested_next_step.title}\n"
            message += f"📝 {nudge.suggested_next_step.description}\n\n"
            
            if len(nudge.micro_steps) > 1:
                message += f"💡 **他の選択肢**:\n"
                for step in nudge.micro_steps[1:3]:  # 最大2つ追加表示
                    message += f"• {step.title} ({step.estimated_minutes}分)\n"
        
        return message
    
    async def send_nudge_notifications(self, discord_client, channel_id: str) -> int:
        """ナッジ通知を送信"""
        try:
            stalled_tasks = await self.check_stalled_tasks()
            
            if not stalled_tasks:
                return 0
            
            # 最も緊急度の高いタスクのみ通知（スパム防止）
            top_nudge = stalled_tasks[0]
            
            # 通知メッセージ作成
            message = f"@here {self.format_nudge_message(top_nudge)}"
            message += f"\n📞 `C! nudge {top_nudge.task_id}` で詳細確認"
            
            # Discord送信（実装は環境に応じて調整）
            channel = discord_client.get_channel(int(channel_id))
            if channel:
                await channel.send(message)
                return 1
            
            return 0
            
        except Exception as e:
            print(f"❌ Nudge notification error: {e}")
            return 0