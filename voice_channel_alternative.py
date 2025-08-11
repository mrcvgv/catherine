#!/usr/bin/env python3
"""
Voice Channel Alternative System
discord.sinks互換性問題の代替実装
音声録音・認識・TTS機能を別アプローチで実現
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import pytz
from openai import OpenAI

JST = pytz.timezone('Asia/Tokyo')

class VoiceChannelAlternative:
    def __init__(self, openai_client: OpenAI, bot: discord.Client):
        self.openai_client = openai_client
        self.bot = bot
        
        # ボイス接続管理
        self.voice_connections = {}  # guild_id -> VoiceClient
        self.voice_states = {}       # guild_id -> state
        
        # 音声設定
        self.voice_settings = {
            'auto_disconnect': 300,    # 5分で自動切断
            'volume': 0.5,            # デフォルト音量
        }
        
        # TTS設定
        self.tts_settings = {
            'voice': 'alloy',          # OpenAI TTS音声
            'speed': 1.0,              # 話速
            'model': 'tts-1'           # TTSモデル
        }
    
    async def join_voice_channel(self, ctx) -> bool:
        """ボイスチャンネル参加（シンプル版）"""
        try:
            # ユーザーがボイスチャンネルにいるかチェック
            if not ctx.author.voice:
                await ctx.send("⚠️ 先にボイスチャンネルに参加してください。")
                return False
            
            channel = ctx.author.voice.channel
            guild_id = ctx.guild.id
            
            # 既に接続済みの場合
            if guild_id in self.voice_connections:
                voice_client = self.voice_connections[guild_id]
                if voice_client.is_connected():
                    await ctx.send(f"🎤 既に {channel.name} に接続中です。")
                    return True
                else:
                    # 切断されていた場合は削除
                    del self.voice_connections[guild_id]
            
            # ボイスチャンネルに接続
            try:
                voice_client = await channel.connect()
                self.voice_connections[guild_id] = voice_client
                
                await ctx.send(f"""🎤 **{channel.name}** に参加しました！

📢 **利用可能な機能:**
• `C! say [テキスト]` - テキスト読み上げ
• `C! play [URL]` - 音声ファイル再生
• `C! stop` - 再生停止
• `C! volume [0-100]` - 音量調整
• `C! leave` - 退出

