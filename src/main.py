from collections import defaultdict
from typing import Literal, Optional, Union, Dict, Any

import discord
from discord import Message as DiscordMessage, app_commands
import logging
import os
import sys

# Add parent directory to path for Firebase import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize logging first
logging.basicConfig(
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s", level=logging.INFO
)

# Firebase integration
try:
    from firebase_config import firebase_manager
    FIREBASE_ENABLED = True
    logging.info("Firebase integration enabled")
except ImportError:
    FIREBASE_ENABLED = False
    logging.warning("Firebase integration not available")

from src.base import Message, Conversation, ThreadConfig
from src.constants import (
    BOT_INVITE_URL,
    DISCORD_BOT_TOKEN,
    EXAMPLE_CONVOS,
    ACTIVATE_THREAD_PREFX,
    MAX_THREAD_MESSAGES,
    SECONDS_DELAY_RECEIVING_MSG,
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
)
import asyncio
import pytz
import uuid
from src.utils import (
    logger,
    should_block,
    close_thread,
    is_last_message_stale,
    discord_message_to_message,
)
from src import completion
from src.completion import generate_completion_response, process_response
from src.moderation import (
    moderate_message,
    send_moderation_blocked_message,
    send_moderation_flagged_message,
)
from src.context_manager import context_manager
from src.notion_integration import NotionIntegration
# Google integration now handled by google_services_integration.py
from src.mention_utils import DiscordMentionHandler, get_mention_string
from src.channel_utils import should_respond_to_message, get_channel_info

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
thread_data = defaultdict()

# システム初期化フラグ
_systems_initialized = False
# Bot インスタンス識別子
BOT_INSTANCE_ID = str(uuid.uuid4())[:8]

# グローバル変数
notion_integration = None
mention_handler = None

# システム初期化用のsetup_hook
@client.event
async def setup_hook():
    """Bot起動時にシステムを初期化"""
    global _systems_initialized, notion_integration, mention_handler
    
    if _systems_initialized:
        logger.info("Systems already initialized, skipping setup_hook")
        return
        
    logger.info(f"[BOT-{BOT_INSTANCE_ID}] Setup hook called - gradual system initialization")
    
    if FIREBASE_ENABLED:
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # 段階的にシステムを初期化（旧メモリベースシステムは削除済み）
            # Phase 1: 外部API管理リマインダーシステムを初期化
            logger.info("Phase 1: Initializing external reminder system...")
            from src.external_reminder_manager import init_external_reminder_manager
            from src.google_services_integration import google_services
            
            external_reminder_system = init_external_reminder_manager(
                notion_integration=None,  # 後で設定
                google_services=google_services,
                discord_bot=client
            )
            
            try:
                logger.info("Initializing external reminder system...")
                initialized = await external_reminder_system.initialize()
                if initialized:
                    await external_reminder_system.start_periodic_checker()
                    logger.info("External reminder system started successfully")
                else:
                    logger.warning("External reminder system initialization failed")
            except Exception as e:
                logger.error(f"Failed to start external reminder system: {e}")
                
            logger.info("Phase 1 system initialization completed in setup_hook")
            
            # Phase 1.5: Initialize unified TODO manager
            try:
                from src.unified_todo_manager import unified_todo_manager
                logger.info("Initializing unified TODO manager...")
                await unified_todo_manager.initialize()
                logger.info("Unified TODO manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize unified TODO manager: {e}")
            
            # Phase 2: MCPブリッジを初期化（オプション）
            try:
                from src.mcp_bridge import mcp_bridge
                logger.info("Phase 2: Initializing MCP Bridge...")
                mcp_initialized = await mcp_bridge.initialize()
                if mcp_initialized:
                    logger.info(f"MCP Bridge initialized successfully")
                    
                    # Notion統合を初期化
                    notion_integration = NotionIntegration(mcp_bridge)
                    mention_handler = DiscordMentionHandler(client)
                    logger.info("Notion integration and mention handler initialized")
                    
                    # 外部リマインダーシステムにNotion統合を設定
                    try:
                        from src.external_reminder_manager import external_reminder_manager
                        external_reminder_manager.notion = notion_integration
                        logger.info("External reminder system updated with Notion integration")
                    except Exception as e:
                        logger.warning(f"Failed to update external reminder system with Notion: {e}")
                else:
                    logger.info("MCP Bridge initialization skipped (no servers configured)")
                    notion_integration = None
                    mention_handler = DiscordMentionHandler(client)
            except Exception as e:
                logger.warning(f"MCP Bridge initialization failed (optional): {e}")
                notion_integration = None
                mention_handler = DiscordMentionHandler(client)
            
            _systems_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize systems in setup_hook: {e}")
    else:
        logger.info("Firebase not enabled, skipping system initialization")
        # Firebase不使用時も基本的なメンションハンドラーは初期化
        if mention_handler is None:
            mention_handler = DiscordMentionHandler(client)
        _systems_initialized = True
    
    logger.info("Setup hook completed")

