#!/usr/bin/env python3
"""
Firebase設定の簡単セットアップガイド
"""

import os
import json

def check_firebase_setup():
    """Firebase設定状況をチェック"""
    print("Firebase setup check\n")
    
    # 環境変数チェック
    firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    
    if not firebase_key:
        print("ERROR: FIREBASE_SERVICE_ACCOUNT_KEY not set\n")
        print_setup_instructions()
        return False
    
    # JSON形式チェック
    try:
        key_data = json.loads(firebase_key)
        print("SUCCESS: FIREBASE_SERVICE_ACCOUNT_KEY is set")
        print(f"SUCCESS: Project ID: {key_data.get('project_id', 'Unknown')}")
        print(f"SUCCESS: Client Email: {key_data.get('client_email', 'Unknown')[:50]}...")
        return True
        
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON format error: {e}")
        print("Please check environment variable value")
        return False

def print_setup_instructions():
    """設定手順を表示"""
    print("=== Firebase Setup Instructions ===")
    print("1. Go to https://console.firebase.google.com/")
    print("2. Create new project with 'Add project'")
    print("3. Create 'Firestore Database' (test mode)")
    print("4. Settings > Service Account > 'Generate new private key'")
    print("5. Copy contents of downloaded JSON file")
    print("6. Set as environment variable:\n")
    
    print("PowerShell command example:")
    print('$env:FIREBASE_SERVICE_ACCOUNT_KEY=\'{"type": "service_account", "project_id": "your-project-id", ...}\'')
    print()
    
    print("Or create .env file:")
    print('FIREBASE_SERVICE_ACCOUNT_KEY={"type": "service_account", "project_id": "your-project-id", ...}')
    print()

def create_sample_env_file():
    """サンプル.envファイルを作成"""
    sample_content = """# Catherine AI 環境変数設定
# 実際の値に置き換えてください

# Discord Bot Token (https://discord.com/developers/applications)
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE

# OpenAI API Key (https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY_HERE

# Firebase Service Account Key (Firebase Console > Settings > Service Accounts > Generate new private key)
FIREBASE_SERVICE_ACCOUNT_KEY={"type": "service_account", "project_id": "your-project-id", "private_key_id": "your-key-id", "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n", "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com", "client_id": "your-client-id", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project.iam.gserviceaccount.com"}

# Railway用のポート設定（Railwayデプロイ時のみ必要）
PORT=8080
"""
    
    env_file = ".env.sample"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    print(f"Created sample environment file '{env_file}'")
    print("Replace with actual values and save as '.env'")

if __name__ == "__main__":
    print("Catherine AI - Firebase Setup Guide\n")
    
    if check_firebase_setup():
        print("\nFirebase setup is successful!")
        print("Run test with:")
        print("python test_firebase.py")
    else:
        print("\nSetup required. Please follow the instructions above.")
        create_sample_env_file()