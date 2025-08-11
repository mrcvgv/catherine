#!/usr/bin/env python3
"""
Action Summary & Decision Logging System
実行後サマリ + 決定ログ化：各アクションの結果を1行で追記
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pytz
from openai import OpenAI
from firebase_config import firebase_manager

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ActionSummary:
    action_id: str
    user_id: str
    action_type: str  # "todo.create", "todo.update", "remind.set", etc.
    input_text: str
    result: str  # 1行サマリー
    success: bool
    timestamp: datetime
    execution_time_ms: int
    changes_made: List[str]
    next_actions: List[str]
    confidence_score: float

@dataclass
class DecisionLog:
    decision_id: str
    user_id: str
    context: str
    decision: str
    reasoning: str  # 結論→根拠→代替案→次の一手
    alternatives: List[str]
    next_steps: List[str]
    timestamp: datetime
    urgency: str  # "high", "medium", "low"
    impact: str   # "high", "medium", "low"

class ActionSummarySystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
    
    async def log_action_result(self, user_id: str, action_type: str, 
                               input_text: str, result_data: Dict,
                               execution_time_ms: int = 0) -> ActionSummary:
        """アクション実行結果をログ"""
        try:
            # 1行サマリー生成
            summary_text = await self._generate_action_summary(
                action_type, input_text, result_data
            )
            
            # 変更内容を抽出
            changes = self._extract_changes(action_type, result_data)
            
            # 次のアクション提案
            next_actions = await self._suggest_next_actions(
                action_type, result_data, input_text
            )
            
            action_summary = ActionSummary(
                action_id=f"{user_id}_{int(datetime.now().timestamp())}",
                user_id=user_id,
                action_type=action_type,
                input_text=input_text[:100],
                result=summary_text,
                success=result_data.get('success', True),
                timestamp=datetime.now(JST),
                execution_time_ms=execution_time_ms,
                changes_made=changes,
                next_actions=next_actions,
                confidence_score=result_data.get('confidence', 1.0)
            )
            
            # Firestoreに保存
            doc_ref = self.db.collection('action_logs').document(action_summary.action_id)
            doc_ref.set(asdict(action_summary))
            
            return action_summary
            
        except Exception as e:
            print(f"❌ Action logging error: {e}")
            return None
    
    async def _generate_action_summary(self, action_type: str, 
                                     input_text: str, result_data: Dict) -> str:
        """1行サマリー生成"""
        try:
            prompt = f"""
以下のアクション実行結果を1行（30字以内）でサマリーしてください：

アクション種別: {action_type}
入力: {input_text}
結果: {result_data}

