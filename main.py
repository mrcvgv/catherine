import os
import asyncio
import discord
from openai import OpenAI

# Railway 用のポート設定（必要に応じて）
PORT = int(os.environ.get("PORT", 8080))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# OpenAI クライアントを新方式で初期化
client_oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@client.event
async def on_ready():
    print(f"✅ Bot Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("C!"):
        prompt = message.content[len("C!"):].strip()
        print(f"📝 Prompt received: {prompt}")

        try:
            # v1 系の書き方に変更
            resp = client_oa.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful secretary named Catherine."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = resp.choices[0].message.content
            await message.channel.send(reply)
            print(f"💬 Reply sent: {reply}")

        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            await message.channel.send("Catherine: うまく返事できなかったわ……ごめんなさい。エラーが出ちゃったみたい。")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN environment variable is not set")
        exit(1)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable is not set")
        exit(1)
    
    print("🚀 Starting Catherine bot...")
    client.run(token)
