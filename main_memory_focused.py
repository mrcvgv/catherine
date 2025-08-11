#!/usr/bin/env python3
"""
Catherine AI - 完全記録重視版
全ての行動・会話を詳細に記録し、長期記憶を活用
"""

import os
import asyncio
import discord
from openai import OpenAI
from datetime import datetime
import pytz

# カスタムモジュール
from firebase_config import firebase_manager
from todo_manager import TodoManager
from conversation_manager import ConversationManager
from proactive_assistant import ProactiveAssistant
from emotional_intelligence import EmotionalIntelligence
from prompt_system import PromptSystem
from reminder_system import ReminderSystem

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# AI・データベース初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
todo_manager = TodoManager(openai_client)
conversation_manager = ConversationManager(openai_client)
proactive_assistant = ProactiveAssistant(openai_client)
emotional_intelligence = EmotionalIntelligence(openai_client)
prompt_system = PromptSystem(openai_client)
reminder_system = ReminderSystem(openai_client, client)  # Discordクライアントも渡す
jst = pytz.timezone('Asia/Tokyo')

@client.event
async def on_ready():
    print(f"🧠 Catherine AI - 完全記録版 起動完了")
    print(f"📚 Firebase記録機能: {'✅ 有効' if firebase_manager.is_available() else '❌ 無効'}")
    print(f"👤 ログイン: {client.user}")
    
    # リマインダーシステムを開始
    await reminder_system.start_reminder_scheduler()
    print(f"🔔 リマインダーシステム起動完了")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    # 二重実行防止（グローバル変数使用）
    if not hasattr(process_command_with_memory, '_processed_messages'):
        process_command_with_memory._processed_messages = set()
    
    message_key = f"{message.id}_{message.author.id}"
    if message_key in process_command_with_memory._processed_messages:
        return
    process_command_with_memory._processed_messages.add(message_key)
    
    user_id = str(message.author.id)
    username = message.author.display_name
    
    # ユーザー活動を記録
    await conversation_manager.update_user_activity(user_id, username)
    
    # 全てのメッセージを記録（C!なしでも）
    if not message.content.startswith("C!"):
        # 通常の会話として記録
        await record_casual_conversation(user_id, message.content)
        return
    
    # C!コマンドの処理
    command_text = message.content[2:].strip()
    print(f"📝 [{datetime.now(jst).strftime('%H:%M:%S')}] {username}: {command_text}")
    
    response = None
    try:
        response = await process_command_with_memory(user_id, command_text, message)
        
    except Exception as e:
        response = "Catherine: 申し訳ありません。エラーが発生しました。"
        print(f"❌ エラー: {e}")
    
    # レスポンス送信（1回のみ）
    if response:
        await message.channel.send(response)
        
        # 会話記録
        try:
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response=response,
                command_type=await detect_command_type(command_text)
            )
        except Exception as log_error:
            print(f"⚠️  記録エラー: {log_error}")

async def record_casual_conversation(user_id: str, message_content: str):
    """通常の会話も記録"""
    try:
        # AI分析で重要な情報を抽出
        analysis_result = await analyze_casual_message(message_content)
        
        if analysis_result.get('should_record', True):
            await conversation_manager.log_conversation(
                user_id=user_id,
                user_message=message_content,
                bot_response="(記録のみ)",
                command_type="casual_observation"
            )
            
    except Exception as e:
        print(f"⚠️  通常会話記録エラー: {e}")

