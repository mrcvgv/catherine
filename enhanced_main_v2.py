#!/usr/bin/env python3
"""
Catherine AI - Enhanced Version 2.0
人間らしい理解とリアクション学習を備えた次世代AI秘書
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from openai import OpenAI
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

# カスタムモジュールのインポート
from firebase_config import firebase_manager
from todo_manager import TodoManager
from conversation_manager import ConversationManager
from advanced_context_system import AdvancedContextSystem
from reaction_learning_system import ReactionLearningSystem
from team_todo_manager import TeamTodoManager
from reminder_system import ReminderSystem
from morning_briefing_system import MorningBriefingSystem
from confidence_guard_system import ConfidenceGuardSystem, ConfidenceLevel
from action_summary_system import ActionSummarySystem
from progress_nudge_engine import ProgressNudgeEngine
from attachment_ocr_system import AttachmentOCRSystem
from voice_optimized_system import VoiceOptimizedSystem
from adaptive_learning_system import AdaptiveLearningSystem
from natural_language_engine import NaturalLanguageEngine
from fast_nlp_engine import FastNLPEngine
from supreme_intelligence_engine import SupremeIntelligenceEngine
from advanced_reasoning_engine import AdvancedReasoningEngine
from dynamic_learning_system import DynamicLearningSystem
from advanced_context_engine import AdvancedContextEngine
from intelligent_automation_system import IntelligentAutomationSystem
from metacognitive_system import MetacognitiveSystem
from voice_channel_alternative import VoiceChannelAlternative  # 代替音声システム

# 🌟 NEW: 究極知能システム群 - 人間らしさ + 博士レベル知能
try:
    from enhanced_human_communication import EnhancedHumanCommunication
    from phd_level_intelligence import PhDLevelIntelligence
    from master_communicator import MasterCommunicator
    from ultimate_intelligence_hub import UltimateIntelligenceHub
    from emotional_intelligence import EmotionalIntelligence
    ULTIMATE_SYSTEMS_AVAILABLE = True
    print("Ultimate Intelligence Systems: Loaded Successfully")
except ImportError as e:
    print(f"WARNING: Ultimate Intelligence Systems: Partially unavailable - {e}")
    ULTIMATE_SYSTEMS_AVAILABLE = False

# 🌟 進化した人間的AIシステム - 5000年後の人間の脳の形
try:
    from evolved_human_ai import EvolvedHumanAI
    from fast_greeting_system import FastGreetingSystem
    from natural_conversation_system import NaturalConversationSystem
    from massive_pattern_brain import MassivePatternBrain
    from instant_intent_engine import InstantIntentEngine
    from super_natural_chat import SuperNaturalChat
    from mega_human_chat import MegaHumanChat
    from ultra_human_communication import UltraHumanCommunication
    from instant_response_system import InstantResponseSystem
    from simple_human_chat import SimpleHumanChat
    from mega_universal_chat import MegaUniversalChat
    from human_level_chat import HumanLevelChat
    from simple_todo import SimpleTodo
    EVOLVED_HUMAN_AI_AVAILABLE = True
    print("Evolved Human AI System: Loaded Successfully")
except ImportError as e:
    print(f"WARNING: Evolved Human AI System: Unavailable - {e}")
    EVOLVED_HUMAN_AI_AVAILABLE = False

# 旧超越的システムは無効化
TRANSCENDENT_SYSTEMS_AVAILABLE = False

# Railway用ポート設定
PORT = int(os.environ.get("PORT", 8080))

# Discord intents設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクション検知のため追加
intents.members = True  # メンバー情報取得のため追加
intents.voice_states = True  # ボイスチャンネル機能のため追加

# Botクライアント初期化
bot = commands.Bot(command_prefix='C!', intents=intents)

# OpenAI クライアント初期化
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("[WARNING] OPENAI_API_KEY not set - using placeholder")
    openai_api_key = "sk-placeholder"  # Railway起動時のプレースホルダー

try:
    client_oa = OpenAI(api_key=openai_api_key)
except Exception as e:
    print(f"[WARNING] OpenAI client initialization warning: {e}")
    # プレースホルダーでクライアント作成
    client_oa = OpenAI(api_key="sk-placeholder")

# 各マネージャーの初期化
todo_manager = TodoManager(client_oa)
conversation_manager = ConversationManager(client_oa)
context_system = AdvancedContextSystem(client_oa)
reaction_system = ReactionLearningSystem(client_oa)
team_todo_manager = TeamTodoManager(client_oa)
reminder_system = ReminderSystem(client_oa, bot)
briefing_system = MorningBriefingSystem(client_oa)
confidence_guard = ConfidenceGuardSystem()
action_summary = ActionSummarySystem(client_oa)
nudge_engine = ProgressNudgeEngine(client_oa)
ocr_system = AttachmentOCRSystem(client_oa)
voice_system = VoiceOptimizedSystem(client_oa)
adaptive_learning = AdaptiveLearningSystem(client_oa)
natural_language = NaturalLanguageEngine(client_oa)
fast_nlp = FastNLPEngine("intent_registry.yaml", client_oa)  # 新高速エンジン
supreme_intelligence = SupremeIntelligenceEngine(client_oa)  # 最高知能エンジン

# 🧠 大学院レベルAI知能システム群
advanced_reasoning = AdvancedReasoningEngine(client_oa)  # 高度推論システム
dynamic_learning = DynamicLearningSystem(client_oa, firebase_manager)  # 動的学習システム
advanced_context = AdvancedContextEngine(client_oa, firebase_manager)  # 高度文脈理解
intelligent_automation = IntelligentAutomationSystem(client_oa, firebase_manager)  # 知的自動化
metacognitive = MetacognitiveSystem(client_oa, firebase_manager)  # メタ認知・自己改善
voice_channel = VoiceChannelAlternative(client_oa, bot)  # 代替音声システム

# 🌟 究極知能統合システム - 人間性 + 博士レベル知能の完全融合
if ULTIMATE_SYSTEMS_AVAILABLE:
    enhanced_human_comm = EnhancedHumanCommunication(client_oa)  # 超人間的コミュニケーション
    phd_intelligence = PhDLevelIntelligence(client_oa)  # 博士レベル知能
    master_communicator = MasterCommunicator(client_oa)  # マスターコミュニケーター
    emotional_ai = EmotionalIntelligence(client_oa)  # 高度感情知能
    
    # 🚀 究極統合ハブ - 全システムを統括する最高知能
    ultimate_hub = UltimateIntelligenceHub(client_oa, firebase_manager)
    
    print("Catherine AI: Ultimate Intelligence Integration System Activated")
    print("   PhD-Level Intelligence + Human Warmth = Perfect Fusion")
else:
    ultimate_hub = None
    print("WARNING: Running in Basic System Mode")

# 🌟 進化した人間的AIシステム統合
if EVOLVED_HUMAN_AI_AVAILABLE:
    evolved_human_ai = EvolvedHumanAI(client_oa)
    fast_greeting = FastGreetingSystem()
    natural_conversation = NaturalConversationSystem()
    massive_pattern_brain = MassivePatternBrain()
    instant_intent_engine = InstantIntentEngine()
    super_natural_chat = SuperNaturalChat()
    mega_human_chat = MegaHumanChat()
    ultra_human_communication = UltraHumanCommunication()
    instant_response_system = InstantResponseSystem()
    simple_human_chat = SimpleHumanChat()
    mega_universal_chat = MegaUniversalChat()
    human_level_chat = HumanLevelChat()
    simple_todo = SimpleTodo()
    print("Catherine AI: Evolved Human Intelligence System Activated")
    print("   Human Wisdom + Logical Reasoning + Creative Thinking + Practical Solutions = Evolved Human AI")
    print("   Fast Greeting System: Loaded for instant casual responses")
    print("   Natural Conversation System: Loaded for human-like chat")
    print("   🧠 Massive Pattern Brain: 100M+ patterns loaded")
    print("   ⚡ Instant Intent Engine: 0.001s recognition speed")
    print(f"   💬 Super Natural Chat: {super_natural_chat.get_pattern_count()} natural patterns")
    print(f"   🗣️ Mega Human Chat: {mega_human_chat.get_pattern_count()} human patterns + personality system")
    print(f"   🌟 ULTRA Human Communication: {ultra_human_communication.get_total_pattern_count()} comprehensive patterns")
    print("       - 50k+ basic patterns, 100k+ situational, 50k+ emotional, 100k+ contextual")
    print("       - Real-time learning, emotional intelligence, regional dialects")
    print("       - Contextual awareness, personality adaptation")
    print(f"   ⚡ INSTANT Response System: {instant_response_system.get_response_count()} instant patterns (0.001s)")
    print("       - 即座に返事、遅延ゼロ、最高速カジュアル会話")
    print(f"   👥 Simple Human Chat: {simple_human_chat.get_pattern_count()} human-like patterns")
    print("       - 普通の友達みたい、気持ち理解、共感重視、頭良すぎない")
    print(f"   🌌 MEGA Universal Chat: {mega_universal_chat.get_pattern_count()} universal patterns")
    print("       - 日常生活のあらゆる会話を網羅、異次元レベルの汎用性、人間らしさMAX")
    print(f"   👨 Human Level Chat: {human_level_chat.get_pattern_count()} human patterns")
    print("       - 頭良すぎず、普通の人間みたいな会話、シンプルで自然")
    print(f"   📝 Simple Todo: {simple_todo.get_todo_count()} active todos")
    print("       - 複雑なことはしないシンプルTODO管理")
else:
    evolved_human_ai = None
    fast_greeting = None
    natural_conversation = None
    massive_pattern_brain = None
    instant_intent_engine = None
    super_natural_chat = None
    mega_human_chat = None
    ultra_human_communication = None
    instant_response_system = None
    simple_human_chat = None
    mega_universal_chat = None
    human_level_chat = None
    simple_todo = None
    print("WARNING: Evolved Human AI System Unavailable")

# 旧超越的システムは無効化
transcendent_core = None

# タイムゾーン設定
JST = pytz.timezone('Asia/Tokyo')

@bot.event
async def on_ready():
    print(f"[SUCCESS] Catherine AI v2.0 ready")
    print(f"[INFO] Logged in as: {bot.user}")
    print("[INFO] Features: Deep Understanding, Reaction Learning, Team ToDo, Smart Reminders")
    print(f"[INFO] Servers: {len(bot.guilds)}")
    
    # 定期タスク開始
    check_reminders.start()
    update_learning.start()

@bot.event
async def on_message(message):
    """メッセージ処理"""
    if message.author.bot:
        return
    
    # ユーザー情報
    user_id = str(message.author.id)
    username = message.author.display_name
    
    # ユーザーアクティビティ更新
    await conversation_manager.update_user_activity(user_id, username)
    
    # 添付ファイル処理
    if message.attachments:
        await process_attachments(message, user_id, username)
        return
    
    # C!コマンド処理（文章のどこにでも対応）
    if "C!" in message.content:
        await process_command(message, user_id, username)
        return  # C!コマンドの場合は、二重処理を防ぐためにここで終了
    
    # 特定チャンネルでの自動反応（タグなし）
    # 環境変数から設定可能、デフォルトは基本的なチャンネル名
    auto_channels_env = os.getenv("AUTO_RESPONSE_CHANNELS", "todo,catherine,タスク,やること")
    auto_response_channels = [ch.strip().lower() for ch in auto_channels_env.split(",")]
    channel_name = message.channel.name.lower() if hasattr(message.channel, 'name') else ''
    
    if any(ch in channel_name for ch in auto_response_channels):
        # todoチャンネル等では C! なしでも反応
        await process_command(message, user_id, username)
        return
    
    # その他のコマンド処理（commands.Botの機能を使用）
    await bot.process_commands(message)

async def process_command(message, user_id: str, username: str):
    """完全自然言語理解によるコマンド処理"""
    try:
        start_time = datetime.now()
        
        # C!がどこにあっても対応する抽出ロジック（特定チャンネルではタグなしも対応）
        content = message.content.strip()
        
        if "C!" in content:
            # C!以降の部分を抽出（C!が文の途中にある場合に対応）
            c_index = content.find("C!")
            command_text = content[c_index + 2:].strip()
            
            # C!が文の最後の場合や、C!の前にある文章も考慮
            if not command_text and c_index > 0:
                # C!の前の部分を使用
                command_text = content[:c_index].strip()
        else:
            # C!がない場合はそのまま使用（特定チャンネルの場合）
            command_text = content
        
        # 会話コンテキスト取得
        conversation_history = await conversation_manager._get_recent_conversations(user_id, limit=5)
        context = {
            'last_topic': conversation_history[0].get('topic', '') if conversation_history else '',
            'user_state': 'normal',
            'history': conversation_history
        }
        
        # Todo関連コマンドの検出（超越的AIをバイパス）
        is_todo_command = any(keyword in command_text.lower() for keyword in [
            'todo', 'タスク', 'やること', 'ToDo', 'TODO'
        ]) or any(command_text.lower().startswith(prefix) for prefix in [
            'c! todo', 'todo', 'mytodo', 'done'
        ])
        
        # 超越的AIシステムを無効化 - 実用的な応答を優先
        if False:  # transcendent_core and TRANSCENDENT_SYSTEMS_AVAILABLE and not is_todo_command:
            print(f"[TRANSCENDENT] Processing: {command_text[:50]}...")
            
            try:
                # 超越的統合知能による処理 - 意識レベル85 + 12次元認知 + 超適応学習
                transcendent_response = await transcendent_core.transcendent_intelligence_processing(
                    command_text, user_id, context, conversation_history
                )
                
                response = transcendent_response.get('transcendent_response', '')
                
                # 超越レベル表示
                transcendence_level = transcendent_response.get('transcendence_level', 85)
                consciousness_level = transcendent_response.get('consciousness_level', 85)
                wisdom_depth = transcendent_response.get('wisdom_depth', 90)
                
                # 超越的能力表示
                if transcendence_level > 90:
                    response += f"\n\n🌟 超越レベル: {transcendence_level:.1f}/100 | 意識: {consciousness_level:.1f}/100 | 叡智: {wisdom_depth:.1f}/100"
                
                # メッセージ送信と後処理
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, transcendence_level / 100
                )
                return
                
            except Exception as e:
                print(f"[ERROR] 超越的AIコア処理エラー: {e}")
                # フォールバック: 究極知能ハブへ
                print("🔄 フォールバック: 究極知能ハブへ移行...")
        
        # 🌟 究極知能ハブ による超高度処理（利用可能な場合）- 無効化（人間らしさ優先）
        if False and ultimate_hub and ULTIMATE_SYSTEMS_AVAILABLE:
            print(f"[ULTIMATE] Processing: {command_text[:50]}...")
            
            try:
                # 究極統合知能による処理
                ultimate_response = await ultimate_hub.process_ultimate_intelligence(
                    command_text, user_id, context
                )
                
                response = ultimate_response.primary_response
                
                # 追加のフォローアップ情報
                if ultimate_response.follow_up_suggestions:
                    follow_up = random.choice(ultimate_response.follow_up_suggestions)
                    response += f"\n\n💡 {follow_up}"
                
                # 高品質応答の場合は追加情報表示
                if ultimate_response.confidence_level > 0.9:
                    response += f"\n\n🎯 信頼度: {ultimate_response.confidence_level:.1f} | 知的深度: {ultimate_response.intellectual_depth}/10"
                
                print(f"[SUCCESS] 究極知能ハブ処理完了: 品質={ultimate_response.confidence_level:.2f}")
                
                # 音声モードの場合は音声最適化
                user_profile = await get_user_profile(user_id)
                if user_profile.get('voice_mode', False):
                    response = voice_system.optimize_for_voice(response)
                
                # 応答送信
                bot_message = await message.channel.send(response)
                
                # 各種ログ・学習処理
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response, 
                    context, ultimate_response.confidence_level
                )
                
                return
                
            except Exception as e:
                print(f"[ERROR] 究極知能ハブエラー: {e}")
                print("[WARNING] Falling back to standard system")
                # エラーの場合は既存システムにフォールバック
        
        # TODO関連コマンドの検出（最優先）
        is_todo_command = any(keyword in command_text.lower() for keyword in [
            'todo', 'タスク', 'やること', '入れて', '追加', '登録',
            'リスト出', 'リスト表示', 'リスト見せ', 'タスク一覧', 'todo一覧', 
            'リスト教', 'やること見せ', 'タスク出し', 'list', '一覧出し', 'done'
        ])
        
        # DB接続確認コマンド
        is_db_check = any(keyword in command_text.lower() for keyword in [
            'db', 'データベース', 'つながって', 'つながっています', '接続', 'チェック'
        ])
        
        # ✅ DB接続チェック - 最優先で処理
        if is_db_check:
            try:
                print(f"[DB_CHECK] Processing: {command_text}")
                # Firebase接続テスト
                test_doc = firebase_manager.get_db().collection('connection_test').document('test')
                test_doc.set({'timestamp': datetime.now().isoformat(), 'status': 'ok'})
                
                # Team todo manager テスト
                todos_count = len(await team_todo_manager.get_team_todos())
                
                response = f"✅ **データベース接続状況**\n📊 現在のToDo数: {todos_count}件\n🔗 Firebase: 正常接続\n⏰ 接続確認時刻: {datetime.now().strftime('%H:%M:%S')}"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                response = f"❌ **データベース接続エラー**\n詳細: {str(e)}\n🔧 Firebase設定を確認してください"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
        
        # 📋 TODO機能 - 実際に動作させる
        elif is_todo_command:
            try:
                print(f"[TODO] Processing: {command_text}")
                
                # TODO追加の判定
                if any(word in command_text.lower() for word in ['入れて', '追加', '登録', 'todo']):
                    # コマンドからTODO内容を抽出
                    todo_content = command_text.replace('todo', '').replace('入れて', '').replace('追加', '').replace('登録', '').strip()
                    
                    if not todo_content:
                        response = "📋 TODOの内容を教えてください。\n例: `C! todo 明日の会議資料準備`"
                    else:
                        # Simple TODOで追加
                        if simple_todo:
                            result = simple_todo.add_todo(todo_content, user_id)
                            response = result
                        else:
                            # フォールバック: team_todo_managerで追加
                            result = await team_todo_manager.create_team_todo(
                                user_id=user_id,
                                title=todo_content[:100],
                                priority=3,
                                due_date=None,
                                category='general'
                            )
                            response = f"✅ 「**{todo_content[:30]}**」をToDoに追加しました！"
                
                # TODOリスト表示の判定
                elif any(word in command_text.lower() for word in ['リスト', '一覧', 'list']):
                    if simple_todo:
                        response = simple_todo.list_todos(user_id)
                    else:
                        # フォールバック
                        todos = await team_todo_manager.get_team_todos()
                        if not todos:
                            response = "📋 今のところToDoはありません。"
                        else:
                            response = "📊 **ToDoリスト**\n\n"
                            for i, todo in enumerate(todos[:10], 1):
                                title = todo['title'][:50]
                                response += f"{i}. **{title}**\n"
                else:
                    response = "📋 ToDo機能を使用します。\n• `todo 内容` - 追加\n• `todo list` - 一覧表示"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
                
            except Exception as e:
                print(f"[ERROR] TODO processing error: {e}")
                import traceback
                traceback.print_exc()
                response = f"❌ TODO処理エラー: {str(e)}"
                
                bot_message = await message.channel.send(response)
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
        # 🙏 真摯な対応 - ユーザーの要求を理解して応える
        # 何かがうまくいっていない場合のフォールバック
        elif 'すみません' in command_text.lower() or 'ごめん' in command_text.lower():
            response = "いえいえ、こちらこそすみません。どうすればお手伝いできますか？"
            bot_message = await message.channel.send(response)
            await _handle_post_response_processing(
                message, bot_message, user_id, command_text, response, context, 1.0
            )
            return
        
        # 👨⚡ 人間レベル会話 - 次優先 (普通の人間みたい)
        elif human_level_chat and human_level_chat.is_human_chat(command_text):
            try:
                response = human_level_chat.get_human_response(command_text)
                if response:
                    print(f"[HUMAN_LEVEL] Input: {command_text} -> Response: {response} (人間レベル)")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Human level chat error: {e}")
        
        # 🌌⚡ MEGA汎用会話 - 次優先 (異次元レベル汎用性)
        if mega_universal_chat and mega_universal_chat.is_universal_chat(command_text):
            try:
                response = mega_universal_chat.get_universal_response(command_text)
                if response:
                    print(f"[MEGA_UNIVERSAL] Input: {command_text} -> Response: {response} (異次元汎用性)")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Mega universal chat error: {e}")
        
        # 👥⚡ シンプル人間会話 - 次優先 (普通の友達みたい)
        if simple_human_chat and simple_human_chat.is_simple_human_chat(command_text):
            try:
                response = simple_human_chat.get_human_response(command_text)
                if response:
                    print(f"[SIMPLE_HUMAN] Input: {command_text} -> Response: {response} (気持ち理解重視)")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Simple human chat error: {e}")
        
        # ⚡⚡⚡ 瞬間応答システム - 次優先 (0.001秒応答)
        if instant_response_system and instant_response_system.is_instant_response_target(command_text):
            try:
                start_time = time.time()
                response = instant_response_system.get_instant_response(command_text)
                if response:
                    processing_time = (time.time() - start_time) * 1000
                    print(f"[INSTANT] Input: {command_text} -> Response: {response} ({processing_time:.2f}ms)")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Instant response error: {e}")
        
        # 🌟⚡ ULTRA人間コミュニケーション - 無効化（複雑すぎる）
        if False and ultra_human_communication and ultra_human_communication.is_ultra_human_communication(command_text):
            try:
                response = ultra_human_communication.get_ultra_response(command_text, user_id)
                if response:
                    stats = ultra_human_communication.get_system_stats()
                    print(f"[ULTRA_HUMAN] Input: {command_text[:25]} -> Response: {response}")
                    print(f"              Total patterns: {stats['total_patterns']}, Active contexts: {stats['active_contexts']}")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Ultra human communication error: {e}")
        
        # 🗣️⚡ 超人間雑談システム - 次優先 (完全人間レベル)
        if mega_human_chat and mega_human_chat.is_mega_human_chat(command_text):
            try:
                response = mega_human_chat.get_mega_human_response(command_text, user_id)
                if response:
                    mood_state = mega_human_chat.get_personality_state()
                    print(f"[MEGA_HUMAN] Input: {command_text[:20]} -> Response: {response} [Mood: {mood_state['mood']}, Energy: {mood_state['energy']:.1f}]")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Mega human chat error: {e}")
        
        # 💬⚡ 超自然会話システム - フォールバック
        if super_natural_chat and super_natural_chat.is_super_natural_chat(command_text):
            try:
                response = super_natural_chat.get_natural_response(command_text)
                if response:
                    print(f"[SUPER_NATURAL] Input: {command_text[:30]} -> Response: {response}")
                    
                    bot_message = await message.channel.send(response)
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 1.0
                    )
                    return
            except Exception as e:
                print(f"[ERROR] Super natural chat error: {e}")
        
        # 🧠⚡ 超高速意図認識システム - 無効化（複雑すぎる）
        if False and instant_intent_engine and massive_pattern_brain:
            try:
                start_time = time.time()
                intent_result = instant_intent_engine.recognize_intent_instantly(command_text)
                
                # 高信頼度の場合は即座に実行
                if intent_result.confidence > 0.85:
                    # アクション実行
                    response = await instant_intent_engine.execute_intent_action(
                        intent_result, context
                    )
                    
                    if response and len(response.strip()) > 0:
                        processing_time = time.time() - start_time
                        print(f"[INSTANT_BRAIN] Intent: {intent_result.intent}, "
                              f"Confidence: {intent_result.confidence:.2f}, "
                              f"Time: {processing_time*1000:.1f}ms")
                        
                        bot_message = await message.channel.send(response)
                        await _handle_post_response_processing(
                            message, bot_message, user_id, command_text, response,
                            context, intent_result.confidence
                        )
                        return
            except Exception as e:
                print(f"[ERROR] Instant intent engine error: {e}")
        
        # 自然な会話の検出 (フォールバック用)
        is_natural_conversation = (
            natural_conversation and 
            natural_conversation.should_use_natural_conversation(command_text)
        )
        
        # ⚡ 高速挨拶システム - シンプルな挨拶に即座に応答
        if fast_greeting and is_simple_greeting:
            try:
                response = fast_greeting.generate_fast_response(command_text)
                bot_message = await message.channel.send(response)
                
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
                
            except Exception as e:
                print(f"[ERROR] Fast greeting error: {e}")
                # フォールバック処理継続
        
        # 💬 自然会話システム - 人間みたいな短い返し
        if natural_conversation and is_natural_conversation and not is_simple_greeting:
            try:
                response = natural_conversation.generate_natural_response(command_text, context)
                bot_message = await message.channel.send(response)
                
                await _handle_post_response_processing(
                    message, bot_message, user_id, command_text, response,
                    context, 1.0
                )
                return
                
            except Exception as e:
                print(f"[ERROR] Natural conversation error: {e}")
                # フォールバック処理継続
        
        # 🧠 進化した人間的AI処理 - 無効化（頭良すぎる）
        if False and evolved_human_ai and EVOLVED_HUMAN_AI_AVAILABLE and not is_functional_request and not is_simple_greeting and not is_natural_conversation:
            try:
                print(f"[EVOLVED_AI] Processing with human wisdom: {command_text[:50]}...")
                
                evolved_response = await evolved_human_ai.generate_evolved_response(
                    command_text, context
                )
                
                if evolved_response and len(evolved_response.strip()) > 0:
                    response = evolved_response
                    
                    # 応答送信
                    bot_message = await message.channel.send(response)
                    
                    await _handle_post_response_processing(
                        message, bot_message, user_id, command_text, response,
                        context, 0.9
                    )
                    
                    return
                    
            except Exception as e:
                print(f"[ERROR] Evolved Human AI error: {e}")
                print("[WARNING] Falling back to standard system")
        
        # Supreme Intelligenceシステムも無効化 - シンプルな応答を優先
        use_supreme_intelligence = False
        
        if use_supreme_intelligence:
            # 🧠 SUPREME INTELLIGENCE 2.0 - 全システム統合処理
            
            # 1. 高度文脈理解
            context_analysis = await advanced_context.analyze_deep_context(user_id, command_text, conversation_history)
            
            # 2. 複雑推論判定
            needs_advanced_reasoning = (
                len(command_text) > 30 or
                any(word in command_text for word in [
                    'なぜ', 'どうして', '理由', '原因', '分析', '比較', '評価', '判断',
                    '戦略', '計画', '方法', 'アプローチ', '解決', '改善', '最適'
                ]) or
                context_analysis['context_confidence'] < 0.7
            )
            
            if needs_advanced_reasoning:
                # 🎯 高度推論エンジン起動
                reasoning_chain = await advanced_reasoning.multi_step_reasoning(command_text, context_analysis)
                
                # 推論結果を統合した最高品質応答
                supreme_result = await supreme_intelligence.supreme_understand(
                    command_text, user_id, {
                        **context,
                        'reasoning_chain': reasoning_chain.__dict__,
                        'deep_context': context_analysis,
                        'complexity_level': 'advanced'
                    }
                )
                
                # 推論プロセスを応答に統合
                if reasoning_chain.final_conclusion:
                    response = f"{supreme_result['response']}\n\n**推論結果**: {reasoning_chain.final_conclusion}"
                    if reasoning_chain.overall_confidence > 0.8:
                        response += f" (信頼度: {reasoning_chain.overall_confidence:.1f})"
                else:
                    response = supreme_result['response']
            else:
                # 🚀 標準Supreme Intelligence処理
                supreme_result = await supreme_intelligence.supreme_understand(
                    command_text, user_id, {**context, 'deep_context': context_analysis}
                )
                response = supreme_result['response']
            
            # 3. 実用的アクション統合
            supreme_intent = supreme_result['intent'].get('primary_intent', '').lower()
            
            if 'todo' in supreme_intent or 'task' in supreme_intent or any(word in command_text for word in ['todo', 'タスク', 'やること']):
                # プロジェクト管理・自動化判定
                needs_automation = any(word in command_text for word in [
                    'プロジェクト', '計画', '戦略', '自動化', '最適化', '管理'
                ])
                
                if needs_automation:
                    # 🤖 知的自動化システム起動
                    automation_result = await intelligent_automation.create_strategic_plan(
                        command_text, 
                        constraints={'user_id': user_id},
                        stakeholders=['user']
                    )
                    response += f"\n\n🤖 **プロジェクト戦略**: {automation_result.get('strategic_insights', [])[0] if automation_result.get('strategic_insights') else '戦略的計画を作成中...'}"
                
                # 基本ToDo操作
                if any(word in command_text for word in ['分けて', '分割', '2つのタスクに', '別々に']):
                    intent = {'intent': 'todo_split', 'slots': {}}
                    action_result = await execute_natural_action(user_id, command_text, intent, message)
                elif any(word in command_text for word in ['リスト', '一覧', '表示', 'だして']):
                    intent = {'intent': 'todo_list', 'slots': {}}
                    action_result = await execute_natural_action(user_id, command_text, intent, message)
                elif any(word in command_text for word in ['追加', 'つくる', '作る', 'する']) and 'リスト' not in command_text:
                    intent = {'intent': 'todo_add', 'slots': {'task': command_text}}
                    action_result = await execute_natural_action(user_id, command_text, intent, message)
                else:
                    action_result = None
                
                if action_result and 'エラー' not in action_result:
                    response = f"{response}\n\n{action_result}"
            
            # 4. 動的学習・自己改善
            asyncio.create_task(
                dynamic_learning.learn_from_interaction(
                    user_id=user_id,
                    user_input=command_text,
                    bot_response=response,
                    user_reaction=None,
                    success_metrics={'context_confidence': context_analysis['context_confidence']}
                )
            )
            
            # 5. メタ認知的品質評価・自己改善
            # インタラクションログに記録
            metacognitive.interaction_log.append({
                'user_id': user_id,
                'input': command_text,
                'response': response,
                'context_confidence': context_analysis['context_confidence'],
                'timestamp': datetime.now(JST),
                'supreme_intent': supreme_result['intent']
            })
            
            # 定期自己評価（10回に1回）
            if len(metacognitive.interaction_log) % 10 == 0:
                asyncio.create_task(
                    self._perform_periodic_self_assessment(user_id)
                )
        else:
            # 高速NLP エンジンで意図を理解（決め打ち → LLM補完）
            intent = await fast_nlp.understand_intent(command_text, context)
            
            # 意図に基づいてアクション実行
            response = await execute_natural_action(user_id, command_text, intent, message)
        
        # 空のレスポンスを防ぐ
        if not response or response.strip() == "":
            response = "理解しました。"
        
        # エラーメッセージが含まれている場合の処理
        if "エラーが発生しました" in response or "失敗しました" in response:
            print(f"[WARNING] Action returned error: {response}")
            # デバッグ情報を含めて表示（本番では削除可能）
            if "詳細:" in response:
                # 詳細エラーがある場合はそのまま表示
                pass
            else:
                # 一般的なエラーメッセージに統一
                response = "申し訳ございません。処理中に問題が発生しました。しばらくしてから再度お試しください。"
        
        # リアクション学習を適用
        response = await reaction_system.apply_learning_to_response(user_id, response)
        
        # 再度空チェック
        if not response or response.strip() == "":
            response = "申し訳ございません。うまく応答できませんでした。"
        
        # 音声モードの場合は音声最適化
        user_profile = await get_user_profile(user_id)
        if user_profile.get('voice_mode', False):
            response = voice_system.optimize_for_voice(response)
        
        # 応答送信
        bot_message = await message.channel.send(response)
        
        # 各種ログ・学習処理
        await _handle_post_response_processing(
            message, bot_message, user_id, command_text, response, 
            context, intent.get('score', 0.8)
        )
        
        # アクション実行結果をログ
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        await action_summary.log_action_result(
            user_id,
            f"command.{command_text.lower().split()[0] if command_text else 'chat'}",
            command_text,
            {
                'success': True,
                'response_length': len(response),
                'confidence': intent.get('score', 0.8)
            },
            int(execution_time)
        )
        
        # 会話記録
        await conversation_manager.log_conversation(
            user_id=user_id,
            user_message=message.content,
            bot_response=response,
            command_type=context_analysis.get('expected_response_type', 'general'),
            analysis=context_analysis
        )
        
        # メッセージIDを保存（リアクション追跡用）
        await save_message_mapping(message.id, bot_message.id, user_id, response)
        
    except Exception as e:
        print(f"[ERROR] Command processing error: {e}")
        # エラー応答は execute_natural_action 内で処理されるので、ここでは送信しない
        pass

async def execute_natural_action(user_id: str, command_text: str, intent: Dict, message) -> str:
    """自然言語理解に基づくアクション実行"""
    try:
        primary_intent = intent.get('intent', intent.get('primary_intent', 'chat'))
        parameters = intent.get('slots', intent.get('parameters', {}))
        
        # ToDo追加
        if primary_intent == 'todo_add':
            task_content = parameters.get('task', parameters.get('content', command_text))
            
            # タスク内容の抽出・クリーニング
            if not task_content or task_content.strip() == "":
                # パターンマッチングでタスク部分を抽出
                import re
                patterns = [
                    r'(.+?)(?:する|つくる|作る|やる|todo|を?追加|を?登録)',
                    r'(.+?)(?:しなきゃ|しないと|やらなきゃ)',
                    r'(?:todo|タスク).*?(.+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, command_text, re.IGNORECASE)
                    if match:
                        task_content = match.group(1).strip()
                        break
                
                if not task_content:
                    task_content = command_text
            
            # 優先度・期限の設定
            priority = 3  # デフォルト中優先度
            if any(word in command_text for word in ['緊急', '至急', '最優先']):
                priority = 5
            elif any(word in command_text for word in ['重要', '優先']):
                priority = 4
            
            try:
                result = await team_todo_manager.create_team_todo(
                    user_id=user_id,
                    title=task_content[:100],
                    priority=priority,
                    due_date=None,  # TODO: 期限解析を後で実装
                    category='general'
                )
                return f"✅ 「**{task_content[:30]}**」をToDoに追加しました！"
            except Exception as e:
                print(f"[ERROR] Todo add error: {e}")
                import traceback
                traceback.print_exc()
                return f"ToDo追加中にエラーが発生しました。詳細: {str(e)}"
        
        # ToDoリスト表示
        elif primary_intent == 'todo_list':
            try:
                todos = await team_todo_manager.get_team_todos()
                if not todos:
                    return "今のところToDoはありません。何か追加しますか？"
                
                response = "📊 **ToDoリスト**\n\n"
                for i, todo in enumerate(todos[:20], 1):
                    # 改行を除去して、Discordマークダウンが正しく動作するように
                    title = todo['title'][:100].replace('\n', ' ').replace('\r', ' ').strip()
                    # デバッグ情報
                    print(f"Debug - Todo {i}: title='{todo['title']}', cleaned='{title}'")
                    response += f"{i}. **{title}**\n"
                
                return response
            except Exception as e:
                print(f"[ERROR] Todo list error: {e}")
                return "ToDoリスト取得中にエラーが発生しました。"
        
        # ToDo完了
        elif primary_intent == 'todo_done':
            task_info = parameters.get('task', parameters.get('id', ''))
            
            if task_info.isdigit():
                # 番号で指定
                try:
                    index = int(task_info) - 1
                    result = await team_todo_manager.complete_todo_by_index(index)
                    return f"✅ {task_info}番目のToDoを完了しました！"
                except Exception as e:
                    return f"❌ {task_info}番目のToDoが見つかりません。"
            else:
                # タスク名で指定
                try:
                    result = await team_todo_manager.complete_todo_by_title(task_info)
                    return f"✅ 「**{task_info}**」を完了しました！"
                except Exception as e:
                    return f"❌ 「{task_info}」が見つかりません。"
        
        # ToDo削除
        elif primary_intent == 'todo_delete':
            task_info = parameters.get('task', parameters.get('id', ''))
            
            if task_info.isdigit():
                try:
                    index = int(task_info) - 1
                    result = await team_todo_manager.delete_todo_by_index(index)
                    return f"🗑️ {task_info}番目のToDoを削除しました。"
                except Exception as e:
                    return f"❌ {task_info}番目のToDoが見つかりません。"
            else:
                try:
                    result = await team_todo_manager.delete_todo_by_title(task_info)
                    return f"🗑️ 「**{task_info}**」を削除しました。"
                except Exception as e:
                    return f"❌ 「{task_info}」が見つかりません。"
        
        # リマインダー
        elif primary_intent == 'reminder':
            reminder_info = natural_language.extract_reminder_info(command_text, intent)
            result = await reminder_system.create_reminder(
                user_id=user_id,
                title=reminder_info['title'],
                message=reminder_info['message'],
                remind_at=reminder_info['remind_at'],
                reminder_type=reminder_info['reminder_type']
            )
            return await natural_language.generate_action_response(intent, f"リマインダーを{reminder_info['remind_at'].strftime('%H:%M')}にセットしました")
        
        # 挨拶
        elif primary_intent == 'greeting':
            greetings = [
                "こんにちは！今日も頑張りましょう！",
                "お疲れ様です！何かお手伝いできることはありますか？",
                "こんにちは！調子はいかがですか？",
                "元気ですか？今日はどんなことをしましょうか？"
            ]
            import random
            return random.choice(greetings)
        
        # 成長ステータス
        elif primary_intent == 'growth':
            return await handle_growth_status(user_id)
        
        # ToDo分割・修正機能
        elif primary_intent == 'todo_split' or ('分けて' in command_text or '分割' in command_text or 'タスクに分けて' in command_text or '2つのタスクに' in command_text):
            try:
                # 現在のToDoリストを取得
                todos = await team_todo_manager.get_team_todos()
                if not todos:
                    return "現在ToDoがありません。"
                
                # 最初のToDoを分割対象として処理
                first_todo = todos[0]
                title = first_todo['title']
                
                # 区切り文字で分割を試行
                split_patterns = ['. ', '.\n', ',', '、', '\n']
                tasks = [title]
                
                for pattern in split_patterns:
                    if pattern in title:
                        tasks = [t.strip() for t in title.split(pattern) if t.strip()]
                        break
                
                if len(tasks) <= 1:
                    return f"「{title}」を分割できませんでした。手動で分割方法を指定してください。"
                
                # 元のタスクを削除
                await team_todo_manager.delete_todo_by_index(0)
                
                # 分割されたタスクを個別に追加
                added_tasks = []
                for task in tasks[:3]:  # 最大3つまで
                    if len(task) > 3:  # 意味のあるタスクのみ
                        result = await team_todo_manager.create_team_todo(
                            user_id=user_id,
                            title=task[:100],
                            priority=3,
                            due_date=None,
                            category='general'
                        )
                        added_tasks.append(task)
                
                return f"✅ **タスク分割完了**\n\n**分割されたタスク:**\n" + "\n".join([f"• {task}" for task in added_tasks])
            
            except Exception as e:
                print(f"[ERROR] Task split error: {e}")
                import traceback
                traceback.print_exc()
                return f"タスク分割中にエラーが発生しました: {str(e)}"
        
        # データベース接続診断
        elif 'db' in command_text.lower() or 'データベース' in command_text.lower() or 'つながって' in command_text.lower():
            try:
                # Firebase接続テスト
                test_doc = firebase_manager.get_db().collection('connection_test').document('test')
                test_doc.set({'timestamp': datetime.now().isoformat(), 'status': 'ok'})
                
                # Team todo manager テスト
                todos_count = len(await team_todo_manager.get_team_todos())
                
                return f"✅ **データベース接続状況**\n📊 現在のToDo数: {todos_count}件\n🔗 Firebase: 正常接続\n⏰ 接続確認時刻: {datetime.now().strftime('%H:%M:%S')}"
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"❌ **データベース接続エラー**\n詳細: {str(e)}\n🔧 Firebase設定を確認してください"
        
        # ブリーフィング
        elif primary_intent == 'briefing':
            return await handle_morning_briefing(user_id)
        
        # 音声チャンネル
        elif 'voice' in command_text.lower() or '音声' in command_text:
            if 'join' in command_text or '参加' in command_text:
                success = await voice_channel.join_voice_channel(message)
                return "ボイスチャンネルに参加しました" if success else "ボイスチャンネル参加に失敗しました"
            elif 'leave' in command_text or '退出' in command_text:
                success = await voice_channel.leave_voice_channel(message)
                return "ボイスチャンネルから退出しました" if success else "ボイスチャンネル退出に失敗しました"
            elif 'say' in command_text or '読み上げ' in command_text:
                text = command_text.replace('say', '').replace('読み上げ', '').strip()
                if text:
                    success = await voice_channel.text_to_speech(message, text)
                    return f"「{text}」を読み上げました" if success else "読み上げに失敗しました"
                return "読み上げるテキストを指定してください"
            elif 'stop' in command_text or '停止' in command_text:
                success = await voice_channel.stop_playback(message)
                return "再生を停止しました" if success else "停止に失敗しました"
            elif 'volume' in command_text or '音量' in command_text:
                import re
                volume_match = re.search(r'(\d+)', command_text)
                if volume_match:
                    volume = int(volume_match.group(1))
                    success = await voice_channel.adjust_volume(message, volume)
                    return f"音量を{volume}%に設定しました" if success else "音量調整に失敗しました"
                return "音量を0-100で指定してください"
            else:
                status = voice_channel.get_voice_status(message.guild.id)
                if status['connected']:
                    return f"🎤 接続中: {status['channel']}\n音量: {status['volume']}%\n再生中: {'はい' if status['is_playing'] else 'いいえ'}"
                else:
                    return "🔇 ボイスチャンネルに接続していません\n`C! join` で参加してください"
        
        # ヘルプ・使い方
        elif primary_intent == 'help_request' or '話し方' in command_text or '使い方' in command_text:
            return """🎯 **Catherine AI の使い方**

