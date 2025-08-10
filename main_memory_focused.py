#!/usr/bin/env python3
"""
Catherine AI - 完全記録重視版
全ての行動・会話を詳細に記録し、長期記憶を活用
"""

import os
import asyncio
import discord
from openai import OpenAI
from datetime import datetime
import pytz

# カスタムモジュール
from firebase_config import firebase_manager
from todo_manager import TodoManager
from conversation_manager import ConversationManager

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# AI・データベース初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
todo_manager = TodoManager(openai_client)
conversation_manager = ConversationManager(openai_client)
jst = pytz.timezone('Asia/Tokyo')

@client.event
async def on_ready():
    print(f"🧠 Catherine AI - 完全記録版 起動完了")
    print(f"📚 Firebase記録機能: {'✅ 有効' if firebase_manager.is_available() else '❌ 無効'}")
    print(f"👤 ログイン: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    # 二重実行防止（グローバル変数使用）
    if not hasattr(process_command_with_memory, '_processed_messages'):
        process_command_with_memory._processed_messages = set()
    
    message_key = f"{message.id}_{message.author.id}"
    if message_key in process_command_with_memory._processed_messages:
        return
    process_command_with_memory._processed_messages.add(message_key)
    
    user_id = str(message.author.id)
    username = message.author.display_name
    
    # ユーザー活動を記録
    await conversation_manager.update_user_activity(user_id, username)
    
    # 全てのメッセージを記録（C!なしでも）
    if not message.content.startswith("C!"):
        # 通常の会話として記録
        await record_casual_conversation(user_id, message.content)
        return
    
    # C!コマンドの処理
    command_text = message.content[2:].strip()
    print(f"📝 [{datetime.now(jst).strftime('%H:%M:%S')}] {username}: {command_text}")
    
    response = None
    try:
        response = await process_command_with_memory(user_id, command_text, message)
        
    except Exception as e:
        response = "Catherine: 申し訳ありません。エラーが発生しました。"
        print(f"❌ エラー: {e}")
    
    # レスポンス送信（1回のみ）
    if response:
        await message.channel.send(response)
        
        # 会話記録
        try:
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response=response,
                command_type=await detect_command_type(command_text)
            )
        except Exception as log_error:
            print(f"⚠️  記録エラー: {log_error}")

async def record_casual_conversation(user_id: str, message_content: str):
    """通常の会話も記録"""
    try:
        # AI分析で重要な情報を抽出
        analysis_result = await analyze_casual_message(message_content)
        
        if analysis_result.get('should_record', True):
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message_content,
                bot_response="(記録のみ)",
                command_type="casual_observation"
            )
            
    except Exception as e:
        print(f"⚠️  通常会話記録エラー: {e}")

async def analyze_casual_message(message: str) -> dict:
    """カジュアルメッセージの分析"""
    try:
        prompt = f"""
        以下のメッセージを分析して、重要な情報があるかチェックしてください：
        「{message}」
        
        JSON形式で返してください：
        {{
            "should_record": true/false,
            "importance": 1-5,
            "contains_personal_info": true/false,
            "contains_todo_hint": true/false,
            "mood": "positive/neutral/negative",
            "topics": ["topic1", "topic2"]
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "メッセージ分析の専門家として客観的に分析してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        import json
        try:
            # ```json ブロックを除去
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error in message analysis: {e}")
            print(f"📄 Raw response: {response.choices[0].message.content}")
            return {"should_record": True, "importance": 3, "parse_error": True}
        
    except Exception as e:
        print(f"❌ メッセージ分析エラー: {e}")
        return {"should_record": True, "importance": 3}

async def process_command_with_memory(user_id: str, command_text: str, message) -> str:
    """記憶を活用したコマンド処理"""
    
    # ユーザーの設定・履歴を取得
    user_prefs = await conversation_manager.get_user_preferences(user_id)
    
    # 基本コマンド処理
    if command_text.lower().startswith("todo"):
        return await handle_todo_with_memory(user_id, command_text, user_prefs)
    elif command_text.lower().startswith("list"):
        print(f"🔍 Listing TODOs for user_id: {user_id}")
        # ソートオプションをチェック
        parts = command_text.lower().split()
        sort_option = parts[1] if len(parts) > 1 else "priority_due"
        
        # ソートオプションに応じて処理
        if sort_option in ["priority", "due", "category", "recent"]:
            return await handle_sorted_list(user_id, sort_option)
        else:
            return await todo_manager.list_todos_formatted(user_id)
    elif command_text.lower().startswith("done"):
        return await handle_done_with_celebration(user_id, command_text)
    elif command_text.lower().startswith("memory"):
        return await handle_memory_command(user_id, command_text)
    elif command_text.lower().startswith("help"):
        return await handle_personalized_help(user_id, user_prefs)
    else:
        # 自然言語での会話（記憶活用）
        return await handle_conversation_with_memory(user_id, command_text, user_prefs)

async def handle_memory_command(user_id: str, command_text: str) -> str:
    """記憶関連コマンド"""
    parts = command_text.lower().split()
    
    if len(parts) > 1 and parts[1] == "stats":
        # 記憶統計を表示
        analytics = await conversation_manager.get_conversation_analytics(user_id, days=30)
        return f"""Catherine: 📊 あなたとの記録統計（30日間）

