#!/usr/bin/env python3
"""
Final Demo - こうへい最終仕様完全実装
- 番号指定削除/完了 + ポストアクション
- 自然文リマインド + 宛先確認フロー
- 毎朝8:00定期通知
"""

import asyncio
from datetime import datetime, timedelta
from firebase_todo_enhanced import FirebaseTodoEnhanced

async def demo_kouhei_final_spec():
    """こうへい最終仕様の完全デモ"""
    print("🚀 Firebase ToDo Enhanced - こうへい最終仕様デモ")
    print("=" * 80)
    
    todo_system = FirebaseTodoEnhanced()
    user_id = "kouhei"
    channel_id = "general"
    
    # ====== Phase 1: TODO基本操作 ======
    print("\n📝 【Phase 1】 TODO基本操作")
    print("-" * 50)
    
    todos_to_add = [
        "todo add 「ロンT制作」 明日18時 high #CCT",
        "todo add 「DUBポートレート下描き」 明後日17時 urgent #CCT", 
        "todo add 「学習レポート」 来月1日9時 normal #学習",
        "todo add 「ミーティング資料」 今夜20時 high #work",
        "todo add 「CCTウェブ更新」 来週月曜12時 normal #CCT"
    ]
    
    for i, cmd in enumerate(todos_to_add, 1):
        print(f"\n[{i}] {cmd}")
        result = await todo_system.process_message(cmd, user_id, channel_id, f"add_{i}")
        print(f"    → {result.get('message', 'エラー')[:100]}...")
        await asyncio.sleep(0.1)
    
    # リスト表示
    print("\n\n📋 【Phase 2】 リスト表示（番号付き）")
    print("-" * 50)
    list_result = await todo_system.process_message("todo list", user_id, channel_id, "list_1")
    print(list_result.get('message', ''))
    
    # ====== Phase 2: 番号指定操作（ポストアクション確認） ======
    print("\n\n🎯 【Phase 3】 番号指定操作 + ポストアクション")
    print("-" * 50)
    
    print("\n▶️ 1. 番号指定完了（1,3 完了）:")
    complete_result = await todo_system.process_message("1,3 完了", user_id, channel_id, "complete_1")
    print(complete_result.get('message', ''))
    
    print("\n▶️ 2. 範囲指定完了（4〜5済み）:")
    range_result = await todo_system.process_message("4〜5済み", user_id, channel_id, "range_1")
    print(range_result.get('message', ''))
    
    # 追加でTODOを入れる
    await todo_system.process_message("todo add 「テスト1」今日", user_id, channel_id, "test1")
    await todo_system.process_message("todo add 「テスト2」明日", user_id, channel_id, "test2")
    
    # リスト再表示
    list_result2 = await todo_system.process_message("todo list", user_id, channel_id, "list_2")
    print(f"\n📋 現在のリスト:\n{list_result2.get('message', '')}")
    
    print("\n▶️ 3. 削除操作（確認→実行→ポストアクション）:")
    delete_result = await todo_system.process_message("1は消しといて", user_id, channel_id, "delete_1")
    print(delete_result.get('message', ''))
    
    # 確認に「はい」
    if 'confirm' in delete_result.get('response_type', ''):
        print("\n▶️ 4. 確認に「はい」:")
        confirm_result = await todo_system.process_message("はい", user_id, channel_id, "confirm_1")
        print(confirm_result.get('message', ''))
    
    # ====== Phase 3: リマインド機能 ======
    print("\n\n⏰【Phase 4】 リマインド機能")
    print("-" * 50)
    
    reminder_tests = [
        ("18:30に@mrcで『在庫チェック』リマインド", "完全指定リマインド"),
        ("明日9:00に会議リマインド", "宛先未指定（確認フロー）"),
        ("8/15 18:00にみんなで締切のお知らせ", "日付指定リマインド"),
        ("月曜日の朝9時にミーティング通知", "相対日時リマインド"),
    ]
    
    for cmd, desc in reminder_tests:
        print(f"\n▶️ {desc}:")
        print(f"入力: {cmd}")
        result = await todo_system.process_message(cmd, user_id, channel_id, f"remind_{cmd[:10]}")
        print(f"結果: {result.get('message', 'エラー')}")
        
        # 宛先未指定の確認フローテスト
        if result.get('response_type') == 'reminder_mention_needed':
            print("  → 確認フロー発動。「はい」で@everyone設定:")
            confirm_result = await todo_system.process_message("はい", user_id, channel_id, "remind_confirm")
            print(f"  → {confirm_result.get('message', '')}")
        
        await asyncio.sleep(0.2)
    
    # ====== Phase 4: 毎朝8:00機能のデモ ======
    print("\n\n🌅 【Phase 5】 毎朝8:00定期通知デモ")
    print("-" * 50)
    
    # 今日の予定を取得
    today = datetime.now().date()
    daily_schedule = await todo_system.get_daily_todos_and_reminders(today, channel_id)
    print("今日の予定（8:00に@everyoneで自動送信される内容）:")
    print(daily_schedule)
    
    # 明日の予定も確認
    tomorrow = today + timedelta(days=1)
    tomorrow_schedule = await todo_system.get_daily_todos_and_reminders(tomorrow, channel_id)
    print(f"\n明日({tomorrow.strftime('%m/%d')})の予定:")
    print(tomorrow_schedule)
    
    # ====== Phase 5: 各種パターンテスト ======
    print("\n\n🧪 【Phase 6】 こうへいパターン完全テスト")
    print("-" * 50)
    
    pattern_tests = [
        ("１，３は消しといて", "全角数字"),
        ("2と4完了", "「と」区切り"),
        ("全部けして", "一括削除"),
        ("最初の2つ完了", "相対指定"),
    ]
    
    # テスト用に少しTODO追加
    for i in range(5):
        await todo_system.process_message(f"todo add 「パターンテスト{i+1}」今日", 
                                        user_id, channel_id, f"pattern_{i}")
    
    # 最新リスト
    pattern_list = await todo_system.process_message("todo list", user_id, channel_id, "pattern_list")
    print("パターンテスト用リスト:")
    print(pattern_list.get('message', ''))
    
    for cmd, desc in pattern_tests:
        print(f"\n▶️ {desc}: {cmd}")
        result = await todo_system.process_message(cmd, user_id, channel_id, f"pattern_{desc}")
        
        # 確認が必要な場合は自動で「はい」
        if 'confirm' in result.get('response_type', ''):
            print("  → 確認フロー: はい")
            result = await todo_system.process_message("はい", user_id, channel_id, "auto_confirm")
        
        print(f"  結果: {result.get('message', '')[:200]}...")
        await asyncio.sleep(0.3)
    
    print("\n" + "=" * 80)
    print("🎉 こうへい最終仕様デモ完了！")
    print("\n✅ **実装完了機能:**")
    print("  📋 番号指定削除・完了（1,3,5 / 1-3 / １〜３）")
    print("  🔄 ポストアクション（操作後に最新リスト自動表示）")
    print("  ⏰ 自然文リマインド（@everyone/@mrc/@supy対応）")
    print("  ❓ 宛先未指定時の確認フロー")
    print("  🌅 毎朝8:00定期予定通知（TODO+リマインド統合）")
    print("  🧠 全角半角・範囲指定の自動正規化")
    print("  🔒 確認プロンプト付き破壊的操作")
    print("  📊 Firebase永続化 + 監査ログ")

