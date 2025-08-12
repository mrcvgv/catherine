#!/usr/bin/env python3
"""
Firebase ToDo Enhanced 統合パッチ
enhanced_main_v2.py の TODO処理部分を置き換えるコード

使い方:
1. enhanced_main_v2.py の 446行目付近の以下の部分を見つける:
   # 📋 高度TODOシステム - 本格的なTODO機能
   elif is_todo_command and ADVANCED_TODO_AVAILABLE:

2. その部分全体（try-except ブロック含む）を以下のコードで置き換える
"""

# ============= ここから置き換え開始 =============

        # 📋 Firebase強化版TODOシステム - 番号指定削除/完了対応
        elif is_todo_command and FIREBASE_TODO_AVAILABLE:
            try:
                print(f"[FIREBASE_TODO_ENHANCED] Processing: {command_text}")
                
                # Firebase強化版TODOで処理
                result = await firebase_todo.process_message(
                    message_text=command_text,
                    user_id=user_id,
                    channel_id=str(message.channel.id),
                    message_id=str(message.id)
                )
                
                # レスポンス構築
                response = result.get('message', '')
                
                # 提案がある場合は追加
                if result.get('suggestions'):
                    response += "\n\n💡 **候補:**"
                    for suggestion in result['suggestions']:
                        response += f"\n• {suggestion}"
                
                # 返信
                bot_message = await message.channel.send(response)
                
                # 確認待ちアクションを保存（削除/完了の確認用）
                if result.get('pending_action'):
                    # 一時的に message の属性として保存
                    message.pending_todo_action = result['pending_action']
                
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
                
            except Exception as e:
                print(f"[ERROR] Firebase Todo Enhanced error: {e}")
                import traceback
                traceback.print_exc()
                
                # フォールバック: 高度TODOシステム
                if ADVANCED_TODO_AVAILABLE:
                    try:
                        response = await advanced_todo.process_message(message, user_id)
                    except:
                        response = f"❌ TODOシステムエラー: {str(e)}"
                else:
                    # フォールバック: シンプルTODO
                    try:
                        if simple_todo and 'list' in command_text.lower():
                            response = simple_todo.list_todos(user_id)
                        elif simple_todo:
                            todo_content = command_text.replace('todo', '').strip()
                            if todo_content:
                                response = simple_todo.add_todo(todo_content, user_id)
                            else:
                                response = "📋 TODOの内容を教えてください。"
                        else:
                            response = f"❌ TODOシステムエラー: {str(e)}"
                    except:
                        response = f"❌ TODOシステムエラー: {str(e)}"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
        
        # 📋 高度TODOシステム - 本格的なTODO機能（Firebase利用不可時のフォールバック）
        elif is_todo_command and ADVANCED_TODO_AVAILABLE and not FIREBASE_TODO_AVAILABLE:
            try:
                print(f"[ADVANCED_TODO] Processing: {command_text}")
                
                # 高度TODOシステムで処理
                response = await advanced_todo.process_message(message, user_id)
                
                if response:
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
                else:
                    # フォールバック処理
                    response = "❌ TODO処理でエラーが発生しました。"
                
            except Exception as e:
                print(f"[ERROR] Advanced TODO error: {e}")
                import traceback
                traceback.print_exc()
                
                # フォールバック: シンプルTODO
                try:
                    if simple_todo and 'list' in command_text.lower():
                        response = simple_todo.list_todos(user_id)
                    elif simple_todo:
                        todo_content = command_text.replace('todo', '').strip()
                        if todo_content:
                            response = simple_todo.add_todo(todo_content, user_id)
                        else:
                            response = "📋 TODOの内容を教えてください。"
                    else:
                        response = f"❌ 高度TODOシステムエラー: {str(e)}"
                except:
                    response = f"❌ TODOシステムエラー: {str(e)}"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return

# ============= ここまで置き換え =============


# ============= 確認待ち処理用の追加関数 =============
"""
また、以下のコードを on_message 関数の中に追加してください（"はい"/"いいえ"の確認処理用）:

# 確認待ちアクションがある場合の処理
if hasattr(message, 'in_reply_to') and message.in_reply_to:
    # 返信先メッセージから pending_todo_action を取得
    try:
        ref_message = await message.channel.fetch_message(message.in_reply_to)
        if hasattr(ref_message, 'pending_todo_action'):
            pending = ref_message.pending_todo_action
            
            # はい/いいえの確認
            if command_text.lower() in ['はい', 'yes', 'y', 'ok']:
                if pending['type'] == 'bulk_delete':
                    result = await firebase_todo.execute_pending_delete(
                        pending['indices'], user_id, str(message.channel.id)
                    )
                    response = result['message']
                elif pending['type'] == 'bulk_complete':
                    # 複数完了実行（確認必要だった場合）
                    for idx in pending['indices']:
                        if 1 <= idx <= len(firebase_todo.last_listed_todos):
                            todo = firebase_todo.last_listed_todos[idx-1]
                            firebase_todo.db.collection(firebase_todo.collection_name).document(
                                todo.id
                            ).update({
                                'status': 'done',
                                'updated_at': datetime.now(JST),
                                'completed_at': datetime.now(JST)
                            })
                    # ポストアクション付きレスポンス
                    completed_nums = [f"#{i}" for i in pending['indices']]
                    response = f"✅ 完了: {', '.join(completed_nums)}（{len(pending['indices'])}件）"
                    updated_list = await firebase_todo._get_updated_list(user_id, str(message.channel.id))
                    if updated_list:
                        response += "\n\n" + updated_list
                    else:
                        response += "\n\n🎉 全部片付きました！"
                elif pending['type'] == 'delete':
                    # 単一削除実行
                    firebase_todo.db.collection(firebase_todo.collection_name).document(
                        pending['todo_id']
                    ).delete()
                    response = f"🗑️ 削除完了: {pending.get('title', pending['todo_id'])}"
                    # 単一削除でもポストアクション
                    updated_list = await firebase_todo._get_updated_list(user_id, str(message.channel.id))
                    if updated_list:
                        response += "\n\n" + updated_list
                    else:
                        response += "\n\n🎉 全部片付きました！"
                else:
                    response = "処理を実行しました。"
            else:
                response = "❌ キャンセルしました。"
            
            bot_message = await message.channel.send(response)
            return
    except:
        pass
"""