# Handle TODO commands
async def handle_todo_command(user: discord.User, intent: Dict[str, Any]) -> str:
    """TODO操作を処理"""
    from src.todo_manager import todo_manager
    from personality_system import witch_personality
    
    action = intent.get('action')
    user_id = str(user.id)
    
    try:
        if action == 'create':
            # TODO作成
            todo = await todo_manager.create_todo(
                user_id=user_id,
                title=intent.get('title', 'タスク'),
                description='',
                due_date=intent.get('due_date'),
                priority=intent.get('priority', 'normal')
            )
            
            # 魔女風のレスポンス
            response = witch_personality.enhance_todo_response('create', {
                'title': todo['title'],
                'priority': todo.get('priority', 'normal')
            })
            
            if todo.get('due_date'):
                due_date_jst = todo['due_date'].astimezone(pytz.timezone('Asia/Tokyo'))
                response += f"\n📅 期限: {due_date_jst.strftime('%Y-%m-%d %H:%M')}"
                
            # 学習システムから適応的な返答を取得
            try:
                from learning_system import catherine_learning
                adaptive_response = await catherine_learning.generate_adaptive_response(
                    'todo_create', {'priority': todo.get('priority', 'normal')}
                )
                response += "\n\n" + adaptive_response
            except Exception as e:
                # フォールバック
                witch_create_tips = [
                    "「リスト」って言えば見せてあげるよ",
                    "よくできました、偉いねぇ",
                    "また一つ増えちゃったね",
                    "ちゃんと覚えておいたからね"
                ]
                import random
                response += "\n\n" + random.choice(witch_create_tips)
            
            # TODO作成後に自動でチーム全体のリストを表示
            todos = await todo_manager.get_todos(include_completed=False)
            if todos:
                response += "\n\n" + "─" * 30 + "\n"
                response += todo_manager.format_todo_list(todos)
            
        elif action == 'list':
            # TODOリスト表示（チーム全体）
            todos = await todo_manager.get_todos(
                include_completed=intent.get('include_completed', False)
            )
            
            # 魔女風の前置き
            intro = witch_personality.enhance_todo_response('list', {'count': len(todos)})
            response = intro + "\n\n" + todo_manager.format_todo_list(todos)
            
            if not intent.get('include_completed') and len(todos) > 0:
                # 学習システムから適応的な一言を取得
                try:
                    from learning_system import catherine_learning
                    adaptive_tip = await catherine_learning.generate_adaptive_response(
                        'todo_list', {'todo_count': len(todos)}
                    )
                    response += "\n" + adaptive_tip
                except Exception as e:
                    # フォールバック
                    witch_tips = [
                        "さあ、今日も頑張るんだよ",
                        "一つずつ片付けていきな",
                        "やることが山積みだねぇ",
                        "無理は禁物だからね"
                    ]
                    import random
                    response += "\n" + random.choice(witch_tips)
            
        elif action == 'complete':
            # TODO完了（チーム全体）
            todos = await todo_manager.get_todos()
            
            if intent.get('todo_number') and intent['todo_number'] <= len(todos):
                todo = todos[intent['todo_number'] - 1]
                success = await todo_manager.complete_todo(todo['id'], user_id)
                if success:
                    response = witch_personality.enhance_todo_response('complete', {'title': todo['title']})
                    
                    # 完了後に自動でリストを表示
                    remaining_todos = await todo_manager.get_todos(include_completed=False)
                    if remaining_todos:
                        response += "\n\n" + "─" * 30 + "\n"
                        response += todo_manager.format_todo_list(remaining_todos)
                    else:
                        response += "\n\nあらあら、全部完了したのかい？偉いねぇ"
                else:
                    response = "あらら、完了にできなかったみたいだねぇ..."
            else:
                response = "おや？その番号は見つからないよ。もう一度確認してごらん"
        
        elif action == 'delete':
            # TODO削除（複数削除対応）
            if intent.get('todo_numbers') and len(intent['todo_numbers']) > 1:
                # 複数削除
                result = await todo_manager.delete_todos_by_numbers(intent['todo_numbers'], user_id)
                if result['success']:
                    deleted_titles = ', '.join(result['deleted_titles'])
                    witch_multi_delete = [
                        f"ふむ、{result['deleted_count']}個も消すのかい？\n{deleted_titles}\n\nまあ、あんたの判断に任せるよ",
                        f"{result['deleted_count']}個まとめて片付けるのね\n{deleted_titles}\n\n一気にやるタイプかい",
                        f"あらあら、{result['deleted_count']}個も削除ね\n{deleted_titles}\n\n思い切りがいいじゃないか",
                        f"やれやれ、{result['deleted_count']}個も消すの？\n{deleted_titles}\n\n後悔しないようにね"
                    ]
                    import random
                    response = random.choice(witch_multi_delete)
                    if result.get('failed_numbers'):
                        response += f"\nでも番号 {result['failed_numbers']} は消せなかったよ"
                    
                    # 複数削除後に自動でリストを表示
                    remaining_todos = await todo_manager.get_todos(include_completed=False)
                    if remaining_todos:
                        response += "\n\n" + "─" * 30 + "\n"
                        response += todo_manager.format_todo_list(remaining_todos)
                    else:
                        response += "\n\nあらあら、全部なくなったじゃないか"
                else:
                    witch_delete_fail = [
                        "あらら、削除できなかったみたいだねぇ",
                        "やれやれ、うまくいかなかったよ",
                        "おや？何か間違えたようだね",
                        "困ったねぇ、消せなかったよ"
                    ]
                    import random
                    response = f"{random.choice(witch_delete_fail)}\\n{result.get('message', '')}"
            else:
                # 単一削除（従来の処理）
                todos = await todo_manager.get_todos(include_completed=True)
                
                if intent.get('todo_number') and intent['todo_number'] <= len(todos):
                    todo = todos[intent['todo_number'] - 1]
                    success = await todo_manager.delete_todo(todo['id'], user_id)
                    if success:
                        response = witch_personality.enhance_todo_response('delete', {'title': todo['title']})
                        
                        # 単一削除後に自動でリストを表示
                        remaining_todos = await todo_manager.get_todos(include_completed=False)
                        if remaining_todos:
                            response += "\n\n" + "─" * 30 + "\n"
                            response += todo_manager.format_todo_list(remaining_todos)
                        else:
                            response += "\n\nあらあら、全部なくなったじゃないか"
                    else:
                        response = "やれやれ、削除できなかったよ。困ったねぇ"
                else:
                    response = "その番号は見つからないねぇ。ちゃんと確認しな"
        
        elif action == 'priority':
            # 優先度変更
            if intent.get('todo_number') and intent.get('new_priority'):
                result = await todo_manager.update_todo_priority_by_number(
                    intent['todo_number'],
                    user_id,
                    intent['new_priority']
                )
                
                if result['success']:
                    priority_icons = {
                        'urgent': '⚫',
                        'high': '🔴',
                        'normal': '🟡',
                        'low': '🟢'
                    }
                    icon = priority_icons.get(intent['new_priority'], '')
                    response = f"ふむ、優先度を変えるのかい？\n{icon} {result['message']}\n\n📋 リストは自動的に優先度順に並び替えられるよ。激高が一番上にくるからね"
                    
                    # 優先度変更後に自動でリストを表示
                    todos = await todo_manager.get_todos(include_completed=False)
                    if todos:
                        response += "\n\n" + "─" * 30 + "\n"
                        response += todo_manager.format_todo_list(todos)
                else:
                    response = f"あらら、{result.get('message', '優先度を変更できなかったねぇ')}"
            else:
                response = "番号と新しい優先度を教えてごらん（例: 5は優先度激高に変えて）"
        
        elif action == 'update':
            # TODO名前変更
            if intent.get('todo_number') and intent.get('new_content'):
                result = await todo_manager.update_todo_by_number(
                    intent['todo_number'], 
                    user_id, 
                    intent['new_content']
                )
                if result['success']:
                    witch_rename = [
                        f"TODO {intent['todo_number']} の名前を変更したよ\n「{result['old_title']}」→「{result['new_title']}」\n\n気が変わりやすいねぇ",
                        f"名前変更完了だよ\n「{result['old_title']}」→「{result['new_title']}」\n\nまあ、分かりやすい方がいいからね",
                        f"タイトルを変えたね\n「{result['old_title']}」→「{result['new_title']}」\n\n新しい名前の方がマシかい？",
                        f"リネーム完了さ\n「{result['old_title']}」→「{result['new_title']}」\n\nころころ変えるもんじゃないよ？"
                    ]
                    import random
                    response = random.choice(witch_rename)
                    
                    # タイトル変更後に自動でリストを表示
                    todos = await todo_manager.get_todos(include_completed=False)
                    if todos:
                        response += "\n\n" + "─" * 30 + "\n"
                        response += todo_manager.format_todo_list(todos)
                else:
                    witch_update_fail = [
                        "あらら、名前変更に失敗したねぇ",
                        "やれやれ、うまくいかなかったよ",
                        "困ったね、変更できなかったみたい",
                        "おや、何かがおかしいようだね"
                    ]
                    import random
                    response = f"{random.choice(witch_update_fail)}\\n{result.get('message', 'TODOの更新に失敗しました')}"
            else:
                witch_update_help = [
                    "番号と新しい名前を教えてごらん（例: 1は買い物リストにして）",
                    "どの番号の何を変えたいのか言いな",
                    "番号と新しい名前、両方必要だよ",
                    "何番のタイトルをどう変えるのかい？"
                ]
                import random
                response = random.choice(witch_update_help)
        
        elif action == 'remind':
            # リマインダー設定
            logger.info(f"Remind intent: {intent}")  # デバッグログ
            
            # カスタムメッセージリマインダーの場合
            if intent.get('custom_message') and not intent.get('todo_number') and not intent.get('is_list_reminder'):
                remind_time = intent.get('remind_time')
                if remind_time:
                    from scheduler_system import scheduler_system
                    if scheduler_system:
                        todo_data = {
                            'user_id': user_id,
                            'custom_message': intent['custom_message'],
                            'channel_target': intent.get('channel_target', 'todo'),
                            'mention_target': intent.get('mention_target', 'everyone'),
                            'is_list_reminder': False
                        }
                        
                        task_id = await scheduler_system.schedule_reminder(
                            remind_time, 
                            todo_data, 
                            is_recurring=False
                        )
                        
                        # JSTで表示
                        time_jst = remind_time.astimezone(pytz.timezone('Asia/Tokyo'))
                        time_str = time_jst.strftime('%Y-%m-%d %H:%M JST')
                        mention_str = f'@{intent.get("mention_target", "everyone")}'
                        channel_str = f'#{intent.get("channel_target", "todo")}チャンネル'
                        
                        response = f"🔔 カスタムメッセージ「{intent['custom_message']}」のリマインダーを{time_str}に{channel_str}で{mention_str}宛に設定しました"
                    else:
                        response = "❌ スケジューラーシステムが利用できません"
                else:
                    response = "❌ リマインダー時間を指定してください"
                    
            elif intent.get('is_list_reminder'):
                # 全リスト通知の設定
                remind_time = intent.get('remind_time')
                remind_type = intent.get('remind_type', 'custom')
                logger.info(f"Setting list reminder at {remind_time}, type: {remind_type}")  # デバッグログ
                
                if remind_time:
                    # スケジューラーに登録
                    from scheduler_system import scheduler_system
                    if scheduler_system:
                        todo_data = {
                            'user_id': user_id,
                            'title': 'TODOリスト全体',
                            'channel_target': intent.get('channel_target', 'todo'),
                            'mention_target': intent.get('mention_target', 'everyone'),
                            'is_list_reminder': True
                        }
                        
                        task_id = await scheduler_system.schedule_reminder(
                            remind_time, 
                            todo_data, 
                            is_recurring=(remind_type == 'recurring')
                        )
                        
                        # JSTで表示
                        time_jst = remind_time.astimezone(pytz.timezone('Asia/Tokyo'))
                        time_str = time_jst.strftime('%Y-%m-%d %H:%M JST')
                        mention_str = f'@{intent.get("mention_target", "everyone")}'
                        channel_str = f'#{intent.get("channel_target", "todo")}チャンネル'
                        recurring_str = '（毎日繰り返し）' if remind_type == 'recurring' else ''
                        
                        response = f"🔔 TODOリスト全体のリマインダーを{time_str}に{channel_str}で{mention_str}宛に設定しました{recurring_str}"
                    else:
                        response = "❌ スケジューラーシステムが利用できません"
                else:
                    response = "❌ リマインダー時間を指定してください"
                    
            elif intent.get('todo_number'):
                result = await todo_manager.set_reminder_by_number(
                    intent['todo_number'],
                    user_id,
                    intent.get('remind_time'),
                    intent.get('remind_type', 'custom'),
                    intent.get('mention_target', 'everyone'),
                    intent.get('channel_target', 'todo')
                )
                
                if result['success']:
                    response = f"🔔 {result['message']}"
                    
                    # 即座にリマインダーの場合、チャンネルにメンション付きで送信
                    if result.get('immediate'):
                        try:
                            # チャンネルを取得
                            channel_name = result.get('channel_target', 'todo')
                            channel = None
                            
                            # チャンネルを検索
                            for guild in client.guilds:
                                for ch in guild.channels:
                                    if ch.name.lower() == channel_name.lower() and hasattr(ch, 'send'):
                                        channel = ch
                                        break
                                if channel:
                                    break
                            
                            if channel:
                                # 新しいメンションハンドラーを使用
                                mention_target = result.get('mention_target', 'everyone')
                                if mention_handler:
                                    mention_data = mention_handler.parse_mention_text(mention_target, channel.guild)
                                    mention = mention_data.get('mention_string', '@everyone')
                                    logger.info(f"[main.py] Parsed mention: {mention} for target: {mention_target}")
                                else:
                                    # フォールバック
                                    mention = get_mention_string(mention_target, channel.guild, client)
                                
                                # リマインダーメッセージを送信
                                witch_urgent = [
                                    "ほら、今すぐやらないとマズいよ！",
                                    "急ぎの用事だから、すぐに取り掛かりな",
                                    "さあさあ、今すぐ始めるんだよ",
                                    "待ったなしだね、頑張りな",
                                    "のんびりしてる場合じゃないよ",
                                    "急いで、急いで！",
                                    "今すぐ片付けちゃいな"
                                ]
                                import random
                                urgent_comment = random.choice(witch_urgent)
                                await channel.send(f"{mention}\n{result.get('todo_title', 'TODO')}\n{urgent_comment}")
                            else:
                                logger.error(f"Channel '{channel_name}' not found")
                                
                        except Exception as e:
                            logger.error(f"Failed to send channel reminder: {e}")
                    elif result.get('remind_time'):
                        # スケジュールされたリマインダーの場合もスケジューラーに登録
                        from scheduler_system import scheduler_system
                        logger.info(f"Scheduling reminder: {result}")
                        if scheduler_system:
                            todo_data = {
                                'user_id': user_id,
                                'title': result.get('todo_title', 'TODO'),
                                'channel_target': result.get('channel_target', 'todo'),
                                'mention_target': result.get('mention_target', 'everyone'),
                                'is_list_reminder': False,
                                'custom_message': result.get('custom_message')
                            }
                            
                            task_id = await scheduler_system.schedule_reminder(
                                result['remind_time'], 
                                todo_data, 
                                is_recurring=False
                            )
                            logger.info(f"Scheduled reminder task: {task_id}")
                        else:
                            logger.error("Scheduler system not available for individual reminder")
                else:
                    response = f"❌ {result.get('message', 'リマインダーの設定に失敗しました')}"
            else:
                response = "❌ 番号を指定してください（例: 1を明日リマインド）"
        
        else:
            witch_help_messages = [
                "ふむ、何を言ってるのかわからないねぇ...\n\n「〇〇を追加」「リスト」「1番削除」「5は優先度激高に」\nこんな風に言ってごらん。覚えが悪いねぇ",
                "あらあら、理解できないよ...\n\n「タスクを追加」「一覧見せて」「優先度変更」\nもう少し分かりやすく言いな",
                "やれやれ、何のことだい？\n\n「TODO追加」「削除」「リマインド設定」\n基本的な使い方を覚えておくれよ",
                "おや、意味がわからないねぇ...\n\nシンプルに「追加」「削除」「リスト」って言えばいいのに\nまったく、困った子だね"
            ]
            import random
            response = random.choice(witch_help_messages)
            
    except Exception as e:
        logger.error(f"TODO operation error: {e}")
        response = f"あらら、何かおかしなことが起きちゃったよ: {str(e)[:50]}...\nやれやれ、困ったねぇ"
    
    return response


