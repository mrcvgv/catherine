#!/usr/bin/env python3
"""
Morning Briefing System
朝ブリーフ：今日の最重要3件＋所要時間見積＋空き時間活用案
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import pytz
from openai import OpenAI
from firebase_config import firebase_manager

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class BriefingItem:
    title: str
    priority: int
    estimated_hours: float
    deadline: Optional[datetime]
    category: str
    assignee: str
    status: str
    urgency_reason: str

class MorningBriefingSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
        
    async def generate_daily_briefing(self, team_mode: bool = True) -> Dict:
        """朝のブリーフィング生成"""
        try:
            now = datetime.now(JST)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # 今日のタスクを取得
            if team_mode:
                tasks = await self._get_team_tasks_today()
            else:
                tasks = await self._get_personal_tasks_today()
            
            # 優先度とタイムライン分析
            briefing_items = await self._analyze_tasks(tasks)
            
            # AI分析でブリーフィング作成
            briefing = await self._create_briefing_analysis(briefing_items, now)
            
            return {
                'date': now.strftime('%Y年%m月%d日 (%A)'),
                'time_generated': now.isoformat(),
                'summary': briefing['summary'],
                'top_3_tasks': briefing['top_3'],
                'time_estimates': briefing['time_estimates'],
                'free_time_suggestions': briefing['free_time'],
                'risks_alerts': briefing['risks'],
                'quick_wins': briefing['quick_wins'],
                'total_workload': briefing['workload'],
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Briefing generation error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_team_tasks_today(self) -> List[Dict]:
        """チームの今日のタスク取得"""
        try:
            # 期限が今日またはそれ以前の未完了タスク
            now = datetime.now(JST)
            today_end = now.replace(hour=23, minute=59, second=59)
            
            query = self.db.collection('team_todos')\
                .where('status', 'in', ['pending', 'in_progress'])\
                .limit(50)
            
            tasks = []
            for doc in query.stream():
                task = doc.to_dict()
                # 今日やるべきタスクを優先的に選択
                if (task.get('due_date') and task['due_date'] <= today_end) or \
                   task.get('priority', 0) >= 4:
                    tasks.append(task)
            
            # 優先度でソート
            tasks.sort(key=lambda x: (-x.get('priority', 0), x.get('created_at', datetime.min)))
            return tasks[:20]  # 最大20件
            
        except Exception as e:
            print(f"❌ Team tasks retrieval error: {e}")
            return []
    
    async def _get_personal_tasks_today(self) -> List[Dict]:
        """個人の今日のタスク取得（実装は環境に応じて調整）"""
        # 個人タスク用のクエリを実装
        return []
    
    async def _analyze_tasks(self, tasks: List[Dict]) -> List[BriefingItem]:
        """タスク分析"""
        briefing_items = []
        
        for task in tasks:
            # 緊急度の理由を判定
            urgency_reason = self._calculate_urgency_reason(task)
            
            # 所要時間見積もり
            estimated_hours = task.get('estimated_hours', 1.0)
            if not estimated_hours:
                estimated_hours = await self._estimate_task_duration(task['title'])
            
            item = BriefingItem(
                title=task['title'],
                priority=task.get('priority', 3),
                estimated_hours=estimated_hours,
                deadline=task.get('due_date'),
                category=task.get('category', 'other'),
                assignee=task.get('assignee', 'unassigned'),
                status=task.get('status', 'pending'),
                urgency_reason=urgency_reason
            )
            briefing_items.append(item)
        
        return briefing_items
    
    def _calculate_urgency_reason(self, task: Dict) -> str:
        """緊急度の理由を判定"""
        now = datetime.now(JST)
        
        if task.get('due_date'):
            time_left = task['due_date'] - now
            if time_left.total_seconds() < 0:
                return "期限超過"
            elif time_left.days == 0:
                return "今日が期限"
            elif time_left.days == 1:
                return "明日が期限"
            elif time_left.days <= 3:
                return f"{time_left.days}日後期限"
        
        if task.get('priority', 0) >= 4:
            return "高優先度"
        
        if task.get('status') == 'blocked':
            return "ブロック解除要"
        
        return "通常"
    
    async def _estimate_task_duration(self, title: str) -> float:
        """AIで作業時間見積もり"""
        try:
            prompt = f"""
以下のタスクの作業時間を見積もってください（時間単位）：

タスク: {title}

以下のガイドラインで判断：
- 調査・リサーチ: 1-3時間
- 設計・企画: 2-4時間  
- 実装・制作: 3-8時間
- テスト・レビュー: 1-2時間
- 会議・打合せ: 0.5-2時間
- ドキュメント作成: 1-3時間

