#!/usr/bin/env python3
"""
Catherine AI - Enhanced Version 2.0
人間らしい理解とリアクション学習を備えた次世代AI秘書
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from openai import OpenAI
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

# カスタムモジュールのインポート
from firebase_config import firebase_manager
from todo_manager import TodoManager
from conversation_manager import ConversationManager
from advanced_context_system import AdvancedContextSystem
from reaction_learning_system import ReactionLearningSystem
from team_todo_manager import TeamTodoManager
from reminder_system import ReminderSystem
from morning_briefing_system import MorningBriefingSystem
from confidence_guard_system import ConfidenceGuardSystem, ConfidenceLevel
from action_summary_system import ActionSummarySystem
from progress_nudge_engine import ProgressNudgeEngine
from attachment_ocr_system import AttachmentOCRSystem
from voice_optimized_system import VoiceOptimizedSystem
# from voice_channel_system import VoiceChannelSystem  # 一時的に無効化（discord.sinks互換性問題）

# Railway用ポート設定
PORT = int(os.environ.get("PORT", 8080))

# Discord intents設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクション検知のため追加
intents.members = True  # メンバー情報取得のため追加
intents.voice_states = True  # ボイスチャンネル機能のため追加

# Botクライアント初期化
bot = commands.Bot(command_prefix='C!', intents=intents)

# OpenAI クライアント初期化
client_oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 各マネージャーの初期化
todo_manager = TodoManager(client_oa)
conversation_manager = ConversationManager(client_oa)
context_system = AdvancedContextSystem(client_oa)
reaction_system = ReactionLearningSystem(client_oa)
team_todo_manager = TeamTodoManager(client_oa)
reminder_system = ReminderSystem(client_oa, bot)
briefing_system = MorningBriefingSystem(client_oa)
confidence_guard = ConfidenceGuardSystem()
action_summary = ActionSummarySystem(client_oa)
nudge_engine = ProgressNudgeEngine(client_oa)
ocr_system = AttachmentOCRSystem(client_oa)
voice_system = VoiceOptimizedSystem(client_oa)
# voice_channel = VoiceChannelSystem(client_oa, bot)  # 一時的に無効化

# タイムゾーン設定
JST = pytz.timezone('Asia/Tokyo')

@bot.event
async def on_ready():
    print(f"✅ Catherine AI v2.0 起動完了")
    print(f"🤖 ログイン: {bot.user}")
    print("🎯 機能: 深層理解, リアクション学習, チームToDo, スマートリマインダー")
    print(f"📊 サーバー数: {len(bot.guilds)}")
    
    # 定期タスク開始
    check_reminders.start()
    update_learning.start()

@bot.event
async def on_message(message):
    """メッセージ処理"""
    if message.author.bot:
        return
    
    # ユーザー情報
    user_id = str(message.author.id)
    username = message.author.display_name
    
    # ユーザーアクティビティ更新
    await conversation_manager.update_user_activity(user_id, username)
    
    # 添付ファイル処理
    if message.attachments:
        await process_attachments(message, user_id, username)
        return
    
    # C!コマンド処理
    if message.content.startswith("C!"):
        await process_command(message, user_id, username)
    
    # コマンド処理（commands.Botの機能を使用）
    await bot.process_commands(message)

async def process_command(message, user_id: str, username: str):
    """コマンド処理のメイン関数"""
    try:
        command_text = message.content[len("C!"):].strip()
        
        # 会話履歴を取得
        conversation_history = await conversation_manager._get_recent_conversations(user_id, limit=10)
        
        # 深層コンテキスト分析
        context_analysis = await context_system.analyze_deep_context(
            user_id, 
            command_text, 
            conversation_history
        )
        
        # ユーザープロファイル取得
        user_profile = await get_user_profile(user_id)
        
        # コマンドルーティング
        response = await route_command(
            user_id, 
            command_text, 
            context_analysis,
            user_profile,
            message
        )
        
        # リアクション学習を適用
        response = await reaction_system.apply_learning_to_response(user_id, response)
        
        # 音声モードの場合は音声最適化
        user_profile = await get_user_profile(user_id)
        if user_profile.get('voice_mode', False):
            response = voice_system.optimize_for_voice(response)
        
        # 応答送信
        bot_message = await message.channel.send(response)
        
        # アクション実行結果をログ
        execution_time = (datetime.now() - datetime.now()).total_seconds() * 1000  # 実際の実行時間を計算
        await action_summary.log_action_result(
            user_id,
            f"command.{command_lower.split()[0] if command_lower else 'chat'}",
            command_text,
            {
                'success': True,
                'response_length': len(response),
                'confidence': context_analysis.get('confidence_score', 0.8)
            },
            int(execution_time)
        )
        
        # 会話記録
        await conversation_manager.log_conversation(
            user_id=user_id,
            user_message=message.content,
            bot_response=response,
            command_type=context_analysis.get('expected_response_type', 'general'),
            analysis=context_analysis
        )
        
        # メッセージIDを保存（リアクション追跡用）
        await save_message_mapping(message.id, bot_message.id, user_id, response)
        
    except Exception as e:
        print(f"❌ Command processing error: {e}")
        error_msg = "申し訳ございません。処理中にエラーが発生しました。"
        await message.channel.send(error_msg)

async def route_command(user_id: str, command_text: str, 
                       context_analysis: Dict, 
                       user_profile: Dict,
                       message) -> str:
    """コマンドのルーティング"""
    
    command_lower = command_text.lower()
    
    # ToDo関連（listはチーム、mylistは個人）
    if command_lower.startswith("todo"):
        return await handle_team_todo_create(user_id, command_text, message)
    elif command_lower.startswith("update"):
        return await handle_todo_update(user_id, command_text)
    elif command_lower.startswith("list"):
        return await handle_team_list(command_text)
    elif command_lower.startswith("assign"):
        return await handle_team_assign(command_text)
    elif command_lower.startswith("report"):
        return await handle_team_report()
    elif command_lower.startswith("dashboard"):
        return await handle_team_dashboard()
    
    # 個人ToDo関連
    elif command_lower.startswith("mytodo"):
        return await handle_personal_todo(user_id, command_text, context_analysis)
    elif command_lower.startswith("mylist"):
        return await handle_personal_list(user_id, command_text)
    elif command_lower.startswith("done"):
        return await handle_done_todo(user_id, command_text, is_team=True)
    elif command_lower.startswith("mydone"):
        return await handle_done_todo(user_id, command_text, is_team=False)
    
    # リマインダー関連
    elif command_lower.startswith("remind"):
        return await handle_reminder(user_id, command_text)
    elif command_lower.startswith("reminders"):
        return await handle_list_reminders(user_id)
    
    # 学習・設定関連
    elif command_lower.startswith("learn"):
        return await handle_learning_status(user_id)
    elif command_lower.startswith("preferences"):
        return await handle_preferences(user_id)
    elif command_lower.startswith("humor"):
        return await handle_humor_setting(user_id, command_text)
    elif command_lower.startswith("style"):
        return await handle_style_setting(user_id, command_text)
    
    # ブリーフィング関連
    elif command_lower.startswith("briefing") or command_lower.startswith("朝"):
        return await handle_morning_briefing()
    elif command_lower.startswith("brief"):
        return await handle_morning_briefing()
    
    # 新システム関連
    elif command_lower.startswith("summary") or command_lower.startswith("履歴"):
        return await handle_action_summary(user_id, command_text)
    elif command_lower.startswith("nudge") or command_lower.startswith("停滞"):
        return await handle_progress_nudge(command_text)
    elif command_lower.startswith("voice") or command_lower.startswith("音声"):
        return await handle_voice_mode_toggle(user_id)
    elif command_lower.startswith("decision") or command_lower.startswith("決裁"):
        return await handle_decision_memo(user_id, command_text)
    
    # ボイスチャンネル関連（一時的に無効化）
    elif command_lower.startswith("join"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("leave"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("listen"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("stop"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("status"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    
    # ヘルプ
    elif command_lower.startswith("help"):
        return await handle_help()
    
    # 自然言語処理
    else:
        return await handle_natural_conversation(
            user_id, 
            command_text, 
            context_analysis,
            user_profile
        )

@bot.event
async def on_reaction_add(reaction, user):
    """リアクション追加時の処理"""
    if user.bot:
        return
    
    try:
        # メッセージマッピングを取得
        mapping = await get_message_mapping(reaction.message.id)
        if not mapping:
            return
        
        # リアクション学習を実行
        await reaction_system.process_reaction(
            user_id=str(user.id),
            message_id=str(reaction.message.id),
            reaction=str(reaction.emoji),
            bot_response=mapping['bot_response'],
            user_message=mapping['user_message']
        )
        
        # フィードバック確認メッセージ（オプション）
        if str(reaction.emoji) in ['👍', '👎', '❤️', '❌']:
            feedback_msg = await get_feedback_message(str(reaction.emoji))
            await reaction.message.channel.send(
                f"{user.mention} {feedback_msg}", 
                delete_after=5  # 5秒後に削除
            )
        
    except Exception as e:
        print(f"❌ Reaction processing error: {e}")

# チームToDo関連のハンドラー
async def handle_team_todo_create(user_id: str, command_text: str, message) -> str:
    """チームToDo作成"""
    try:
        # "todo" を除いた部分を取得
        content = command_text[4:].strip()
        
        if not content:
            return "📝 チームToDoの内容を教えてください。\n例: `C! todo @mrc バックエンドAPI実装`"
        
        # メンション解析
        assignee = "unassigned"
        if message.mentions:
            mentioned_user = message.mentions[0]
            # ユーザー名から担当者を判定
            if 'mrc' in mentioned_user.name.lower():
                assignee = 'mrc'
            elif 'supy' in mentioned_user.name.lower():
                assignee = 'supy'
        
        # コンテンツからメンションを削除
        for mention in message.mentions:
            content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        content = content.strip()
        
        # ToDo作成
        todo = await team_todo_manager.create_team_todo(
            creator_id=user_id,
            title=content,
            assignee=assignee
        )
        
        if todo:
            priority_emoji = "🔥" if todo['priority'] >= 4 else "⚡" if todo['priority'] >= 3 else "📌"
            assignee_name = team_todo_manager.team_members[assignee]['name']
            
            return f"{priority_emoji} **チームToDo登録完了**\n"\
                   f"📋 タスク: {todo['title']}\n"\
                   f"👤 担当: {assignee_name}\n"\
                   f"📁 カテゴリ: {todo['category']}\n"\
                   f"⏱️ 推定: {todo['estimated_hours']}時間"
        else:
            return "❌ チームToDoの作成に失敗しました。"
            
    except Exception as e:
        print(f"❌ Team ToDo creation error: {e}")
        return "エラーが発生しました。"

async def handle_team_list(command_text: str) -> str:
    """チームToDoリスト表示"""
    try:
        # フィルター解析
        filters = {}
        if '@mrc' in command_text.lower() or 'mrc' in command_text.lower():
            filters['assignee'] = 'mrc'
        elif '@supy' in command_text.lower() or 'supy' in command_text.lower():
            filters['assignee'] = 'supy'
        elif 'unassigned' in command_text.lower():
            filters['assignee'] = 'unassigned'
        
        # ステータスフィルター
        if 'completed' in command_text.lower():
            filters['status'] = 'completed'
        elif 'progress' in command_text.lower():
            filters['status'] = 'in_progress'
        elif 'blocked' in command_text.lower():
            filters['status'] = 'blocked'
        
        # ToDo取得
        todos = await team_todo_manager.get_team_todos(filters)
        
        if not todos:
            return "📋 該当するチームToDoはありません。"
        
        # リスト作成
        response = "📊 **チームToDoリスト**\n\n"
        
        # 担当者別にグループ化
        by_assignee = {}
        for todo in todos[:30]:  # 最大30件
            assignee = todo.get('assignee', 'unassigned')
            if assignee not in by_assignee:
                by_assignee[assignee] = []
            by_assignee[assignee].append(todo)
        
        # 表示
        for assignee, assignee_todos in by_assignee.items():
            assignee_name = team_todo_manager.team_members[assignee]['name']
            response += f"**👤 {assignee_name}**\n"
            
            for i, todo in enumerate(assignee_todos, 1):
                priority_emoji = "🔥" if todo['priority'] >= 4 else "⚡" if todo['priority'] >= 3 else "📌"
                status_emoji = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'review': '👀',
                    'blocked': '🚫',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(todo['status'], '❓')
                
                due_text = ""
                if todo.get('due_date'):
                    due_text = f" 📅{todo['due_date'].strftime('%m/%d')}"
                
                response += f"  {i}. {priority_emoji}{status_emoji} {todo['title'][:50]}{due_text}\n"
            
            response += "\n"
        
        if len(todos) > 30:
            response += f"... 他{len(todos) - 30}件\n"
        
        return response
        
    except Exception as e:
        print(f"❌ Team list error: {e}")
        return "リスト取得中にエラーが発生しました。"

async def handle_team_dashboard() -> str:
    """チームダッシュボード表示"""
    try:
        dashboard = await team_todo_manager.get_team_dashboard()
        
        response = "📊 **チームダッシュボード**\n\n"
        
        # サマリー
        response += f"**📈 概要**\n"
        response += f"総タスク: {dashboard['total_tasks']}\n"
        response += f"チーム速度: {dashboard['team_velocity']:.1f} タスク/日\n\n"
        
        # ワークロード
        response += "**👥 ワークロード**\n"
        for member_id, data in dashboard['workload_distribution'].items():
            bar_length = int(data['utilization'] / 10)
            bar = '█' * bar_length + '░' * (10 - bar_length)
            response += f"{data['name']}: [{bar}] {data['utilization']:.0f}%\n"
        response += "\n"
        
        # ステータス
        response += "**📋 ステータス**\n"
        for status, count in dashboard['by_status'].items():
            status_name = team_todo_manager.task_statuses.get(status, status)
            response += f"{status_name}: {count}\n"
        
        # アラート
        if dashboard['overdue_tasks']:
            response += f"\n⚠️ 期限超過: {len(dashboard['overdue_tasks'])}件"
        if dashboard['blocked_tasks']:
            response += f"\n🚫 ブロック中: {len(dashboard['blocked_tasks'])}件"
        
        return response
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return "ダッシュボード生成中にエラーが発生しました。"

async def handle_team_report() -> str:
    """チームレポート生成"""
    return await team_todo_manager.generate_team_report()

# 個人ToDo関連のハンドラー
async def handle_personal_todo(user_id: str, command_text: str, context_analysis: Dict) -> str:
    """個人ToDo作成"""
    try:
        # "mytodo" を除いた部分を取得
        content = command_text[6:].strip()
        
        if not content:
            return "📝 個人ToDoの内容を教えてください。\n例: `C! mytodo 明日の会議資料準備`"
        
        # ToDo作成（既存のtodo_managerを使用）
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=content,
            description=""
        )
        
        priority_emoji = "🔥" if todo_data['priority'] >= 4 else "⚡" if todo_data['priority'] >= 3 else "📌"
        
        return f"{priority_emoji} **個人ToDo登録完了**\n"\
               f"📋 タスク: {todo_data['title']}\n"\
               f"📁 カテゴリ: {todo_data['category']}\n"\
               f"⚠️ 優先度: {todo_data['priority']}"
        
    except Exception as e:
        print(f"❌ Personal ToDo creation error: {e}")
        return "エラーが発生しました。"

async def handle_personal_list(user_id: str, command_text: str) -> str:
    """個人ToDoリスト表示"""
    try:
        todos = await todo_manager.get_user_todos(user_id, status="pending")
        
        if not todos:
            return "📋 現在、個人の未完了ToDoはありません。"
        
        response = "📝 **個人ToDoリスト**\n\n"
        
        for i, todo in enumerate(todos[:15], 1):
            priority_emoji = "🔥" if todo['priority'] >= 4 else "⚡" if todo['priority'] >= 3 else "📌"
            due_text = ""
            if todo.get('due_date'):
                due_text = f" 📅{todo['due_date'].strftime('%m/%d')}"
            
            response += f"{i}. {priority_emoji} {todo['title'][:50]}{due_text}\n"
        
        if len(todos) > 15:
            response += f"\n... 他{len(todos) - 15}件"
        
        return response
        
    except Exception as e:
        print(f"❌ Personal list error: {e}")
        return "リスト取得中にエラーが発生しました。"

async def handle_done_todo(user_id: str, command_text: str, is_team: bool = True) -> str:
    """ToDo完了処理（チーム/個人）"""
    try:
        # 番号を抽出
        parts = command_text.split()
        if len(parts) < 2:
            return "完了するToDoの番号を指定してください。\n例: `C! done 1`"
        
        try:
            todo_num = int(parts[1]) - 1
        except ValueError:
            return "番号は数字で指定してください。"
        
        if is_team:
            # チームToDo完了
            todos = await team_todo_manager.get_team_todos()
            if 0 <= todo_num < len(todos):
                todo = todos[todo_num]
                success = await team_todo_manager.update_todo_status(
                    todo['todo_id'], 
                    'completed',
                    f"{user_id} が完了"
                )
                if success:
                    return f"✅ チームToDo完了: {todo['title']}"
                else:
                    return "❌ 完了処理に失敗しました。"
            else:
                return "指定された番号のToDoが見つかりません。"
        else:
            # 個人ToDo完了
            todos = await todo_manager.get_user_todos(user_id, status="pending")
            if 0 <= todo_num < len(todos):
                todo = todos[todo_num]
                success = await todo_manager.update_todo_status(todo['todo_id'], "completed")
                if success:
                    return f"✅ 個人ToDo完了: {todo['title']}"
                else:
                    return "❌ 完了処理に失敗しました。"
            else:
                return "指定された番号のToDoが見つかりません。"
                
    except Exception as e:
        print(f"❌ Done todo error: {e}")
        return "エラーが発生しました。"

async def handle_team_assign(command_text: str) -> str:
    """チームToDo担当者変更"""
    try:
        parts = command_text.split()
        if len(parts) < 3:
            return "使い方: `C! assign [番号] [@新担当者]`"
        
        try:
            todo_num = int(parts[1]) - 1
        except ValueError:
            return "番号は数字で指定してください。"
        
        # 新担当者を特定
        new_assignee = "unassigned"
        if '@mrc' in command_text.lower():
            new_assignee = 'mrc'
        elif '@supy' in command_text.lower():
            new_assignee = 'supy'
        
        # ToDo取得と更新
        todos = await team_todo_manager.get_team_todos()
        if 0 <= todo_num < len(todos):
            todo = todos[todo_num]
            success = await team_todo_manager.assign_todo(
                todo['todo_id'],
                new_assignee,
                f"手動再割り当て"
            )
            
            if success:
                assignee_name = team_todo_manager.team_members[new_assignee]['name']
                return f"✅ 担当者変更完了: {todo['title']}\n新担当者: {assignee_name}"
            else:
                return "❌ 担当者変更に失敗しました。"
        else:
            return "指定された番号のToDoが見つかりません。"
            
    except Exception as e:
        print(f"❌ Assign error: {e}")
        return "エラーが発生しました。"

async def handle_todo_update(user_id: str, command_text: str) -> str:
    """自然言語でのToDo更新処理"""
    try:
        # "update" を除いた部分を取得
        update_text = command_text[6:].strip()
        
        if not update_text:
            return "更新内容を教えてください。\n例: `C! update 「API設計」の期日を明後日17:00に`"
        
        # チームToDoを取得
        team_todos = await team_todo_manager.get_team_todos()
        
        # 更新アクションを構築
        result = context_system.build_update_actions(update_text, team_todos)
        
        if not result.get('actions'):
            return result.get('talk', '更新処理に失敗しました。')
        
        action = result['actions'][0]
        
        # 確認が必要な場合
        if action.get('confirm_required'):
            # 候補一覧を表示
            from advanced_context_system import resolve_task_id
            task_id, cands = resolve_task_id(update_text, team_todos)
            if len(cands) > 1:
                response = result['talk'] + "\n\n📋 **候補一覧:**\n"
                for i, todo in enumerate(cands[:5], 1):
                    response += f"{i}. {todo['title']}\n"
                response += "\n番号で指定してください。例: `C! update 1の期日を明日に`"
                return response
        
        # 実際の更新処理
        task_id = action.get('id')
        success = False
        
        # 更新データを準備
        update_data = {}
        if action.get('priority'):
            # 優先度をDBの形式に変換
            priority_map = {"high": 5, "medium": 3, "low": 1}
            update_data['priority'] = priority_map.get(action['priority'], 3)
            
        if action.get('due'):
            # ISO8601文字列をdatetimeに変換
            from datetime import datetime
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            due_date = datetime.fromisoformat(action['due'].replace('Z', '+00:00'))
            update_data['due_date'] = due_date
            
        if action.get('title'):
            update_data['title'] = action['title']
            
        if action.get('details'):
            update_data['description'] = action['details']
            
        if action.get('assignee'):
            # 担当者変更
            success = await team_todo_manager.assign_todo(
                task_id, 
                action['assignee'], 
                "自然言語による変更"
            )
        
        # チームToDoのその他フィールド更新
        if update_data:
            doc_ref = team_todo_manager.db.collection('team_todos').document(task_id)
            update_data['updated_at'] = datetime.now(jst)
            doc_ref.update(update_data)
            success = True
        
        if success:
            return f"✅ {result['talk']}"
        else:
            return "❌ 更新に失敗しました。"
            
    except Exception as e:
        print(f"❌ Todo update error: {e}")
        return "更新処理中にエラーが発生しました。"

# 自然言語会話処理
async def handle_natural_conversation(user_id: str, message: str, 
                                     context_analysis: Dict,
                                     user_profile: Dict) -> str:
    """自然言語での会話処理"""
    try:
        # ToDo更新パターンを検出
        update_patterns = [
            r'(.+?)(の|を)?(期日|締切|期限).*(変|延長|延期|移動|更新)',
            r'(.+?)(の|を)?(優先度|重要度).*(変|更新|上げ|下げ)',
            r'(.+?)(の|を)?(タイトル|名前).*(変|更新)',
            r'(.+?)を?(.+?)(に担当|の担当)'
        ]
        
        is_update = any(re.search(pattern, message) for pattern in update_patterns)
        
        if is_update:
            # チームToDoを取得して更新処理
            team_todos = await team_todo_manager.get_team_todos()
            result = context_system.build_update_actions(message, team_todos)
            
            if result.get('actions'):
                # 更新処理を実行
                return await execute_update_action(result)
            else:
                # 更新の提案
                return f"{result.get('talk', '')}\n\n💡 具体的な更新は: `C! update {message}`"
        
        # 通常のアクション抽出
        actions = await context_system.extract_actionable_items(message, context_analysis)
        
        # 確信度評価
        confidence = confidence_guard.assess_confidence(
            message, 
            context_analysis,
            candidates=[]  # 必要に応じて候補を渡す
        )
        
        # 人間らしい応答生成
        response = await context_system.generate_human_like_response(
            user_id,
            context_analysis,
            user_profile
        )
        
        # 確信度に基づく応答調整
        if confidence.requires_confirmation:
            response = confidence_guard.format_confidence_response(confidence, response)
        
        # アクション実行の提案
        if actions:
            response += "\n\n💡 **実行可能なアクション:**\n"
            for action in actions:
                if action['type'] == 'todo' and action['confidence'] > 0.7:
                    response += f"• ToDoとして登録しますか？: `C! todo {action['content'][:30]}...`\n"
                elif action['type'] == 'reminder' and action['confidence'] > 0.6:
                    response += f"• リマインダーを設定しますか？: `C! remind {action['content'][:30]}...`\n"
        
        return response
        
    except Exception as e:
        print(f"❌ Natural conversation error: {e}")
        return "すみません、うまく理解できませんでした。もう一度お願いできますか？"

async def execute_update_action(result: Dict) -> str:
    """更新アクションを実行"""
    try:
        action = result['actions'][0]
        task_id = action.get('id')
        
        if not task_id:
            return result.get('talk', '更新処理に失敗しました。')
        
        # 更新処理（簡略版）
        update_data = {}
        if action.get('priority'):
            priority_map = {"high": 5, "medium": 3, "low": 1}
            update_data['priority'] = priority_map.get(action['priority'], 3)
            
        if action.get('due'):
            from datetime import datetime
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            due_date = datetime.fromisoformat(action['due'].replace('Z', '+00:00'))
            update_data['due_date'] = due_date
            
        if action.get('title'):
            update_data['title'] = action['title']
            
        # データベース更新
        if update_data:
            doc_ref = team_todo_manager.db.collection('team_todos').document(task_id)
            update_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo'))
            doc_ref.update(update_data)
            return f"✅ {result['talk']}"
        
        return result.get('talk', '更新完了')
        
    except Exception as e:
        print(f"❌ Execute update error: {e}")
        return "更新処理中にエラーが発生しました。"

async def handle_morning_briefing() -> str:
    """朝のブリーフィング処理"""
    try:
        briefing = await briefing_system.generate_daily_briefing(team_mode=True)
        
        if not briefing.get('success'):
            return "❌ ブリーフィング生成に失敗しました。"
        
        return briefing_system.format_briefing_message(briefing)
        
    except Exception as e:
        print(f"❌ Briefing error: {e}")
        return "ブリーフィング処理中にエラーが発生しました。"

# 新システムのハンドラー
async def handle_action_summary(user_id: str, command_text: str) -> str:
    """アクション履歴サマリー処理"""
    try:
        hours = 24  # デフォルト24時間
        
        # 時間指定があれば抽出
        import re
        hour_match = re.search(r'(\d+)(時間|h)', command_text)
        if hour_match:
            hours = int(hour_match.group(1))
        
        summary = await action_summary.get_recent_action_summary(user_id, hours)
        return summary
        
    except Exception as e:
        print(f"❌ Action summary error: {e}")
        return "履歴取得中にエラーが発生しました。"

async def handle_progress_nudge(command_text: str) -> str:
    """進捗ナッジ処理"""
    try:
        # 特定タスクのナッジか全体チェックかを判定
        if len(command_text.split()) > 1:
            # 特定タスクの場合（実装は必要に応じて）
            return "特定タスクのナッジ機能は開発中です。"
        else:
            # 全体の停滞チェック
            stalled_tasks = await nudge_engine.check_stalled_tasks()
            
            if not stalled_tasks:
                return "🎉 現在停滞しているタスクはありません！順調です。"
            
            response = f"⚠️ **停滞タスク検知** ({len(stalled_tasks)}件)\n\n"
            
            # 上位3件を表示
            for nudge in stalled_tasks[:3]:
                response += nudge_engine.format_nudge_message(nudge, include_actions=True)
                response += "\n---\n"
            
            if len(stalled_tasks) > 3:
                response += f"他{len(stalled_tasks) - 3}件の停滞タスクがあります。"
            
            return response
        
    except Exception as e:
        print(f"❌ Nudge error: {e}")
        return "ナッジ処理中にエラーが発生しました。"

async def handle_voice_mode_toggle(user_id: str) -> str:
    """音声モード切替"""
    try:
        # ユーザー設定を取得/更新
        doc_ref = firebase_manager.get_db().collection('user_profiles').document(user_id)
        doc = doc_ref.get()
        
        current_voice_mode = False
        if doc.exists:
            profile = doc.to_dict()
            current_voice_mode = profile.get('voice_mode', False)
        
        # 切り替え
        new_voice_mode = not current_voice_mode
        
        update_data = {
            'voice_mode': new_voice_mode,
            'updated_at': datetime.now(JST)
        }
        
        if doc.exists:
            doc_ref.update(update_data)
        else:
            update_data.update({
                'user_id': user_id,
                'created_at': datetime.now(JST)
            })
            doc_ref.set(update_data)
        
        mode_text = "ON" if new_voice_mode else "OFF"
        response = f"🎤 音声モードを{mode_text}にしました。"
        
        if new_voice_mode:
            response = voice_system.optimize_for_voice(response)
            
        return response
        
    except Exception as e:
        print(f"❌ Voice toggle error: {e}")
        return "音声モード切替中にエラーが発生しました。"

async def handle_decision_memo(user_id: str, command_text: str) -> str:
    """決裁メモ作成"""
    try:
        # "decision" を除いた部分を取得
        memo_content = command_text[8:].strip() if command_text.lower().startswith('decision') else command_text[2:].strip()
        
        if not memo_content:
            return "決裁メモの内容を教えてください。\n例: `C! decision 新システム導入を承認。ROI改善のため。`"
        
        # 簡単な形式で決定と理由を分離
        parts = memo_content.split('。', 1)
        decision = parts[0]
        reasoning = parts[1] if len(parts) > 1 else ""
        
        # 決裁メモ作成
        decision_log = await action_summary.create_decision_memo(
            user_id=user_id,
            context=f"ユーザー入力: {memo_content}",
            decision=decision,
            reasoning=reasoning
        )
        
        if decision_log:
            return action_summary.format_decision_memo(decision_log)
        else:
            return "❌ 決裁メモの作成に失敗しました。"
        
    except Exception as e:
        print(f"❌ Decision memo error: {e}")
        return "決裁メモ作成中にエラーが発生しました。"

async def process_attachments(message, user_id: str, username: str):
    """添付ファイル処理"""
    try:
        analyses = []
        all_created_todos = []
        
        for attachment in message.attachments:
            # ファイルをダウンロード
            attachment_data = await attachment.read()
            
            # ファイルタイプ判定
            attachment_type = "image"
            if attachment.filename.lower().endswith(('.pdf')):
                attachment_type = "pdf"
            elif attachment.filename.lower().endswith(('.txt', '.md')):
                attachment_type = "text"
            
            # OCR処理
            analysis = await ocr_system.process_attachment(
                user_id, attachment_data, attachment.filename, attachment_type
            )
            analyses.append(analysis)
            
            # ToDo作成
            if analysis.extracted_tasks:
                created_todos = await ocr_system.create_todos_from_analysis(analysis, user_id)
                all_created_todos.extend(created_todos)
        
        # 結果レポート
        if len(analyses) == 1:
            report = ocr_system.format_analysis_report(analyses[0], all_created_todos)
        else:
            # 複数ファイルの場合
            report = await ocr_system.batch_process_attachments(
                user_id, 
                [{'data': await att.read(), 'filename': att.filename, 'type': 'image'} for att in message.attachments]
            )
        
        await message.channel.send(report)
        
        # アクション履歴に記録
        await action_summary.log_action_result(
            user_id,
            "attachment.process",
            f"添付ファイル処理: {len(message.attachments)}件",
            {
                'success': True,
                'files_processed': len(message.attachments),
                'tasks_created': len(all_created_todos),
                'analyses': len(analyses)
            }
        )
        
    except Exception as e:
        print(f"❌ Attachment processing error: {e}")
        await message.channel.send("添付ファイルの処理中にエラーが発生しました。")

# ボイスチャンネルハンドラー（一時的に削除 - discord.sinks互換性問題）

# ヘルプ機能
async def handle_help() -> str:
    """ヘルプメッセージ"""
    return """