# Firebase conversation logging
async def save_conversation_to_firebase(user_id: str, channel_id: str, message: str, response: str):
    """Save conversation to Firebase"""
    if not FIREBASE_ENABLED:
        return
    
    try:
        from datetime import datetime
        import pytz
        
        db = firebase_manager.get_db()
        conversation_data = {
            'user_id': user_id,
            'channel_id': channel_id,
            'user_message': message,
            'bot_response': response,
            'timestamp': datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC).isoformat(),
            'message_type': 'chat_completion'
        }
        
        # Save to Firebase
        db.collection('conversations').add(conversation_data)
        logging.info(f"Conversation saved to Firebase for user {user_id}")
        
    except Exception as e:
        logging.error(f"Failed to save conversation to Firebase: {e}")


@client.event
async def on_ready():
    logger.info(f"[BOT-{BOT_INSTANCE_ID}] We have logged in as {client.user}. Invite URL: {BOT_INVITE_URL}")
    completion.MY_BOT_NAME = client.user.name
    completion.MY_BOT_EXAMPLE_CONVOS = []
    for c in EXAMPLE_CONVOS:
        messages = []
        for m in c.messages:
            if m.user == "Lenard":
                messages.append(Message(user=client.user.name, text=m.text))
            else:
                messages.append(m)
        completion.MY_BOT_EXAMPLE_CONVOS.append(Conversation(messages=messages))
    
    # Sync slash commands globally
    try:
        logger.info("Starting command sync...")
        synced = await tree.sync()
        logger.info(f"Successfully synced {len(synced)} command(s) globally")
        
        # Also sync to specific guilds if needed
        from src.constants import ALLOWED_SERVER_IDS
        for guild_id in ALLOWED_SERVER_IDS:
            try:
                guild = discord.Object(id=guild_id)
                guild_commands = await tree.sync(guild=guild)
                logger.info(f"Synced {len(guild_commands)} command(s) to guild {guild_id}")
            except Exception as guild_error:
                logger.error(f"Failed to sync commands to guild {guild_id}: {guild_error}")
                
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