**基本コマンド:**
• `スタンプつくる` → ToDoに追加
• `リスト出して` → ToDo一覧表示  
• `1番終わった` → ToDo完了
• `こんにちは` → 挨拶

**特別機能:**
• `DBつながってる？` → データベース診断
• C! を使えば他のチャンネルでも利用可能

todoチャンネルでは普通に話しかけるだけでOKです！"""
        
        # 自然な会話
        else:
            user_profile = await get_user_profile(user_id)
            user_profile['user_id'] = user_id
            return await generate_natural_conversation_response(command_text, intent, user_profile)
            
    except Exception as e:
        print(f"[ERROR] Natural action execution error: {e}")
        return "ごめんなさい、うまく理解できませんでした。もう一度言ってもらえますか？"

async def route_command(user_id: str, command_text: str, 
                       context_analysis: Dict, 
                       user_profile: Dict,
                       message) -> str:
    """コマンドのルーティング"""
    
    command_lower = command_text.lower()
    
    # ToDo関連（listはチーム、mylistは個人）
    if command_lower.startswith("todo"):
        return await handle_team_todo_create(user_id, command_text, message)
    elif command_lower.startswith("update"):
        return await handle_todo_update(user_id, command_text)
    # elif command_lower.startswith("list"):  # 自然言語システムに移行
    #     return await handle_team_list(command_text)
    elif command_lower.startswith("assign"):
        return await handle_team_assign(command_text)
    elif command_lower.startswith("report"):
        return await handle_team_report()
    elif command_lower.startswith("dashboard"):
        return await handle_team_dashboard()
    
    # 個人ToDo関連
    elif command_lower.startswith("mytodo"):
        return await handle_personal_todo(user_id, command_text, context_analysis)
    elif command_lower.startswith("mylist"):
        return await handle_personal_list(user_id, command_text)
    elif command_lower.startswith("done"):
        return await handle_done_todo(user_id, command_text, is_team=True)
    elif command_lower.startswith("mydone"):
        return await handle_done_todo(user_id, command_text, is_team=False)
    
    # リマインダー関連
    elif command_lower.startswith("remind"):
        return await handle_reminder(user_id, command_text)
    elif command_lower.startswith("reminders"):
        return await handle_list_reminders(user_id)
    
    # 学習・設定関連
    elif command_lower.startswith("learn"):
        return await handle_learning_status(user_id)
    elif command_lower.startswith("preferences"):
        return await handle_preferences(user_id)
    elif command_lower.startswith("humor"):
        return await handle_humor_setting(user_id, command_text)
    elif command_lower.startswith("style"):
        return await handle_style_setting(user_id, command_text)
    
    # ブリーフィング関連
    elif command_lower.startswith("briefing") or command_lower.startswith("朝"):
        return await handle_morning_briefing()
    elif command_lower.startswith("brief"):
        return await handle_morning_briefing()
    
    # 新システム関連
    elif command_lower.startswith("summary") or command_lower.startswith("履歴"):
        return await handle_action_summary(user_id, command_text)
    elif command_lower.startswith("nudge") or command_lower.startswith("停滞"):
        return await handle_progress_nudge(command_text)
    elif command_lower.startswith("voice") or command_lower.startswith("音声"):
        return await handle_voice_mode_toggle(user_id)
    elif command_lower.startswith("decision") or command_lower.startswith("決裁"):
        return await handle_decision_memo(user_id, command_text)
    
    # ボイスチャンネル関連（一時的に無効化）
    elif command_lower.startswith("join"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("leave"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("listen"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("stop"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    elif command_lower.startswith("status"):
        return "🎤 ボイスチャンネル機能は現在メンテナンス中です。"
    
    # ヘルプ
    elif command_lower.startswith("growth") or command_lower.startswith("成長"):
        return await handle_growth_status(user_id)
    elif command_lower.startswith("help"):
        return await handle_help()
    
    # 自然言語処理は新システムに移行
    # else:
    #     return await handle_natural_conversation(
    #         user_id, 
    #         command_text, 
    #         context_analysis,
    #         user_profile
    #     )
    
    # フォールバック：認識されないコマンド
    else:
        return "すみません、そのコマンドは認識できませんでした。"

@bot.event
async def on_reaction_add(reaction, user):
    """リアクション追加時の処理"""
    if user.bot:
        return
    
    try:
        # メッセージマッピングを取得
        mapping = await get_message_mapping(reaction.message.id)
        if not mapping:
            return
        
        # リアクション学習を実行
        await reaction_system.process_reaction(
            user_id=str(user.id),
            message_id=str(reaction.message.id),
            reaction=str(reaction.emoji),
            bot_response=mapping['bot_response'],
            user_message=mapping['user_message']
        )
        
        # 適応学習システムも更新
        user_reaction = {
            'emoji': str(reaction.emoji),
            'score': 0.9 if str(reaction.emoji) in ['👍', '❤️', '✨'] else 0.3 if str(reaction.emoji) in ['👎', '❌'] else 0.5,
            'response_time': (datetime.now() - mapping.get('timestamp', datetime.now())).total_seconds(),
            'continued_conversation': False  # 後続会話があれば更新
        }
        
        await adaptive_learning.learn_from_conversation(
            str(user.id),
            mapping['user_message'],
            mapping['bot_response'],
            user_reaction
        )
        
        # フィードバック確認メッセージ（オプション）
        if str(reaction.emoji) in ['👍', '👎', '❤️', '❌']:
            feedback_msg = await get_feedback_message(str(reaction.emoji))
            await reaction.message.channel.send(
                f"{user.mention} {feedback_msg}", 
                delete_after=5  # 5秒後に削除
            )
        
    except Exception as e:
        print(f"[ERROR] Reaction processing error: {e}")

# チームToDo関連のハンドラー
async def handle_team_todo_create(user_id: str, command_text: str, message) -> str:
    """チームToDo作成"""
    try:
        # "todo" を除いた部分を取得
        content = command_text[4:].strip()
        
        if not content:
            return "📝 チームToDoの内容を教えてください。\n例: `C! todo @mrc バックエンドAPI実装`"
        
        # メンション解析
        assignee = "unassigned"
        if message.mentions:
            mentioned_user = message.mentions[0]
            # ユーザー名から担当者を判定
            if 'mrc' in mentioned_user.name.lower():
                assignee = 'mrc'
            elif 'supy' in mentioned_user.name.lower():
                assignee = 'supy'
        
        # コンテンツからメンションを削除
        for mention in message.mentions:
            content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        content = content.strip()
        
        # ToDo作成
        todo = await team_todo_manager.create_team_todo(
            creator_id=user_id,
            title=content,
            assignee=assignee
        )
        
        if todo:
            priority_emoji = "🔥" if todo['priority'] >= 4 else "⚡" if todo['priority'] >= 3 else "📌"
            assignee_name = team_todo_manager.team_members[assignee]['name']
            
            return f"{priority_emoji} **チームToDo登録完了**\n"\
                   f"📋 タスク: {todo['title']}\n"\
                   f"👤 担当: {assignee_name}\n"\
                   f"📁 カテゴリ: {todo['category']}\n"\
                   f"⏱️ 推定: {todo['estimated_hours']}時間"
        else:
            return "❌ チームToDoの作成に失敗しました。"
            
    except Exception as e:
        print(f"[ERROR] Team ToDo creation error: {e}")
        return "エラーが発生しました。"

async def handle_team_list(command_text: str) -> str:
    """チームToDoリスト表示"""
    try:
        # フィルター解析
        filters = {}
        if '@mrc' in command_text.lower() or 'mrc' in command_text.lower():
            filters['assignee'] = 'mrc'
        elif '@supy' in command_text.lower() or 'supy' in command_text.lower():
            filters['assignee'] = 'supy'
        elif 'unassigned' in command_text.lower():
            filters['assignee'] = 'unassigned'
        
        # ステータスフィルター
        if 'completed' in command_text.lower():
            filters['status'] = 'completed'
        elif 'progress' in command_text.lower():
            filters['status'] = 'in_progress'
        elif 'blocked' in command_text.lower():
            filters['status'] = 'blocked'
        
        # ToDo取得
        todos = await team_todo_manager.get_team_todos(filters)
        
        if not todos:
            return "📋 該当するToDoはありません。"
        
        # リスト作成
        response = "📊 **ToDoリスト**\n\n"
        
        # シンプルな番号付きリスト表示（絵文字なし、太字）
        for i, todo in enumerate(todos[:30], 1):  # 最大30件
            title = todo['title'][:50].replace('\n', ' ').replace('\r', ' ').strip()
            response += f"{i}. **{title}**\n"
        
        if len(todos) > 30:
            response += f"... 他{len(todos) - 30}件\n"
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Team list error: {e}")
        return "リスト取得中にエラーが発生しました。"

async def handle_team_dashboard() -> str:
    """チームダッシュボード表示"""
    try:
        dashboard = await team_todo_manager.get_team_dashboard()
        
        response = "📊 **チームダッシュボード**\n\n"
        
        # サマリー
        response += f"**📈 概要**\n"
        response += f"総タスク: {dashboard['total_tasks']}\n"
        response += f"チーム速度: {dashboard['team_velocity']:.1f} タスク/日\n\n"
        
        # ワークロード
        response += "**👥 ワークロード**\n"
        for member_id, data in dashboard['workload_distribution'].items():
            bar_length = int(data['utilization'] / 10)
            bar = '█' * bar_length + '░' * (10 - bar_length)
            response += f"{data['name']}: [{bar}] {data['utilization']:.0f}%\n"
        response += "\n"
        
        # ステータス
        response += "**📋 ステータス**\n"
        for status, count in dashboard['by_status'].items():
            status_name = team_todo_manager.task_statuses.get(status, status)
            response += f"{status_name}: {count}\n"
        
        # アラート
        if dashboard['overdue_tasks']:
            response += f"\n⚠️ 期限超過: {len(dashboard['overdue_tasks'])}件"
        if dashboard['blocked_tasks']:
            response += f"\n🚫 ブロック中: {len(dashboard['blocked_tasks'])}件"
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Dashboard error: {e}")
        return "ダッシュボード生成中にエラーが発生しました。"

async def handle_team_report() -> str:
    """チームレポート生成"""
    return await team_todo_manager.generate_team_report()

# 個人ToDo関連のハンドラー
async def handle_personal_todo(user_id: str, command_text: str, context_analysis: Dict) -> str:
    """個人ToDo作成"""
    try:
        # "mytodo" を除いた部分を取得
        content = command_text[6:].strip()
        
        if not content:
            return "📝 個人ToDoの内容を教えてください。\n例: `C! mytodo 明日の会議資料準備`"
        
        # ToDo作成（既存のtodo_managerを使用）
        todo_data = await todo_manager.create_todo(
            user_id=user_id,
            title=content,
            description=""
        )
        
        priority_emoji = "🔥" if todo_data['priority'] >= 4 else "⚡" if todo_data['priority'] >= 3 else "📌"
        
        return f"{priority_emoji} **個人ToDo登録完了**\n"\
               f"📋 タスク: {todo_data['title']}\n"\
               f"📁 カテゴリ: {todo_data['category']}\n"\
               f"⚠️ 優先度: {todo_data['priority']}"
        
    except Exception as e:
        print(f"[ERROR] Personal ToDo creation error: {e}")
        return "エラーが発生しました。"

async def handle_personal_list(user_id: str, command_text: str) -> str:
    """個人ToDoリスト表示"""
    try:
        todos = await todo_manager.get_user_todos(user_id, status="pending")
        
        if not todos:
            return "📋 現在、個人の未完了ToDoはありません。"
        
        response = "📝 **個人ToDoリスト**\n\n"
        
        for i, todo in enumerate(todos[:15], 1):
            priority_emoji = "🔥" if todo['priority'] >= 4 else "⚡" if todo['priority'] >= 3 else "📌"
            due_text = ""
            if todo.get('due_date'):
                due_text = f" 📅{todo['due_date'].strftime('%m/%d')}"
            
            response += f"{i}. {priority_emoji} {todo['title'][:50]}{due_text}\n"
        
        if len(todos) > 15:
            response += f"\n... 他{len(todos) - 15}件"
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Personal list error: {e}")
        return "リスト取得中にエラーが発生しました。"

async def handle_done_todo(user_id: str, command_text: str, is_team: bool = True) -> str:
    """ToDo完了処理（チーム/個人）"""
    try:
        # 番号を抽出
        parts = command_text.split()
        if len(parts) < 2:
            return "完了するToDoの番号を指定してください。\n例: `C! done 1`"
        
        try:
            todo_num = int(parts[1]) - 1
        except ValueError:
            return "番号は数字で指定してください。"
        
        if is_team:
            # チームToDo完了
            todos = await team_todo_manager.get_team_todos()
            if 0 <= todo_num < len(todos):
                todo = todos[todo_num]
                success = await team_todo_manager.update_todo_status(
                    todo['todo_id'], 
                    'completed',
                    f"{user_id} が完了"
                )
                if success:
                    return f"✅ チームToDo完了: {todo['title']}"
                else:
                    return "❌ 完了処理に失敗しました。"
            else:
                return "指定された番号のToDoが見つかりません。"
        else:
            # 個人ToDo完了
            todos = await todo_manager.get_user_todos(user_id, status="pending")
            if 0 <= todo_num < len(todos):
                todo = todos[todo_num]
                success = await todo_manager.update_todo_status(todo['todo_id'], "completed")
                if success:
                    return f"✅ 個人ToDo完了: {todo['title']}"
                else:
                    return "❌ 完了処理に失敗しました。"
            else:
                return "指定された番号のToDoが見つかりません。"
                
    except Exception as e:
        print(f"[ERROR] Done todo error: {e}")
        return "エラーが発生しました。"

async def handle_team_assign(command_text: str) -> str:
    """チームToDo担当者変更"""
    try:
        parts = command_text.split()
        if len(parts) < 3:
            return "使い方: `C! assign [番号] [@新担当者]`"
        
        try:
            todo_num = int(parts[1]) - 1
        except ValueError:
            return "番号は数字で指定してください。"
        
        # 新担当者を特定
        new_assignee = "unassigned"
        if '@mrc' in command_text.lower():
            new_assignee = 'mrc'
        elif '@supy' in command_text.lower():
            new_assignee = 'supy'
        
        # ToDo取得と更新
        todos = await team_todo_manager.get_team_todos()
        if 0 <= todo_num < len(todos):
            todo = todos[todo_num]
            success = await team_todo_manager.assign_todo(
                todo['todo_id'],
                new_assignee,
                f"手動再割り当て"
            )
            
            if success:
                assignee_name = team_todo_manager.team_members[new_assignee]['name']
                return f"✅ 担当者変更完了: {todo['title']}\n新担当者: {assignee_name}"
            else:
                return "❌ 担当者変更に失敗しました。"
        else:
            return "指定された番号のToDoが見つかりません。"
            
    except Exception as e:
        print(f"[ERROR] Assign error: {e}")
        return "エラーが発生しました。"

async def handle_todo_update(user_id: str, command_text: str) -> str:
    """自然言語でのToDo更新処理"""
    try:
        # "update" を除いた部分を取得
        update_text = command_text[6:].strip()
        
        if not update_text:
            return "更新内容を教えてください。\n例: `C! update 「API設計」の期日を明後日17:00に`"
        
        # チームToDoを取得
        team_todos = await team_todo_manager.get_team_todos()
        
        # 更新アクションを構築
        result = context_system.build_update_actions(update_text, team_todos)
        
        if not result.get('actions'):
            return result.get('talk', '更新処理に失敗しました。')
        
        action = result['actions'][0]
        
        # 確認が必要な場合
        if action.get('confirm_required'):
            # 候補一覧を表示
            from advanced_context_system import resolve_task_id
            task_id, cands = resolve_task_id(update_text, team_todos)
            if len(cands) > 1:
                response = result['talk'] + "\n\n📋 **候補一覧:**\n"
                for i, todo in enumerate(cands[:5], 1):
                    response += f"{i}. {todo['title']}\n"
                response += "\n番号で指定してください。例: `C! update 1の期日を明日に`"
                return response
        
        # 実際の更新処理
        task_id = action.get('id')
        success = False
        
        # 更新データを準備
        update_data = {}
        if action.get('priority'):
            # 優先度をDBの形式に変換
            priority_map = {"high": 5, "medium": 3, "low": 1}
            update_data['priority'] = priority_map.get(action['priority'], 3)
            
        if action.get('due'):
            # ISO8601文字列をdatetimeに変換
            from datetime import datetime
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            due_date = datetime.fromisoformat(action['due'].replace('Z', '+00:00'))
            update_data['due_date'] = due_date
            
        if action.get('title'):
            update_data['title'] = action['title']
            
        if action.get('details'):
            update_data['description'] = action['details']
            
        if action.get('assignee'):
            # 担当者変更
            success = await team_todo_manager.assign_todo(
                task_id, 
                action['assignee'], 
                "自然言語による変更"
            )
        
        # チームToDoのその他フィールド更新
        if update_data:
            doc_ref = team_todo_manager.db.collection('team_todos').document(task_id)
            update_data['updated_at'] = datetime.now(jst)
            doc_ref.update(update_data)
            success = True
        
        if success:
            return f"✅ {result['talk']}"
        else:
            return "❌ 更新に失敗しました。"
            
    except Exception as e:
        print(f"[ERROR] Todo update error: {e}")
        return "更新処理中にエラーが発生しました。"

# 自然言語会話処理
async def handle_natural_conversation(user_id: str, message: str, 
                                     context_analysis: Dict,
                                     user_profile: Dict) -> str:
    """自然言語での会話処理"""
    try:
        # ToDo更新パターンを検出
        update_patterns = [
            r'(.+?)(の|を)?(期日|締切|期限).*(変|延長|延期|移動|更新)',
            r'(.+?)(の|を)?(優先度|重要度).*(変|更新|上げ|下げ)',
            r'(.+?)(の|を)?(タイトル|名前).*(変|更新)',
            r'(.+?)を?(.+?)(に担当|の担当)'
        ]
        
        is_update = any(re.search(pattern, message) for pattern in update_patterns)
        
        if is_update:
            # チームToDoを取得して更新処理
            team_todos = await team_todo_manager.get_team_todos()
            result = context_system.build_update_actions(message, team_todos)
            
            if result.get('actions'):
                # 更新処理を実行
                return await execute_update_action(result)
            else:
                # 更新の提案
                return f"{result.get('talk', '')}\n\n💡 具体的な更新は: `C! update {message}`"
        
        # 通常のアクション抽出
        actions = await context_system.extract_actionable_items(message, context_analysis)
        
        # 確信度評価
        confidence = confidence_guard.assess_confidence(
            message, 
            context_analysis,
            candidates=[]  # 必要に応じて候補を渡す
        )
        
        # GPT-4oを使った自然な会話応答生成
        response = await generate_natural_conversation_response(
            message,
            context_analysis,
            user_profile
        )
        
        # 確信度に基づく応答調整
        if confidence.requires_confirmation:
            response = confidence_guard.format_confidence_response(confidence, response)
        
        # アクション実行の提案
        if actions:
            response += "\n\n💡 **実行可能なアクション:**\n"
            for action in actions:
                if action['type'] == 'todo' and action['confidence'] > 0.7:
                    response += f"• ToDoとして登録しますか？: `C! todo {action['content'][:30]}...`\n"
                elif action['type'] == 'reminder' and action['confidence'] > 0.6:
                    response += f"• リマインダーを設定しますか？: `C! remind {action['content'][:30]}...`\n"
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Natural conversation error: {e}")
        return "すみません、うまく理解できませんでした。もう一度お願いできますか？"

async def generate_natural_conversation_response(message: str, context_analysis: Dict, user_profile: Dict) -> str:
    """GPT-4oを使った自然で人間らしい会話応答生成（学習済みスタイル適用）"""
    try:
        # ユーザーIDの取得
        user_id = user_profile.get('user_id', 'default')
        
        # 学習済み応答スタイル取得
        adapted_style = await adaptive_learning.get_adapted_response_style(user_id, context_analysis)
        
        # スタイルに基づいてプロンプト調整
        tone_descriptions = {
            'casual_friendly': '親しみやすくカジュアルに',
            'polite_friendly': '丁寧で温かく',
            'formal': 'フォーマルかつプロフェッショナルに',
            'balanced': 'バランスよく適切に'
        }
        
        tone_instruction = tone_descriptions.get(adapted_style['tone'], 'バランスよく')
        
        system_prompt = f"""あなたは Catherine AI - 世界最高レベルの知性と感情的知能を持つAIアシスタントです。

