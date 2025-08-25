#!/usr/bin/env python3
"""
Discordメンション機能のテスト
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mention_utils import DiscordMentionHandler, parse_mention_from_text, get_mention_string

def test_mention_parsing():
    """メンション解析のテスト"""
    print("=== メンション解析テスト ===")
    
    test_cases = [
        "@everyone",
        "みんな",
        "全員",
        "@mrc",
        "@supy",
        "mrcさん",
        "supyさん",
        "@admin",
        "管理者",
        "@developer",
        "role:moderator",
        "@unknown_user",
        "何もなし"
    ]
    
    for test_input in test_cases:
        result = parse_mention_from_text(test_input)
        print(f"入力: '{test_input}' -> メンション: '{result['mention_string']}' (タイプ: {result['mention_type']})")
    
    print("\n=== 自然言語メンション解析テスト ===")
    
    natural_cases = [
        "mrcにリマインドして",
        "supyさんに教えて",
        "管理者に通知してください",
        "開発者向けのリマインダー",
        "みんなにお知らせ",
        "全員に周知",
        "メンバーに連絡"
    ]
    
    for test_input in natural_cases:
        result = parse_mention_from_text(test_input)
        print(f"自然言語: '{test_input}' -> メンション: '{result['mention_string']}'")

def test_mention_formats():
    """Discord文法メンション形式のテスト"""
    print("\n=== Discord文法メンション形式テスト ===")
    
    # ユーザーメンション: <@user_id>
    user_id = "123456789012345678"
    user_mention = f"<@{user_id}>"
    print(f"ユーザーメンション: {user_mention}")
    
    # ロールメンション: <@&role_id>
    role_id = "987654321098765432"
    role_mention = f"<@&{role_id}>"
    print(f"ロールメンション: {role_mention}")
    
    # 特別なメンション
    print(f"全員メンション: @everyone")
    print(f"オンラインメンション: @here")
    
def test_todo_nlu_integration():
    """TodoNLUとの統合テスト"""
    print("\n=== TodoNLU統合テスト ===")
    
    from todo_nlu import todo_nlu
    
    test_messages = [
        "mrcに明日10時にリマインドして",
        "supyさんに来週水曜にTODOリストを教えて",
        "みんなに今日の夕方リマインダー",
        "管理者に月曜日にタスク通知",
        "開発者向けに緊急リマインダー",
        "@everyoneに毎日9時にリスト表示"
    ]
    
    for message in test_messages:
        intent = todo_nlu.parse_message(message)
        if intent.get('action') == 'remind':
            print(f"メッセージ: '{message}'")
            print(f"  -> メンション対象: {intent.get('mention_target')}")
            print(f"  -> チャンネル: {intent.get('channel_target')}")
            print(f"  -> 時間: {intent.get('remind_time')}")
            print()

def test_edge_cases():
    """エッジケース・特殊ケースのテスト"""
    print("=== エッジケーステスト ===")
    
    edge_cases = [
        "",  # 空文字列
        "@",  # @のみ
        "@@",  # @@
        "@1234",  # 数字のみ
        "@user@domain.com",  # メールアドレス形式
        "@あいうえお",  # 日本語文字
        "@ スペース",  # スペースを含む
        "@user1 @user2",  # 複数メンション
        "text @user more text",  # 埋め込みメンション
    ]
    
    for case in edge_cases:
        try:
            result = parse_mention_from_text(case)
            print(f"'{case}' -> '{result['mention_string']}'")
        except Exception as e:
            print(f"'{case}' -> エラー: {e}")

if __name__ == "__main__":
    print("Discord mention function test started\n")
    
    test_mention_parsing()
    test_mention_formats()
    test_todo_nlu_integration()
    test_edge_cases()
    
    print("\nTest completed")
    print("\nImplemented features:")
    print("- @everyone, @here, みんな, 全員 -> @everyone")
    print("- @user, userさん -> <@user_id>")
    print("- @role, role:name -> <@&role_id>")
    print("- Natural language mention (mrcにリマインド etc.)")
    print("- Multiple mention support")
    print("- Error handling")