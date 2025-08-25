"""
シンプルなBot - 基本機能のみ
"""

import discord
from discord import Message as DiscordMessage
import logging
import os
import sys
from datetime import datetime
import pytz

# 設定
logging.basicConfig(
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# プロジェクトパス追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.constants import DISCORD_BOT_TOKEN, ALLOWED_SERVER_IDS
from src.simple_google_service import google_service
from src.channel_utils import should_respond_to_message, get_channel_info

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# グローバル変数
google_initialized = False

@client.event
async def on_ready():
    """Bot起動時"""
    global google_initialized
    
    logger.info(f"✅ Bot logged in as {client.user}")
    
    # Google Service初期化
    try:
        google_initialized = google_service.initialize()
        if google_initialized:
            logger.info("✅ Google Services ready")
        else:
            logger.warning("⚠️ Google Services not available")
    except Exception as e:
        logger.error(f"Google initialization error: {e}")
    
    logger.info("🚀 Bot ready to respond!")

@client.event
async def on_message(message: DiscordMessage):
    """メッセージ処理"""
    try:
        # 自分のメッセージは無視
        if message.author == client.user:
            return
        
        # サーバー制限チェック
        if message.guild and message.guild.id not in ALLOWED_SERVER_IDS:
            return
        
        # チャンネル制限チェック
        if not should_respond_to_message(message, client.user.id):
            return
        
        # メッセージ処理
        user = message.author
        content = message.content.lower().strip()
        
        logger.info(f"Processing message from {user}: {content}")
        
        response = None
        
        # 基本的なコマンド処理
        if any(word in content for word in ['リスト', '一覧', '全', 'list', 'タスク', 'やること']):
            response = await handle_task_list()
        
        elif any(word in content for word in ['メール', 'mail', 'gmail', 'email']):
            response = await handle_email_check()
        
        elif content in ['よう', 'hello', 'hi', 'こんにちは', 'おはよう']:
            response = "よう！何か手伝おうか？\n\n使い方:\n- 「リスト」→ タスク一覧\n- 「メール」→ メール確認"
        
        elif '追加' in content and 'タスク' in content:
            # タスク追加処理
            task_text = content.replace('タスク', '').replace('追加', '').replace('を', '').strip()
            if task_text:
                response = await handle_task_create(task_text)
            else:
                response = "タスクの内容を教えて！（例：「会議準備をタスクに追加」）"
        
        else:
            response = "何か手伝おうか？\n\n・「リスト」でタスク一覧\n・「メール」でメール確認\n・「○○をタスクに追加」でタスク作成"
        
        # 応答送信
        if response:
            await message.reply(response)
            logger.info(f"Responded to {user}")
        
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await message.reply("あらら、何かおかしなことが起きちゃったよ")

async def handle_task_list():
    """タスク一覧表示"""
    try:
        if not google_initialized:
            return "⚠️ Google Tasksに接続できません"
        
        tasks = google_service.get_tasks()
        
        if not tasks:
            return "📋 現在のタスクはありません"
        
        response = "📋 **現在のタスク一覧**\n\n"
        for i, task in enumerate(tasks, 1):
            response += f"{i}. **{task['title']}**\n"
            if task['notes']:
                response += f"   {task['notes']}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Task list error: {e}")
        return "タスク一覧の取得に失敗しました"

async def handle_email_check():
    """メール確認"""
    try:
        if not google_initialized:
            return "⚠️ Gmailに接続できません"
        
        emails = google_service.get_unread_emails()
        
        if not emails:
            return "📧 未読メールはありません"
        
        response = f"📧 **未読メール ({len(emails)}件)**\n\n"
        for i, email in enumerate(emails, 1):
            response += f"{i}. **{email['subject']}**\n"
            response += f"   From: {email['from']}\n"
            response += f"   {email['snippet'][:100]}...\n\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Email check error: {e}")
        return "メールチェックに失敗しました"

async def handle_task_create(task_text):
    """タスク作成"""
    try:
        if not google_initialized:
            return "⚠️ Google Tasksに接続できません"
        
        success = google_service.create_task(task_text)
        
        if success:
            return f"✅ タスクを作成しました：「{task_text}」"
        else:
            return "❌ タスク作成に失敗しました"
        
    except Exception as e:
        logger.error(f"Task create error: {e}")
        return "タスク作成に失敗しました"

if __name__ == "__main__":
    logger.info("🚀 Starting simple Catherine bot...")
    client.run(DISCORD_BOT_TOKEN)