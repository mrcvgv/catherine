#!/usr/bin/env python3
"""
Catherine AI - Integrated Version
Combines best features from multiple Discord bots with Firebase TODO management
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import pytz
from aiohttp import web
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

# ========== Configuration ==========
class Config:
    """Centralized configuration management"""
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Model configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Bot settings
    BOT_PREFIX = os.getenv("BOT_PREFIX", "C! ")
    MAX_CONVERSATION_LENGTH = int(os.getenv("MAX_CONVERSATION_LENGTH", "20"))
    
    # System prompt
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """
    You are Catherine AI, a helpful and friendly Discord assistant.
    You can help with tasks, have conversations, and manage TODO lists.
    You speak naturally in both English and Japanese.
    """).strip()

# ========== Logging Setup ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Provider System ==========
class ProviderType(Enum):
    """Available AI providers"""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    FREE = "free"

@dataclass
class ModelInfo:
    """Information about an AI model"""
    name: str
    provider: ProviderType
    description: str = ""
    supports_vision: bool = False
    max_tokens: int = 4096

class AIProvider:
    """Base AI provider interface"""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize the provider's client"""
        pass
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a chat completion"""
        raise NotImplementedError

class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""
    def initialize_client(self):
        if self.api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI provider initialized")
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.client:
            return "OpenAI API key not configured"
        
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', Config.DEFAULT_MODEL),
                messages=messages,
                max_tokens=kwargs.get('max_tokens', Config.MAX_TOKENS),
                temperature=kwargs.get('temperature', Config.TEMPERATURE),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error: {str(e)}"

# ========== Conversation Management ==========
@dataclass
class ConversationSession:
    """Manages a user's conversation session"""
    user_id: str
    channel_id: str
    messages: List[Dict[str, str]]
    created_at: datetime
    last_activity: datetime
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.messages.append({"role": role, "content": content})
        self.last_activity = datetime.now(pytz.UTC)
        
        # Trim conversation if too long
        if len(self.messages) > Config.MAX_CONVERSATION_LENGTH:
            # Keep system message and recent messages
            system_msgs = [m for m in self.messages if m["role"] == "system"]
            recent_msgs = self.messages[-(Config.MAX_CONVERSATION_LENGTH - len(system_msgs)):]
            self.messages = system_msgs + recent_msgs

class ConversationManager:
    """Manages all conversation sessions"""
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.provider = OpenAIProvider(Config.OPENAI_API_KEY)
    
    def get_or_create_session(self, user_id: str, channel_id: str) -> ConversationSession:
        """Get existing session or create new one"""
        session_key = f"{user_id}_{channel_id}"
        
        if session_key not in self.sessions:
            now = datetime.now(pytz.UTC)
            self.sessions[session_key] = ConversationSession(
                user_id=user_id,
                channel_id=channel_id,
                messages=[{"role": "system", "content": Config.SYSTEM_PROMPT}],
                created_at=now,
                last_activity=now
            )
        
        return self.sessions[session_key]
    
    async def get_response(self, user_id: str, channel_id: str, message: str) -> str:
        """Get AI response for a message"""
        session = self.get_or_create_session(user_id, channel_id)
        session.add_message("user", message)
        
        response = await self.provider.chat_completion(session.messages)
        session.add_message("assistant", response)
        
        return response
    
    def clear_session(self, user_id: str, channel_id: str):
        """Clear a conversation session"""
        session_key = f"{user_id}_{channel_id}"
        if session_key in self.sessions:
            del self.sessions[session_key]

# ========== Firebase Integration ==========
try:
    from firebase_config import firebase_manager
    from team_todo_manager import TeamTodoManager
    from openai import OpenAI
    
    # Initialize with sync client for compatibility
    sync_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    team_todo_manager = TeamTodoManager(sync_client)
    logger.info("Firebase TODO system loaded")
except Exception as e:
    logger.warning(f"Firebase TODO system unavailable: {e}")
    team_todo_manager = None

