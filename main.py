import os
import asyncio
import discord
from openai import OpenAI

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

    if message.content.startswith("!catherine"):
        prompt = message.content[len("!catherine"):].strip()
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
    asyncio.run(client.start(os.getenv("DISCORD_TOKEN")))
