#!/usr/bin/env python3

"""
実際のDiscordチャンネル名でテスト
"""

import os
import sys
from unittest.mock import Mock
import io

# UTF-8エンコーディング
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_real_channels():
    """実際のチャンネル名でテスト"""
    
    print("Testing with REAL Discord Channel Names")
    print("======================================")
    
    # .envから読み込み
    from dotenv import load_dotenv
    load_dotenv()
    
    # constants.pyの読み込みテスト
    try:
        from src.constants import ALLOWED_CHANNEL_NAMES, CATHERINE_CHANNELS
        print(f"Loaded constants:")
        print(f"  ALLOWED_CHANNEL_NAMES: {ALLOWED_CHANNEL_NAMES}")
        print(f"  CATHERINE_CHANNELS: {CATHERINE_CHANNELS}")
    except Exception as e:
        print(f"ERROR loading constants: {e}")
        return
    
    print("\nReal Channel Test:")
    print("=" * 50)
    
    try:
        from src.channel_utils import is_allowed_channel, is_catherine_channel, should_respond_to_message
        
        # Mock Discordメッセージ作成（実際のチャンネル名使用）
        def create_mock_message(channel_name, content="Hello", is_dm=False, mentions_bot=False):
            message = Mock()
            message.author = Mock()
            message.content = content
            message.mentions = []
            
            if is_dm:
                from discord import DMChannel
                message.channel = Mock(spec=DMChannel)
            else:
                from discord import TextChannel
                message.channel = Mock(spec=TextChannel)
                message.channel.name = channel_name
                
            if mentions_bot:
                bot_user = Mock()
                bot_user.bot = True
                message.mentions = [bot_user]
                
            return message
        
        # 実際のチャンネル名でテストケース
        real_test_cases = [
            # (channel_name, content, is_dm, mentions_bot, expected_respond, description)
            ("catherine", "おはよう", False, False, True, "Catherine専用チャンネル - 全メッセージに応答"),
            ("catherine", "タスク作成して", False, False, True, "Catherine専用チャンネル - 全メッセージに応答"),
            ("一般", "こんにちは", False, False, False, "一般チャンネル - メンションなしは応答なし"),
            ("一般", "Catherine ヘルプ", False, False, True, "一般チャンネル - Catherine言及で応答"),
            ("一般", "@catherine タスク", False, True, True, "一般チャンネル - Bot言及で応答"),
            ("suzunebrain", "こんにちは", False, False, False, "suzunebrainチャンネル - メンションなしは応答なし"),
            ("suzunebrain", "Catherine お疲れさま", False, False, True, "suzunebrainチャンネル - Catherine言及で応答"),
            ("rules", "ルール確認", False, False, False, "許可されていないチャンネル"),
            ("rules", "@catherine ヘルプ", False, True, False, "許可されていないチャンネル - メンションでも応答なし"),
            (None, "DMメッセージ", True, False, True, "DM - 常に応答"),
        ]
        
        print("Channel Name     | Content           | Expected | Actual | Result")
        print("-" * 65)
        
        all_passed = True
        
        for channel_name, content, is_dm, mentions_bot, expected_respond, description in real_test_cases:
            message = create_mock_message(channel_name, content, is_dm, mentions_bot)
            
            actual_respond = should_respond_to_message(message)
            test_passed = actual_respond == expected_respond
            all_passed = all_passed and test_passed
            
            status = "OK" if test_passed else "FAIL"
            channel_display = channel_name or "DM"
            
            print(f"{channel_display:<16} | {content[:17]:<17} | {expected_respond!s:<8} | {actual_respond!s:<6} | {status}")
            
            if not test_passed:
                print(f"  -> {description}")
                print(f"     Expected: {expected_respond}, Actual: {actual_respond}")
        
        print("-" * 65)
        
        if all_passed:
            print("✅ All real channel tests passed!")
        else:
            print("❌ Some tests failed")
            
    except Exception as e:
        print(f"ERROR testing channel utils: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nCurrent Behavior:")
    print("=" * 30)
    print("✅ Catherine responds to ALL messages in:")
    print("   - #catherine")
    print("   - DM")
    print("")
    print("⚠️ Catherine responds ONLY when mentioned in:")
    print("   - #一般")
    print("   - #suzunebrain")
    print("")
    print("🚫 Catherine does NOT respond in:")
    print("   - #rules, #moderator-only, #links, etc.")

if __name__ == "__main__":
    test_real_channels()