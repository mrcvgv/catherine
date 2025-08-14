# test_discord_token.py
import os, asyncio, discord
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
print("DISCORD_BOT_TOKEN prefix:", (token or "")[:10] + "..." if token else "None", "len=", len(token or ""))

if not token:
    print("❌ DISCORD_BOT_TOKEN not found in environment")
    print("Available env vars with 'DISCORD':", [k for k in os.environ.keys() if "DISCORD" in k])
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print("✅ Discord ready as", bot.user)
    await bot.close()

try:
    bot.run(token)
except Exception as e:
    print("❌ Discord connection failed:", e)