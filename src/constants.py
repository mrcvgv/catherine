from dotenv import load_dotenv
import os
import dacite
import yaml
from typing import Dict, List, Literal

from src.base import Config

load_dotenv()


# load config.yaml
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG: Config = dacite.from_dict(
    Config, yaml.safe_load(open(os.path.join(SCRIPT_DIR, "config.yaml"), "r"))
)

BOT_NAME = CONFIG.name
BOT_INSTRUCTIONS = CONFIG.instructions
EXAMPLE_CONVOS = CONFIG.example_conversations

# Debug: Print available environment variables for DISCORD_BOT_TOKEN
print("DEBUG: Available environment variables:")
discord_token_keys = [key for key in os.environ.keys() if "DISCORD" in key]
print(f"Discord-related keys: {discord_token_keys}")

# Support both DISCORD_BOT_TOKEN and DISCORD_TOKEN for flexibility
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_TOKEN")
if not DISCORD_BOT_TOKEN:
    print("ERROR: Neither DISCORD_BOT_TOKEN nor DISCORD_TOKEN found in environment variables")
    print("Available env vars:", list(os.environ.keys())[:10])  # Show first 10 keys
    raise ValueError("DISCORD_BOT_TOKEN or DISCORD_TOKEN is required")

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
if not DISCORD_CLIENT_ID:
    raise ValueError("DISCORD_CLIENT_ID is required")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required")

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-3.5-turbo")

ALLOWED_SERVER_IDS: List[int] = []
server_ids_str = os.environ.get("ALLOWED_SERVER_IDS", "")
if server_ids_str:
    server_ids = server_ids_str.split(",")
    for s in server_ids:
        if s.strip():
            ALLOWED_SERVER_IDS.append(int(s.strip()))
else:
    print("WARNING: No ALLOWED_SERVER_IDS set, bot will not respond to any servers")

SERVER_TO_MODERATION_CHANNEL: Dict[int, int] = {}
server_channels = os.environ.get("SERVER_TO_MODERATION_CHANNEL", "").split(",")
for s in server_channels:
    if s.strip():  # 空文字列をスキップ
        values = s.split(":")
        if len(values) == 2:  # 正しい形式かチェック
            SERVER_TO_MODERATION_CHANNEL[int(values[0])] = int(values[1])

# Send Messages, Create Public Threads, Send Messages in Threads, Manage Messages, Manage Threads, Read Message History, Use Slash Command
BOT_INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions=328565073920&scope=bot"

MODERATION_VALUES_FOR_BLOCKED = {
    "harassment": 0.5,
    "harassment/threatening": 0.1,
    "hate": 0.5,
    "hate/threatening": 0.1,
    "self-harm": 0.2,
    "self-harm/instructions": 0.5,
    "self-harm/intent": 0.7,
    "sexual": 0.5,
    "sexual/minors": 0.2,
    "violence": 0.7,
    "violence/graphic": 0.8,
}

MODERATION_VALUES_FOR_FLAGGED = {
    "harassment": 0.5,
    "harassment/threatening": 0.1,
    "hate": 0.4,
    "hate/threatening": 0.05,
    "self-harm": 0.1,
    "self-harm/instructions": 0.5,
    "self-harm/intent": 0.7,
    "sexual": 0.3,
    "sexual/minors": 0.1,
    "violence": 0.1,
    "violence/graphic": 0.1,
}

SECONDS_DELAY_RECEIVING_MSG = (
    3  # give a delay for the bot to respond so it can catch multiple messages
)
MAX_THREAD_MESSAGES = 200
ACTIVATE_THREAD_PREFX = "💬✅"
INACTIVATE_THREAD_PREFIX = "💬❌"
MAX_CHARS_PER_REPLY_MSG = (
    1500  # discord has a 2k limit, we just break message into 1.5k
)

AVAILABLE_MODELS = Literal["gpt-3.5-turbo", "gpt-4", "gpt-4-1106-preview", "gpt-4-32k", "gpt-4o", "gpt-4o-mini"]