# ========== Intent Detection ==========
def extract_edit_content(text: str) -> str:
    """Extract new content from edit commands"""
    import re
    patterns = [
        r'(\d+)の内容は[、，]?(.+?)です?[。、]?変更',
        r'(\d+)を[「"](.*?)[」"]に変更',
        r'(\d+)[を]?(.+?)に[直す|修正|更新|編集|変更]',
        r'(\d+)[変更|編集|修正|更新][、，]?(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match and len(match.groups()) >= 2:
            content = match.group(2).strip()
            content = re.sub(r'[。、，\s]+$', '', content)
            if content:
                return content
    return ""

def detect_todo_intent(text: str):
    """Enhanced intent detection with number parsing"""
    text_lower = text.lower()
    import re
    
    # Number extraction
    numbers = []
    number_patterns = [
        r'(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.?',
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',
        r'(\d+)[,、\s](\d+)[,、\s](\d+)[,、\s](\d+)',
        r'(\d+)[,、\s](\d+)[,、\s](\d+)',
        r'(\d+)[,、\s](\d+)',
        r'(\d+)番?',
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        if matches:
            if isinstance(matches[0], tuple):
                numbers.extend([int(n) for n in matches[0] if n])
            else:
                numbers.extend([int(n) for n in matches if n])
            break
    
    # Bulk delete check
    is_bulk_delete = any(keyword in text_lower for keyword in [
        'ぜんぶ削除', '全部削除', '全て削除', 'すべて削除',
        'ぜんぶ消し', '全部消し', 'すべて消し',
        'ぜんぶ消して', '全部消して', 'すべて消して'
    ])
    
    # Intent checks
    is_todo_delete = (any(keyword in text_lower for keyword in [
        '消して', '削除', '取り消し', 'けして', '消せ', 'remove', 'delete'
    ]) and numbers) or is_bulk_delete
    
    is_todo_done = any(keyword in text_lower for keyword in [
        'done', '完了', '終わった', 'できた', '済み'
    ]) and numbers
    
    is_todo_edit = any(keyword in text_lower for keyword in [
        '変更', '編集', '修正', '更新', '直す', 'edit', 'change', 'update'
    ]) and numbers
    
    is_todo_list = any(keyword in text_lower for keyword in [
        'リスト出', 'リスト表示', 'リスト見せ', 'リストだして', 'リスト教', 'リストだし',
        'タスク一覧', 'todo一覧', 'やること見せ', 'タスク出し', 'list',
        '一覧出し', '一覧表示', '確認', '見せて', 'だして', 'リストして'
    ]) and not is_todo_delete
    
    is_todo_add = (any(keyword in text_lower for keyword in [
        '追加', '登録', '入れて', '作って', 'つくって', '新しく', 'いれて',
        'todoいれ', 'todo追加', 'todo登録'
    ]) or 'todo' in text_lower) and not is_todo_list and not is_todo_delete and not is_todo_done and not is_todo_edit
    
    is_todo_command = is_todo_list or is_todo_add or is_todo_done or is_todo_delete or is_todo_edit or any(
        keyword in text_lower for keyword in ['todo', 'タスク', 'やること']
    )
    
    return is_todo_command, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete

# ========== Discord Bot ==========
class CatherineBot(commands.Bot):
    """Enhanced Catherine Discord Bot"""
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.conversation_manager = ConversationManager()
        self.jst = pytz.timezone('Asia/Tokyo')
    
    async def setup_hook(self):
        """Setup bot hooks"""
        # Sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced")
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'{self.user} is ready!')
        logger.info(f'Connected to {len(self.guilds)} guilds')

# Create bot instance
bot = CatherineBot()

# ========== Health Check Server ==========
async def health_check(request):
    """Railway health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Catherine AI Integrated',
        'version': '2.0'
    })

async def init_health_server():
    """Initialize health check server"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Health server started on port {port}")
    return runner

# ========== Slash Commands ==========
@bot.tree.command(name="chat", description="Start a conversation with Catherine AI")
@app_commands.describe(message="Your message to Catherine")
async def chat_command(interaction: discord.Interaction, message: str):
    """Chat with AI using slash command"""
    await interaction.response.defer()
    
    try:
        response = await bot.conversation_manager.get_response(
            str(interaction.user.id),
            str(interaction.channel_id),
            message
        )
        
        # Split response if too long
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.channel.send(chunk)
        else:
            await interaction.followup.send(response)
    
    except Exception as e:
        logger.error(f"Chat command error: {e}")
        await interaction.followup.send("申し訳ありません、エラーが発生しました。")

