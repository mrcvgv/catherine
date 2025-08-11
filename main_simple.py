#!/usr/bin/env python3
"""
Catherine AI - シンプル版（Firebase不要）
基本的な会話機能のみ
"""

import os
import discord
from openai import OpenAI

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# OpenAI設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@client.event
async def on_ready():
    print(f"✅ Catherine Bot (Simple) - {client.user} がログインしました")

@client.event  
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("C!"):
        prompt = message.content[2:].strip()
        
        if not prompt:
            await message.channel.send("Catherine: 何かお手伝いできることはありますか？")
            return
            
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "あなたは「Catherine」という名前の優秀なAI秘書です。親切で丁寧に応答してください。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            reply = response.choices[0].message.content
            await message.channel.send(f"Catherine: {reply}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            await message.channel.send("Catherine: 申し訳ありません。エラーが発生しました。")

if __name__ == "__main__":
    # 環境変数チェック
    discord_token = os.getenv("DISCORD_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not discord_token:
        print("❌ DISCORD_TOKEN が設定されていません")
        exit(1)
        
    if not openai_key:
        print("❌ OPENAI_API_KEY が設定されていません") 
        exit(1)
    
    print("🚀 Catherine AI (Simple版) 起動中...")
    client.run(discord_token)