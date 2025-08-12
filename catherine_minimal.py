#!/usr/bin/env python3
"""
Catherine AI - Minimal Clean Version
Fixed intent detection + health check only
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from openai import OpenAI
import json
from datetime import datetime
import pytz
from aiohttp import web
import threading

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='C! ', intents=intents)

# OpenAI client
client_oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))

# Firebase setup
try:
    from firebase_config import firebase_manager
    from team_todo_manager import TeamTodoManager
    team_todo_manager = TeamTodoManager(client_oa)
    print("[OK] Firebase TODO system loaded")
except Exception as e:
    print(f"[ERROR] Firebase TODO system unavailable: {e}")
    firebase_manager = None
    team_todo_manager = None

# Simple TODO fallback
try:
    from simple_todo import SimpleTodo
    simple_todo = SimpleTodo()
    print("[OK] Simple TODO system loaded")
except ImportError:
    simple_todo = None
    print("[ERROR] Simple TODO system unavailable")

# Health Check Server
async def health_check(request):
    """Railway health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Catherine AI Discord Bot'
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        'message': 'Catherine AI is running',
        'status': 'online'
    })

async def init_health_server():
    """Initialize aiohttp health server"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', root_handler)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"[OK] Health server started on port {port}")
    return runner

# TODO intent detection (ENHANCED)
def extract_edit_content(text: str) -> str:
    """編集コマンドから新しい内容を抽出"""
    import re
    
    # "3の内容は、maat台紙つくる。です。変更して" → "maat台紙つくる。"
    # "3を"新しい内容"に変更" → "新しい内容"
    # "3変更 新しい内容" → "新しい内容"
    
    patterns = [
        r'(\d+)の内容は[、，]?(.+?)です?[。、]?変更',  # "3の内容は、maat台紙つくる。です。変更して"
        r'(\d+)を[「"](.*?)[」"]に変更',  # "3を"新しい内容"に変更"
        r'(\d+)[を]?[「"](.*?)[」"]に[直す|修正|更新|編集|変更]',  # 各種編集キーワード
        r'(\d+)[を]?(.+?)に[直す|修正|更新|編集|変更]',  # "3をmaat台紙つくるに変更"
        r'(\d+)[変更|編集|修正|更新][、，]?(.+)',  # "3変更 新しい内容"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match and len(match.groups()) >= 2:
            content = match.group(2).strip()
            # 不要な文字を除去
            content = re.sub(r'[。、，\s]+$', '', content)
            if content:
                return content
    
    return ""

def detect_todo_intent(text: str):
    """Enhanced intent detection with number parsing"""
    text_lower = text.lower()
    
    # 番号抽出
    import re
    numbers = []
    
    # パターン: "1.2.4.5.6.7消して" または "1,2,3削除" など
    number_patterns = [
        r'(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.?',  # 1.2.4.5.6.7.
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',  # 1,2,3,4,5,6
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',  # 1,2,3,4,5  
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',  # 1,2,3,4
        r'(\d+)[,、\s](\d+)[,、\s](\d+)',  # 1,2,3
        r'(\d+)[,、\s](\d+)',  # 1,2
        r'(\d+)番?',  # 単独数字（「番」あり/なし）
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        if matches:
            if isinstance(matches[0], tuple):
                numbers.extend([int(n) for n in matches[0] if n])
            else:
                numbers.extend([int(n) for n in matches if n])
            break
    
    # TODO削除系キーワード（番号込み）
    is_todo_delete = any(keyword in text_lower for keyword in [
        '消して', '削除', '取り消し', 'けして', '消せ', 'remove', 'delete'
    ]) and numbers
    
    # TODO完了系キーワード（番号込み）
    is_todo_done = any(keyword in text_lower for keyword in [
        'done', '完了', '終わった', 'できた', '済み'
    ]) and numbers
    
    # TODO編集系キーワード（番号込み）
    is_todo_edit = any(keyword in text_lower for keyword in [
        '変更', '編集', '修正', '更新', '直す', 'edit', 'change', 'update'
    ]) and numbers
    
    # TODO表示系キーワード（最優先）
    is_todo_list = any(keyword in text_lower for keyword in [
        'リスト出', 'リスト表示', 'リスト見せ', 'リストだして', 'リスト教',
        'タスク一覧', 'todo一覧', 'やること見せ', 'タスク出し', 'list',
        '一覧出し', '一覧表示', '確認', '見せて', 'だして', 'リストして'
    ]) and not is_todo_delete
    
    # TODO追加系キーワード（表示系を除外）
    is_todo_add = any(keyword in text_lower for keyword in [
        '追加', '登録', '入れて', '作って', 'つくって', '新しく'
    ]) and not is_todo_list and not is_todo_delete and not is_todo_done and not is_todo_edit
    
    # 総合TODO判定
    is_todo_command = is_todo_list or is_todo_add or is_todo_done or is_todo_delete or is_todo_edit or any(keyword in text_lower for keyword in [
        'todo', 'タスク', 'やること'
    ])
    
    return is_todo_command, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers

async def handle_todo_list():
    """TODO一覧表示"""
    if team_todo_manager:
        try:
            todos = await team_todo_manager.get_team_todos()
            if not todos:
                return "📝 TODOはありません"
            
            response = "📊 **TODOリスト**\n\n"
            for i, todo in enumerate(todos[:30], 1):
                title = todo['title'][:50].replace('\n', ' ').replace('\r', ' ').strip()
                response += f"{i}. **{title}**\n"
            return response
        except Exception as e:
            print(f"[ERROR] Team TODO list error: {e}")
    
    # Fallback to simple TODO
    if simple_todo:
        return simple_todo.list_todos('default')
    
    return "❌ TODO機能が利用できません"

async def handle_todo_add(content: str, user_id: str):
    """TODO追加"""
    if not content.strip():
        return "📋 TODOの内容を教えてください。"
    
    if simple_todo:
        return simple_todo.add_todo(content, user_id)
    
    return "❌ TODO追加機能が利用できません"

async def handle_todo_delete(numbers: list):
    """TODO削除（番号指定）"""
    if not numbers:
        return "❌ 削除する番号を指定してください"
    
    if team_todo_manager:
        try:
            todos = await team_todo_manager.get_team_todos()
            print(f"[DEBUG] Retrieved {len(todos)} TODOs from Firebase")
            if not todos:
                return "📝 削除するTODOがありません"
            
            # Debug: Show structure of first TODO
            if todos:
                first_todo = todos[0]
                print(f"[DEBUG] First TODO structure: {list(first_todo.keys())}")
                print(f"[DEBUG] First TODO sample: {first_todo}")
            
            deleted_items = []
            for num in sorted(numbers, reverse=True):  # 逆順で削除
                if 1 <= num <= len(todos):
                    todo_to_delete = todos[num-1]
                    # Try different possible ID fields
                    todo_id = todo_to_delete.get('id') or todo_to_delete.get('todo_id') or todo_to_delete.get('_id')
                    print(f"[DEBUG] TODO {num} structure: {list(todo_to_delete.keys())}")
                    print(f"[DEBUG] Attempting to delete TODO {num}: ID={todo_id}, Title={todo_to_delete.get('title', 'NO_TITLE')}")
                    
                    if not todo_id:
                        print(f"[ERROR] No ID found for TODO {num}")
                        continue
                    
                    # Firebase TODO削除（statusを変更）
                    success = await team_todo_manager.update_todo_status(
                        todo_id, 'deleted', f'Deleted by user command'
                    )
                    print(f"[DEBUG] Delete result for TODO {num} (ID={todo_id}): {success}")
                    
                    if success:
                        deleted_items.append(f"{num}. {todo_to_delete['title'][:30]}")
                else:
                    print(f"[DEBUG] TODO number {num} out of range (1-{len(todos)})")
            
            if deleted_items:
                return f"🗑️ **削除完了:**\n" + "\n".join(deleted_items)
            else:
                return "❌ 指定されたTODOを削除できませんでした"
                
        except Exception as e:
            print(f"[ERROR] Team TODO delete error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to simple TODO
    if simple_todo:
        deleted_items = []
        for num in numbers:
            result = simple_todo.delete_todo(num, 'default')
            if "削除:" in result:
                deleted_items.append(result)
        
        if deleted_items:
            return "🗑️ **削除完了:**\n" + "\n".join(deleted_items)
    
    return "❌ TODO削除機能が利用できません"

async def handle_todo_complete(numbers: list):
    """TODO完了（番号指定）"""
    if not numbers:
        return "❌ 完了する番号を指定してください"
    
    if team_todo_manager:
        try:
            todos = await team_todo_manager.get_team_todos()
            if not todos:
                return "📝 完了するTODOがありません"
            
            completed_items = []
            for num in numbers:
                if 1 <= num <= len(todos):
                    todo_to_complete = todos[num-1]
                    # Try different possible ID fields
                    todo_id = todo_to_complete.get('id') or todo_to_complete.get('todo_id') or todo_to_complete.get('_id')
                    print(f"[DEBUG] Attempting to complete TODO {num}: ID={todo_id}, Title={todo_to_complete.get('title', 'NO_TITLE')}")
                    
                    if not todo_id:
                        print(f"[ERROR] No ID found for TODO {num}")
                        continue
                    
                    # Firebase TODO完了（statusを変更）
                    success = await team_todo_manager.update_todo_status(
                        todo_id, 'completed', f'Completed by user command'
                    )
                    print(f"[DEBUG] Complete result for TODO {num} (ID={todo_id}): {success}")
                    
                    if success:
                        completed_items.append(f"{num}. {todo_to_complete['title'][:30]}")
            
            if completed_items:
                return f"✅ **完了:**\n" + "\n".join(completed_items)
            else:
                return "❌ 指定されたTODOを完了できませんでした"
                
        except Exception as e:
            print(f"[ERROR] Team TODO complete error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to simple TODO
    if simple_todo:
        completed_items = []
        for num in numbers:
            result = simple_todo.complete_todo(num, 'default')
            if "完了:" in result:
                completed_items.append(result)
        
        if completed_items:
            return "✅ **完了:**\n" + "\n".join(completed_items)
    
    return "❌ TODO完了機能が利用できません"

async def handle_todo_edit(numbers: list, new_content: str):
    """TODO編集（番号指定）"""
    if not numbers:
        return "❌ 編集する番号を指定してください"
    
    if not new_content.strip():
        return "❌ 新しい内容を入力してください"
    
    if team_todo_manager:
        try:
            todos = await team_todo_manager.get_team_todos()
            if not todos:
                return "📝 編集するTODOがありません"
            
            edited_items = []
            for num in numbers:
                if 1 <= num <= len(todos):
                    todo_to_edit = todos[num-1]
                    todo_id = todo_to_edit.get('id') or todo_to_edit.get('todo_id') or todo_to_edit.get('_id')
                    old_title = todo_to_edit.get('title', 'NO_TITLE')
                    print(f"[DEBUG] Attempting to edit TODO {num}: ID={todo_id}, Old='{old_title}' -> New='{new_content}'")
                    
                    if not todo_id:
                        print(f"[ERROR] No ID found for TODO {num}")
                        continue
                    
                    # Firebase TODO編集（titleを更新）
                    success = await team_todo_manager.update_todo_title(
                        todo_id, new_content
                    )
                    print(f"[DEBUG] Edit result for TODO {num} (ID={todo_id}): {success}")
                    
                    if success:
                        edited_items.append(f"{num}. {old_title[:20]} → {new_content[:20]}")
            
            if edited_items:
                return f"✏️ **編集完了:**\n" + "\n".join(edited_items)
            else:
                return "❌ 指定されたTODOを編集できませんでした"
                
        except Exception as e:
            print(f"[ERROR] Team TODO edit error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to simple TODO
    if simple_todo:
        edited_items = []
        for num in numbers:
            # Simple TODO doesn't have edit function, so we'll provide guidance
            edited_items.append(f"{num}. 編集機能は現在Firebaseモードでのみ対応")
        
        if edited_items:
            return "⚠️ **編集機能制限:**\n" + "\n".join(edited_items)
    
    return "❌ TODO編集機能が利用できません"

@bot.event
async def on_ready():
    print(f'[READY] {bot.user} is ready!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Skip bot commands
    if message.content.startswith('C!'):
        await bot.process_commands(message)
        return
    
    command_text = message.content.strip()
    user_id = str(message.author.id)
    
    # Enhanced Intent detection
    is_todo_command, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers = detect_todo_intent(command_text)
    
    if is_todo_command:
        print(f"[TODO] Processing: {command_text} | Numbers: {numbers}")
        
        try:
            if is_todo_list:
                # TODO一覧表示
                response = await handle_todo_list()
            elif is_todo_delete:
                # TODO削除（番号指定）
                response = await handle_todo_delete(numbers)
            elif is_todo_done:
                # TODO完了（番号指定）
                response = await handle_todo_complete(numbers)
            elif is_todo_edit:
                # TODO編集（番号指定）
                new_content = extract_edit_content(command_text)
                if new_content:
                    response = await handle_todo_edit(numbers, new_content)
                else:
                    response = f"❌ 編集内容が見つかりません。\n例: `3の内容は、新しいタスク名です。変更して`"
            elif is_todo_add:
                # TODO追加
                response = await handle_todo_add(command_text, user_id)
            else:
                # 曖昧な場合の確認
                response = f"**{command_text}** について、何をしますか？\n\n" + \
                    "📝 ①追加する\n📋 ②一覧を見る\n✅ ③完了する\n🗑️ ④削除する\n✏️ ⑤編集する\n\n" + \
                    "番号か、「追加」「リスト」「完了」「削除」「編集」で教えてください。"
            
            await message.channel.send(response)
            return
        except Exception as e:
            print(f"[ERROR] TODO processing error: {e}")
            await message.channel.send("TODO処理中にエラーが発生しました。")
            return
    
    # Basic chat responses
    if any(word in command_text.lower() for word in ['こんにちは', 'hello', '元気']):
        await message.channel.send("こんにちは！何かお手伝いできることはありますか？")
    elif any(word in command_text.lower() for word in ['ありがとう', 'thanks']):
        await message.channel.send("どういたしまして！")
    elif 'help' in command_text.lower() or 'ヘルプ' in command_text.lower():
        help_msg = """**Catherine AI - 使い方**

📋 **TODO機能:**
- `リスト出して` → TODO一覧表示
- `[内容] 追加` → TODO追加
- `1,2,3完了` → TODO完了
- `1,2,3消して` → TODO削除  
- `3の内容は、新しいタスクです。変更して` → TODO編集

✨ **編集例:**
- `3の内容は、maat台紙つくる。です。変更して`
- `1を"新しいタスク名"に変更`
- `2変更 修正されたタスク`

💬 **その他:**
- 普通に話しかけてください
- `こんにちは` で挨拶
"""
        await message.channel.send(help_msg)

if __name__ == "__main__":
    async def main():
        # Health server開始
        await init_health_server()
        
        # Discord bot開始
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("[ERROR] DISCORD_TOKEN not set")
            return
        
        print("[START] Catherine AI (Minimal) starting...")
        await bot.start(token)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[STOP] Catherine AI stopped")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()