# /chat message:
@tree.command(name="chat", description="Create a new thread for conversation")
@app_commands.describe(message="The first prompt to start the chat with")
@app_commands.describe(model="The model to use for the chat")
@app_commands.describe(
    temperature="Controls randomness. Higher values mean more randomness. Between 0 and 1 (default 0.7)"
)
@app_commands.describe(
    max_tokens="How many tokens the model should output at max for each message."
)
async def chat_command(
    interaction: discord.Interaction,
    message: str,
    model: AVAILABLE_MODELS = DEFAULT_MODEL,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 512,
):
    logger.info(f"Chat command triggered by {interaction.user.name} in guild {interaction.guild_id}")
    
    # Immediately defer to avoid timeout
    await interaction.response.defer(ephemeral=False)
    
    try:
        # only support creating thread in text channel
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.followup.send("This command can only be used in text channels.", ephemeral=True)
            return

        # block servers not in allow list
        if should_block(guild=interaction.guild):
            await interaction.followup.send("This server is not authorized to use this bot.", ephemeral=True)
            return

        user = interaction.user
        logger.info(f"Chat command by {user} {message[:20]}")

        # Check for valid temperature
        if temperature is not None and (temperature < 0 or temperature > 1):
            await interaction.followup.send(
                f"You supplied an invalid temperature: {temperature}. Temperature must be between 0 and 1.",
                ephemeral=True,
            )
            return

        # Check for valid max_tokens
        if max_tokens is not None and (max_tokens < 1 or max_tokens > 4096):
            await interaction.followup.send(
                f"You supplied an invalid max_tokens: {max_tokens}. Max tokens must be between 1 and 4096.",
                ephemeral=True,
            )
            return

        try:
            # moderate the message
            flagged_str, blocked_str = moderate_message(message=message, user=user)
            await send_moderation_blocked_message(
                guild=interaction.guild,
                user=user,
                blocked_str=blocked_str,
                message=message,
            )
            if len(blocked_str) > 0:
                # message was blocked
                await interaction.followup.send(
                    f"Your prompt has been blocked by moderation.\n{message}",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                description=f"<@{user.id}> wants to chat! 🤖💬",
                color=discord.Color.green(),
            )
            embed.add_field(name="model", value=model)
            embed.add_field(name="temperature", value=temperature, inline=True)
            embed.add_field(name="max_tokens", value=max_tokens, inline=True)
            embed.add_field(name=user.name, value=message)

            if len(flagged_str) > 0:
                # message was flagged
                embed.color = discord.Color.yellow()
                embed.title = "⚠️ This prompt was flagged by moderation."

            response = await interaction.followup.send(embed=embed, wait=True)

            await send_moderation_flagged_message(
                guild=interaction.guild,
                user=user,
                flagged_str=flagged_str,
                message=message,
                url=response.jump_url,
            )
        except Exception as e:
            logger.exception(e)
            await interaction.followup.send(
                f"Failed to start chat {str(e)}", ephemeral=True
            )
            return

        # create the thread from the channel instead of the response
        thread = await interaction.channel.create_thread(
            name=f"{ACTIVATE_THREAD_PREFX} {user.name[:20]} - {message[:30]}",
            message=response,
            slowmode_delay=1,
            reason="gpt-bot",
            auto_archive_duration=60,
        )
        thread_data[thread.id] = ThreadConfig(
            model=model, max_tokens=max_tokens, temperature=temperature
        )
        async with thread.typing():
            # fetch completion
            messages = [Message(user=user.name, text=message)]
            response_data = await generate_completion_response(
                messages=messages, user=user, thread_config=thread_data[thread.id]
            )
            # send the result
            await process_response(
                user=user, thread=thread, response_data=response_data
            )
    except Exception as e:
        logger.exception(e)
        await interaction.followup.send(
            f"Failed to start chat: {str(e)}", ephemeral=True
        )


