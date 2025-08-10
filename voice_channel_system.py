#!/usr/bin/env python3
"""
Voice Channel System
Discord ボイスチャンネル機能：音声認識・TTS・音声コマンド
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import discord
from discord import FFmpegPCMAudio
import pytz
from openai import OpenAI
from voice_optimized_system import VoiceOptimizedSystem

JST = pytz.timezone('Asia/Tokyo')

class VoiceChannelSystem:
    def __init__(self, openai_client: OpenAI, bot: discord.Client):
        self.openai_client = openai_client
        self.bot = bot
        self.voice_system = VoiceOptimizedSystem(openai_client)
        
        # ボイス接続の管理
        self.voice_connections = {}  # guild_id -> VoiceClient
        self.listening_users = {}    # user_id -> listening_state
        self.voice_queues = {}       # guild_id -> audio_queue
        
        # 音声設定
        self.voice_settings = {
            'listen_timeout': 30,      # 音声認識タイムアウト（秒）
            'auto_disconnect': 300,    # 自動切断時間（秒）
            'noise_threshold': 0.3,    # ノイズ閾値
            'response_delay': 1.0,     # 応答遅延（秒）
        }
        
        # TTS設定
        self.tts_settings = {
            'voice': 'alloy',          # OpenAI TTS音声
            'speed': 1.0,              # 話速
            'format': 'mp3'            # 音声フォーマット
        }
    
    async def join_voice_channel(self, ctx) -> bool:
        """ボイスチャンネル参加"""
        try:
            # ユーザーがボイスチャンネルにいるかチェック
            if not ctx.author.voice:
                await ctx.send("⚠️ 先にボイスチャンネルに参加してください。")
                return False
            
            channel = ctx.author.voice.channel
            guild_id = ctx.guild.id
            
            # 既に接続済みの場合
            if guild_id in self.voice_connections:
                await ctx.send(f"🎤 既に {channel.name} に接続中です。")
                return True
            
            # ボイスチャンネルに接続
            voice_client = await channel.connect()
            self.voice_connections[guild_id] = voice_client
            self.voice_queues[guild_id] = asyncio.Queue()
            
            await ctx.send(f"🎤 **{channel.name}** に参加しました！\n"
                         f"📢 `C! listen` で音声認識開始\n"
                         f"🔇 `C! leave` で退出")
            
            # 自動切断タスクを開始
            asyncio.create_task(self._auto_disconnect_task(guild_id))
            
            return True
            
        except Exception as e:
            print(f"❌ Voice join error: {e}")
            await ctx.send("ボイスチャンネルへの参加に失敗しました。")
            return False
    
    async def leave_voice_channel(self, ctx) -> bool:
        """ボイスチャンネル退出"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.voice_connections:
                await ctx.send("📵 ボイスチャンネルに接続していません。")
                return False
            
            voice_client = self.voice_connections[guild_id]
            
            # 音声認識を停止
            await self.stop_listening(ctx, send_message=False)
            
            # 切断
            await voice_client.disconnect()
            
            # クリーンアップ
            del self.voice_connections[guild_id]
            if guild_id in self.voice_queues:
                del self.voice_queues[guild_id]
            
            await ctx.send("👋 ボイスチャンネルから退出しました。")
            return True
            
        except Exception as e:
            print(f"❌ Voice leave error: {e}")
            await ctx.send("ボイスチャンネルからの退出に失敗しました。")
            return False
    
    async def start_listening(self, ctx) -> bool:
        """音声認識開始"""
        try:
            guild_id = ctx.guild.id
            user_id = str(ctx.author.id)
            
            if guild_id not in self.voice_connections:
                await ctx.send("⚠️ 先に `C! join` でボイスチャンネルに参加してください。")
                return False
            
            if user_id in self.listening_users:
                await ctx.send("🎧 既に音声認識中です。")
                return True
            
            # リスニング状態を設定
            self.listening_users[user_id] = {
                'guild_id': guild_id,
                'channel_id': ctx.channel.id,
                'start_time': datetime.now(JST),
                'active': True
            }
            
            voice_client = self.voice_connections[guild_id]
            
            # 音声キャプチャを開始
            voice_client.start_recording(
                discord.sinks.WaveSink(),
                self._voice_callback,
                ctx
            )
            
            await ctx.send("🎧 **音声認識開始**\n"
                         f"🗣️ 話しかけてください（{self.voice_settings['listen_timeout']}秒でタイムアウト）\n"
                         f"🔇 `C! stop` で停止")
            
            # タイムアウトタスクを開始
            asyncio.create_task(self._listening_timeout_task(user_id, ctx))
            
            return True
            
        except Exception as e:
            print(f"❌ Listening start error: {e}")
            await ctx.send("音声認識の開始に失敗しました。")
            return False
    
    async def stop_listening(self, ctx, send_message: bool = True) -> bool:
        """音声認識停止"""
        try:
            guild_id = ctx.guild.id
            user_id = str(ctx.author.id)
            
            if user_id not in self.listening_users:
                if send_message:
                    await ctx.send("🔇 音声認識は開始されていません。")
                return False
            
            # リスニング停止
            del self.listening_users[user_id]
            
            if guild_id in self.voice_connections:
                voice_client = self.voice_connections[guild_id]
                voice_client.stop_recording()
            
            if send_message:
                await ctx.send("🔇 音声認識を停止しました。")
            
            return True
            
        except Exception as e:
            print(f"❌ Listening stop error: {e}")
            if send_message:
                await ctx.send("音声認識の停止に失敗しました。")
            return False
    
    async def _voice_callback(self, sink: discord.sinks.WaveSink, channel, *args):
        """音声データコールバック"""
        try:
            if not sink.audio_data:
                return
            
            # 最新の音声データを取得
            for user_id, audio in sink.audio_data.items():
                if str(user_id) in self.listening_users:
                    # 音声認識を実行
                    await self._process_voice_input(user_id, audio.file, channel)
                    
        except Exception as e:
            print(f"❌ Voice callback error: {e}")
    
    async def _process_voice_input(self, user_id: int, audio_file: io.BytesIO, 
                                  channel) -> None:
        """音声入力処理"""
        try:
            user_id_str = str(user_id)
            
            if user_id_str not in self.listening_users:
                return
            
            # Whisper APIで音声認識
            audio_file.seek(0)
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_file.read())
                temp_file_path = temp_file.name
            
            try:
                # Whisper API呼び出し
                with open(temp_file_path, 'rb') as audio:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language="ja"
                    )
                
                recognized_text = transcript.text
                
                if recognized_text and len(recognized_text.strip()) > 0:
                    # 音声認識の誤変換を修正
                    corrected_text = self.voice_system.correct_voice_recognition(recognized_text)
                    
                    # コマンド処理
                    await self._handle_voice_command(user_id_str, corrected_text, channel)
                
            finally:
                # 一時ファイル削除
                os.unlink(temp_file_path)
                
        except Exception as e:
            print(f"❌ Voice processing error: {e}")
    
    async def _handle_voice_command(self, user_id: str, text: str, channel) -> None:
        """音声コマンド処理"""
        try:
            # 「キャサリン」で始まる場合のみ処理
            wake_words = ['キャサリン', 'catherine', 'ケイ']
            text_lower = text.lower()
            
            if not any(wake_word in text_lower for wake_word in wake_words):
                return
            
            # ウェイクワードを除去
            for wake_word in wake_words:
                text = text.replace(wake_word, '').replace(wake_word.capitalize(), '').strip()
            
            if len(text) < 2:
                await self._speak_response("はい、何でしょうか？", channel)
                return
            
            # 音声認識結果を表示
            await channel.send(f"🎤 **音声認識**: {text}")
            
            # コマンド変換（自然言語→コマンド形式）
            command = await self._convert_voice_to_command(text)
            
            if command:
                # 擬似メッセージオブジェクト作成
                class VoiceMessage:
                    def __init__(self, content, author_id, channel):
                        self.content = f"C! {command}"
                        self.author = type('obj', (object,), {'id': int(user_id)})()
                        self.channel = channel
                        self.attachments = []
                
                # コマンド処理を実行
                voice_message = VoiceMessage(command, user_id, channel)
                # 既存のprocess_command関数を使用
                # await process_command(voice_message, user_id, "VoiceUser")
                
                # 簡易応答（実際の実装では上記のprocess_commandを使用）
                response = f"音声コマンドを実行中: {command}"
                await self._speak_response(response, channel)
            else:
                await self._speak_response("申し訳ございません。コマンドを理解できませんでした。", channel)
                
        except Exception as e:
            print(f"❌ Voice command handling error: {e}")
    
    async def _convert_voice_to_command(self, text: str) -> Optional[str]:
        """音声コマンド変換"""
        try:
            # 基本的なコマンドマッピング
            command_patterns = {
                r'(リスト|一覧)': 'list',
                r'(やること|todo|タスク).*作成': 'todo {}',
                r'(やること|todo|タスク).*完了': 'done {}',
                r'(更新|変更)': 'update {}',
                r'(ブリーフィング|朝の報告)': 'briefing',
                r'(履歴|サマリー)': 'summary',
                r'(停滞|ナッジ)': 'nudge',
                r'(ヘルプ|助けて)': 'help'
            }
            
            import re
            
            for pattern, command_template in command_patterns.items():
                if re.search(pattern, text):
                    if '{}' in command_template:
                        # テキストから関連部分を抽出
                        content = re.sub(pattern, '', text).strip()
                        return command_template.format(content)
                    else:
                        return command_template
            
            # マッチしない場合はそのままテキストとして処理
            return text
            
        except Exception as e:
            print(f"❌ Voice command conversion error: {e}")
            return None
    
    async def _speak_response(self, text: str, channel) -> None:
        """音声応答（TTS）"""
        try:
            guild_id = channel.guild.id
            
            if guild_id not in self.voice_connections:
                return
            
            voice_client = self.voice_connections[guild_id]
            
            # 音声最適化
            optimized_text = self.voice_system.optimize_for_voice(text, context="tts")
            
            # OpenAI TTS APIで音声生成
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=self.tts_settings['voice'],
                input=optimized_text,
                speed=self.tts_settings['speed']
            )
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            try:
                # Discord音声再生
                if not voice_client.is_playing():
                    audio_source = FFmpegPCMAudio(temp_file_path)
                    voice_client.play(audio_source)
                    
                    # 再生完了を待機
                    while voice_client.is_playing():
                        await asyncio.sleep(0.1)
                
            finally:
                # 一時ファイル削除
                await asyncio.sleep(1)  # 再生完了を確実に待つ
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                
        except Exception as e:
            print(f"❌ TTS error: {e}")
    
    async def _auto_disconnect_task(self, guild_id: int) -> None:
        """自動切断タスク"""
        try:
            await asyncio.sleep(self.voice_settings['auto_disconnect'])
            
            if guild_id in self.voice_connections:
                voice_client = self.voice_connections[guild_id]
                
                # アクティブなリスナーがいない場合は切断
                active_listeners = [
                    user_id for user_id, state in self.listening_users.items()
                    if state['guild_id'] == guild_id and state['active']
                ]
                
                if not active_listeners:
                    await voice_client.disconnect()
                    del self.voice_connections[guild_id]
                    
                    # チャンネルに通知
                    for channel in voice_client.guild.text_channels:
                        if channel.name == 'general' or 'bot' in channel.name:
                            await channel.send("🔇 非アクティブのため自動的に退出しました。")
                            break
                            
        except Exception as e:
            print(f"❌ Auto disconnect error: {e}")
    
    async def _listening_timeout_task(self, user_id: str, ctx) -> None:
        """音声認識タイムアウトタスク"""
        try:
            await asyncio.sleep(self.voice_settings['listen_timeout'])
            
            if user_id in self.listening_users:
                await self.stop_listening(ctx, send_message=True)
                await ctx.send("⏰ 音声認識がタイムアウトしました。")
                
        except Exception as e:
            print(f"❌ Listening timeout error: {e}")
    
    def get_voice_status(self, guild_id: int) -> Dict:
        """ボイス状態取得"""
        try:
            is_connected = guild_id in self.voice_connections
            active_listeners = [
                user_id for user_id, state in self.listening_users.items()
                if state['guild_id'] == guild_id and state['active']
            ]
            
            return {
                'connected': is_connected,
                'channel': self.voice_connections[guild_id].channel.name if is_connected else None,
                'listening_count': len(active_listeners),
                'active_listeners': active_listeners
            }
            
        except Exception as e:
            print(f"❌ Voice status error: {e}")
            return {'connected': False, 'listening_count': 0, 'active_listeners': []}