数値のみで回答してください（例: 2.5）
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            duration_str = response.choices[0].message.content.strip()
            return float(duration_str)
            
        except:
            return 1.5  # デフォルト
    
    async def _create_briefing_analysis(self, items: List[BriefingItem], now: datetime) -> Dict:
        """AIでブリーフィング分析"""
        try:
            # タスク情報をテキスト化
            task_summary = ""
            for i, item in enumerate(items, 1):
                deadline_str = item.deadline.strftime('%m/%d %H:%M') if item.deadline else "未設定"
                task_summary += f"{i}. {item.title} ({item.estimated_hours}h, {item.assignee}, 期限:{deadline_str}, {item.urgency_reason})\n"
            
            prompt = f"""
あなたは超優秀な経営者向け秘書です。以下のタスク状況を30秒で理解できるブリーフィングにしてください。

【今日の日時】{now.strftime('%Y/%m/%d (%A) %H:%M')}

【タスク一覧】
{task_summary}

以下のJSON形式で回答してください：
{{
    "summary": "今日の全体状況を1行で",
    "top_3": [
        {{"task": "タスク名", "reason": "選択理由", "time": "見積時間"}},
        {{"task": "タスク名", "reason": "選択理由", "time": "見積時間"}},
        {{"task": "タスク名", "reason": "選択理由", "time": "見積時間"}}
    ],
    "time_estimates": {{
        "total_hours": 総所要時間,
        "morning_block": "午前の推奨タスク",
        "afternoon_block": "午後の推奨タスク"
    }},
    "free_time": [
        "空き時間の活用案1（5-15分でできること）",
        "空き時間の活用案2"
    ],
    "risks": [
        "今日のリスク・懸念事項"
    ],
    "quick_wins": [
        "すぐ完了できそうなタスク（30分以内）"
    ],
    "workload": "適正/過多/軽め"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Briefing analysis error: {e}")
            return self._get_fallback_briefing(items)
    
    def _get_fallback_briefing(self, items: List[BriefingItem]) -> Dict:
        """フォールバックブリーフィング"""
        top_3 = items[:3] if items else []
        total_hours = sum(item.estimated_hours for item in items)
        
        return {
            'summary': f"本日のタスク {len(items)} 件、総所要時間 {total_hours:.1f} 時間",
            'top_3': [
                {
                    'task': item.title,
                    'reason': item.urgency_reason,
                    'time': f"{item.estimated_hours}h"
                } for item in top_3
            ],
            'time_estimates': {
                'total_hours': total_hours,
                'morning_block': '優先度高のタスクを午前に',
                'afternoon_block': 'ルーチンタスクを午後に'
            },
            'free_time': ['メール確認', '次の日の準備'],
            'risks': ['期限の迫っているタスクを優先'],
            'quick_wins': [item.title for item in items if item.estimated_hours <= 0.5],
            'workload': '適正' if total_hours <= 8 else '過多' if total_hours > 10 else '軽め'
        }
    
    def format_briefing_message(self, briefing: Dict) -> str:
        """ブリーフィングをDiscordメッセージ形式に"""
        if not briefing.get('success'):
            return "❌ ブリーフィング生成に失敗しました。"
        
        message = f"🌅 **{briefing['date']} - 朝のブリーフィング**\n\n"
        
        # サマリー
        message += f"📋 **概況**: {briefing['summary']}\n\n"
        
        # TOP3タスク
        message += "🎯 **今日の最重要3件**\n"
        for i, task in enumerate(briefing['top_3'], 1):
            message += f"{i}. **{task['task']}** ({task['time']}) - {task['reason']}\n"
        message += "\n"
        
        # 時間見積もり
        est = briefing['time_estimates']
        message += f"⏰ **時間配分** (総計: {est['total_hours']:.1f}h)\n"
        message += f"🌅 午前: {est['morning_block']}\n"
        message += f"🌇 午後: {est['afternoon_block']}\n\n"
        
        # ワークロード
        workload_emoji = {"適正": "✅", "過多": "⚠️", "軽め": "😌"}
        message += f"📊 **ワークロード**: {workload_emoji.get(briefing['workload'], '📊')} {briefing['workload']}\n\n"
        
        # リスク
        if briefing['risks_alerts']:
            message += "⚠️ **注意事項**\n"
            for risk in briefing['risks_alerts']:
                message += f"• {risk}\n"
            message += "\n"
        
        # クイックウィン
        if briefing['quick_wins']:
            message += "⚡ **すぐ片付くタスク**\n"
            for win in briefing['quick_wins'][:3]:
                message += f"• {win}\n"
            message += "\n"
        
        # 空き時間活用
        if briefing['free_time_suggestions']:
            message += "💡 **スキマ時間で**\n"
            for suggestion in briefing['free_time_suggestions']:
                message += f"• {suggestion}\n"
        
        message += "\n良い一日を！🚀"
        
        return message