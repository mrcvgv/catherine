#!/usr/bin/env python3
"""
Firebase ToDo Enhanced システムのテストコード
番号指定削除・完了機能をテスト
"""

import asyncio
from firebase_todo_enhanced import FirebaseTodoEnhanced

async def test_todo_system():
    """TODOシステムのテスト"""
    print("=" * 60)
    print("Firebase ToDo Enhanced システムテスト")
    print("=" * 60)
    
    todo = FirebaseTodoEnhanced()
    user_id = "test_user_123"
    channel_id = "test_channel_456"
    
    # テストケース
    test_cases = [
        # 1. TODO追加
        ("todo add 「ロンT制作」 明日18時 high #CCT", "TODO追加テスト"),
        ("明後日までにDUBさんのポートレート下描き、私にアサインして #CCT", "自然言語追加"),
        ("「学習レポート」来月1日 9:00 なるはや", "優先度付き追加"),
        ("今夜までにミーティング資料", "今夜期限のタスク"),
        ("「CCTウェブ更新」来週月曜 #CCT #web", "複数タグ"),
        
        # 2. TODO一覧表示
        ("todo list", "一覧表示"),
        
        # 3. 番号指定での完了
        ("1,3 完了", "番号指定完了（カンマ区切り）"),
        ("2-4 済み", "範囲指定完了"),
        
        # 4. 番号指定での削除
        ("1,2 削除", "番号指定削除（確認必要）"),
        ("全部消して", "全削除（確認必要）"),
        
        # 5. 自然言語での操作
        ("最初の2つ完了", "自然言語番号指定"),
        ("１と３けして", "全角数字削除"),
        
        # 6. タグ検索
        ("todo list #CCT", "タグフィルタ"),
        
        # 7. 優先度フィルタ
        ("todo list high", "優先度フィルタ"),
    ]
    
    print("\n📝 テスト開始")
    print("-" * 60)
    
    for i, (command, description) in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {description}")
        print(f"Input: {command}")
        
        try:
            result = await todo.process_message(
                message_text=command,
                user_id=user_id,
                channel_id=channel_id,
                message_id=f"test_msg_{i}"
            )
            
            print(f"Success: {result.get('success', False)}")
            print(f"Response: {result.get('message', '')[:200]}")
            
            if result.get('target_indices'):
                print(f"Target indices: {result['target_indices']}")
            
            if result.get('suggestions'):
                print(f"Suggestions: {result['suggestions'][:3]}")
            
            if result.get('pending_action'):
                print(f"⚠️ 確認待ち: {result['pending_action']['type']}")
                
                # 確認に「はい」と答える場合のシミュレーション
                if result['pending_action']['type'] == 'bulk_delete':
                    print("  → 「はい」で削除実行をシミュレート")
                    delete_result = await todo.execute_pending_delete(
                        result['pending_action']['indices'],
                        user_id
                    )
                    print(f"  削除結果: {delete_result.get('message', '')[:100]}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 少し待機
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

def test_number_parser():
    """番号パーサーのテスト"""
    from todo_nlu_enhanced import NumberParser
    
    print("\n📊 番号パーサーテスト")
    print("-" * 60)
    
    parser = NumberParser()
    
    test_inputs = [
        ("1,3,5は消しといて", 10),
        ("２と４完了", 10),
        ("1-3削除", 10),
        ("１，３ 完了", 10),
        ("全部消して", 10),
        ("最初の3つ", 10),
        ("最後のやつ", 10),
        ("上から2個", 10),
        ("1,2,3,4,5,6,7,8,9,10", 10),
        ("1-100", 10),  # 上限を超える
        ("No.2とNo.4", 10),
    ]
    
    for text, max_idx in test_inputs:
        normalized = parser.normalize_text(text)
        indices = parser.parse_indices(text, max_idx)
        print(f"Input: {text}")
        print(f"  Normalized: {normalized}")
        print(f"  Indices: {indices}")
        print()

def test_date_parser():
    """日時パーサーのテスト"""
    from todo_nlu_enhanced import RelativeDateParser
    from datetime import datetime
    
    print("\n📅 日時パーサーテスト")
    print("-" * 60)
    
    parser = RelativeDateParser()
    
    test_inputs = [
        "今日",
        "明日",
        "明後日",
        "今夜",
        "明日18時",
        "来週月曜",
        "来月1日 9:00",
        "8/20 21:00",
        "明後日朝9時",
        "再来週水曜",
        "3日後",
    ]
    
    for text in test_inputs:
        result = parser.parse(text)
        if result:
            print(f"Input: {text}")
            print(f"  Result: {result.strftime('%Y-%m-%d %H:%M %Z')}")
        else:
            print(f"Input: {text} -> Parse failed")
        print()

if __name__ == "__main__":
    print("テストを実行します...\n")
    
    # 番号パーサーテスト
    test_number_parser()
    
    # 日時パーサーテスト
    test_date_parser()
    
    # メインのTODOシステムテスト
    # 注意: Firebaseが設定されている必要があります
    try:
        asyncio.run(test_todo_system())
    except Exception as e:
        print(f"\n⚠️ Firebase接続エラー: {e}")
        print("Firebase設定を確認してください。")