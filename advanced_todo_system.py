#!/usr/bin/env python3
"""
Advanced Todo System for Catherine AI
完全機能統合版 - Discord ToDo Assistant
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import discord
from discord.ext import commands

from todo_database import TodoDatabase, Task, TaskStatus, Priority
from todo_nlu import TodoNLU, Intent, ParseResult

class AdvancedTodoSystem:
    """高度ToDo管理システム - Catherine AI統合版"""
    
    def __init__(self, db_path: str = "catherine_todo.db"):
        self.db = TodoDatabase(db_path)
        self.nlu = TodoNLU()
        
        # 確認待ちアクション（メッセージID -> アクション情報）
        self.pending_confirmations: Dict[str, Dict] = {}
        
        # 統計情報
        self.stats = {
            'commands_processed': 0,
            'tasks_created': 0,
            'success_rate': 0.0
        }
        
        print("✅ Advanced Todo System initialized")
    
    async def process_message(self, message: discord.Message, user_id: str) -> Optional[str]:
        """Discordメッセージを処理してToDo操作を実行"""
        try:
            self.stats['commands_processed'] += 1
            
            # NLU解析
            text = message.content.strip()
            result = self.nlu.parse(
                text=text,
                user_id=user_id,
                channel_id=str(message.channel.id),
                message_id=str(message.id)
            )
            
            # エラーの場合
            if result.error:
                return self._format_error_response(result.error, result.suggestions)
            
            # 確認が必要な場合
            if result.constraints.get('confirm_needed'):
                return await self._handle_confirmation_needed(result, message)
            
            # 意図別実行
            response = await self._execute_intent(result, user_id, message)
            
            # 成功統計更新
            if response and not response.startswith('❌'):
                self.stats['success_rate'] = (self.stats['success_rate'] * 0.9) + (1.0 * 0.1)
            else:
                self.stats['success_rate'] = self.stats['success_rate'] * 0.9
            
            return response
            
        except Exception as e:
            print(f"❌ Todo system error: {e}")
            import traceback
            traceback.print_exc()
            return "❌ システムエラーが発生しました。しばらくしてから再度お試しください。"
    
    async def handle_reaction(self, payload: discord.RawReactionActionEvent) -> Optional[str]:
        """リアクションによる確認処理"""
        message_id = str(payload.message_id)
        
        if message_id not in self.pending_confirmations:
            return None
        
        action_info = self.pending_confirmations[message_id]
        
        # ✅で確認、❌でキャンセル
        if str(payload.emoji) == '✅':
            # 確認されたアクションを実行
            result = action_info['result']
            response = await self._execute_intent(result, action_info['user_id'], None)
            del self.pending_confirmations[message_id]
            return f"✅ 確認済み: {response}"
            
        elif str(payload.emoji) == '❌':
            # キャンセル
            del self.pending_confirmations[message_id]
            return "❌ 操作をキャンセルしました。"
        
        return None
    
    async def _execute_intent(self, result: ParseResult, user_id: str, message: Optional[discord.Message]) -> str:
        """意図に基づいてアクション実行"""
        try:
            intent = result.intent
            task_info = result.task
            
            if intent == Intent.ADD.value:
                return await self._handle_add_task(task_info, user_id)
            
            elif intent == Intent.LIST.value:
                return await self._handle_list_tasks(task_info, user_id)
            
            elif intent == Intent.COMPLETE.value:
                return await self._handle_complete_task(task_info, user_id)
            
            elif intent == Intent.UPDATE.value:
                return await self._handle_update_task(task_info, user_id)
            
            elif intent == Intent.DELETE.value:
                return await self._handle_delete_task(task_info, user_id)
            
            elif intent == Intent.FIND.value:
                return await self._handle_find_tasks(task_info, user_id)
            
            elif intent == Intent.POSTPONE.value:
                return await self._handle_postpone_task(task_info, user_id)
            
            else:
                return f"❌ 不明な操作: {intent}"
                
        except Exception as e:
            print(f"❌ Intent execution error: {e}")
            return f"❌ 操作実行エラー: {str(e)}"
    
    async def _handle_add_task(self, task_info: Dict, user_id: str) -> str:
        """タスク追加処理"""
        try:
            # Taskオブジェクト作成
            task = Task(
                title=task_info.get('title', ''),
                description=task_info.get('description'),
                priority=task_info.get('priority', 'normal'),
                assignees=task_info.get('assignees', []),
                tags=task_info.get('tags', []),
                created_by=user_id,
                source_msg_id=task_info.get('source_msg_id', ''),
                channel_id=task_info.get('channel_id', '')
            )
            
            # 期日設定
            if task_info.get('due'):
                task.due_at = datetime.fromisoformat(task_info['due'])
            
            # データベースに追加
            added_task = self.db.add_task(task)
            if not added_task:
                return "❌ タスク追加に失敗しました（重複の可能性）"
            
            self.stats['tasks_created'] += 1
            
            # レスポンス作成
            response = f"✅ **追加｜『{added_task.title}』**"
            
            if added_task.due_at:
                due_str = added_task.due_at.strftime('%m/%d %H:%M')
                response += f" 〆 {due_str}"
            
            if added_task.priority != 'normal':
                priority_emoji = {'urgent': '🔥', 'high': '⚡', 'low': '📌'}
                emoji = priority_emoji.get(added_task.priority, '')
                response += f" ｜優先: {emoji}{added_task.priority}"
            
            if added_task.assignees:
                response += f" ｜担当: {', '.join(f'@{a}' for a in added_task.assignees)}"
            
            if added_task.tags:
                response += f" ｜{' '.join(f'#{t}' for t in added_task.tags)}"
            
            response += f" ｜ID: #{added_task.id}"
            
            return response
            
        except ValueError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            print(f"❌ Add task error: {e}")
            return "❌ タスク追加処理でエラーが発生しました"
    
    async def _handle_list_tasks(self, filters: Dict, user_id: str) -> str:
        """タスク一覧表示"""
        try:
            # フィルター適用
            status = filters.get('status')
            tags = filters.get('tags')
            channel_id = filters.get('channel_id')
            
            tasks = self.db.get_tasks(
                status=status,
                tags=tags,
                channel_id=channel_id,
                limit=20
            )
            
            if not tasks:
                filter_desc = ""
                if status:
                    filter_desc += f"ステータス:{status} "
                if tags:
                    filter_desc += f"タグ:{','.join(tags)} "
                return f"📋 {filter_desc}該当するタスクはありません"
            
            # 応答作成
            response = "📊 **ToDoリスト**\n\n"
            
            for i, task in enumerate(tasks, 1):
                # ステータス絵文字
                status_emoji = {'open': '⏳', 'done': '✅', 'cancelled': '❌'}
                emoji = status_emoji.get(task.status, '❓')
                
                # 優先度絵文字
                priority_emoji = {'urgent': '🔥', 'high': '⚡', 'normal': '', 'low': '📌'}
                p_emoji = priority_emoji.get(task.priority, '')
                
                # 基本情報
                line = f"{i}. {emoji} **{task.title}** {p_emoji}"
                
                # 期日
                if task.due_at:
                    due_str = task.due_at.strftime('%m/%d %H:%M')
                    if task.due_at < datetime.now(task.due_at.tzinfo):
                        line += f" ⚠️{due_str}"
                    else:
                        line += f" 〆{due_str}"
                
                # 担当者
                if task.assignees:
                    line += f" @{','.join(task.assignees)}"
                
                # タグ
                if task.tags:
                    line += f" {' '.join(f'#{t}' for t in task.tags)}"
                
                line += f" `#{task.id}`\n"
                response += line
            
            # 統計情報
            if len(tasks) >= 20:
                response += "\n*（最大20件まで表示）*"
            
            # サマリー
            stats = self.db.get_stats()
            if stats:
                response += f"\n\n📈 **サマリー**: "
                response += f"全{stats['total_tasks']}件 "
                if stats['overdue_count'] > 0:
                    response += f"｜期限切れ {stats['overdue_count']}件"
            
            return response
            
        except Exception as e:
            print(f"❌ List tasks error: {e}")
            return "❌ タスク一覧取得でエラーが発生しました"
    
    async def _handle_complete_task(self, task_info: Dict, user_id: str) -> str:
        """タスク完了処理"""
        try:
            # タスク特定
            task = await self._find_target_task(task_info, user_id)
            if not task:
                return "❌ 該当するタスクが見つかりません"
            
            # 完了状態に更新
            success = self.db.update_task(
                task.id,
                {'status': TaskStatus.DONE.value},
                user_id
            )
            
            if success:
                return f"✅ **完了｜『{task.title}』** #{task.id}"
            else:
                return f"❌ タスク完了処理に失敗しました"
                
        except Exception as e:
            print(f"❌ Complete task error: {e}")
            return "❌ タスク完了処理でエラーが発生しました"
    
    async def _handle_update_task(self, task_info: Dict, user_id: str) -> str:
        """タスク更新処理"""
        try:
            # タスク特定
            task = await self._find_target_task(task_info, user_id)
            if not task:
                return "❌ 該当するタスクが見つかりません"
            
            updates = task_info.get('updates', {})
            if not updates:
                return "❌ 更新内容が指定されていません"
            
            # 更新実行
            success = self.db.update_task(task.id, updates, user_id)
            
            if success:
                update_desc = []
                for key, value in updates.items():
                    if key == 'priority':
                        update_desc.append(f"優先度→{value}")
                    elif key == 'due':
                        due_dt = datetime.fromisoformat(value)
                        update_desc.append(f"期日→{due_dt.strftime('%m/%d %H:%M')}")
                
                return f"✅ **更新｜『{task.title}』** {' '.join(update_desc)} #{task.id}"
            else:
                return "❌ タスク更新に失敗しました"
                
        except Exception as e:
            print(f"❌ Update task error: {e}")
            return "❌ タスク更新処理でエラーが発生しました"
    
    async def _handle_delete_task(self, task_info: Dict, user_id: str) -> str:
        """タスク削除処理"""
        try:
            # タスク特定
            task = await self._find_target_task(task_info, user_id)
            if not task:
                return "❌ 該当するタスクが見つかりません"
            
            # 削除実行
            success = self.db.delete_task(task.id, user_id)
            
            if success:
                return f"🗑️ **削除｜『{task.title}』** #{task.id}"
            else:
                return "❌ タスク削除に失敗しました"
                
        except Exception as e:
            print(f"❌ Delete task error: {e}")
            return "❌ タスク削除処理でエラーが発生しました"
    
    async def _handle_find_tasks(self, search_info: Dict, user_id: str) -> str:
        """タスク検索処理"""
        try:
            query = search_info.get('query', '')
            if not query:
                return "❌ 検索キーワードを指定してください"
            
            tasks = self.db.find_tasks(query)
            
            if not tasks:
                return f"🔍 「{query}」に該当するタスクは見つかりませんでした"
            
            response = f"🔍 **検索結果「{query}」**\n\n"
            
            for i, task in enumerate(tasks[:10], 1):
                status_emoji = {'open': '⏳', 'done': '✅', 'cancelled': '❌'}
                emoji = status_emoji.get(task.status, '❓')
                
                response += f"{i}. {emoji} **{task.title}**"
                if task.due_at:
                    due_str = task.due_at.strftime('%m/%d %H:%M')
                    response += f" 〆{due_str}"
                response += f" `#{task.id}`\n"
            
            if len(tasks) > 10:
                response += f"\n*（他{len(tasks)-10}件）*"
            
            return response
            
        except Exception as e:
            print(f"❌ Find tasks error: {e}")
            return "❌ タスク検索でエラーが発生しました"
    
    async def _handle_postpone_task(self, task_info: Dict, user_id: str) -> str:
        """タスク延期処理"""
        try:
            # タスク特定
            task = await self._find_target_task(task_info, user_id)
            if not task:
                return "❌ 該当するタスクが見つかりません"
            
            # 新しい期日
            new_due = task_info.get('new_due')
            if not new_due:
                return "❌ 延期先の日時が指定されていません"
            
            # 更新実行
            success = self.db.update_task(
                task.id,
                {'due_at': datetime.fromisoformat(new_due)},
                user_id
            )
            
            if success:
                due_dt = datetime.fromisoformat(new_due)
                return f"📅 **延期｜『{task.title}』** → {due_dt.strftime('%m/%d %H:%M')} #{task.id}"
            else:
                return "❌ タスク延期に失敗しました"
                
        except Exception as e:
            print(f"❌ Postpone task error: {e}")
            return "❌ タスク延期処理でエラーが発生しました"
    
    async def _find_target_task(self, task_info: Dict, user_id: str) -> Optional[Task]:
        """対象タスクを特定"""
        # ID指定
        if 'task_id' in task_info:
            tasks = self.db.get_tasks(limit=1000)  # 全取得
            for task in tasks:
                if task.id == task_info['task_id']:
                    return task
        
        # タイトル検索
        if 'title_query' in task_info:
            tasks = self.db.find_tasks(task_info['title_query'])
            if tasks:
                return tasks[0]  # 最初の候補
        
        # キーワード検索
        if 'keywords' in task_info:
            for keyword in task_info['keywords']:
                tasks = self.db.find_tasks(keyword)
                if tasks:
                    return tasks[0]
        
        return None
    
    async def _handle_confirmation_needed(self, result: ParseResult, message: discord.Message) -> str:
        """確認が必要な場合の処理"""
        # 確認待ちアクションを保存
        self.pending_confirmations[str(message.id)] = {
            'result': result,
            'user_id': str(message.author.id),
            'timestamp': datetime.now()
        }
        
        # 確認メッセージ作成
        intent = result.intent
        task_info = result.task
        
        if intent == Intent.DELETE.value:
            task_title = task_info.get('title_query', 'タスク')
            response = f"⚠️ **削除確認**\n『{task_title}』を削除しますか？\n\n✅で実行、❌でキャンセル"
        else:
            response = f"⚠️ **確認が必要**\n{intent}操作を実行しますか？\n\n✅で実行、❌でキャンセル"
        
        return response
    
    def _format_error_response(self, error: Dict, suggestions: List[str]) -> str:
        """エラー応答フォーマット"""
        response = f"❌ **{error.get('message', 'エラーが発生しました')}**"
        
        if suggestions:
            response += "\n\n💡 **候補:**\n"
            for i, suggestion in enumerate(suggestions[:3], 1):
                response += f"{i}. {suggestion}\n"
        
        suggestion = error.get('suggestion')
        if suggestion:
            response += f"\n💭 {suggestion}"
        
        return response
    
    def get_system_stats(self) -> Dict[str, Any]:
        """システム統計取得"""
        db_stats = self.db.get_stats()
        
        return {
            **self.stats,
            **db_stats,
            'pending_confirmations': len(self.pending_confirmations)
        }

# Catherine AI統合用のヘルパー関数
async def handle_todo_command(message: discord.Message, todo_system: AdvancedTodoSystem) -> Optional[str]:
    """Catherine AI用のToDo処理エントリーポイント"""
    user_id = str(message.author.id)
    
    # ToDo関連の判定
    content = message.content.lower()
    todo_keywords = [
        'todo', 'タスク', 'やること', '追加', '登録', '完了', '削除', 
        '一覧', 'リスト', '検索', '延期', '更新', '修正'
    ]
    
    if not any(keyword in content for keyword in todo_keywords):
        return None
    
    # ToDo処理実行
    response = await todo_system.process_message(message, user_id)
    return response

if __name__ == "__main__":
    # テスト実行
    import asyncio
    
    async def test():
        system = AdvancedTodoSystem("test_advanced_todo.db")
        
        # ダミーメッセージ作成
        class DummyMessage:
            def __init__(self, content: str):
                self.content = content
                self.id = 123456
                self.channel = type('obj', (object,), {'id': 789})()
                self.author = type('obj', (object,), {'id': 'user123'})()
        
        test_messages = [
            "todo add 「ロンT制作」 明日18時 high #CCT",
            "todo list #CCT",
            "「ロンT制作」完了",
            "todo done 1"
        ]
        
        for msg_text in test_messages:
            print(f"\n📝 Test: {msg_text}")
            msg = DummyMessage(msg_text)
            response = await system.process_message(msg, "user123")
            print(f"Response: {response}")
        
        # 統計表示
        stats = system.get_system_stats()
        print(f"\n📊 Stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    asyncio.run(test())