💡 **音声入力について:**
現在、Discordからの直接音声入力は技術的制限により一時停止中です。
代わりに音声ファイルを送信していただければ、文字起こしが可能です。""")
                
                # 自動切断タスクを開始
                asyncio.create_task(self._auto_disconnect_task(guild_id))
                
                return True
                
            except discord.errors.ClientException as e:
                await ctx.send(f"❌ 接続エラー: {str(e)}")
                return False
                
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
            
            # 再生中なら停止
            if voice_client.is_playing():
                voice_client.stop()
            
            # 切断
            await voice_client.disconnect()
            
            # クリーンアップ
            del self.voice_connections[guild_id]
            
            await ctx.send("👋 ボイスチャンネルから退出しました。")
            return True
            
        except Exception as e:
            print(f"❌ Voice leave error: {e}")
            await ctx.send("ボイスチャンネルからの退出に失敗しました。")
            return False
    
    async def text_to_speech(self, ctx, text: str) -> bool:
        """テキスト読み上げ（TTS）"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.voice_connections:
                await ctx.send("⚠️ 先に `C! join` でボイスチャンネルに参加してください。")
                return False
            
            voice_client = self.voice_connections[guild_id]
            
            if voice_client.is_playing():
                await ctx.send("⏸️ 現在再生中です。`C! stop` で停止してください。")
                return False
            
            # テキストの最適化（長すぎる場合は切る）
            if len(text) > 500:
                text = text[:497] + "..."
            
            # OpenAI TTS APIで音声生成
            try:
                response = self.openai_client.audio.speech.create(
                    model=self.tts_settings['model'],
                    voice=self.tts_settings['voice'],
                    input=text,
                    speed=self.tts_settings['speed']
                )
                
                # 一時ファイルに保存
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                # Discord音声再生
                audio_source = FFmpegPCMAudio(temp_file_path)
                audio_source = PCMVolumeTransformer(audio_source, volume=self.voice_settings['volume'])
                
                voice_client.play(
                    audio_source,
                    after=lambda e: self._cleanup_temp_file(temp_file_path, e)
                )
                
                await ctx.send(f"🔊 読み上げ中: 「{text[:50]}...」" if len(text) > 50 else f"🔊 読み上げ中: 「{text}」")
                return True
                
            except Exception as e:
                print(f"❌ TTS API error: {e}")
                await ctx.send("音声生成に失敗しました。")
                return False
                
        except Exception as e:
            print(f"❌ TTS error: {e}")
            await ctx.send("テキスト読み上げに失敗しました。")
            return False
    
    async def transcribe_audio_file(self, attachment) -> Optional[str]:
        """音声ファイルの文字起こし"""
        try:
            # 音声ファイルかチェック
            audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm']
            if not any(attachment.filename.lower().endswith(ext) for ext in audio_extensions):
                return None
            
            # ファイルサイズチェック（25MB以下）
            if attachment.size > 25 * 1024 * 1024:
                return "❌ ファイルサイズが大きすぎます（最大25MB）"
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(attachment.filename)[1], delete=False) as temp_file:
                await attachment.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Whisper APIで文字起こし
                with open(temp_file_path, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="ja"
                    )
                
                return transcript.text
                
            finally:
                # 一時ファイル削除
                os.unlink(temp_file_path)
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return f"❌ 文字起こしエラー: {str(e)}"
    
    async def stop_playback(self, ctx) -> bool:
        """再生停止"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.voice_connections:
                await ctx.send("📵 ボイスチャンネルに接続していません。")
                return False
            
            voice_client = self.voice_connections[guild_id]
            
            if voice_client.is_playing():
                voice_client.stop()
                await ctx.send("⏹️ 再生を停止しました。")
            else:
                await ctx.send("🔇 現在再生中の音声はありません。")
            
            return True
            
        except Exception as e:
            print(f"❌ Stop playback error: {e}")
            await ctx.send("再生停止に失敗しました。")
            return False
    
    async def adjust_volume(self, ctx, volume: int) -> bool:
        """音量調整"""
        try:
            if volume < 0 or volume > 100:
                await ctx.send("⚠️ 音量は0-100の範囲で指定してください。")
                return False
            
            self.voice_settings['volume'] = volume / 100.0
            
            guild_id = ctx.guild.id
            if guild_id in self.voice_connections:
                voice_client = self.voice_connections[guild_id]
                if hasattr(voice_client.source, 'volume'):
                    voice_client.source.volume = self.voice_settings['volume']
            
            await ctx.send(f"🔊 音量を {volume}% に設定しました。")
            return True
            
        except Exception as e:
            print(f"❌ Volume adjustment error: {e}")
            await ctx.send("音量調整に失敗しました。")
            return False
    
    def _cleanup_temp_file(self, file_path: str, error=None):
        """一時ファイルクリーンアップ"""
        try:
            if error:
                print(f"❌ Playback error: {error}")
            
            # 少し待ってから削除（再生完了を確実に待つ）
            asyncio.create_task(self._delayed_cleanup(file_path))
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    async def _delayed_cleanup(self, file_path: str):
        """遅延クリーンアップ"""
        await asyncio.sleep(2)
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
    
    async def _auto_disconnect_task(self, guild_id: int):
        """自動切断タスク"""
        try:
            await asyncio.sleep(self.voice_settings['auto_disconnect'])
            
            if guild_id in self.voice_connections:
                voice_client = self.voice_connections[guild_id]
                
                # アクティビティチェック
                if not voice_client.is_playing():
                    await voice_client.disconnect()
                    del self.voice_connections[guild_id]
                    
                    # 通知（可能であれば）
                    for channel in voice_client.guild.text_channels:
                        if 'general' in channel.name or 'bot' in channel.name:
                            await channel.send("🔇 非アクティブのため自動的に退出しました。")
                            break
                            
        except Exception as e:
            print(f"❌ Auto disconnect error: {e}")
    
    def get_voice_status(self, guild_id: int) -> Dict:
        """ボイス状態取得"""
        try:
            is_connected = guild_id in self.voice_connections
            
            if is_connected:
                voice_client = self.voice_connections[guild_id]
                return {
                    'connected': True,
                    'channel': voice_client.channel.name if voice_client.channel else None,
                    'is_playing': voice_client.is_playing(),
                    'volume': int(self.voice_settings['volume'] * 100)
                }
            
            return {
                'connected': False,
                'channel': None,
                'is_playing': False,
                'volume': int(self.voice_settings['volume'] * 100)
            }
            
        except Exception as e:
            print(f"❌ Voice status error: {e}")
            return {'connected': False}