# calls for each message
@client.event
async def on_message(message: DiscordMessage):
    try:
        # ignore messages from the bot
        if message.author == client.user:
            return
        
        # block servers not in allow list
        if should_block(guild=message.guild):
            return
        
        # チャンネル制限チェック - Catherineが応答すべきかどうか
        if not should_respond_to_message(message, client.user.id):
            channel_info = get_channel_info(message, client.user.id)
            logger.info(f"Message ignored - not responding in channel '{channel_info.get('channel_name', 'unknown')}' (Catherine channels only or mention required)")
            return
        
        # Handle all messages (DM or channel)
        user = message.author
        content = message.content
        
        # 統合メッセージハンドラーの使用
        try:
            from src.unified_message_handler import unified_handler
            
            async with message.channel.typing():
                response = await unified_handler.handle_message(message)
            
            if response:
                await message.reply(response)
                
                # 会話をFirebaseに保存
                if _systems_initialized and FIREBASE_ENABLED:
                    await save_conversation_to_firebase(str(user.id), str(message.channel.id), content, response)
                
                logger.info("Message processed successfully by unified handler")
                return
            else:
                logger.warning("No response generated by unified handler")
        
        except Exception as e:
            logger.error(f"Error in unified handler: {e}")
            # フォールバック: シンプルな返答
            await message.reply("あらあら、ちょっと調子が悪いみたいだね。もう一度試してもらえるかい？")
            return

    except Exception as e:
        logger.error(f"Critical error in message handler: {e}")
        await message.reply("ごめんなさい、何か問題が起きたようです。")

