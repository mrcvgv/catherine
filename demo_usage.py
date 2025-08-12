#!/usr/bin/env python3
"""
Firebase ToDo Enhanced システムの使用例
こうへいの指定した仕様に完全準拠した動作デモ
"""

import asyncio
from firebase_todo_enhanced import FirebaseTodoEnhanced

async def demo_kouhei_style():
    """こうへいスタイルのTODO操作デモ"""
    print("🚀 Firebase ToDo Enhanced - こうへい仕様デモ")
    print("=" * 60)
    
    todo = FirebaseTodoEnhanced()
    user_id = "kouhei"
    channel_id = "general_channel"
    
    # 1. TODO追加（こうへいの自然な言い回し）
    print("\n📝 【Step 1】 TODOを追加")
    add_commands = [
        "todo add 「ロンT制作」 明日18時 high #CCT",
        "明後日までにDUBさんのポートレート下描き、私にアサインして #CCT", 
        "「学習レポート」来月1日 9:00 なるはや",
        "今夜までにミーティング資料",
        "「CCTウェブ更新」来週月曜 #CCT #web"
    ]
    
    for i, cmd in enumerate(add_commands, 1):
        print(f"\n[{i}] {cmd}")
        result = await todo.process_message(cmd, user_id, channel_id, f"msg_{i}")
        print(f"    → {result.get('message', 'エラー')[:80]}...")
        await asyncio.sleep(0.2)
    
    # 2. リスト表示
    print("\n\n📋 【Step 2】 リスト表示（番号付き）")
    list_result = await todo.process_message("todo list", user_id, channel_id, "msg_list")
    print(list_result.get('message', ''))
    
    # 3. こうへいスタイルの番号指定操作
    print("\n\n🎯 【Step 3】 こうへいスタイルの操作")
    
    # 番号指定完了（ポストアクション付き）
    print("\n▶️ 番号指定完了:")
    complete_result = await todo.process_message("1,3 完了", user_id, channel_id, "msg_complete")
    print(complete_result.get('message', ''))
    
    # 番号指定削除（確認→実行→ポストアクション）
    print("\n▶️ 番号指定削除:")
    delete_result = await todo.process_message("2は消しといて", user_id, channel_id, "msg_delete")
    print(delete_result.get('message', ''))
    
    # 確認に「はい」で答える
    if delete_result.get('pending_action'):
        print("\n▶️ 確認に「はい」:")
        confirm_result = await todo.execute_pending_delete(
            delete_result['pending_action']['indices'], 
            user_id, 
            channel_id
        )
        print(confirm_result.get('message', ''))
    
    # 4. 全角数字や範囲指定のテスト
    print("\n\n🌏 【Step 4】 全角・範囲指定テスト")
    
    # 先にもう少しTODOを追加
    more_todos = [
        "「テスト1」今日",
        "「テスト2」明日", 
        "「テスト3」明後日"
    ]
    
    for cmd in more_todos:
        await todo.process_message(cmd, user_id, channel_id, f"test_{cmd}")
        await asyncio.sleep(0.1)
    
    # 最新リスト
    list_result2 = await todo.process_message("todo list", user_id, channel_id, "msg_list2")
    print(list_result2.get('message', ''))
    
    # 全角数字での操作
    print("\n▶️ 全角数字での操作:")
    fullwidth_result = await todo.process_message("１と３けして", user_id, channel_id, "msg_fullwidth")
    print(fullwidth_result.get('message', ''))
    
    # 範囲指定
    print("\n▶️ 範囲指定:")
    range_result = await todo.process_message("1〜2完了", user_id, channel_id, "msg_range")
    print(range_result.get('message', ''))
    
    print("\n" + "=" * 60)
    print("🎉 デモ完了！")
    print("\n💡 **対応パターン:**")
    print("  • 1,3,5は消しといて")
    print("  • 2と4完了")  
    print("  • 1-3削除 / 1〜3")
    print("  • １，３ 完了（全角）")
    print("  • 全部消して")
    print("  • 最初の3つ / 上から2個")
    print("  • 削除→確認→はい/いいえ")
    print("  • ポストアクション：操作後に自動で最新リスト表示")

def test_number_parser_kouhei():
    """こうへい仕様の番号パーサーテスト"""
    from todo_nlu_enhanced import NumberParser
    
    print("\n🧪 こうへい仕様の番号パーサーテスト")
    print("-" * 50)
    
    test_cases = [
        ("1,3,5は消しといて", 10),
        ("2と4完了", 10),
        ("1-3削除", 10),
        ("１，３ 完了", 10),
        ("全部消して", 5),
        ("最初の3つ", 10),
        ("最後のやつ", 8),
        ("上から2個", 10),
        ("No.2とNo.4", 10),
        ("1〜3けして", 10),
        ("２～５済み", 10),
    ]
    
    for text, max_idx in test_cases:
        indices = NumberParser.parse_indices(text, max_idx)
        print(f"'{text}' (max={max_idx}) → {indices}")

if __name__ == "__main__":
    # 番号パーサーのテスト
    test_number_parser_kouhei()
    
    # メインデモ（Firebase必要）
    try:
        print("\n🔥 Firebase接続確認中...")
        asyncio.run(demo_kouhei_style())
    except Exception as e:
        print(f"\n⚠️ Firebase接続エラー: {e}")
        print("Firebase設定を確認してください。")
        print("設定方法: firebase-adminsdk-*.json ファイルを配置するか")
        print("環境変数 FIREBASE_SERVICE_ACCOUNT_KEY を設定してください。")