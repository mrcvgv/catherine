#!/usr/bin/env python3
"""
Catherine Task Manager - Simple Task Management Bot for Discord
Based on Discord Task Manager Bot design principles
"""

import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List
from datetime import datetime
import json
import pytz
from aiohttp import web
import logging

# ========== Configuration ==========
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "t!")
PORT = int(os.getenv("PORT", 8080))

# ========== Logging Setup ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Task Storage ==========
class TaskManager:
    """Simple in-memory task manager with JSON persistence"""
    
    def __init__(self, storage_file="tasks.json"):
        self.storage_file = storage_file
        self.tasks = {}  # {guild_id: {task_id: task_data}}
        self.next_id = {}  # {guild_id: next_available_id}
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', {})
                    self.next_id = data.get('next_id', {})
                    logger.info(f"Loaded tasks from {self.storage_file}")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            self.tasks = {}
            self.next_id = {}
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            data = {
                'tasks': self.tasks,
                'next_id': self.next_id
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved tasks to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def add_task(self, guild_id: str, text: str, assigned_to: Optional[str] = None) -> int:
        """Add a new task"""
        guild_id = str(guild_id)
        
        # Initialize guild if not exists
        if guild_id not in self.tasks:
            self.tasks[guild_id] = {}
            self.next_id[guild_id] = 1
        
        # Get next ID
        task_id = self.next_id[guild_id]
        self.next_id[guild_id] += 1
        
        # Create task
        self.tasks[guild_id][str(task_id)] = {
            'id': task_id,
            'text': text,
            'assigned_to': assigned_to,
            'is_done': False,
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'completed_at': None
        }
        
        self.save_tasks()
        return task_id
    
    def get_tasks(self, guild_id: str, include_done: bool = False) -> List[Dict]:
        """Get all tasks for a guild"""
        guild_id = str(guild_id)
        
        if guild_id not in self.tasks:
            return []
        
        tasks = []
        for task_data in self.tasks[guild_id].values():
            if include_done or not task_data['is_done']:
                tasks.append(task_data)
        
        # Sort by ID
        tasks.sort(key=lambda x: x['id'])
        return tasks
    
    def mark_done(self, guild_id: str, task_id: int) -> bool:
        """Mark a task as done"""
        guild_id = str(guild_id)
        task_id = str(task_id)
        
        if guild_id in self.tasks and task_id in self.tasks[guild_id]:
            self.tasks[guild_id][task_id]['is_done'] = True
            self.tasks[guild_id][task_id]['completed_at'] = datetime.now(pytz.UTC).isoformat()
            self.save_tasks()
            return True
        return False
    
    def mark_undone(self, guild_id: str, task_id: int) -> bool:
        """Mark a task as not done"""
        guild_id = str(guild_id)
        task_id = str(task_id)
        
        if guild_id in self.tasks and task_id in self.tasks[guild_id]:
            self.tasks[guild_id][task_id]['is_done'] = False
            self.tasks[guild_id][task_id]['completed_at'] = None
            self.save_tasks()
            return True
        return False
    
    def delete_task(self, guild_id: str, task_id: int) -> bool:
        """Delete a task"""
        guild_id = str(guild_id)
        task_id = str(task_id)
        
        if guild_id in self.tasks and task_id in self.tasks[guild_id]:
            del self.tasks[guild_id][task_id]
            self.save_tasks()
            return True
        return False
    
    def clear_all(self, guild_id: str) -> int:
        """Clear all tasks for a guild"""
        guild_id = str(guild_id)
        
        if guild_id in self.tasks:
            count = len(self.tasks[guild_id])
            self.tasks[guild_id] = {}
            self.next_id[guild_id] = 1
            self.save_tasks()
            return count
        return 0

# ========== Discord Bot ==========
class TaskBot(commands.Bot):
    """Simple Task Management Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.task_manager = TaskManager()
    
    async def setup_hook(self):
        """Setup bot hooks"""
        await self.tree.sync()
        logger.info("Commands synced")
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'Task Bot {self.user} is ready!')
        logger.info(f'Prefix: {BOT_PREFIX}')
        logger.info(f'Connected to {len(self.guilds)} guilds')

# Create bot instance
bot = TaskBot()

# ========== Health Check Server ==========
async def health_check(request):
    """Railway health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Catherine Task Manager'
    })

