import os
import asyncio
import discord
from openai import OpenAI
import json
from datetime import datetime
import uuid

# Firebase とカスタムモジュールのインポート
from firebase_config import firebase_manager
from todo_manager import TodoManager
from conversation_manager import ConversationManager

# Railway 用のポート設定
PORT = int(os.environ.get("PORT", 8080))

# Discord intents 設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# OpenAI クライアント初期化
client_oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# マネージャークラスの初期化
todo_manager = TodoManager(client_oa)
conversation_manager = ConversationManager(client_oa)

@client.event
async def on_ready():
    print(f"✅ Enhanced Catherine Bot Logged in as {client.user}")
    print("🎯 Features: ToDo管理, 会話記録, パーソナリティ調整")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    username = message.author.display_name
    
    # ユーザー情報を更新/作成
    await conversation_manager.update_user_activity(user_id, username)

    # C! コマンドの処理
    if message.content.startswith("C!"):
        command_text = message.content[len("C!"):].strip()
        print(f"📝 Command received from {username}: {command_text}")

        try:
            # コマンドの種類を判定
            response = await process_command(user_id, command_text, message)
            
            # 会話を記録
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response=response,
                command_type=await detect_command_type(command_text)
            )
            
            await message.channel.send(response)
            print(f"💬 Response sent to {username}")

        except Exception as e:
            error_msg = "Catherine: すみません、エラーが発生しました。しばらくしてからもう一度お試しください。"
            print(f"❌ Error processing command: {e}")
            await message.channel.send(error_msg)
            
            # エラーも記録
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response=error_msg,
                command_type="error",
                error=str(e)
            )

async def process_command(user_id: str, command_text: str, message) -> str:
    """コマンドを処理して適切な応答を返す"""
    
    # 特殊コマンドの処理
    if command_text.lower().startswith("todo"):
        return await handle_todo_command(user_id, command_text)
    elif command_text.lower().startswith("list"):
        return await handle_list_command(user_id)
    elif command_text.lower().startswith("done"):
        return await handle_done_command(user_id, command_text)
    elif command_text.lower().startswith("humor"):
        return await handle_humor_command(user_id, command_text)
    elif command_text.lower().startswith("style"):
        return await handle_style_command(user_id, command_text)
    elif command_text.lower().startswith("help"):
        return await handle_help_command()
    else:
        # 自然言語での会話・ToDo抽出
        return await handle_natural_conversation(user_id, command_text)

async def handle_todo_command(user_id: str, command_text: str) -> str:
    """ToDo作成コマンドの処理"""
    # "todo" を除いた部分を取得
    todo_content = command_text[4:].strip()
    
    if not todo_content:
        return "Catherine: ToDoの内容を教えてください。\n例: `C! todo 明日までに資料作成`"
    
    # ToDo作成
    todo_data = await todo_manager.create_todo(
        user_id=user_id,
        title=todo_content,
        description=""
    )
    
    priority_emoji = "🔥" if todo_data['priority'] >= 4 else "📌" if todo_data['priority'] >= 3 else "📝"
    
    return f"Catherine: {priority_emoji} 承知いたしました！\n"\
           f"「{todo_data['title']}」を優先度{todo_data['priority']}で登録しました。\n"\
           f"カテゴリ: {todo_data['category']}"

async def handle_list_command(user_id: str) -> str:
    """ToDoリスト表示"""
    todos = await todo_manager.get_user_todos(user_id, status="pending")
    
    if not todos:
        return "Catherine: 現在、未完了のToDoはありません。お疲れ様です！✨"
    
    response = "Catherine: 📋 現在のToDoリスト:\n\n"
    for i, todo in enumerate(todos[:10], 1):  # 最大10件
        priority_emoji = "🔥" if todo['priority'] >= 4 else "📌" if todo['priority'] >= 3 else "📝"
        due_text = ""
        if todo.get('due_date'):
            due_text = f" (期限: {todo['due_date'].strftime('%m/%d %H:%M')})"
        
        response += f"{i}. {priority_emoji} {todo['title']}{due_text}\n"
    
    if len(todos) > 10:
        response += f"\n... 他{len(todos) - 10}件"
    
    return response