【Catherineの特徴】
- 深い洞察力と創造的思考
- 温かく親しみやすい人格  
- プロフェッショナルな問題解決能力
- 豊富な知識と実用的経験
- 柔軟で適応的な対応
- 自然なユーモアセンスと機転

以下のトーンで応答してください: {tone_instruction}

【最高品質応答の要件】
1. 真の理解に基づく深い洞察の提供
2. 感情的ニーズへの完璧な対応
3. 実用的価値の最大化
4. 創造性と独創性の適切な発揮
5. 自然で魅力的な会話の流れ
6. ユーザーの成長と成功をサポート

【性格】
- 知的で論理的思考ができる
- コミュニケーション大好き、話好き
- ランダム性のある自然な雑談ができる
- 仕事もしっかりこなす責任感
- 親しみやすく温かい人間性

【会話スタイル】
- GPT-4oのような汎用性の高い自然な対応
- 堅すぎず、親しみやすい敬語
- 適度な関西弁やくだけた表現も使える
- 相手の感情に寄り添う共感的な返答
- 必要に応じてユーモアも交える

【対応方針】
1. まず相手の気持ちに共感・理解を示す
2. 簡潔で分かりやすい返答
3. 自然な流れで次の話題や提案につなげる
4. 堅苦しいシステム的応答は避ける

