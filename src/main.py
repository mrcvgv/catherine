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

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
thread_data = defaultdict()

# Handle TODO commands
async def handle_todo_command(user: discord.User, intent: Dict[str, Any]) -> str:
    """TODO操作を処理"""
    from src.todo_manager import todo_manager
    
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
            
            response = f"✅ TODOを追加しました！\n\n"
            response += f"📝 **{todo['title']}**\n"
            if todo.get('due_date'):
                response += f"📅 期限: {todo['due_date'].strftime('%Y-%m-%d %H:%M')}\n"
            response += f"🎯 優先度: {todo['priority']}\n"
            response += f"\n💡 ヒント: 「TODOリスト」と言うと一覧が見れます！"
            
        elif action == 'list':
            # TODOリスト表示
            todos = await todo_manager.get_todos(
                user_id=user_id,
                include_completed=intent.get('include_completed', False)
            )
            response = todo_manager.format_todo_list(todos)
            
            if not intent.get('include_completed'):
                response += "\n💡 完了済みも見たい場合は「完了したTODOも見せて」と言ってください！"
            
        elif action == 'complete':
            # TODO完了
            todos = await todo_manager.get_todos(user_id=user_id)
            
            if intent.get('todo_number') and intent['todo_number'] <= len(todos):
                todo = todos[intent['todo_number'] - 1]
                success = await todo_manager.complete_todo(todo['id'], user_id)
                if success:
                    response = f"✅ 「{todo['title']}」を完了にしました！お疲れ様でした！🎉"
                else:
                    response = "❌ TODOの完了に失敗しました。"
            else:
                response = "❌ 該当するTODOが見つかりません。番号を確認してください。"
        
        elif action == 'delete':
            # TODO削除
            todos = await todo_manager.get_todos(user_id=user_id, include_completed=True)
            
            if intent.get('todo_number') and intent['todo_number'] <= len(todos):
                todo = todos[intent['todo_number'] - 1]
                success = await todo_manager.delete_todo(todo['id'], user_id)
                if success:
                    response = f"🗑️ 「{todo['title']}」を削除しました。"
                else:
                    response = "❌ TODOの削除に失敗しました。"
            else:
                response = "❌ 該当するTODOが見つかりません。番号を確認してください。"
        
        else:
            response = "❓ TODO操作を理解できませんでした。\n使い方:\n- TODO追加: 「〇〇をTODOに追加」\n- リスト表示: 「TODOリスト」\n- 完了: 「1番を完了」\n- 削除: 「2番を削除」"
            
    except Exception as e:
        logger.error(f"TODO operation error: {e}")
        response = f"❌ エラーが発生しました: {str(e)}"
    
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
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'message_type': 'chat_completion'
        }
        
        # Save to Firebase
        db.collection('conversations').add(conversation_data)
        logging.info(f"Conversation saved to Firebase for user {user_id}")
        
    except Exception as e:
        logging.error(f"Failed to save conversation to Firebase: {e}")


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user}. Invite URL: {BOT_INVITE_URL}")
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
    temperature="Controls randomness. Higher values mean more randomness. Between 0 and 1"
)
@app_commands.describe(
    max_tokens="How many tokens the model should output at max for each message."
)
async def chat_command(
    interaction: discord.Interaction,
    message: str,
    model: AVAILABLE_MODELS = DEFAULT_MODEL,
    temperature: Optional[float] = 1.0,
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
        
        # Handle all messages (DM or channel)
        user = message.author
        content = message.content
        
        # TODO機能のインポート
        try:
            from src.todo_manager import todo_manager
            from src.todo_nlu import todo_nlu
            
            # TODO操作を解析
            todo_intent = todo_nlu.parse_message(content)
            
            if todo_intent.get('action') and todo_intent.get('confidence', 0) > 0.5:
                # TODO操作を実行
                async with message.channel.typing():
                    response_text = await handle_todo_command(user, todo_intent)
                    await message.reply(response_text)
                    
                    # Firebaseに保存
                    channel_id = f"dm_{user.id}" if isinstance(message.channel, discord.DMChannel) else str(message.channel.id)
                    await save_conversation_to_firebase(
                        user_id=str(user.id),
                        channel_id=channel_id,
                        message=content,
                        response=response_text
                    )
                return
        except ImportError:
            logger.warning("TODO modules not available")
        
        # Log the message
        if isinstance(message.channel, discord.DMChannel):
            logger.info(f"DM from {user}: {content[:50]}")
        else:
            logger.info(f"Message from {user} in {message.guild}: {content[:50]}")
        
        # Moderate the message
        flagged_str, blocked_str = moderate_message(
            message=content, user=user
        )
        
        # Handle blocked messages
        if len(blocked_str) > 0:
            await message.delete()
            await message.channel.send(
                embed=discord.Embed(
                    description=f"❌ Message was blocked by moderation.",
                    color=discord.Color.red()
                ),
                delete_after=10
            )
            return
        
        # Show typing indicator
        async with message.channel.typing():
            # Generate response using GPT-4o
            logger.info(f"Generating response for: {content[:50]}")
            try:
                # Create thread config for the response
                thread_config = ThreadConfig(
                    model="gpt-4o",
                    temperature=1.0,
                    max_tokens=512
                )
                
                response_data = await generate_completion_response(
                    messages=[Message(user=user.name, text=content)],
                    user=user,
                    thread_config=thread_config
                )
                
                # Send response
                if response_data and response_data.reply_text:
                    logger.info(f"Sending response: {response_data.reply_text[:50]}")
                    # Split long messages if needed
                    from src.utils import split_into_shorter_messages
                    shorter_response = split_into_shorter_messages(response_data.reply_text)
                    for r in shorter_response:
                        await message.reply(r)
                    
                    # Save conversation to Firebase
                    channel_id = f"dm_{user.id}" if isinstance(message.channel, discord.DMChannel) else str(message.channel.id)
                    await save_conversation_to_firebase(
                        user_id=str(user.id),
                        channel_id=channel_id,
                        message=content,
                        response=response_data.reply_text
                    )
                else:
                    logger.error(f"No response generated for message: {content}")
                    if response_data and response_data.status_text:
                        await message.reply(f"エラー: {response_data.status_text}")
                    else:
                        await message.reply("申し訳ございません。応答の生成に失敗しました。")
            except Exception as gen_error:
                logger.error(f"Error generating response: {gen_error}")
                await message.reply(f"エラーが発生しました: {str(gen_error)[:100]}")
        
        # Below is the old thread logic (now unreachable)
        channel = message.channel
        if not isinstance(channel, discord.Thread):
            return

        thread = channel
        if thread.owner_id != client.user.id:
            return

        if (
            thread.archived
            or thread.locked
            or not thread.name.startswith(ACTIVATE_THREAD_PREFX)
        ):
            return

        if thread.message_count > MAX_THREAD_MESSAGES:
            # too many messages, no longer going to reply
            await close_thread(thread=thread)
            return

        # moderate the message
        flagged_str, blocked_str = moderate_message(
            message=message.content, user=message.author
        )
        await send_moderation_blocked_message(
            guild=message.guild,
            user=message.author,
            blocked_str=blocked_str,
            message=message.content,
        )
        if len(blocked_str) > 0:
            try:
                await message.delete()
                await thread.send(
                    embed=discord.Embed(
                        description=f"❌ **{message.author}'s message has been deleted by moderation.**",
                        color=discord.Color.red(),
                    )
                )
                return
            except Exception as e:
                await thread.send(
                    embed=discord.Embed(
                        description=f"❌ **{message.author}'s message has been blocked by moderation but could not be deleted. Missing Manage Messages permission in this Channel.**",
                        color=discord.Color.red(),
                    )
                )
                return
        await send_moderation_flagged_message(
            guild=message.guild,
            user=message.author,
            flagged_str=flagged_str,
            message=message.content,
            url=message.jump_url,
        )
        if len(flagged_str) > 0:
            await thread.send(
                embed=discord.Embed(
                    description=f"⚠️ **{message.author}'s message has been flagged by moderation.**",
                    color=discord.Color.yellow(),
                )
            )

        # wait a bit in case user has more messages
        if SECONDS_DELAY_RECEIVING_MSG > 0:
            await asyncio.sleep(SECONDS_DELAY_RECEIVING_MSG)
            if is_last_message_stale(
                interaction_message=message,
                last_message=thread.last_message,
                bot_id=client.user.id,
            ):
                # there is another message, so ignore this one
                return

        logger.info(
            f"Thread message to process - {message.author}: {message.content[:50]} - {thread.name} {thread.jump_url}"
        )

        channel_messages = [
            discord_message_to_message(message)
            async for message in thread.history(limit=MAX_THREAD_MESSAGES)
        ]
        channel_messages = [x for x in channel_messages if x is not None]
        channel_messages.reverse()

        # generate the response
        async with thread.typing():
            response_data = await generate_completion_response(
                messages=channel_messages,
                user=message.author,
                thread_config=thread_data[thread.id],
            )

        if is_last_message_stale(
            interaction_message=message,
            last_message=thread.last_message,
            bot_id=client.user.id,
        ):
            # there is another message and its not from us, so ignore this response
            return

        # send response
        await process_response(
            user=message.author, thread=thread, response_data=response_data
        )
        
        # Save conversation to Firebase
        if response_data and 'text' in response_data:
            await save_conversation_to_firebase(
                user_id=str(message.author.id),
                channel_id=str(thread.id),
                message=message.content,
                response=response_data['text']
            )
    except Exception as e:
        logger.exception(e)


client.run(DISCORD_BOT_TOKEN)