@bot.tree.command(name="clear", description="Clear conversation history")
async def clear_command(interaction: discord.Interaction):
    """Clear conversation history"""
    bot.conversation_manager.clear_session(
        str(interaction.user.id),
        str(interaction.channel_id)
    )
    await interaction.response.send_message("✨ 会話履歴をクリアしました。")

@bot.tree.command(name="todo", description="Manage TODO list")
@app_commands.describe(action="Action to perform (list/add/delete/complete)")
@app_commands.describe(content="Content for the action")
async def todo_command(interaction: discord.Interaction, action: str, content: Optional[str] = None):
    """TODO management slash command"""
    await interaction.response.defer()
    
    if not team_todo_manager:
        await interaction.followup.send("❌ TODO機能が利用できません")
        return
    
    try:
        if action == "list":
            todos = await team_todo_manager.get_team_todos()
            if not todos:
                await interaction.followup.send("📝 TODOはありません")
            else:
                response = "📊 **TODOリスト**\n\n"
                for i, todo in enumerate(todos[:30], 1):
                    title = todo['title'][:50].replace('\n', ' ').strip()
                    response += f"{i}. **{title}**\n"
                await interaction.followup.send(response)
        
        elif action == "add" and content:
            result = await team_todo_manager.create_team_todo(
                creator_id=str(interaction.user.id),
                title=content,
                description="",
                priority=3
            )
            if result:
                await interaction.followup.send(f"📝 TODO追加: {content}")
            else:
                await interaction.followup.send("❌ TODO追加に失敗しました")
        
        else:
            await interaction.followup.send("使い方: `/todo list` または `/todo add [内容]`")
    
    except Exception as e:
        logger.error(f"TODO command error: {e}")
        await interaction.followup.send("❌ エラーが発生しました")

# ========== Message Handler ==========
@bot.event
async def on_message(message):
    """Handle incoming messages"""
    if message.author == bot.user:
        return
    
    # Process commands first
    if message.content.startswith(Config.BOT_PREFIX):
        await bot.process_commands(message)
        return
    
    # Check if bot is mentioned or in DM
    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    
    if not (is_mentioned or is_dm):
        # Check for TODO commands even without mention
        command_text = message.content.strip()
        is_todo_command, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete = detect_todo_intent(command_text)
        
        if is_todo_command and team_todo_manager:
            await handle_todo_command(message, command_text, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete)
        return
    
    # Remove mention from message
    content = message.content.replace(f'<@{bot.user.id}>', '').strip()
    
    # Check for TODO intent first
    is_todo_command, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete = detect_todo_intent(content)
    
    if is_todo_command and team_todo_manager:
        await handle_todo_command(message, content, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete)
    else:
        # Regular conversation
        async with message.channel.typing():
            response = await bot.conversation_manager.get_response(
                str(message.author.id),
                str(message.channel.id),
                content
            )
            
            # Split response if too long
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)