フォーマット: "○○を実行→結果" の形式で、要点のみ簡潔に。
例: "API設計ToDoを作成→優先度高で明日期限設定"
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Summary generation error: {e}")
            return f"{action_type}を実行"
    
    def _extract_changes(self, action_type: str, result_data: Dict) -> List[str]:
        """変更内容を抽出"""
        changes = []
        
        if action_type.startswith("todo."):
            if result_data.get('title'):
                changes.append(f"タイトル: {result_data['title']}")
            if result_data.get('due_date'):
                changes.append(f"期限: {result_data['due_date']}")
            if result_data.get('priority'):
                changes.append(f"優先度: {result_data['priority']}")
            if result_data.get('assignee'):
                changes.append(f"担当: {result_data['assignee']}")
        
        elif action_type.startswith("remind."):
            if result_data.get('remind_at'):
                changes.append(f"通知: {result_data['remind_at']}")
            if result_data.get('message'):
                changes.append(f"内容: {result_data['message'][:20]}")
        
        return changes
    
    async def _suggest_next_actions(self, action_type: str, 
                                   result_data: Dict, input_text: str) -> List[str]:
        """次のアクション提案"""
        suggestions = []
        
        # ToDoに関連する次のアクション
        if action_type == "todo.create":
            if result_data.get('priority', 0) >= 4:
                suggestions.append("リマインダー設定を検討")
            if not result_data.get('assignee') or result_data['assignee'] == 'unassigned':
                suggestions.append("担当者を割り当て")
            if not result_data.get('due_date'):
                suggestions.append("期限を設定")
        
        elif action_type == "todo.update":
            suggestions.append("関連タスクも確認")
            if 'priority' in result_data:
                suggestions.append("チームに変更を通知")
        
        elif action_type == "todo.complete":
            suggestions.append("次のタスクを開始")
            suggestions.append("完了報告を作成")
        
        return suggestions[:2]  # 最大2つ
    
    async def create_decision_memo(self, user_id: str, context: str, 
                                  decision: str, reasoning: str = "") -> DecisionLog:
        """決裁メモ生成（結論→根拠→代替案→次の一手）"""
        try:
            # AI分析で構造化
            structured_memo = await self._analyze_decision(context, decision, reasoning)
            
            decision_log = DecisionLog(
                decision_id=f"decision_{user_id}_{int(datetime.now().timestamp())}",
                user_id=user_id,
                context=context,
                decision=decision,
                reasoning=structured_memo['reasoning'],
                alternatives=structured_memo['alternatives'],
                next_steps=structured_memo['next_steps'],
                timestamp=datetime.now(JST),
                urgency=structured_memo.get('urgency', 'medium'),
                impact=structured_memo.get('impact', 'medium')
            )
            
            # 保存
            doc_ref = self.db.collection('decision_logs').document(decision_log.decision_id)
            doc_ref.set(asdict(decision_log))
            
            return decision_log
            
        except Exception as e:
            print(f"❌ Decision logging error: {e}")
            return None
    
    async def _analyze_decision(self, context: str, decision: str, 
                               reasoning: str) -> Dict:
        """決定を構造化分析"""
        try:
            prompt = f"""
以下の決定事項を構造化してください：

【状況】{context}
【決定】{decision}
【理由】{reasoning}

以下のJSON形式で回答：
{{
    "reasoning": "根拠を明確に（なぜこの決定なのか）",
    "alternatives": ["代替案1", "代替案2", "代替案3"],
    "next_steps": ["次の一手1", "次の一手2"],
    "urgency": "high/medium/low",
    "impact": "high/medium/low",
    "risks": ["リスク要因"],
    "success_metrics": ["成功指標"]
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
            print(f"❌ Decision analysis error: {e}")
            return {
                'reasoning': reasoning,
                'alternatives': [],
                'next_steps': [],
                'urgency': 'medium',
                'impact': 'medium'
            }
    
    async def get_recent_action_summary(self, user_id: str, 
                                       hours: int = 24) -> str:
        """直近のアクションサマリー取得"""
        try:
            cutoff_time = datetime.now(JST) - timedelta(hours=hours)
            
            query = self.db.collection('action_logs')\
                .where('user_id', '==', user_id)\
                .where('timestamp', '>=', cutoff_time)\
                .order_by('timestamp', direction='DESCENDING')\
                .limit(20)
            
            actions = []
            for doc in query.stream():
                actions.append(doc.to_dict())
            
            if not actions:
                return "📝 直近のアクション履歴はありません。"
            
            # サマリー生成
            summary = f"📊 **直近{hours}時間のアクション履歴**\n\n"
            
            success_count = sum(1 for a in actions if a.get('success', True))
            total_count = len(actions)
            
            summary += f"✅ 成功: {success_count}/{total_count}件\n\n"
            
            # 最新5件を表示
            for action in actions[:5]:
                timestamp = action['timestamp'].strftime('%m/%d %H:%M')
                result = action.get('result', 'N/A')
                summary += f"• {timestamp}: {result}\n"
            
            # 次のアクション提案
            all_next_actions = []
            for action in actions:
                all_next_actions.extend(action.get('next_actions', []))
            
            if all_next_actions:
                unique_next = list(set(all_next_actions))[:3]
                summary += f"\n💡 **推奨される次のアクション:**\n"
                for next_action in unique_next:
                    summary += f"• {next_action}\n"
            
            return summary
            
        except Exception as e:
            print(f"❌ Action summary retrieval error: {e}")
            return "アクション履歴の取得に失敗しました。"
    
    def format_decision_memo(self, decision_log: DecisionLog) -> str:
        """決裁メモのフォーマット"""
        urgency_emoji = {"high": "🔥", "medium": "⚡", "low": "📌"}
        impact_emoji = {"high": "💥", "medium": "📈", "low": "📝"}
        
        memo = f"📋 **決裁メモ** {urgency_emoji.get(decision_log.urgency, '📝')}{impact_emoji.get(decision_log.impact, '📝')}\n\n"
        
        memo += f"**📅 日時:** {decision_log.timestamp.strftime('%Y/%m/%d %H:%M')}\n"
        memo += f"**🎯 結論:** {decision_log.decision}\n\n"
        
        memo += f"**📊 根拠:**\n{decision_log.reasoning}\n\n"
        
        if decision_log.alternatives:
            memo += f"**🔄 代替案:**\n"
            for i, alt in enumerate(decision_log.alternatives, 1):
                memo += f"{i}. {alt}\n"
            memo += "\n"
        
        if decision_log.next_steps:
            memo += f"**➡️ 次の一手:**\n"
            for i, step in enumerate(decision_log.next_steps, 1):
                memo += f"{i}. {step}\n"
        
        return memo