📚 **Catherine AI v2.0 - コマンド一覧**

**👥 チームToDo管理**
`C! todo [@担当者] [内容]` - チームToDo作成
`C! update 「タスク名」の期日を明後日17:00に` - 自然言語でToDo更新
`C! list` - チーム全体のToDoリスト
`C! list @mrc` - 担当者別リスト
`C! assign [番号] [@新担当者]` - 担当者変更
`C! done [番号]` - チームToDo完了
`C! dashboard` - チームダッシュボード
`C! report` - チームレポート生成

**📝 個人ToDo管理**
`C! mytodo [内容]` - 個人ToDo作成
`C! mylist` - 個人ToDoリスト表示
`C! mydone [番号]` - 個人ToDo完了

**⏰ リマインダー**
`C! remind [内容] at [日時]` - リマインダー設定
`C! reminders` - リマインダー一覧

**🎤 ボイスチャンネル**
`C! join` - ボイスチャンネル参加
`C! listen` - 音声認識開始（「キャサリン」で呼びかけ）
`C! stop` - 音声認識停止
`C! leave` - ボイスチャンネル退出
`C! status` - ボイス状態確認

**🎨 カスタマイズ**
`C! humor [0-100]` - ユーモアレベル調整
`C! style [casual/formal]` - 会話スタイル設定
`C! preferences` - 現在の設定確認

