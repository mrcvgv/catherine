#!/usr/bin/env python3
"""
Catherine AI - 完全記録機能のデモ
"""

import asyncio
import os
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
from conversation_manager import ConversationManager
from firebase_config import firebase_manager

async def demo_perfect_memory():
    """完全記録機能のデモンストレーション"""
    
    # OpenAI クライアント初期化
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    conv_manager = ConversationManager(openai_client)
    
    # テストユーザーID
    test_user = "demo_user_123"
    
    print("🧠 Catherine AI - 完全記録機能デモ\n")
    
    # 1. 過去の会話を記録（シミュレーション）
    print("📝 過去の会話を記録中...")
    
    sample_conversations = [
        {
            "user_message": "明日プレゼンがあるんだ",
            "bot_response": "Catherine: プレゼンの準備、頑張ってくださいね！資料作成のお手伝いが必要でしたらお声かけください。",
            "topics": ["work", "presentation"]
        },
        {
            "user_message": "コーヒーが好きなんだ",
            "bot_response": "Catherine: コーヒーがお好きなんですね！どんな種類がお気に入りですか？",
            "topics": ["personal", "coffee", "preferences"]
        },
        {
            "user_message": "最近忙しくて疲れてる",
            "bot_response": "Catherine: お疲れ様です。休息も大切ですよ。何かサポートできることがあれば教えてください。",
            "topics": ["personal", "health", "work_life_balance"]
        }
    ]
    
    for i, conv in enumerate(sample_conversations):
        await conv_manager.log_conversation(
            user_id=test_user,
            user_message=conv["user_message"],
            bot_response=conv["bot_response"], 
            command_type="conversation"
        )
        print(f"  ✅ 会話 {i+1} を記録")
    
    print()
    
    # 2. 記憶を活用した応答生成
    print("🎯 記憶を活用した個人化応答の生成...\n")
    
    # ユーザー設定を更新
    await conv_manager.update_user_preferences(test_user, {
        "humor_level": 70,
        "conversation_style": 60
    })
    
    # 記憶を活用した応答
    test_inputs = [
        "今日もプレゼンの練習してるよ",
        "コーヒー飲んで一息ついてる", 
        "今週も忙しそうだなあ"
    ]
    
    for user_input in test_inputs:
        print(f"👤 ユーザー: {user_input}")
        
        # ユーザー設定を取得
        user_prefs = await conv_manager.get_user_preferences(test_user)
        
        # 記憶を活用した応答生成
        response = await conv_manager.generate_response(
            user_id=test_user,
            user_input=user_input,
            user_preferences=user_prefs
        )
        
        print(f"🤖 {response}")
        print()
        
        # この会話も記録
        await conv_manager.log_conversation(
            user_id=test_user,
            user_message=user_input,
            bot_response=response,
            command_type="conversation"
        )
    
    # 3. 会話分析レポート
    print("📊 会話分析レポート生成...\n")
    
    analytics = await conv_manager.get_conversation_analytics(test_user, days=30)
    
    print("=== 会話分析結果 ===")
    print(f"総会話数: {analytics.get('total_conversations', 0)}")
    print(f"平均満足度: {analytics.get('average_satisfaction', 0):.1f}%")
    print(f"平均有用性: {analytics.get('average_helpfulness', 0):.1f}%")
    print(f"1日あたり会話数: {analytics.get('conversations_per_day', 0):.1f}")
    
    if analytics.get('command_distribution'):
        print("\nコマンド使用状況:")
        for cmd, count in analytics['command_distribution'].items():
            print(f"  {cmd}: {count}回")
    
    print("\n✨ Catherine AIは全ての会話を記憶し、")
    print("   あなたの好みや話題に応じて応答を最適化します！")

if __name__ == "__main__":
    if not firebase_manager.is_available():
        print("❌ Firebaseが設定されていません")
        print("完全記録機能を使用するには、Firebaseの設定が必要です")
        exit(1)
    
    asyncio.run(demo_perfect_memory())