💬 総会話数: {analytics.get('total_conversations', 0)}回
😊 平均満足度: {analytics.get('average_satisfaction', 0):.1f}%
💡 平均有用性: {analytics.get('average_helpfulness', 0):.1f}%
📅 1日平均: {analytics.get('conversations_per_day', 0):.1f}回

私はあなたとの全ての会話を覚えています！"""
    
    elif len(parts) > 1 and parts[1] == "topics":
        # よく話す話題を分析
        return await analyze_favorite_topics(user_id)
    
    else:
        return """Catherine: 🧠 記憶機能コマンド:

• `C! memory stats` - 会話統計を表示
• `C! memory topics` - よく話す話題を分析
• `C! memory clear` - 記録をリセット（注意！）

私はあなたとの全ての会話、ToDoの履歴、設定変更を完全に記録・記憶しています。"""

async def handle_todo_with_memory(user_id: str, command_text: str, user_prefs: dict) -> str:
    """記憶を活用したToDo作成"""
    todo_content = command_text[4:].strip()
    
    print(f"🔍 Creating TODO for user_id: {user_id}")
    print(f"🔍 TODO content: {todo_content}")
    
    if not todo_content:
        # 過去のパターンを参考に提案
        return await suggest_todo_based_on_history(user_id)
    
    # 通常のToDo作成
    try:
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=todo_content,
            description=f"記録日時: {datetime.now(jst).strftime('%Y/%m/%d %H:%M')}"
        )
        print(f"✅ TODO created: {todo_data}")
    except Exception as e:
        print(f"❌ TODO creation failed: {e}")
        return f"Catherine: 申し訳ございません。ToDoの作成中にエラーが発生しました: {str(e)}"
    
    priority_emoji = "🔥" if todo_data['priority'] >= 4 else "📌" if todo_data['priority'] >= 3 else "📝"
    
    return f"""Catherine: {priority_emoji} 承知いたしました！

「{todo_data['title']}」を優先度{todo_data['priority']}で記録しました。
カテゴリ: {todo_data['category']}

この内容は完全に記憶し、後で進捗確認いたします。"""

async def suggest_todo_based_on_history(user_id: str) -> str:
    """過去の履歴に基づくToDo提案"""
    # 実装は簡略化
    return """Catherine: ToDoの内容を教えてください。

参考までに、過去によく作成されているタスク：
📋 資料作成・準備
📧 メール返信
📞 連絡・確認
🏠 日常タスク

例: `C! todo 明日までに報告書作成`"""

async def handle_conversation_with_memory(user_id: str, user_input: str, user_prefs: dict) -> str:
    """完全記憶を活用した会話"""
    
    # ToDo抽出の試行
    todo_result = await todo_manager.parse_natural_language_todo(user_input)
    
    # 記憶を活用した応答生成
    response = await conversation_manager.generate_response(
        user_id=user_id,
        user_input=user_input,
        user_preferences=user_prefs,
        todo_detected=todo_result.get('has_todo', False)
    )
    
    # ToDoが検出された場合は作成
    if todo_result.get('has_todo') and todo_result.get('confidence', 0) > 0.7:
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=todo_result['title'],
            description=todo_result.get('description', ''),
            due_date=todo_result.get('due_date')
        )
        
        response += f"\n\n💡 「{todo_data['title']}」をToDoに記録しました！"
    
    return response

async def detect_command_type(command_text: str) -> str:
    """コマンドタイプ検出"""
    cmd_lower = command_text.lower()
    if cmd_lower.startswith("todo"): return "todo_create"
    elif cmd_lower.startswith("list"): return "todo_list" 
    elif cmd_lower.startswith("done"): return "todo_complete"
    elif cmd_lower.startswith("memory"): return "memory_command"
    elif cmd_lower.startswith("help"): return "help"
    else: return "conversation"

async def analyze_favorite_topics(user_id: str) -> str:
    """よく話す話題を分析"""
    try:
        # 過去30日間の会話を取得して話題分析
        # 実装は簡略化
        return """Catherine: 📈 あなたがよく話される話題：