def test_number_parser_final():
    """最終版番号パーサーテスト"""
    from todo_nlu_enhanced import NumberParser
    
    print("\n🔢 最終版番号パーサーテスト")
    print("-" * 40)
    
    test_cases = [
        ("1,3,5は消しといて", 10),
        ("2と4完了", 10),
        ("1-3削除", 10),
        ("１，３ 完了", 10),  # 全角
        ("全部消して", 5),
        ("最初の3つ", 10),
        ("最後のやつ", 8),
        ("上から2個", 10),
        ("No.2とNo.4", 10),
        ("1〜3けして", 10),  # 波ダッシュ
        ("２～５済み", 10),  # 全角波ダッシュ
        ("1 と 3 と 5", 10),  # スペース区切り
        ("1,2,3,4,5,6,7,8,9,10", 10),  # 全指定
    ]
    
    for text, max_idx in test_cases:
        indices = NumberParser.parse_indices(text, max_idx)
        print(f"'{text}' (max={max_idx}) → {indices}")

def test_reminder_parsing():
    """リマインドパーサーテスト"""
    from discord_reminder_system import ReminderSystem
    
    print("\n⏰ リマインドパーサーテスト")
    print("-" * 40)
    
    reminder_system = ReminderSystem()
    
    test_cases = [
        "18:30に@mrcで『在庫チェック』リマインド",
        "明日9:00に会議リマインド",
        "8/15 18:00にみんなで締切のお知らせ",
        "月曜日の朝9時にミーティング通知",
        "今夜8時に@supyで作業完了確認",
        "11日にプレゼン準備リマインド",
        "8月15日午後2時に@everyoneで定例会議",
    ]
    
    for test in test_cases:
        result = reminder_system.parse_reminder_text(test)
        print(f"\n入力: {test}")
        print(f"  メッセージ: {result['message']}")
        print(f"  時刻: {result['remind_at']}")
        print(f"  宛先: {result['mentions']}")
        print(f"  確度: {result['confidence']:.2f}")
        if result['error']:
            print(f"  エラー: {result['error']['message']}")

if __name__ == "__main__":
    print("🧪 こうへい最終仕様 - 全機能テスト")
    
    # パーサーテスト
    test_number_parser_final()
    test_reminder_parsing()
    
    # メインデモ
    try:
        print("\n🔥 Firebase接続してフルデモ実行...")
        asyncio.run(demo_kouhei_final_spec())
    except Exception as e:
        print(f"\n⚠️ Firebase接続エラー: {e}")
        print("Firebase設定確認:")
        print("1. firebase-adminsdk-*.json ファイルを配置")
        print("2. または環境変数 FIREBASE_SERVICE_ACCOUNT_KEY を設定")
        print("3. Firestoreでコレクション作成権限を確認")