async def handle_todo_command(message, command_text, is_todo_list, is_todo_add, is_todo_done, is_todo_delete, is_todo_edit, numbers, is_bulk_delete):
    """Handle TODO-related commands"""
    try:
        if is_todo_list:
            todos = await team_todo_manager.get_team_todos()
            if not todos:
                await message.channel.send("📝 TODOはありません")
            else:
                response = "📊 **TODOリスト**\n\n"
                for i, todo in enumerate(todos[:30], 1):
                    title = todo['title'][:50].replace('\n', ' ').strip()
                    response += f"{i}. **{title}**\n"
                await message.channel.send(response)
        
        elif is_todo_delete:
            if is_bulk_delete:
                deleted_count = await team_todo_manager.clear_all_todos()
                if deleted_count > 0:
                    await message.channel.send(f"🗑️ **全削除完了:** {deleted_count}個のTODOを削除しました")
                else:
                    await message.channel.send("📝 削除するTODOがありませんでした")
            elif numbers:
                todos = await team_todo_manager.get_team_todos()
                deleted_items = []
                for num in sorted(numbers, reverse=True):
                    if 1 <= num <= len(todos):
                        todo = todos[num-1]
                        todo_id = todo.get('id')
                        if todo_id:
                            success = await team_todo_manager.delete_todo_permanently(todo_id)
                            if success:
                                deleted_items.append(f"{num}. {todo['title'][:30]}")
                
                if deleted_items:
                    await message.channel.send(f"🗑️ **削除完了:**\n" + "\n".join(deleted_items))
                else:
                    await message.channel.send("❌ 削除できませんでした")
        
        elif is_todo_edit and numbers:
            new_content = extract_edit_content(command_text)
            if new_content:
                todos = await team_todo_manager.get_team_todos()
                edited_items = []
                for num in numbers:
                    if 1 <= num <= len(todos):
                        todo = todos[num-1]
                        todo_id = todo.get('id')
                        if todo_id:
                            success = await team_todo_manager.update_todo_title(todo_id, new_content)
                            if success:
                                edited_items.append(f"{num}. {todo['title'][:20]} → {new_content[:20]}")
                
                if edited_items:
                    await message.channel.send(f"✏️ **編集完了:**\n" + "\n".join(edited_items))
                else:
                    await message.channel.send("❌ 編集できませんでした")
            else:
                await message.channel.send("❌ 編集内容が見つかりません")
        
        elif is_todo_done and numbers:
            todos = await team_todo_manager.get_team_todos()
            completed_items = []
            for num in numbers:
                if 1 <= num <= len(todos):
                    todo = todos[num-1]
                    todo_id = todo.get('id')
                    if todo_id:
                        success = await team_todo_manager.update_todo_status(todo_id, 'completed')
                        if success:
                            completed_items.append(f"{num}. {todo['title'][:30]}")
            
            if completed_items:
                await message.channel.send(f"✅ **完了:**\n" + "\n".join(completed_items))
            else:
                await message.channel.send("❌ 完了できませんでした")
        
        elif is_todo_add:
            # Clean up TODO keywords
            clean_content = command_text
            remove_patterns = ['todoいれて', 'todo追加', 'todo登録', '追加して', '登録して', '入れて', 'いれて']
            for pattern in remove_patterns:
                clean_content = clean_content.replace(pattern, '').strip()
            
            if clean_content:
                # Parse multi-line TODOs
                lines = []
                for line in clean_content.split('\n'):
                    line = line.strip()
                    if line and line.startswith('・'):
                        items = [item.strip() for item in line.split('・') if item.strip()]
                        lines.extend(items)
                    elif line:
                        lines.append(line)
                
                added_items = []
                for line in lines:
                    if line:
                        result = await team_todo_manager.create_team_todo(
                            creator_id=str(message.author.id),
                            title=line,
                            description="",
                            priority=3
                        )
                        if result:
                            added_items.append(line[:30])
                
                if added_items:
                    await message.channel.send(f"📝 **TODO追加完了:**\n" + "\n".join([f"• {item}" for item in added_items]))
                else:
                    await message.channel.send("❌ TODO追加に失敗しました")
            else:
                await message.channel.send("📋 TODOの内容を教えてください")
        
        else:
            # Ambiguous TODO command
            await message.channel.send(
                f"**{command_text}** について、何をしますか？\n\n"
                "📝 ①追加する\n📋 ②一覧を見る\n✅ ③完了する\n🗑️ ④削除する\n✏️ ⑤編集する\n\n"
                "番号か、「追加」「リスト」「完了」「削除」「編集」で教えてください。"
            )
    
    except Exception as e:
        logger.error(f"TODO handling error: {e}")
        await message.channel.send("❌ TODO処理中にエラーが発生しました")

# ========== Main Entry Point ==========
async def main():
    """Main entry point"""
    # Start health server
    await init_health_server()
    
    # Start Discord bot
    token = Config.DISCORD_TOKEN
    if not token:
        logger.error("DISCORD_TOKEN not set")
        return
    
    logger.info("Starting Catherine AI Integrated...")
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Catherine AI stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()