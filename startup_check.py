#!/usr/bin/env python3
"""
Catherine AI Startup Check Script
Railway環境でのクラッシュデバッグ用
"""

import os
import sys

print("=" * 60)
print("Catherine AI Startup Environment Check")
print("=" * 60)

# 環境変数チェック
print("\n[Environment Variables]")
env_vars = {
    "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "PORT": os.getenv("PORT", "8080"),
    "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not on Railway"),
}

for key, value in env_vars.items():
    if value and key in ["DISCORD_TOKEN", "OPENAI_API_KEY"]:
        # マスク表示
        masked = "*" * 10 + value[-5:] if len(value) > 5 else "SHORT"
        print(f"  {key}: {masked}")
    elif value:
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: NOT SET")

# Python環境チェック
print("\n[Python Environment]")
print(f"  Python version: {sys.version}")
print(f"  Platform: {sys.platform}")

# 必須モジュールチェック
print("\n[Module Import Test]")
modules_to_test = [
    "discord",
    "openai",
    "firebase_admin",
    "pytz",
    "yaml",
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"  ✓ {module_name}")
    except ImportError as e:
        print(f"  ✗ {module_name}: {e}")

# Firebase設定チェック
print("\n[Firebase Configuration]")
firebase_key_file = "catherine-9e862-firebase-adminsdk-fbsvc-28368629ce.json"
if os.path.exists(firebase_key_file):
    print(f"  ✓ Firebase key file exists: {firebase_key_file}")
else:
    print(f"  ✗ Firebase key file not found: {firebase_key_file}")

# ローカルモジュールチェック
print("\n[Local Module Files]")
local_files = [
    "enhanced_main_v2.py",
    "human_level_chat.py",
    "simple_todo.py",
    "firebase_config.py",
    "team_todo_manager.py",
]

for file_name in local_files:
    if os.path.exists(file_name):
        print(f"  ✓ {file_name}")
    else:
        print(f"  ✗ {file_name}")

print("\n" + "=" * 60)
print("Check Complete")
print("=" * 60)