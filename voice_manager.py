import asyncio
import discord
import speech_recognition as sr
import io
import wave
from typing import Optional, Callable
from openai import OpenAI
import tempfile
import os

class VoiceManager:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.voice_client: Optional[discord.VoiceClient] = None
        self.audio_buffer = []
        
    async def join_voice_channel(self, voice_channel: discord.VoiceChannel) -> bool:
        """ボイスチャンネルに参加"""
        try:
            self.voice_client = await voice_channel.connect()
            print(f"✅ Joined voice channel: {voice_channel.name}")
            return True
        except Exception as e:
            print(f"❌ Failed to join voice channel: {e}")
            return False
    
    async def leave_voice_channel(self) -> bool:
        """ボイスチャンネルから退出"""
        try:
            if self.voice_client:
                await self.voice_client.disconnect()
                self.voice_client = None
                print("✅ Left voice channel")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to leave voice channel: {e}")
            return False
    
    async def start_listening(self, callback: Callable[[str], None]) -> bool:
        """音声認識開始"""
        if not self.voice_client:
            return False
        
        try:
            self.is_recording = True
            
            # カスタム音声シンクを作成
            voice_sink = VoiceSink(self.recognizer, self.openai_client, callback)
            self.voice_client.start_recording(voice_sink, self._recording_finished)
            
            print("🎤 Started voice recognition")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start voice recognition: {e}")
            return False
    
    async def stop_listening(self) -> bool:
        """音声認識停止"""
        try:
            if self.voice_client and self.is_recording:
                self.voice_client.stop_recording()
                self.is_recording = False
                print("🔇 Stopped voice recognition")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to stop voice recognition: {e}")
            return False
    
    def _recording_finished(self, sink, channel, *args):
        """録音完了時のコールバック"""
        print("📼 Recording finished")

class VoiceSink(discord.sinks.WaveSink):
    """カスタム音声シンク - 音声データを処理"""
    
    def __init__(self, recognizer: sr.Recognizer, openai_client: OpenAI, 
                 text_callback: Callable[[str], None]):
        super().__init__()
        self.recognizer = recognizer
        self.openai_client = openai_client
        self.text_callback = text_callback
        self.silence_threshold = 1.0  # 秒
        self.last_audio_time = 0
    
    def wants_opus(self) -> bool:
        return False
    
    def write(self, data, user):
        """音声データの書き込み処理"""
        if user:  # ボットの音声は除外
            super().write(data, user)
            
            # 音声データが一定量溜まったら処理
            if len(self.audio_data.get(user.id, [])) > 48000:  # 約1秒分
                asyncio.create_task(self._process_audio(user.id))
    
    async def _process_audio(self, user_id: int):
        """音声データを処理してテキストに変換"""
        try:
            if user_id not in self.audio_data:
                return
            
            # 音声データを WAV 形式で保存
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(2)  # ステレオ
                    wav_file.setsampwidth(2)  # 16bit
                    wav_file.setframerate(48000)  # サンプリング周波数
                    
                    # 音声データを書き込み
                    audio_bytes = b''.join(self.audio_data[user_id])
                    wav_file.writeframes(audio_bytes)
                
                # OpenAI Whisperで音声認識
                text = await self._transcribe_with_whisper(temp_file.name)
                
                if text and text.strip():
                    self.text_callback(f"🎤 {text}")
                
                # 処理済みデータをクリア
                self.audio_data[user_id] = []
                
                # 一時ファイルを削除
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
    
    async def _transcribe_with_whisper(self, audio_file_path: str) -> Optional[str]:
        """OpenAI Whisper APIで音声をテキストに変換"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ja"  # 日本語指定
                )
                return transcript.text
                
        except Exception as e:
            print(f"❌ Whisper transcription error: {e}")
            return None

class VoiceCommands:
    """音声コマンド処理クラス"""
    
    @staticmethod
    async def process_voice_command(text: str, voice_manager: VoiceManager) -> str:
        """音声から認識されたテキストを処理"""
        text_lower = text.lower()
        
        # 音声コマンドの判定
        if "じょいん" in text_lower or "参加" in text_lower:
            return "voice_join"
        elif "りーぶ" in text_lower or "退出" in text_lower or "バイバイ" in text_lower:
            return "voice_leave"
        elif "とぅーどぅー" in text_lower or "やること" in text_lower or "タスク" in text_lower:
            return "todo_create"
        elif "りすと" in text_lower or "一覧" in text_lower:
            return "todo_list"
        elif "完了" in text_lower or "終わった" in text_lower:
            return "todo_done"
        else:
            return "conversation"  # 通常の会話として処理
    
    @staticmethod
    def extract_todo_from_voice(text: str) -> Optional[str]:
        """音声からToDoを抽出"""
        # 「〜をやる」「〜する」「〜を追加」などのパターンを検出
        todo_patterns = [
            "をやる", "する", "を追加", "をして", "をやって",
            "をお願い", "を忘れずに", "をリマインド"
        ]
        
        for pattern in todo_patterns:
            if pattern in text:
                # パターンの前の部分をToDoとして抽出
                todo_text = text.split(pattern)[0].strip()
                if len(todo_text) > 2:  # 最低限の長さチェック
                    return todo_text
        
        return None