# End of on_message handler

# Google Workspace統合用のヘルパー関数

def format_google_response(result: dict, action: str) -> str:
    """Google Workspace操作結果を魔女風の返答に変換"""
    if result.get('success'):
        if action == 'gmail_check':
            count = result.get('count', 0)
            emails = result.get('emails', [])
            if count > 0:
                response = f"ふふ、メールが{count}通あるよ\n\n"
                for i, email in enumerate(emails[:3], 1):
                    response += f"{i}. **{email['subject']}**\n   From: {email['from']}\n   {email['snippet']}\n\n"
                if count > 3:
                    response += f"...他{count-3}通あるよ"
                return response
            else:
                return "あら、新しいメールはないようだね"
                
        elif action == 'tasks_create':
            return f"ふふ、Googleタスク「{result.get('title', '')}」を作成したよ"
            
        elif action == 'docs_create':
            return f"あらあら、Googleドキュメント「{result.get('title', '')}」を作成したよ\n🔗 [ドキュメントを開く]({result.get('url', '#')})"
            
        elif action == 'sheets_create':
            return f"やれやれ、スプレッドシート「{result.get('title', '')}」を作成したよ\n📊 [シートを開く]({result.get('url', '#')})"
            
        elif action == 'calendar_create_event':
            return f"まったく、カレンダーイベント「{result.get('title', '')}」を追加したよ\n📅 予定を忘れないようにね"
            
        else:
            return result.get('message', 'うまくいったようだね')
    else:
        error = result.get('error', '不明なエラー')
        return f"あらあら、うまくいかなかったようだね: {error}"

# システム初期化はsetup_hookで実行される

logger.info(f"[BOT-{BOT_INSTANCE_ID}] Starting Discord bot...")
client.run(DISCORD_BOT_TOKEN)
