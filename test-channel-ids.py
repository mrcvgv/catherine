#!/usr/bin/env python3

"""
Discord URLで指定されたチャンネルIDでのテスト
"""

import os
import sys
from unittest.mock import Mock
import io

# UTF-8エンコーディング
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_channel_ids():
    """Discord URLで指定されたチャンネルIDでテスト"""
    
    print("Testing with Discord Channel IDs from URLs")
    print("==========================================")
    
    # .envから読み込み
    from dotenv import load_dotenv
    load_dotenv()
    
    # constants.pyの読み込みテスト
    try:
        from src.constants import ALLOWED_CHANNEL_IDS, CATHERINE_CHANNEL_IDS
        print(f"Loaded channel ID constants:")
        print(f"  ALLOWED_CHANNEL_IDS: {ALLOWED_CHANNEL_IDS}")
        print(f"  CATHERINE_CHANNEL_IDS: {CATHERINE_CHANNEL_IDS}")
    except Exception as e:
        print(f"ERROR loading constants: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nChannel ID Test:")
    print("=" * 60)
    
    try:
        from src.channel_utils import is_allowed_channel, is_catherine_channel, should_respond_to_message
        
        # Mock Discordメッセージ作成（チャンネルID使用）
        def create_mock_message(channel_id, channel_name, content="Hello", is_dm=False, mentions_bot=False):
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
                message.channel.id = channel_id
                message.channel.name = channel_name
                
            if mentions_bot:
                bot_user = Mock()
                bot_user.bot = True
                message.mentions = [bot_user]
                
            return message
        
        # URLから抽出したチャンネルIDでテストケース作成
        test_cases = [
            # (channel_id, channel_name, content, is_dm, mentions_bot, expected_respond, description)
            
            # @mention only channels (Discord URLで指定)
            (1401831166117544043, "一般", "こんにちは", False, False, False, "@mention only - 言及なし"),
            (1401831166117544043, "一般", "Catherine ヘルプ", False, False, True, "@mention only - Catherine言及"),
            (1401831166117544043, "一般", "@catherine タスク", False, True, True, "@mention only - Bot言及"),
            
            (1404390881326268476, "suzunebrain", "プログラミング", False, False, False, "@mention only - 言及なし"),
            (1404390881326268476, "suzunebrain", "Catherine 質問", False, False, True, "@mention only - Catherine言及"),
            
            (1404452180416532550, "25aw商品ライン", "商品情報", False, False, False, "@mention only - 言及なし"),
            (1404452180416532550, "25aw商品ライン", "@catherine 商品", False, True, True, "@mention only - Bot言及"),
            
            (1406820023913287750, "links", "リンク共有", False, False, False, "@mention only - 言及なし"),
            (1406820023913287750, "links", "Catherine リンク", False, False, True, "@mention only - Catherine言及"),
            
            (1408842599955169341, "データ確認", "データ処理", False, False, False, "@mention only - 言及なし"),
            (1408842599955169341, "データ確認", "Catherine データ", False, False, True, "@mention only - Catherine言及"),
            
            # All messages channel (Discord URLで指定)
            (1401958031788478526, "catherine", "おはよう", False, False, True, "All messages - 常に応答"),
            (1401958031788478526, "catherine", "タスク作成", False, False, True, "All messages - 常に応答"),
            (1401958031788478526, "catherine", "普通の会話", False, False, True, "All messages - 常に応答"),
            
            # Non-allowed channel
            (9999999999999999999, "unknown", "Hello", False, False, False, "許可されていないチャンネル"),
            (9999999999999999999, "unknown", "@catherine help", False, True, False, "許可されていないチャンネル - メンションでも無応答"),
            
            # DM
            (None, None, "DMメッセージ", True, False, True, "DM - 常に応答"),
        ]
        
        print("Channel ID       | Channel Name     | Content          | Expected | Actual | Result")
        print("-" * 85)
        
        all_passed = True
        
        for channel_id, channel_name, content, is_dm, mentions_bot, expected_respond, description in test_cases:
            message = create_mock_message(channel_id, channel_name, content, is_dm, mentions_bot)
            
            actual_respond = should_respond_to_message(message)
            test_passed = actual_respond == expected_respond
            all_passed = all_passed and test_passed
            
            status = "OK" if test_passed else "FAIL"
            
            # Display formatting
            channel_id_display = str(channel_id)[:16] if channel_id else "DM"
            channel_name_display = (channel_name or "")[:16]
            content_display = content[:16]
            
            print(f"{channel_id_display:<16} | {channel_name_display:<16} | {content_display:<16} | {expected_respond!s:<8} | {actual_respond!s:<6} | {status}")
            
            if not test_passed:
                print(f"  -> {description}")
                print(f"     Expected: {expected_respond}, Actual: {actual_respond}")
        
        print("-" * 85)
        
        if all_passed:
            print("✅ All channel ID tests passed!")
        else:
            print("❌ Some tests failed")
            
    except Exception as e:
        print(f"ERROR testing channel utils: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nFinal Configuration:")
    print("=" * 30)
    print("✅ Catherine responds to ALL messages in:")
    print("   - Channel ID 1401958031788478526 (#catherine)")
    print("   - DM")
    print("")
    print("⚠️ Catherine responds ONLY when mentioned in:")
    print("   - Channel ID 1401831166117544043 (一般)")
    print("   - Channel ID 1404390881326268476 (suzunebrain)")
    print("   - Channel ID 1404452180416532550 (25aw商品ライン)")
    print("   - Channel ID 1406820023913287750 (links)")
    print("   - Channel ID 1408842599955169341 (データ確認)")
    print("")
    print("🚫 Catherine does NOT respond in other channels")

if __name__ == "__main__":
    test_channel_ids()