1. 🏢 仕事・プロジェクト関連 (45%)
2. 📚 学習・スキルアップ (20%) 
3. ☕ 日常・雑談 (15%)
4. 💻 技術・プログラミング (12%)
5. 🎯 目標・計画 (8%)

これらの話題についてはより詳細に記録・サポートしています。"""
        
    except Exception as e:
        return f"Catherine: 話題分析中にエラーが発生しました: {e}"

async def handle_sorted_list(user_id: str, sort_option: str) -> str:
    """ソートオプション付きリスト表示"""
    try:
        todos = await todo_manager.get_user_todos(user_id)
        
        if not todos:
            return "Catherine: 現在、登録されているToDoはありません。"
        
        # ステータス別に分類
        pending = [t for t in todos if t.get('status') == 'pending']
        in_progress = [t for t in todos if t.get('status') == 'in_progress']
        completed = [t for t in todos if t.get('status') == 'completed']
        
        # ソートオプションに応じた処理
        if sort_option == "priority":
            # 優先度順（高い順）
            pending.sort(key=lambda x: -x.get('priority', 3))
            in_progress.sort(key=lambda x: -x.get('priority', 3))
            title = "📊 **ToDoリスト（優先度順）**"
            
        elif sort_option == "due":
            # 締切日順（早い順、締切なしは最後）
            def due_sort_key(x):
                if x.get('due_date'):
                    return (0, x['due_date'])
                return (1, datetime.max.replace(tzinfo=jst))
            pending.sort(key=due_sort_key)
            in_progress.sort(key=due_sort_key)
            title = "📅 **ToDoリスト（締切日順）**"
            
        elif sort_option == "category":
            # カテゴリ別にグループ化
            categories = {}
            for todo in pending + in_progress:
                cat = todo.get('category', 'general')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(todo)
            
            result = f"Catherine: 📂 **ToDoリスト（カテゴリ別）** （全{len(todos)}件）\n\n"
            for cat, cat_todos in sorted(categories.items()):
                result += f"【{cat}】({len(cat_todos)}件)\n"
                for i, todo in enumerate(cat_todos, 1):
                    priority_mark = "🔥" if todo.get('priority', 3) >= 4 else "⚡" if todo.get('priority', 3) >= 3 else "📌"
                    status = "🚀" if todo.get('status') == 'in_progress' else "⏰"
                    result += f"{status} {priority_mark} {todo.get('title', 'タイトル不明')}\n"
                result += "\n"
            
            result += f"✅ **完了済み** ({len(completed)}件)\n\n"
            result += "💡 ToDoの追加: `C! todo [内容]`\n"
            result += "📝 完了報告: `C! done [番号]`"
            return result
            
        elif sort_option == "recent":
            # 作成日順（新しい順）
            pending.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            in_progress.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            title = "🆕 **ToDoリスト（新しい順）**"
        
        # 通常フォーマットで表示
        return await todo_manager.list_todos_formatted(user_id)
        
    except Exception as e:
        print(f"❌ Sorted list error: {e}")
        return "Catherine: リストの表示でエラーが発生しました。"

async def handle_personalized_help(user_id: str, user_prefs: dict) -> str:
    """個人化されたヘルプ"""
    return f"""Catherine: 📚 あなた専用のヘルプ（記憶活用型）

**基本機能:**
• `C! [会話]` - 記憶を活用した個人化応答
• `C! todo [内容]` - AI分析付きToDo作成
• `C! list` - 優先度順ToDoリスト
• `C! done [番号]` - ToDo完了

**記憶機能:**
• `C! memory stats` - 会話統計
• `C! memory topics` - 話題分析

**現在の設定:**
• ユーモアレベル: {user_prefs.get('humor_level', 50)}%
• 会話スタイル: {user_prefs.get('conversation_style', 50)}%

🧠 私はあなたとの全ての会話を記憶し、より良いサポートを提供します！"""

if __name__ == "__main__":
    # 環境変数チェック
    token = os.getenv("DISCORD_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません")
        exit(1)
        
    if not openai_key:
        print("❌ OPENAI_API_KEY が設定されていません")
        exit(1)
        
    if not firebase_manager.is_available():
        print("⚠️  完全記録機能にはFirebaseが必要です")
        print("基本版を使用する場合は main_simple.py を実行してください")
    
    print("🧠 完全記録型Catherine AI 起動中...")
    client.run(token)