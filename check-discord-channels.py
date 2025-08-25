#!/usr/bin/env python3
"""
実際のDiscordチャンネル名を確認
"""

import discord
import asyncio
import os
import sys
from dotenv import load_dotenv

# UTF-8エンコーディング設定
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

class ChannelInspector(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
    
    async def on_ready(self):
        print(f'Bot: {self.user} is ready')
        print('=' * 50)
        
        for guild in self.guilds:
            print(f'Server: {guild.name} (ID: {guild.id})')
            print('Text Channels:')
            
            for channel in guild.channels:
                if hasattr(channel, 'send'):  # Text channels only
                    try:
                        channel_name = channel.name
                        print(f'  #{channel_name:<20} (ID: {channel.id})')
                    except Exception as e:
                        print(f'  [Channel decode error] (ID: {channel.id})')
            
            print('\nAll Channel Names (raw):')
            channel_names = []
            for channel in guild.channels:
                if hasattr(channel, 'send'):
                    try:
                        channel_names.append(channel.name)
                    except:
                        channel_names.append('[decode_error]')
            
            print('Channel names list:', channel_names)
            print('\nCurrent .env configuration:')
            print('ALLOWED_CHANNEL_NAMES:', os.getenv('ALLOWED_CHANNEL_NAMES', 'not set'))
            print('CATHERINE_CHANNELS:', os.getenv('CATHERINE_CHANNELS', 'not set'))
            
        await self.close()

def main():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print('ERROR: DISCORD_BOT_TOKEN not found in environment')
        return
    
    client = ChannelInspector()
    try:
        client.run(token)
    except Exception as e:
        print(f'Connection error: {e}')

if __name__ == '__main__':
    main()