async def init_health_server():
    """Initialize health check server"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Health server started on port {PORT}")
    return runner

# ========== Slash Commands ==========
@bot.tree.command(name="add", description="Add a new task")
@app_commands.describe(text="The task description")
@app_commands.describe(assign="Mention a user to assign the task to them")
async def add_command(interaction: discord.Interaction, text: str, assign: Optional[discord.Member] = None):
    """Add a new task"""
    assigned_to = str(assign.id) if assign else None
    task_id = bot.task_manager.add_task(interaction.guild_id, text, assigned_to)
    
    response = f"✅ Task **#{task_id}** added: {text}"
    if assign:
        response += f" (assigned to {assign.mention})"
    
    await interaction.response.send_message(response)

@bot.tree.command(name="list", description="List all pending tasks")
async def list_command(interaction: discord.Interaction):
    """List all pending tasks"""
    tasks = bot.task_manager.get_tasks(interaction.guild_id, include_done=False)
    
    if not tasks:
        await interaction.response.send_message("📋 No pending tasks!")
        return
    
    response = "📋 **Pending Tasks:**\n\n"
    for i, task in enumerate(tasks, 1):
        response += f"**{i}.** {task['text']} - ID: **{task['id']}**"
        if task['assigned_to']:
            response += f" - <@{task['assigned_to']}>"
        response += "\n"
    
    response += "\n*To mark a task as done, use `/done [ID]`*"
    await interaction.response.send_message(response)

@bot.tree.command(name="done", description="Mark a task as done")
@app_commands.describe(task_id="The ID of the task to mark as done")
async def done_command(interaction: discord.Interaction, task_id: int):
    """Mark a task as done"""
    success = bot.task_manager.mark_done(interaction.guild_id, task_id)
    
    if success:
        await interaction.response.send_message(f"✅ Task **#{task_id}** marked as done!")
    else:
        await interaction.response.send_message(f"❌ Task **#{task_id}** not found!")

@bot.tree.command(name="done-list", description="List all completed tasks")
async def done_list_command(interaction: discord.Interaction):
    """List all completed tasks"""
    tasks = bot.task_manager.get_tasks(interaction.guild_id, include_done=True)
    done_tasks = [t for t in tasks if t['is_done']]
    
    if not done_tasks:
        await interaction.response.send_message("📋 No completed tasks!")
        return
    
    response = "✅ **Completed Tasks:**\n\n"
    for i, task in enumerate(done_tasks, 1):
        response += f"**{i}.** ~~{task['text']}~~ - ID: **{task['id']}**"
        if task['assigned_to']:
            response += f" - <@{task['assigned_to']}>"
        response += "\n"
    
    response += "\n*To undo a task, use `/undo [ID]`*"
    await interaction.response.send_message(response)

@bot.tree.command(name="undo", description="Mark a task as not done")
@app_commands.describe(task_id="The ID of the task to mark as not done")
async def undo_command(interaction: discord.Interaction, task_id: int):
    """Mark a task as not done"""
    success = bot.task_manager.mark_undone(interaction.guild_id, task_id)
    
    if success:
        await interaction.response.send_message(f"↩️ Task **#{task_id}** marked as not done!")
    else:
        await interaction.response.send_message(f"❌ Task **#{task_id}** not found!")

@bot.tree.command(name="delete", description="Delete a task")
@app_commands.describe(task_id="The ID of the task to delete")
async def delete_command(interaction: discord.Interaction, task_id: int):
    """Delete a task"""
    success = bot.task_manager.delete_task(interaction.guild_id, task_id)
    
    if success:
        await interaction.response.send_message(f"🗑️ Task **#{task_id}** deleted!")
    else:
        await interaction.response.send_message(f"❌ Task **#{task_id}** not found!")

@bot.tree.command(name="clear", description="Clear all tasks")
async def clear_command(interaction: discord.Interaction):
    """Clear all tasks"""
    count = bot.task_manager.clear_all(interaction.guild_id)
    await interaction.response.send_message(f"🗑️ Cleared **{count}** tasks!")

@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="📋 Task Manager Bot Help",
        description="Simple task management for your Discord server",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Commands",
        value=(
            "**/add [text] [@user]** - Add a new task (optionally assign to user)\n"
            "**/list** - Show all pending tasks\n"
            "**/done [ID]** - Mark a task as done\n"
            "**/done-list** - Show all completed tasks\n"
            "**/undo [ID]** - Mark a task as not done\n"
            "**/delete [ID]** - Delete a task\n"
            "**/clear** - Clear all tasks\n"
            "**/help** - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Text Commands (Alternative)",
        value=(
            f"**{BOT_PREFIX}add [text]** - Add a task\n"
            f"**{BOT_PREFIX}list** - List tasks\n"
            f"**{BOT_PREFIX}done [ID]** - Mark done\n"
            f"**{BOT_PREFIX}done-list** - Show completed"
        ),
        inline=False
    )
    
    embed.set_footer(text="Task IDs are shown in the task list")
    
    await interaction.response.send_message(embed=embed)

# ========== Text Commands ==========
@bot.command(name="add")
async def text_add(ctx, *, text: str):
    """Add a task via text command"""
    # Check for mentions
    assigned_to = None
    if ctx.message.mentions:
        assigned_to = str(ctx.message.mentions[0].id)
        # Remove mention from text
        for mention in ctx.message.mentions:
            text = text.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '').strip()
    
    task_id = bot.task_manager.add_task(ctx.guild.id, text, assigned_to)
    
    response = f"✅ Task **#{task_id}** added: {text}"
    if assigned_to:
        response += f" (assigned to <@{assigned_to}>)"
    
    await ctx.send(response)

@bot.command(name="list")
async def text_list(ctx):
    """List tasks via text command"""
    tasks = bot.task_manager.get_tasks(ctx.guild.id, include_done=False)
    
    if not tasks:
        await ctx.send("📋 No pending tasks!")
        return
    
    response = "📋 **Pending Tasks:**\n\n"
    for i, task in enumerate(tasks, 1):
        response += f"**{i}.** {task['text']} - ID: **{task['id']}**"
        if task['assigned_to']:
            response += f" - <@{task['assigned_to']}>"
        response += "\n"
    
    response += f"\n*To mark done: `{BOT_PREFIX}done [ID]`*"
    await ctx.send(response)

@bot.command(name="done")
async def text_done(ctx, task_id: int):
    """Mark task as done via text command"""
    success = bot.task_manager.mark_done(ctx.guild.id, task_id)
    
    if success:
        await ctx.send(f"✅ Task **#{task_id}** marked as done!")
    else:
        await ctx.send(f"❌ Task **#{task_id}** not found!")

@bot.command(name="done-list")
async def text_done_list(ctx):
    """List done tasks via text command"""
    tasks = bot.task_manager.get_tasks(ctx.guild.id, include_done=True)
    done_tasks = [t for t in tasks if t['is_done']]
    
    if not done_tasks:
        await ctx.send("📋 No completed tasks!")
        return
    
    response = "✅ **Completed Tasks:**\n\n"
    for i, task in enumerate(done_tasks, 1):
        response += f"**{i}.** ~~{task['text']}~~ - ID: **{task['id']}**"
        if task['assigned_to']:
            response += f" - <@{task['assigned_to']}>"
        response += "\n"
    
    response += f"\n*To undo: `{BOT_PREFIX}undo [ID]`*"
    await ctx.send(response)

@bot.command(name="undo")
async def text_undo(ctx, task_id: int):
    """Undo task via text command"""
    success = bot.task_manager.mark_undone(ctx.guild.id, task_id)
    
    if success:
        await ctx.send(f"↩️ Task **#{task_id}** marked as not done!")
    else:
        await ctx.send(f"❌ Task **#{task_id}** not found!")

# ========== Main Entry Point ==========
async def main():
    """Main entry point"""
    # Start health server
    await init_health_server()
    
    # Start Discord bot
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set")
        return
    
    logger.info("Starting Task Manager Bot...")
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Task Manager Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()