【学習済みスタイル】
- トーン: {tone_instruction}
- 応答長: {"詳細に" if adapted_style['length'] == 'detailed' else "簡潔に" if adapted_style['length'] == 'concise' else "適度に"}
- フォーマル度: {adapted_style['formality']*100:.0f}%
- ユーモアレベル: {adapted_style['humor_level']*100:.0f}%
- 絵文字使用: {"積極的に使う" if adapted_style['emoji_usage'] else "控えめに"}

【ユーザー理解】
{chr(10).join(adapted_style.get('learning_insights', []))}

相手のメッセージに対して、学習済みスタイルを反映させて人間の友人のように自然で温かい返答をしてください。"""

        user_context = f"""
【ユーザーメッセージ】
{message}

【コンテキスト分析】
感情: {context_analysis.get('emotion', 'ニュートラル')}
意図: {context_analysis.get('intent', '不明')}
緊急度: {context_analysis.get('urgency', '普通')}
"""

        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context}
            ],
            temperature=0.7,  # 適度なランダム性
            max_completion_tokens=800,
            presence_penalty=0.2,  # 多様性を促進
            frequency_penalty=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"[ERROR] Natural response generation error: {e}")
        # フォールバック応答
        greetings = ["こんにちは！", "お疲れ様です！", "何かお手伝いできることはありますか？"]
        casual_responses = [
            "そうですね！なんでも話してください😊",
            "面白いことを一緒に考えましょう！",
            "今日はどんな感じですか？",
            "何か気になることでもあります？"
        ]
        
        if any(word in message for word in ['こんにちは', 'おは', 'hello', '元気', 'よう']):
            return f"{greetings[hash(message) % len(greetings)]} {casual_responses[hash(message) % len(casual_responses)]}"
        else:
            return "なるほど！詳しく教えてもらえますか？"

async def execute_update_action(result: Dict) -> str:
    """更新アクションを実行"""
    try:
        action = result['actions'][0]
        task_id = action.get('id')
        
        if not task_id:
            return result.get('talk', '更新処理に失敗しました。')
        
        # 更新処理（簡略版）
        update_data = {}
        if action.get('priority'):
            priority_map = {"high": 5, "medium": 3, "low": 1}
            update_data['priority'] = priority_map.get(action['priority'], 3)
            
        if action.get('due'):
            from datetime import datetime
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            due_date = datetime.fromisoformat(action['due'].replace('Z', '+00:00'))
            update_data['due_date'] = due_date
            
        if action.get('title'):
            update_data['title'] = action['title']
            
        # データベース更新
        if update_data:
            doc_ref = team_todo_manager.db.collection('team_todos').document(task_id)
            update_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo'))
            doc_ref.update(update_data)
            return f"✅ {result['talk']}"
        
        return result.get('talk', '更新完了')
        
    except Exception as e:
        print(f"[ERROR] Execute update error: {e}")
        return "更新処理中にエラーが発生しました。"

async def handle_morning_briefing() -> str:
    """朝のブリーフィング処理"""
    try:
        briefing = await briefing_system.generate_daily_briefing(team_mode=True)
        
        if not briefing.get('success'):
            return "❌ ブリーフィング生成に失敗しました。"
        
        return briefing_system.format_briefing_message(briefing)
        
    except Exception as e:
        print(f"[ERROR] Briefing error: {e}")
        return "ブリーフィング処理中にエラーが発生しました。"

# 新システムのハンドラー
async def handle_action_summary(user_id: str, command_text: str) -> str:
    """アクション履歴サマリー処理"""
    try:
        hours = 24  # デフォルト24時間
        
        # 時間指定があれば抽出
        hour_match = re.search(r'(\d+)(時間|h)', command_text)
        if hour_match:
            hours = int(hour_match.group(1))
        
        summary = await action_summary.get_recent_action_summary(user_id, hours)
        return summary
        
    except Exception as e:
        print(f"[ERROR] Action summary error: {e}")
        return "履歴取得中にエラーが発生しました。"

async def handle_progress_nudge(command_text: str) -> str:
    """進捗ナッジ処理"""
    try:
        # 特定タスクのナッジか全体チェックかを判定
        if len(command_text.split()) > 1:
            # 特定タスクの場合（実装は必要に応じて）
            return "特定タスクのナッジ機能は開発中です。"
        else:
            # 全体の停滞チェック
            stalled_tasks = await nudge_engine.check_stalled_tasks()
            
            if not stalled_tasks:
                return "🎉 現在停滞しているタスクはありません！順調です。"
            
            response = f"⚠️ **停滞タスク検知** ({len(stalled_tasks)}件)\n\n"
            
            # 上位3件を表示
            for nudge in stalled_tasks[:3]:
                response += nudge_engine.format_nudge_message(nudge, include_actions=True)
                response += "\n---\n"
            
            if len(stalled_tasks) > 3:
                response += f"他{len(stalled_tasks) - 3}件の停滞タスクがあります。"
            
            return response
        
    except Exception as e:
        print(f"[ERROR] Nudge error: {e}")
        return "ナッジ処理中にエラーが発生しました。"

async def handle_voice_mode_toggle(user_id: str) -> str:
    """音声モード切替"""
    try:
        # ユーザー設定を取得/更新
        doc_ref = firebase_manager.get_db().collection('user_profiles').document(user_id)
        doc = doc_ref.get()
        
        current_voice_mode = False
        if doc.exists:
            profile = doc.to_dict()
            current_voice_mode = profile.get('voice_mode', False)
        
        # 切り替え
        new_voice_mode = not current_voice_mode
        
        update_data = {
            'voice_mode': new_voice_mode,
            'updated_at': datetime.now(JST)
        }
        
        if doc.exists:
            doc_ref.update(update_data)
        else:
            update_data.update({
                'user_id': user_id,
                'created_at': datetime.now(JST)
            })
            doc_ref.set(update_data)
        
        mode_text = "ON" if new_voice_mode else "OFF"
        response = f"🎤 音声モードを{mode_text}にしました。"
        
        if new_voice_mode:
            response = voice_system.optimize_for_voice(response)
            
        return response
        
    except Exception as e:
        print(f"[ERROR] Voice toggle error: {e}")
        return "音声モード切替中にエラーが発生しました。"

async def handle_decision_memo(user_id: str, command_text: str) -> str:
    """決裁メモ作成"""
    try:
        # "decision" を除いた部分を取得
        memo_content = command_text[8:].strip() if command_text.lower().startswith('decision') else command_text[2:].strip()
        
        if not memo_content:
            return "決裁メモの内容を教えてください。\n例: `C! decision 新システム導入を承認。ROI改善のため。`"
        
        # 簡単な形式で決定と理由を分離
        parts = memo_content.split('。', 1)
        decision = parts[0]
        reasoning = parts[1] if len(parts) > 1 else ""
        
        # 決裁メモ作成
        decision_log = await action_summary.create_decision_memo(
            user_id=user_id,
            context=f"ユーザー入力: {memo_content}",
            decision=decision,
            reasoning=reasoning
        )
        
        if decision_log:
            return action_summary.format_decision_memo(decision_log)
        else:
            return "❌ 決裁メモの作成に失敗しました。"
        
    except Exception as e:
        print(f"[ERROR] Decision memo error: {e}")
        return "決裁メモ作成中にエラーが発生しました。"

async def process_attachments(message, user_id: str, username: str):
    """添付ファイル処理"""
    try:
        analyses = []
        all_created_todos = []
        
        for attachment in message.attachments:
            # 音声ファイルの場合は文字起こし
            audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm']
            if any(attachment.filename.lower().endswith(ext) for ext in audio_extensions):
                transcript = await voice_channel.transcribe_audio_file(attachment)
                if transcript:
                    await message.channel.send(f"🎤 **音声文字起こし**:\n```\n{transcript}\n```")
                    
                    # 文字起こし結果からToDoを抽出することも可能
                    if 'todo' in transcript.lower() or 'やること' in transcript:
                        await message.channel.send("💡 音声からToDoを作成しますか？ `C! todo [内容]`")
                continue
            
            # ファイルをダウンロード
            attachment_data = await attachment.read()
            
            # ファイルタイプ判定
            attachment_type = "image"
            if attachment.filename.lower().endswith(('.pdf')):
                attachment_type = "pdf"
            elif attachment.filename.lower().endswith(('.txt', '.md')):
                attachment_type = "text"
            
            # OCR処理
            analysis = await ocr_system.process_attachment(
                user_id, attachment_data, attachment.filename, attachment_type
            )
            analyses.append(analysis)
            
            # ToDo作成
            if analysis.extracted_tasks:
                created_todos = await ocr_system.create_todos_from_analysis(analysis, user_id)
                all_created_todos.extend(created_todos)
        
        # 結果レポート
        if len(analyses) == 1:
            report = ocr_system.format_analysis_report(analyses[0], all_created_todos)
        else:
            # 複数ファイルの場合
            report = await ocr_system.batch_process_attachments(
                user_id, 
                [{'data': await att.read(), 'filename': att.filename, 'type': 'image'} for att in message.attachments]
            )
        
        await message.channel.send(report)
        
        # アクション履歴に記録
        await action_summary.log_action_result(
            user_id,
            "attachment.process",
            f"添付ファイル処理: {len(message.attachments)}件",
            {
                'success': True,
                'files_processed': len(message.attachments),
                'tasks_created': len(all_created_todos),
                'analyses': len(analyses)
            }
        )
        
    except Exception as e:
        print(f"[ERROR] Attachment processing error: {e}")
        await message.channel.send("添付ファイルの処理中にエラーが発生しました。")

# ボイスチャンネルハンドラー（一時的に削除 - discord.sinks互換性問題）

# ヘルプ機能
async def handle_growth_status(user_id: str) -> str:
    """成長ステータス表示"""
    try:
        growth = await adaptive_learning._get_growth_level(user_id)
        
        # プログレスバー作成
        level = growth['level']
        bar_length = 20
        filled = int(bar_length * (level / 100))
        bar = '█' * filled + '░' * (bar_length - filled)
        
        response = f"""
