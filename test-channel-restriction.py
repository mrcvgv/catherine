#!/usr/bin/env python3

"""
Catherine チャンネル制限機能テスト
環境変数とチャンネル制御ロジックをテスト
"""

import os
import sys
from unittest.mock import Mock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_channel_restriction():
    """チャンネル制限機能をテスト"""
    
    print("Testing Catherine Channel Restriction")
    print("=====================================")
    
    # 環境変数設定をテスト
    print("\nEnvironment Variables Test:")
    print("=" * 40)
    
    # .envから読み込み
    from dotenv import load_dotenv
    load_dotenv()
    
    allowed_channels = os.getenv("ALLOWED_CHANNEL_NAMES", "catherine,todo,general")
    catherine_channels = os.getenv("CATHERINE_CHANNELS", "catherine")
    
    print(f"ALLOWED_CHANNEL_NAMES: {allowed_channels}")
    print(f"CATHERINE_CHANNELS: {catherine_channels}")
    
    # constants.pyの読み込みテスト
    try:
        from src.constants import ALLOWED_CHANNEL_NAMES, CATHERINE_CHANNELS
        print(f"OK Constants loaded successfully")
        print(f"   ALLOWED_CHANNEL_NAMES: {ALLOWED_CHANNEL_NAMES}")
        print(f"   CATHERINE_CHANNELS: {CATHERINE_CHANNELS}")
    except Exception as e:
        print(f"ERROR loading constants: {e}")
        return
    
    # チャンネルユーティリティのテスト
    print("\nChannel Utils Test:")
    print("=" * 40)
    
    try:
        from src.channel_utils import is_allowed_channel, is_catherine_channel, should_respond_to_message
        
        # Mock Discordメッセージ作成
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
        
        # テストケース
        test_cases = [
            # (channel_name, content, is_dm, mentions_bot, expected_allowed, expected_catherine, expected_respond)
            ("catherine", "Hello", False, False, True, True, True),           # Catherine専用チャンネル - 全メッセージに応答
            ("catherine", "普通の会話", False, False, True, True, True),        # Catherine専用チャンネル - 言及なしでも応答
            ("todo", "Create task", False, False, True, False, False),         # 許可チャンネル - 言及なしは応答なし
            ("todo", "Catherine help me", False, False, True, False, True),    # 許可チャンネル + Catherine言及
            ("general", "Hello everyone", False, False, True, False, False),   # 一般チャンネル - 言及なしは応答なし
            ("general", "@catherine help", False, True, True, False, True),    # 一般チャンネル + Bot言及
            ("random", "Hello", False, False, False, False, False),            # 非許可チャンネル
            (None, "DM message", True, False, True, True, True),               # DM - 常に応答
        ]
        
        print("Channel Test Results:")
        print("-" * 60)
        print("Channel      | Content           | Allowed | Catherine | Respond")
        print("-" * 60)
        
        all_passed = True
        
        for channel_name, content, is_dm, mentions_bot, expected_allowed, expected_catherine, expected_respond in test_cases:
            message = create_mock_message(channel_name, content, is_dm, mentions_bot)
            
            actual_allowed = is_allowed_channel(message)
            actual_catherine = is_catherine_channel(message)
            actual_respond = should_respond_to_message(message)
            
            # 結果チェック
            allowed_ok = actual_allowed == expected_allowed
            catherine_ok = actual_catherine == expected_catherine
            respond_ok = actual_respond == expected_respond
            
            test_passed = allowed_ok and catherine_ok and respond_ok
            all_passed = all_passed and test_passed
            
            status = "OK" if test_passed else "FAIL"
            channel_display = channel_name or "DM"
            
            print(f"{channel_display:<12} | {content:<17} | {actual_allowed!s:<7} | {actual_catherine!s:<9} | {actual_respond!s:<7} {status}")
            
            if not test_passed:
                print(f"  Expected: allowed={expected_allowed}, catherine={expected_catherine}, respond={expected_respond}")
                print(f"  Actual:   allowed={actual_allowed}, catherine={actual_catherine}, respond={actual_respond}")
        
        print("-" * 60)
        
        if all_passed:
            print("All channel restriction tests passed!")
        else:
            print("Some tests failed")
            
    except Exception as e:
        print(f"ERROR testing channel utils: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 実際の動作例
    print("\nUsage Examples:")
    print("=" * 40)
    print("Catherine will respond to ALL messages in:")
    print("   - #catherine channel (all conversations)")
    print("   - DM messages (always)")
    print("")
    print("Catherine will respond ONLY when mentioned in:")
    print("   - Other allowed channels (#todo, #general):")
    print("     * 'Catherine, help me'")
    print("     * '@Catherine bot'")
    print("     * 'Catherine task create'")
    print("")
    print("Catherine will NOT respond in:")
    print("   - Non-allowed channels")
    print("   - Allowed channels without @mention")
    print("")
    print("New Configuration:")
    print("   #catherine: responds to all conversations")
    print("   #todo, #general: responds only when @mentioned")
    print("   others: no response")

if __name__ == "__main__":
    test_channel_restriction()