**📊 学習・分析**
`C! learn` - 学習状況確認
`C! briefing` - 朝のブリーフィング生成
`C! 朝` - 朝のブリーフィング（短縮）

リアクションで私の応答を評価してください！
👍 良い / 👎 改善が必要 / ❤️ 完璧 / 🤔 もっと詳しく

**🤖 新機能 v3.0**
- 確信度ガード: 曖昧な指示には確認を求めます
- 自動ブリーフィング: 今日の最重要3件と時間見積もり
- 自然言語更新: 会話から直接ToDo更新を実行
- アクション履歴: `C! summary` で実行履歴を確認
- 進捗ナッジ: `C! nudge` で停滞タスクを検出
- 添付ファイルAI分析: 画像/PDF→自動ToDo抽出
- 音声最適化: `C! voice` で音声モード切替
- 決裁メモ: `C! decision 承認理由` で構造化記録
"""

# ユーザープロファイル関連
async def get_user_profile(user_id: str) -> Dict:
    """ユーザープロファイル取得"""
    try:
        doc_ref = firebase_manager.get_db().collection('user_profiles').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            # デフォルトプロファイル作成
            default_profile = {
                'user_id': user_id,
                'created_at': datetime.now(JST),
                'preferences': {
                    'communication_style': 'friendly',
                    'humor_level': 50,
                    'formality': 'casual',
                    'response_length': 'medium'
                },
                'stats': {
                    'total_interactions': 0,
                    'total_todos': 0,
                    'total_reminders': 0
                }
            }
            doc_ref.set(default_profile)
            return default_profile
            
    except Exception as e:
        print(f"❌ Profile retrieval error: {e}")
        return {}

# メッセージマッピング（リアクション追跡用）
async def save_message_mapping(user_message_id: str, bot_message_id: str, 
                              user_id: str, bot_response: str):
    """メッセージIDのマッピングを保存"""
    try:
        mapping = {
            'user_message_id': str(user_message_id),
            'bot_message_id': str(bot_message_id),
            'user_id': user_id,
            'bot_response': bot_response,
            'timestamp': datetime.now(JST)
        }
        
        doc_ref = firebase_manager.get_db().collection('message_mappings').document(str(bot_message_id))
        doc_ref.set(mapping)
        
    except Exception as e:
        print(f"❌ Message mapping error: {e}")

async def get_message_mapping(message_id: str) -> Optional[Dict]:
    """メッセージマッピングを取得"""
    try:
        doc_ref = firebase_manager.get_db().collection('message_mappings').document(str(message_id))
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
        
    except Exception as e:
        print(f"❌ Mapping retrieval error: {e}")
        return None

async def get_feedback_message(emoji: str) -> str:
    """リアクションに対するフィードバックメッセージ"""
    messages = {
        '👍': 'フィードバックありがとうございます！より良い応答を心がけます。',
        '👎': 'ご指摘ありがとうございます。改善いたします。',
        '❤️': 'とても嬉しいです！これからも頑張ります！',
        '❌': '申し訳ございません。次回は改善いたします。'
    }
    return messages.get(emoji, 'フィードバックを受け取りました。')

# 定期タスク
@tasks.loop(minutes=1)
async def check_reminders():
    """リマインダーチェック（1分ごと）"""
    try:
        # アクティブなリマインダーをチェック
        now = datetime.now(JST)
        # シンプルなクエリに変更（インデックス不要）
        reminders = firebase_manager.get_db().collection('reminders')\
            .where('status', '==', 'active')\
            .stream()
        
        for reminder_doc in reminders:
            reminder = reminder_doc.to_dict()
            
            # Pythonでフィルタリング
            reminder_time = reminder.get('next_reminder')
            if not reminder_time or reminder_time > now:
                continue
            
            # 通知送信
            user_id = reminder['user_id']
            message = f"@everyone 📢 **リマインダー**\n"\
                     f"🔔 {reminder['title']}\n"\
                     f"💬 {reminder['message']}"
            # ユーザーのDMチャンネルを取得または該当チャンネルに送信
            # 実装は環境に応じて調整
            
            # リマインダー更新
            if reminder['reminder_type'] == 'once':
                reminder_doc.reference.update({'status': 'completed'})
            else:
                # 次回のリマインダー時刻を計算
                pass
                
    except Exception as e:
        print(f"❌ Reminder check error: {e}")

@tasks.loop(hours=1)
async def update_learning():
    """学習モデルの定期更新（1時間ごと）"""
    try:
        print("📚 学習モデル更新中...")
        
        # 進捗ナッジの送信チェック
        channel_id = os.getenv("NUDGE_CHANNEL_ID")
        if channel_id:
            nudge_count = await nudge_engine.send_nudge_notifications(bot, channel_id)
            if nudge_count > 0:
                print(f"📬 {nudge_count}件のナッジ通知を送信")
        
    except Exception as e:
        print(f"❌ Learning update error: {e}")

# Bot起動
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません")
        exit(1)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY が設定されていません")
        exit(1)
    
    print("🚀 Catherine AI v2.0 起動中...")
    bot.run(token)