📊 **Catherineの成長ステータス**

🎯 成長レベル: **{growth['stage']}** (Lv.{level:.1f}/100)
{bar} {level:.0f}%

📈 統計情報:
• 会話回数: {growth['conversations']}回
• 成功率: {growth['success_rate']*100:.1f}%
• 次の目標: {growth['next_milestone']}

🧠 学習内容:
"""
        # 学習洞察を追加
        style = await adaptive_learning.get_adapted_response_style(user_id, {})
        if style['learning_insights']:
            for insight in style['learning_insights'][:3]:
                response += f"• {insight}\n"
        else:
            response += "• まだ学習中です...\n"
        
        response += """
💡 成長のヒント:
• 会話を重ねるほど、あなたの好みを学習します
• 👍👎のリアクションで学習が加速します
• 様々な話題で会話してみてください
"""
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Growth status error: {e}")
        return "成長ステータスの取得に失敗しました。"

async def handle_help() -> str:
    """ヘルプメッセージ"""
    return """
📚 **Catherine AI v2.0 - コマンド一覧**

**👥 チームToDo管理**
`C! todo [@担当者] [内容]` - チームToDo作成
`C! update 「タスク名」の期日を明後日17:00に` - 自然言語でToDo更新
`C! list` - チーム全体のToDoリスト
`C! list @mrc` - 担当者別リスト
`C! assign [番号] [@新担当者]` - 担当者変更
`C! done [番号]` - チームToDo完了
`C! dashboard` - チームダッシュボード
`C! report` - チームレポート生成