async def handle_done_command(user_id: str, command_text: str) -> str:
    """ToDo完了処理"""
    # 番号を抽出
    try:
        todo_num = int(command_text.split()[1]) - 1
        todos = await todo_manager.get_user_todos(user_id, status="pending")
        
        if 0 <= todo_num < len(todos):
            todo = todos[todo_num]
            success = await todo_manager.update_todo_status(todo['todo_id'], "completed")
            
            if success:
                return f"Catherine: ✅ 「{todo['title']}」完了です！お疲れ様でした。"
            else:
                return "Catherine: 申し訳ございません。更新に失敗しました。"
        else:
            return "Catherine: 指定された番号のToDoが見つかりません。`C! list`で確認してください。"
            
    except (IndexError, ValueError):
        return "Catherine: 使用方法: `C! done 1` (1は完了したいToDoの番号)"

async def handle_humor_command(user_id: str, command_text: str) -> str:
    """ユーモアレベル調整"""
    try:
        parts = command_text.split()
        if len(parts) >= 2:
            humor_level = int(parts[1])
            if 0 <= humor_level <= 100:
                await conversation_manager.update_user_preferences(
                    user_id, {"humor_level": humor_level}
                )
                humor_desc = {
                    0: "超真面目モード",
                    25: "少し堅めモード", 
                    50: "バランス型",
                    75: "フレンドリーモード",
                    100: "お笑い芸人モード"
                }.get(humor_level, f"{humor_level}%モード")
                
                return f"Catherine: ユーモアレベルを{humor_level}%({humor_desc})に設定しました！"
            else:
                return "Catherine: ユーモアレベルは0-100の間で設定してください。"
        else:
            return "Catherine: 使用方法: `C! humor 50` (0-100)"
    except ValueError:
        return "Catherine: 数値で指定してください。例: `C! humor 75`"

async def handle_style_command(user_id: str, command_text: str) -> str:
    """会話スタイル調整"""
    parts = command_text.split()
    if len(parts) >= 2:
        style = parts[1].lower()
        style_map = {
            "casual": {"formality": 20, "description": "カジュアル"},
            "friendly": {"formality": 40, "description": "フレンドリー"},
            "polite": {"formality": 70, "description": "丁寧"},
            "formal": {"formality": 90, "description": "フォーマル"},
            "business": {"formality": 95, "description": "ビジネス"}
        }
        
        if style in style_map:
            await conversation_manager.update_user_preferences(
                user_id, {"conversation_style": style_map[style]["formality"]}
            )
            return f"Catherine: 会話スタイルを「{style_map[style]['description']}」に設定しました。"
        else:
            return "Catherine: 利用可能なスタイル: casual, friendly, polite, formal, business"
    else:
        return "Catherine: 使用方法: `C! style friendly`"

async def handle_help_command() -> str:
    """ヘルプ表示"""
    return """Catherine: 📚 利用可能なコマンド:

**ToDo管理:**
• `C! todo [内容]` - 新しいToDoを追加
• `C! list` - ToDoリストを表示  
• `C! done [番号]` - ToDoを完了

**パーソナリティ調整:**
• `C! humor [0-100]` - ユーモアレベル調整
• `C! style [casual/friendly/polite/formal/business]` - 会話スタイル

**その他:**
• `C! help` - このヘルプを表示
• `C! [自然な会話]` - 普通に話しかけてください

何でもお気軽に話しかけてくださいね！✨"""

async def handle_natural_conversation(user_id: str, user_input: str) -> str:
    """自然言語での会話処理"""
    
    # ユーザーの設定を取得
    user_prefs = await conversation_manager.get_user_preferences(user_id)
    
    # ToDo抽出の試行
    todo_result = await todo_manager.parse_natural_language_todo(user_input)
    
    # 会話の生成
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
        
        response += f"\n\n💡 「{todo_data['title']}」をToDoリストに追加しました！"
    
    return response

async def detect_command_type(command_text: str) -> str:
    """コマンドタイプを検出"""
    command_lower = command_text.lower()
    if command_lower.startswith("todo"):
        return "todo_create"
    elif command_lower.startswith("list"):
        return "todo_list"
    elif command_lower.startswith("done"):
        return "todo_complete"
    elif command_lower.startswith("humor"):
        return "settings_humor"
    elif command_lower.startswith("style"):
        return "settings_style"
    elif command_lower.startswith("help"):
        return "help"
    else:
        return "conversation"

if __name__ == "__main__":
    # 環境変数チェック
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN environment variable is not set")
        exit(1)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable is not set")
        exit(1)
    
    firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if not firebase_key:
        print("❌ FIREBASE_SERVICE_ACCOUNT_KEY environment variable is not set")
        exit(1)
    
    print("🚀 Starting Enhanced Catherine AI Secretary...")
    client.run(token)