async def analyze_casual_message(message: str) -> dict:
    """カジュアルメッセージの分析"""
    try:
        prompt = f"""
        以下のメッセージを分析して、重要な情報があるかチェックしてください：
        「{message}」
        
        JSON形式で返してください：
        {{
            "should_record": true/false,
            "importance": 1-5,
            "contains_personal_info": true/false,
            "contains_todo_hint": true/false,
            "mood": "positive/neutral/negative",
            "topics": ["topic1", "topic2"]
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "メッセージ分析の専門家として客観的に分析してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        import json
        try:
            # ```json ブロックを除去
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error in message analysis: {e}")
            print(f"📄 Raw response: {response.choices[0].message.content}")
            return {"should_record": True, "importance": 3, "parse_error": True}
        
    except Exception as e:
        print(f"❌ メッセージ分析エラー: {e}")
        return {"should_record": True, "importance": 3}

async def process_command_with_memory(user_id: str, command_text: str, message) -> str:
    """記憶を活用したコマンド処理"""
    
    # ユーザーの設定・履歴を取得
    user_prefs = await conversation_manager.get_user_preferences(user_id)
    
    # 基本コマンド処理
    if command_text.lower().startswith("todo"):
        return await handle_todo_with_memory(user_id, command_text, user_prefs)
    elif command_text.lower().startswith("list"):
        print(f"🔍 Listing TODOs for user_id: {user_id}")
        # ソートオプションをチェック
        parts = command_text.lower().split()
        sort_option = parts[1] if len(parts) > 1 else "priority_due"
        
        # ソートオプションに応じて処理
        if sort_option in ["priority", "due", "category", "recent"]:
            return await handle_sorted_list(user_id, sort_option)
        else:
            return await todo_manager.list_todos_formatted(user_id)
    elif command_text.lower().startswith("done"):
        return await handle_done_with_celebration(user_id, command_text)
    elif command_text.lower().startswith("delete") or command_text.lower().startswith("削除"):
        return await handle_todo_delete(user_id, command_text)
    elif command_text.lower().startswith("edit") or command_text.lower().startswith("編集"):
        return await handle_todo_edit(user_id, command_text)
    elif command_text.lower().startswith("rename") or command_text.lower().startswith("リネーム"):
        return await handle_todo_rename(user_id, command_text)
    elif command_text.lower().startswith("clear"):
        return await handle_todo_clear(user_id, command_text)
    elif command_text.lower().startswith("memory"):
        return await handle_memory_command(user_id, command_text)
    elif command_text.lower().startswith("help"):
        return await handle_personalized_help(user_id, user_prefs)
    elif command_text.lower().startswith("remind") or command_text.lower().startswith("リマインダー"):
        return await handle_reminder_command(user_id, command_text)
    else:
        # 自然言語でのToDo操作を検出
        todo_action = await detect_todo_intent(command_text)
        if todo_action:
            return await handle_natural_todo_command(user_id, command_text, todo_action)
        
        # 通常の自然言語会話（構造化レスポンス + 記憶活用 + 感情知能 + 先読み）
        return await handle_structured_conversation(user_id, command_text, user_prefs)

async def detect_todo_intent(command_text: str) -> dict:
    """自然言語からToDo操作の意図を検出"""
    try:
        prompt = f"""
        以下のメッセージからToDo操作の意図を分析してください：
        「{command_text}」
        
        検出すべき操作:
        - delete/削除: 特定のToDoを削除したい（複数番号、範囲、内容での一括削除も含む）
        - edit/編集: ToDoの内容を変更したい
        - clear/全削除: すべてのToDoを削除したい
        - complete/完了: ToDoを完了にしたい
        - list/一覧: ToDoリストを見たい
        - organize/整理: 同じ内容のToDoをまとめる、重複を削除など
        
        特に注意：
        - 「1と2を消して」「1,2,3番削除」→ 複数の番号を検出
        - 「台紙デザインを全部消して」→ 特定のキーワードで一括削除
        - 「重複を整理して」→ organize アクション
        
        JSON形式で返してください：
        {{
            "action": "delete/edit/clear/complete/list/organize/none",
            "target": "対象となるToDo（番号や内容）",
            "multiple_targets": ["複数の対象がある場合のリスト"],
            "new_content": "新しい内容（editの場合）",
            "confidence": 0.0-1.0
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1",  # 最新モデル使用
            messages=[
                {"role": "system", "content": "あなたは極めて高精度でユーザーの意図を理解する専門AIです。複雑な指示も正確に解析してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 理解力重視  
            max_completion_tokens=1000,
            response_format={"type": "json_object"}  # JSON強制モード
        )
        
        import json
        content = response.choices[0].message.content
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(content)
        return result if result.get('confidence', 0) > 0.7 else None
        
    except Exception as e:
        print(f"❌ Intent detection error: {e}")
        return None

async def handle_natural_todo_command(user_id: str, command_text: str, todo_action: dict) -> str:
    """自然言語でのToDo操作処理"""
    action = todo_action.get('action')
    target = todo_action.get('target', '')
    
    # ToDoリストを取得
    todos = await todo_manager.get_user_todos(user_id)
    pending = [t for t in todos if t.get('status') == 'pending']
    
    if action == 'list':
        return await todo_manager.list_todos_formatted(user_id)
    
    elif action == 'delete':
        deleted_todos = []
        
        # 複数ターゲットがある場合
        multiple_targets = todo_action.get('multiple_targets', [])
        if multiple_targets:
            for target_item in multiple_targets:
                # 番号で削除
                try:
                    num = int(target_item.strip())
                    if 1 <= num <= len(pending):
                        todo = pending[num - 1]
                        todo_manager.db.collection('todos').document(todo['todo_id']).delete()
                        deleted_todos.append(todo['title'])
                except:
                    # 内容で削除
                    for todo in pending:
                        if target_item.lower() in todo.get('title', '').lower():
                            todo_manager.db.collection('todos').document(todo['todo_id']).delete()
                            deleted_todos.append(todo['title'])
                            break
        
        # 単一ターゲット処理
        else:
            # キーワードで一括削除（例：「台紙デザイン」関連）
            if '全部' in target or '全て' in target or '関連' in target:
                keyword = target.replace('全部', '').replace('全て', '').replace('関連', '').strip()
                for todo in pending:
                    if keyword.lower() in todo.get('title', '').lower():
                        todo_manager.db.collection('todos').document(todo['todo_id']).delete()
                        deleted_todos.append(todo['title'])
            else:
                # 通常の単一削除
                matched_todo = None
                try:
                    num = int(''.join(filter(str.isdigit, target)))
                    if 1 <= num <= len(pending):
                        matched_todo = pending[num - 1]
                except:
                    pass
                
                if not matched_todo:
                    for todo in pending:
                        if target.lower() in todo.get('title', '').lower():
                            matched_todo = todo
                            break
                
                if matched_todo:
                    todo_manager.db.collection('todos').document(matched_todo['todo_id']).delete()
                    deleted_todos.append(matched_todo['title'])
        
        if deleted_todos:
            if len(deleted_todos) == 1:
                return f"Catherine: ✅ 「{deleted_todos[0]}」を削除しました。\n\n他にも整理したいものがあれば教えてください。"
            else:
                return f"Catherine: ✅ {len(deleted_todos)}件のToDoを削除しました：\n" + "\n".join([f"・{title}" for title in deleted_todos]) + "\n\nリストがすっきりしましたね！"
        else:
            return f"Catherine: 「{target}」に該当するToDoが見つかりませんでした。現在のリストを確認して、正確な指示をお願いします。"
    
    elif action == 'organize':
        # 重複や類似したToDoを整理
        title_groups = {}
        for todo in pending:
            title = todo.get('title', '').lower()
            # 類似したタイトルをグループ化
            found_group = None
            for key in title_groups.keys():
                if title in key or key in title:
                    found_group = key
                    break
            
            if found_group:
                title_groups[found_group].append(todo)
            else:
                title_groups[title] = [todo]
        
        # 重複があるグループを特定
        duplicates_found = []
        for title, todos_list in title_groups.items():
            if len(todos_list) > 1:
                duplicates_found.extend(todos_list[1:])  # 最初の1個を残して削除
        
        if duplicates_found:
            for todo in duplicates_found:
                todo_manager.db.collection('todos').document(todo['todo_id']).delete()
            return f"Catherine: ✅ {len(duplicates_found)}件の重複ToDoを整理しました。\n\nリストがより見やすくなりましたね！"
        else:
            return "Catherine: 重複するToDoは見つかりませんでした。リストは既に整理されています。"
    
    elif action == 'edit':
        new_content = todo_action.get('new_content', '')
        if not new_content:
            return "Catherine: どのように変更したいか教えてください。"
        
        # ターゲットから該当するToDoを探す
        matched_todo = None
        for todo in pending:
            if target.lower() in todo.get('title', '').lower():
                matched_todo = todo
                break
        
        if matched_todo:
            # AI分析で優先度再評価
            ai_analysis = await todo_manager._analyze_todo_with_ai(new_content, "")
            
            todo_manager.db.collection('todos').document(matched_todo['todo_id']).update({
                'title': new_content,
                'priority': ai_analysis.get('priority', 3),
                'category': ai_analysis.get('category', 'general'),
                'updated_at': datetime.now(jst)
            })
            
            return f"Catherine: ✅ 「{matched_todo['title']}」を「{new_content}」に更新しました。"
        else:
            return f"Catherine: 「{target}」に該当するToDoが見つかりませんでした。"
    
    elif action == 'complete':
        # ターゲットから該当するToDoを探す
        matched_todo = None
        for todo in pending:
            if target.lower() in todo.get('title', '').lower():
                matched_todo = todo
                break
        
        if matched_todo:
            await todo_manager.update_todo_status(matched_todo['todo_id'], 'completed')
            return f"Catherine: 🎉 「{matched_todo['title']}」を完了しました！お疲れ様でした！\n\n次は何をしましょうか？"
        else:
            return f"Catherine: 「{target}」に該当するToDoが見つかりませんでした。"
    
    elif action == 'clear':
        if len(pending) > 0:
            return f"Catherine: 本当に{len(pending)}件のToDoをすべて削除しますか？\n\n削除する場合は「はい、全部削除して」と言ってください。"
        else:
            return "Catherine: 削除するToDoがありません。"
    
    return "Catherine: すみません、どのような操作をしたいか理解できませんでした。"

async def handle_memory_command(user_id: str, command_text: str) -> str:
    """記憶関連コマンド"""
    parts = command_text.lower().split()
    
    if len(parts) > 1 and parts[1] == "stats":
        # 記憶統計を表示
        analytics = await conversation_manager.get_conversation_analytics(user_id, days=30)
        return f"""Catherine: 📊 あなたとの記録統計（30日間）

💬 総会話数: {analytics.get('total_conversations', 0)}回
😊 平均満足度: {analytics.get('average_satisfaction', 0):.1f}%
💡 平均有用性: {analytics.get('average_helpfulness', 0):.1f}%
📅 1日平均: {analytics.get('conversations_per_day', 0):.1f}回

私はあなたとの全ての会話を覚えています！"""
    
    elif len(parts) > 1 and parts[1] == "topics":
        # よく話す話題を分析
        return await analyze_favorite_topics(user_id)
    
    else:
        return """Catherine: 🧠 記憶機能コマンド:

• `C! memory stats` - 会話統計を表示
• `C! memory topics` - よく話す話題を分析
• `C! memory clear` - 記録をリセット（注意！）

私はあなたとの全ての会話、ToDoの履歴、設定変更を完全に記録・記憶しています。"""

async def handle_todo_with_memory(user_id: str, command_text: str, user_prefs: dict) -> str:
    """記憶を活用したToDo作成"""
    todo_content = command_text[4:].strip()
    
    print(f"🔍 Creating TODO for user_id: {user_id}")
    print(f"🔍 TODO content: {todo_content}")
    
    if not todo_content:
        # 過去のパターンを参考に提案
        return await suggest_todo_based_on_history(user_id)
    
    # 通常のToDo作成
    try:
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=todo_content,
            description=f"記録日時: {datetime.now(jst).strftime('%Y/%m/%d %H:%M')}"
        )
        print(f"✅ TODO created: {todo_data}")
    except Exception as e:
        print(f"❌ TODO creation failed: {e}")
        return f"Catherine: 申し訳ございません。ToDoの作成中にエラーが発生しました: {str(e)}"
    
    priority_emoji = "🔥" if todo_data['priority'] >= 4 else "📌" if todo_data['priority'] >= 3 else "📝"
    
    return f"""Catherine: {priority_emoji} 承知いたしました！

「{todo_data['title']}」を優先度{todo_data['priority']}で記録しました。
カテゴリ: {todo_data['category']}

この内容は完全に記憶し、後で進捗確認いたします。"""

async def suggest_todo_based_on_history(user_id: str) -> str:
    """過去の履歴に基づくToDo提案"""
    # 実装は簡略化
    return """Catherine: ToDoの内容を教えてください。

参考までに、過去によく作成されているタスク：
📋 資料作成・準備
📧 メール返信
📞 連絡・確認
🏠 日常タスク

例: `C! todo 明日までに報告書作成`"""

async def handle_conversation_with_memory(user_id: str, user_input: str, user_prefs: dict) -> str:
    """超優秀秘書による完全記憶・感情知能・先読み対応"""
    
    # 1. 感情分析
    emotion_state = await emotional_intelligence.analyze_emotional_state(
        user_id=user_id,
        text=user_input,
        context=f"ユーザー設定: {user_prefs}"
    )
    
    # 2. 感情危機の検出と対応
    crisis_support = await emotional_intelligence.detect_emotional_crisis(user_id, emotion_state)
    if crisis_support:
        return crisis_support.get('immediate_support', '')
    
    # 3. ToDo抽出の試行
    todo_result = await todo_manager.parse_natural_language_todo(user_input)
    
    # 4. 記憶を活用した基本応答生成
    base_response = await conversation_manager.generate_response(
        user_id=user_id,
        user_input=user_input,
        user_preferences=user_prefs,
        todo_detected=todo_result.get('has_todo', False)
    )
    
    # 5. 感情に基づく応答適応
    adapted_response = await emotional_intelligence.adapt_communication_style(
        user_id=user_id,
        emotion_state=emotion_state,
        base_response=base_response
    )
    
    # 6. 先読み提案の生成
    proactive_suggestions = await proactive_assistant.generate_proactive_suggestions(
        user_id=user_id,
        context=user_input
    )
    
    # 7. 最終応答の構築
    final_response = adapted_response
    
    # ToDoが検出された場合は作成
    if todo_result.get('has_todo') and todo_result.get('confidence', 0) > 0.7:
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=todo_result['title'],
            description=todo_result.get('description', ''),
            due_date=todo_result.get('due_date')
        )
        
        final_response += f"\n\n💡 「{todo_data['title']}」をToDoに記録しました！"
    
    # 先読み提案を追加（高ストレス時は控える）
    if proactive_suggestions and emotion_state.get('stress_level', 0.5) < 0.7:
        final_response += proactive_suggestions
    
    # 感情サポートが必要な場合
    if emotion_state.get('support_need', 0.5) > 0.8:
        emotional_support = await emotional_intelligence.provide_emotional_support(user_id, emotion_state)
        final_response += f"\n\n💝 {emotional_support}"
    
    return final_response

async def handle_structured_conversation(user_id: str, user_input: str, user_prefs: dict) -> str:
    """構造化レスポンス（JSON二部構成）による高精度会話処理"""
    try:
        # コンテキスト準備
        context = {
            "user_id": user_id,
            "preferences": user_prefs,
            "current_time": datetime.now(jst).isoformat()
        }
        
        # 構造化レスポンス生成
        structured_response = await prompt_system.generate_structured_response(user_input, context)
        
        # user_idを一時的に設定
        todo_manager._current_user_id = user_id
        
        # アクション実行
        action_results = await prompt_system.execute_actions(
            structured_response.get("actions", []),
            todo_manager,
            conversation_manager
        )
        
        # 実行結果を含めた最終応答
        talk = structured_response.get("talk", "")
        
        # 成功したアクションの報告（scheduledも含む）
        successful_actions = [r for r in action_results if r.get("status") in ["success", "scheduled"]]
        if successful_actions:
            action_summary = []
            for action in successful_actions:
                if action["type"] == "todo.add":
                    action_summary.append(f"✅ ToDo「{action['title']}」を追加")
                elif action["type"] == "reminder.set":
                    if action.get("status") == "scheduled":
                        action_summary.append(f"⏰ {action.get('message', 'リマインダーを設定')}")
                    else:
                        action_summary.append("⏰ リマインダーを設定")
                elif action["type"] == "note.save":
                    action_summary.append("📝 メモを保存")
            
            if action_summary:
                talk += "\n\n" + "\n".join(action_summary)
        
        return f"Catherine: {talk}"
        
    except Exception as e:
        print(f"❌ Structured conversation error: {e}")
        # フォールバック：従来の処理
        return await handle_conversation_with_memory(user_id, user_input, user_prefs)

async def detect_command_type(command_text: str) -> str:
    """コマンドタイプ検出"""
    cmd_lower = command_text.lower()
    if cmd_lower.startswith("todo"): return "todo_create"
    elif cmd_lower.startswith("list"): return "todo_list" 
    elif cmd_lower.startswith("done"): return "todo_complete"
    elif cmd_lower.startswith("memory"): return "memory_command"
    elif cmd_lower.startswith("help"): return "help"
    else: return "conversation"

async def analyze_favorite_topics(user_id: str) -> str:
    """よく話す話題を分析"""
    try:
        # 過去30日間の会話を取得して話題分析
        # 実装は簡略化
        return """Catherine: 📈 あなたがよく話される話題：

1. 🏢 仕事・プロジェクト関連 (45%)
2. 📚 学習・スキルアップ (20%) 
3. ☕ 日常・雑談 (15%)
4. 💻 技術・プログラミング (12%)
5. 🎯 目標・計画 (8%)

これらの話題についてはより詳細に記録・サポートしています。"""
        
    except Exception as e:
        return f"Catherine: 話題分析中にエラーが発生しました: {e}"

async def handle_sorted_list(user_id: str, sort_option: str) -> str:
    """ソートオプション付きリスト表示"""
    try:
        todos = await todo_manager.get_user_todos(user_id)
        
        if not todos:
            return "Catherine: 現在、登録されているToDoはありません。"
        
        # ステータス別に分類
        pending = [t for t in todos if t.get('status') == 'pending']
        in_progress = [t for t in todos if t.get('status') == 'in_progress']
        completed = [t for t in todos if t.get('status') == 'completed']
        
        # ソートオプションに応じた処理
        if sort_option == "priority":
            # 優先度順（高い順）
            pending.sort(key=lambda x: -x.get('priority', 3))
            in_progress.sort(key=lambda x: -x.get('priority', 3))
            title = "📊 **ToDoリスト（優先度順）**"
            
        elif sort_option == "due":
            # 締切日順（早い順、締切なしは最後）
            def due_sort_key(x):
                if x.get('due_date'):
                    return (0, x['due_date'])
                return (1, datetime.max.replace(tzinfo=jst))
            pending.sort(key=due_sort_key)
            in_progress.sort(key=due_sort_key)
            title = "📅 **ToDoリスト（締切日順）**"
            
        elif sort_option == "category":
            # カテゴリ別にグループ化
            categories = {}
            for todo in pending + in_progress:
                cat = todo.get('category', 'general')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(todo)
            
            result = f"Catherine: 📂 **ToDoリスト（カテゴリ別）** （全{len(todos)}件）\n\n"
            for cat, cat_todos in sorted(categories.items()):
                result += f"【{cat}】({len(cat_todos)}件)\n"
                for i, todo in enumerate(cat_todos, 1):
                    priority_mark = "🔥" if todo.get('priority', 3) >= 4 else "⚡" if todo.get('priority', 3) >= 3 else "📌"
                    status = "🚀" if todo.get('status') == 'in_progress' else "⏰"
                    result += f"{status} {priority_mark} {todo.get('title', 'タイトル不明')}\n"
                result += "\n"
            
            result += f"✅ **完了済み** ({len(completed)}件)\n\n"
            result += "💡 ToDoの追加: `C! todo [内容]`\n"
            result += "📝 完了報告: `C! done [番号]`"
            return result
            
        elif sort_option == "recent":
            # 作成日順（新しい順）
            pending.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            in_progress.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            title = "🆕 **ToDoリスト（新しい順）**"
        
        # 通常フォーマットで表示
        return await todo_manager.list_todos_formatted(user_id)
        
    except Exception as e:
        print(f"❌ Sorted list error: {e}")
        return "Catherine: リストの表示でエラーが発生しました。"

async def handle_todo_delete(user_id: str, command_text: str) -> str:
    """ToDo削除処理"""
    parts = command_text.split()
    
    if len(parts) < 2:
        return "Catherine: 削除するToDoの番号を指定してください。\n例: `C! delete 3` または `C! 削除 3`"
    
    try:
        # リストを取得して番号と実際のTodoをマッピング
        todos = await todo_manager.get_user_todos(user_id)
        pending = [t for t in todos if t.get('status') == 'pending']
        
        todo_num = int(parts[1]) - 1
        if 0 <= todo_num < len(pending):
            todo = pending[todo_num]
            todo_id = todo['todo_id']
            title = todo['title']
            
            # Firebase から削除
            todo_manager.db.collection('todos').document(todo_id).delete()
            
            return f"Catherine: ✅ 「{title}」を削除しました。"
        else:
            return f"Catherine: ❌ 番号が範囲外です。1～{len(pending)}の番号を指定してください。"
            
    except ValueError:
        return "Catherine: ❌ 番号は数字で指定してください。"
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return "Catherine: 削除中にエラーが発生しました。"

async def handle_todo_edit(user_id: str, command_text: str) -> str:
    """ToDo編集処理"""
    # 形式: C! edit 番号 新しい内容
    parts = command_text.split(maxsplit=2)
    
    if len(parts) < 3:
        return "Catherine: 編集するToDoの番号と新しい内容を指定してください。\n例: `C! edit 3 新しいタスク内容`"
    
    try:
        todos = await todo_manager.get_user_todos(user_id)
        pending = [t for t in todos if t.get('status') == 'pending']
        
        todo_num = int(parts[1]) - 1
        new_content = parts[2]
        
        if 0 <= todo_num < len(pending):
            todo = pending[todo_num]
            todo_id = todo['todo_id']
            
            # AI分析で優先度再評価
            ai_analysis = await todo_manager._analyze_todo_with_ai(new_content, "")
            
            # Firebase 更新
            todo_manager.db.collection('todos').document(todo_id).update({
                'title': new_content,
                'priority': ai_analysis.get('priority', 3),
                'category': ai_analysis.get('category', 'general'),
                'updated_at': datetime.now(jst)
            })
            
            return f"Catherine: ✅ ToDo #{parts[1]} を「{new_content}」に更新しました。"
        else:
            return f"Catherine: ❌ 番号が範囲外です。"
            
    except ValueError:
        return "Catherine: ❌ 番号は数字で指定してください。"
    except Exception as e:
        print(f"❌ Edit error: {e}")
        return "Catherine: 編集中にエラーが発生しました。"

async def handle_todo_rename(user_id: str, command_text: str) -> str:
    """ToDoリネーム処理（editと同じだが、より直感的）"""
    return await handle_todo_edit(user_id, command_text.replace("rename", "edit").replace("リネーム", "edit"))

async def handle_todo_clear(user_id: str, command_text: str) -> str:
    """ToDo一括クリア処理"""
    parts = command_text.split()
    
    if len(parts) > 1 and parts[1] == "all":
        # 全ToDo削除の確認
        todos = await todo_manager.get_user_todos(user_id)
        pending = [t for t in todos if t.get('status') == 'pending']
        
        if not pending:
            return "Catherine: 削除するToDoがありません。"
        
        # 一括削除
        for todo in pending:
            todo_manager.db.collection('todos').document(todo['todo_id']).delete()
        
        return f"Catherine: ✅ {len(pending)}件のToDoをすべて削除しました。"
    else:
        return "Catherine: 本当にすべてのToDoを削除しますか？\n実行する場合: `C! clear all`"

async def handle_done_with_celebration(user_id: str, command_text: str) -> str:
    """ToDo完了処理"""
    parts = command_text.split()
    
    if len(parts) < 2:
        return "Catherine: 完了するToDoの番号を指定してください。\n例: `C! done 3`"
    
    try:
        todos = await todo_manager.get_user_todos(user_id)
        pending = [t for t in todos if t.get('status') == 'pending']
        
        todo_num = int(parts[1]) - 1
        if 0 <= todo_num < len(pending):
            todo = pending[todo_num]
            todo_id = todo['todo_id']
            title = todo['title']
            
            # ステータス更新
            await todo_manager.update_todo_status(todo_id, 'completed')
            
            return f"Catherine: 🎉 「{title}」を完了しました！お疲れ様でした！"
        else:
            return f"Catherine: ❌ 番号が範囲外です。"
            
    except ValueError:
        return "Catherine: ❌ 番号は数字で指定してください。"
    except Exception as e:
        print(f"❌ Done error: {e}")
        return "Catherine: 完了処理中にエラーが発生しました。"

async def handle_personalized_help(user_id: str, user_prefs: dict) -> str:
    """個人化されたヘルプ"""
    return f"""Catherine: 📚 あなた専用のヘルプ（記憶活用型）

**基本機能:**
• `C! [会話]` - 記憶を活用した個人化応答
• `C! todo [内容]` - AI分析付きToDo作成
• `C! list` - 優先度順ToDoリスト
• `C! done [番号]` - ToDo完了

**ToDo管理:**
• `C! delete [番号]` - ToDo削除
• `C! edit [番号] [新内容]` - ToDo編集
• `C! rename [番号] [新名前]` - ToDoリネーム
• `C! clear all` - 全ToDo削除

**リスト表示:**
• `C! list priority` - 優先度順
• `C! list due` - 締切日順
• `C! list category` - カテゴリ別
• `C! list recent` - 作成日順

**記憶機能:**
• `C! memory stats` - 会話統計
• `C! memory topics` - 話題分析

**現在の設定:**
• ユーモアレベル: {user_prefs.get('humor_level', 50)}%
• 会話スタイル: {user_prefs.get('conversation_style', 50)}%

🧠 私はあなたとの全ての会話を記憶し、より良いサポートを提供します！"""

async def handle_reminder_command(user_id: str, command_text: str) -> str:
    """リマインダー機能の処理"""
    try:
        parts = command_text.split(maxsplit=1)
        
        if len(parts) == 1 or parts[1].lower() in ["list", "一覧"]:
            # リマインダー一覧表示
            reminders = await reminder_system.list_reminders(user_id)
            
            if not reminders:
                return "Catherine: 現在、設定されているリマインダーはありません。\n\n例: `C! remind 明日15時に会議の準備`"
            
            result = "Catherine: 📅 **設定中のリマインダー**\n\n"
            
            for i, reminder in enumerate(reminders[:10], 1):  # 最大10件表示
                title = reminder.get('title', 'タイトル不明')
                next_time = reminder.get('next_reminder')
                reminder_type = reminder.get('reminder_type', 'once')
                
                type_emoji = {
                    'once': '🔔',
                    'daily': '📅', 
                    'weekly': '📆',
                    'monthly': '🗓️',
                    'custom': '⏰'
                }.get(reminder_type, '🔔')
                
                if next_time:
                    time_str = next_time.strftime('%m/%d %H:%M')
                    result += f"{type_emoji} {i}. **{title}**\n   次回: {time_str} ({reminder_type})\n\n"
                else:
                    result += f"{type_emoji} {i}. **{title}** (時刻未設定)\n\n"
            
            result += "💡 新規作成: `C! remind [時刻] [内容]`\n"
            result += "🗑️ 削除: `C! remind delete [番号]`"
            
            return result
            
        elif parts[1].lower().startswith("delete") or parts[1].lower().startswith("削除"):
            # リマインダー削除
            try:
                delete_parts = parts[1].split()
                if len(delete_parts) < 2:
                    return "Catherine: 削除するリマインダーの番号を指定してください。\n例: `C! remind delete 1`"
                
                reminder_num = int(delete_parts[1]) - 1
                reminders = await reminder_system.list_reminders(user_id)
                
                if 0 <= reminder_num < len(reminders):
                    reminder = reminders[reminder_num]
                    success = await reminder_system.delete_reminder(reminder['reminder_id'])
                    
                    if success:
                        return f"Catherine: ✅ 「{reminder['title']}」を削除しました。"
                    else:
                        return "Catherine: ❌ 削除に失敗しました。"
                else:
                    return f"Catherine: ❌ 番号が範囲外です。1～{len(reminders)}の番号を指定してください。"
                    
            except ValueError:
                return "Catherine: ❌ 番号は数字で指定してください。"
            
        else:
            # 新しいリマインダー作成
            natural_input = parts[1]
            result = await reminder_system.create_smart_reminder(user_id, natural_input)
            
            if result.get('error'):
                return f"Catherine: ❌ {result['error']}\n\n例: `C! remind 明日15時に会議の準備`"
            
            title = result.get('title', '新しいリマインダー')
            remind_at = result.get('next_reminder')
            
            if remind_at:
                time_str = remind_at.strftime('%Y/%m/%d %H:%M')
                return f"Catherine: ✅ リマインダー「{title}」を設定しました！\n⏰ 実行予定: {time_str}\n\n必要に応じて `C! remind list` で確認できます。"
            else:
                return f"Catherine: ✅ リマインダー「{title}」を設定しました！"
        
    except Exception as e:
        print(f"❌ Reminder command error: {e}")
        return "Catherine: リマインダーの処理でエラーが発生しました。もう一度お試しください。"

if __name__ == "__main__":
    # 環境変数チェック
    token = os.getenv("DISCORD_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません")
        exit(1)
        
    if not openai_key:
        print("❌ OPENAI_API_KEY が設定されていません")
        exit(1)
        
    if not firebase_manager.is_available():
        print("⚠️  完全記録機能にはFirebaseが必要です")
        print("基本版を使用する場合は main_simple.py を実行してください")
    
    print("🧠 完全記録型Catherine AI 起動中...")
    client.run(token)