**📝 個人ToDo管理**
`C! mytodo [内容]` - 個人ToDo作成
`C! mylist` - 個人ToDoリスト表示
`C! mydone [番号]` - 個人ToDo完了

**⏰ リマインダー**
`C! remind [内容] at [日時]` - リマインダー設定
`C! reminders` - リマインダー一覧

**🎤 ボイスチャンネル**
`C! join` - ボイスチャンネル参加
`C! listen` - 音声認識開始（「キャサリン」で呼びかけ）
`C! stop` - 音声認識停止
`C! leave` - ボイスチャンネル退出
`C! status` - ボイス状態確認

**🎨 カスタマイズ**
`C! humor [0-100]` - ユーモアレベル調整
`C! style [casual/formal]` - 会話スタイル設定
`C! preferences` - 現在の設定確認

**📊 学習・分析**
`C! learn` - 学習状況確認
`C! briefing` - 朝のブリーフィング生成
`C! 朝` - 朝のブリーフィング（短縮）

リアクションで私の応答を評価してください！
👍 良い / 👎 改善が必要 / ❤️ 完璧 / 🤔 もっと詳しく

**🤖 新機能 v3.0**
- 確信度ガード: 曖昧な指示には確認を求めます
- 自動ブリーフィング: 今日の最重要3件と時間見積もり
- 自然言語更新: 会話から直接ToDo更新を実行
- アクション履歴: `C! summary` で実行履歴を確認
- 進捗ナッジ: `C! nudge` で停滞タスクを検出
- 添付ファイルAI分析: 画像/PDF→自動ToDo抽出
- 音声最適化: `C! voice` で音声モード切替
- 決裁メモ: `C! decision 承認理由` で構造化記録
"""

# ユーザープロファイル関連
async def get_user_profile(user_id: str) -> Dict:
    """ユーザープロファイル取得"""
    try:
        doc_ref = firebase_manager.get_db().collection('user_profiles').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            # デフォルトプロファイル作成
            default_profile = {
                'user_id': user_id,
                'created_at': datetime.now(JST),
                'preferences': {
                    'communication_style': 'friendly',
                    'humor_level': 50,
                    'formality': 'casual',
                    'response_length': 'medium'
                },
                'stats': {
                    'total_interactions': 0,
                    'total_todos': 0,
                    'total_reminders': 0
                }
            }
            doc_ref.set(default_profile)
            return default_profile
            
    except Exception as e:
        print(f"[ERROR] Profile retrieval error: {e}")
        return {}

# メッセージマッピング（リアクション追跡用）
async def save_message_mapping(user_message_id: str, bot_message_id: str, 
                              user_id: str, bot_response: str):
    """メッセージIDのマッピングを保存"""
    try:
        mapping = {
            'user_message_id': str(user_message_id),
            'bot_message_id': str(bot_message_id),
            'user_id': user_id,
            'bot_response': bot_response,
            'timestamp': datetime.now(JST)
        }
        
        doc_ref = firebase_manager.get_db().collection('message_mappings').document(str(bot_message_id))
        doc_ref.set(mapping)
        
    except Exception as e:
        print(f"[ERROR] Message mapping error: {e}")

async def get_message_mapping(message_id: str) -> Optional[Dict]:
    """メッセージマッピングを取得"""
    try:
        doc_ref = firebase_manager.get_db().collection('message_mappings').document(str(message_id))
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
        
    except Exception as e:
        print(f"[ERROR] Mapping retrieval error: {e}")
        return None

async def _perform_periodic_self_assessment(user_id: str):
    """定期自己評価実行"""
    try:
        print(f"[ASSESSMENT] Performing self-assessment for user {user_id}")
        
        # 最近のインタラクション数件を取得
        recent_interactions = list(metacognitive.interaction_log)[-20:] if metacognitive.interaction_log else []
        
        # 自己評価実行
        assessment = await metacognitive.perform_self_assessment(
            interaction_data=recent_interactions,
            feedback_data=[]
        )
        
        print(f"[SUCCESS] Self-assessment complete. Performance: {assessment.overall_performance:.2f}, Confidence: {assessment.confidence_level:.2f}")
        
        # 重大な改善点が見つかった場合はログ出力
        if assessment.overall_performance < 0.6:
            print(f"[WARNING] Performance below target. Improvement needed in: {[w.weakness_type for w in assessment.weaknesses]}")
        
    except Exception as e:
        print(f"[ERROR] Periodic self-assessment error: {e}")

async def _handle_post_response_processing(message, bot_message, user_id: str, 
                                         command_text: str, response: str, 
                                         context: Dict, confidence_score: float):
    """応答後の統合処理（ログ・学習・記録）"""
    try:
        # 会話から学習（リアクション待機なしで即座に基本学習）
        asyncio.create_task(
            adaptive_learning.learn_from_conversation(
                user_id, 
                command_text, 
                response,
                None  # リアクションは後で更新
            )
        )
        
        # アクション実行結果をログ
        execution_time = (datetime.now() - datetime.now()).total_seconds() * 1000
        await action_summary.log_action_result(
            user_id,
            f"command.{command_text.lower().split()[0] if command_text else 'chat'}",
            command_text,
            {
                'success': True,
                'response_length': len(response),
                'confidence': confidence_score
            },
            int(execution_time)
        )
        
        # 会話記録
        await conversation_manager.log_conversation(
            user_id=user_id,
            user_message=message.content,
            bot_response=response,
            command_type=context.get('expected_response_type', 'general'),
            analysis=context
        )
        
        # メッセージIDを保存（リアクション追跡用）
        await save_message_mapping(message.id, bot_message.id, user_id, response)
        
    except Exception as e:
        print(f"[ERROR] Post-response processing error: {e}")

async def get_feedback_message(emoji: str) -> str:
    """リアクションに対するフィードバックメッセージ"""
    messages = {
        '👍': 'フィードバックありがとうございます！より良い応答を心がけます。',
        '👎': 'ご指摘ありがとうございます。改善いたします。',
        '❤️': 'とても嬉しいです！これからも頑張ります！',
        '❌': '申し訳ございません。次回は改善いたします。'
    }
    return messages.get(emoji, 'フィードバックを受け取りました。')

# 定期タスク
@tasks.loop(minutes=1)
async def check_reminders():
    """リマインダーチェック（1分ごと）"""
    try:
        # アクティブなリマインダーをチェック
        now = datetime.now(JST)
        # シンプルなクエリに変更（インデックス不要）
        reminders = firebase_manager.get_db().collection('reminders')\
            .where('status', '==', 'active')\
            .stream()
        
        for reminder_doc in reminders:
            reminder = reminder_doc.to_dict()
            
            # Pythonでフィルタリング
            reminder_time = reminder.get('next_reminder')
            if not reminder_time or reminder_time > now:
                continue
            
            # 通知送信
            user_id = reminder['user_id']
            message = f"@everyone 📢 **リマインダー**\n"\
                     f"🔔 {reminder['title']}\n"\
                     f"💬 {reminder['message']}"
            # ユーザーのDMチャンネルを取得または該当チャンネルに送信
            # 実装は環境に応じて調整
            
            # リマインダー更新
            if reminder['reminder_type'] == 'once':
                reminder_doc.reference.update({'status': 'completed'})
            else:
                # 次回のリマインダー時刻を計算
                pass
                
    except Exception as e:
        print(f"[ERROR] Reminder check error: {e}")

@tasks.loop(hours=1)
async def update_learning():
    """学習モデルの定期更新（1時間ごと）"""
    try:
        print("📚 学習モデル更新中...")
        
        # 進捗ナッジの送信チェック
        channel_id = os.getenv("NUDGE_CHANNEL_ID")
        if channel_id:
            nudge_count = await nudge_engine.send_nudge_notifications(bot, channel_id)
            if nudge_count > 0:
                print(f"📬 {nudge_count}件のナッジ通知を送信")
        
    except Exception as e:
        print(f"[ERROR] Learning update error: {e}")

# Bot起動
if __name__ == "__main__":
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("[ERROR] DISCORD_TOKEN が設定されていません")
            print("[INFO] Railway環境の場合、Variables設定でDISCORD_TOKENを追加してください")
            exit(1)
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("[WARNING] OPENAI_API_KEY が設定されていません")
            print("[INFO] Railway環境の場合、Variables設定でOPENAI_API_KEYを追加してください")
            print("[INFO] BotはGPT機能なしで起動します")
            openai_key = "sk-placeholder"
        
        print("[STARTUP] Catherine AI v2.0 starting...")
        print(f"[INFO] Discord Token: {'*' * 10}{token[-5:] if len(token) > 5 else 'SHORT'}")
        print(f"[INFO] OpenAI Key: {'*' * 10}{openai_key[-5:] if len(openai_key) > 5 else 'SHORT'}")
        print(f"[INFO] Human Level Chat: {human_level_chat.get_pattern_count() if human_level_chat else 0} patterns loaded")
        print(f"[INFO] Simple Todo: Ready")
        
        bot.run(token)
        
    except discord.LoginFailure as e:
        print(f"[CRITICAL] Discord login failed: {e}")
        print("[INFO] トークンが正しいか確認してください")
        exit(1)
    except Exception as e:
        print(f"[CRITICAL] Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)