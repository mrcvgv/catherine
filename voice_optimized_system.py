#!/usr/bin/env python3
"""
Voice Optimized Response System
音声・電話向けの最適化：短文化・確認最適化・留守電タスク化
"""

from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime
import pytz
from openai import OpenAI

JST = pytz.timezone('Asia/Tokyo')

class VoiceOptimizedSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        
        # 音声向け設定
        self.voice_settings = {
            'max_sentence_length': 20,      # 1文あたりの最大文字数
            'pause_after_sentences': 1,     # 文間の秒数
            'confirmation_prefix': True,    # はい/いいえを先頭に
            'numbers_in_words': False,      # 数字を漢字で読み上げ
            'avoid_abbreviations': True,    # 略語を避ける
        }
        
        # 音声認識でよくある誤変換パターン
        self.common_misrecognitions = {
            'トゥードゥー': 'ToDo',
            'とぅーどぅー': 'ToDo',
            'りすと': 'リスト',
            'あっぷでーと': '更新',
            'でりーと': '削除',
            'けんめい': '件名',
            'あさいん': '割り当て'
        }
    
    def optimize_for_voice(self, text: str, context: str = "general") -> str:
        """テキストを音声出力用に最適化"""
        try:
            # 1) 基本的なクリーニング
            cleaned_text = self._clean_text_for_voice(text)
            
            # 2) 短文化
            short_sentences = self._break_into_short_sentences(cleaned_text)
            
            # 3) 音声向けの表現に変換
            voice_friendly = self._make_voice_friendly(short_sentences)
            
            # 4) 確認用の場合は特別処理
            if context == "confirmation":
                voice_friendly = self._optimize_confirmation(voice_friendly)
            
            return voice_friendly
            
        except Exception as e:
            print(f"❌ Voice optimization error: {e}")
            return text
    
    def _clean_text_for_voice(self, text: str) -> str:
        """音声用の基本クリーニング"""
        # Markdownの記号を除去
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **太字**
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # *斜体*
        text = re.sub(r'`(.+?)`', r'\1', text)        # `コード`
        text = re.sub(r'#{1,6}\s*', '', text)         # # 見出し
        
        # 特殊文字を読みやすく
        text = text.replace('→', 'から')
        text = text.replace('・', '、')
        text = text.replace('✅', '完了')
        text = text.replace('❌', 'エラー')
        text = text.replace('📝', '')
        text = text.replace('🔥', '重要')
        
        # URL除去
        text = re.sub(r'https?://[^\s]+', 'リンク', text)
        
        return text
    
    def _break_into_short_sentences(self, text: str) -> str:
        """長い文を短く分割"""
        sentences = re.split(r'[。！？\n]', text)
        short_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(sentence) <= self.voice_settings['max_sentence_length']:
                short_sentences.append(sentence)
            else:
                # 長い文を分割
                parts = self._split_long_sentence(sentence)
                short_sentences.extend(parts)
        
        return '。'.join(short_sentences) + '。'
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """長い文を論理的に分割"""
        # 接続詞で分割
        connectors = ['そして', 'また', 'さらに', 'ただし', 'しかし', 'なお', 'ちなみに']
        
        for connector in connectors:
            if connector in sentence:
                parts = sentence.split(connector, 1)
                if len(parts) == 2:
                    return [parts[0].strip(), connector + parts[1].strip()]
        
        # 読点で分割
        if '、' in sentence:
            parts = sentence.split('、', 1)
            if len(parts) == 2 and len(parts[0]) > 10:
                return [parts[0], parts[1]]
        
        # 強制的に分割
        mid = len(sentence) // 2
        return [sentence[:mid], sentence[mid:]]
    
    def _make_voice_friendly(self, text: str) -> str:
        """音声向けの表現に変換"""
        # 数字の読み方を調整
        if not self.voice_settings['numbers_in_words']:
            text = re.sub(r'(\d+)件', r'\1けん', text)
            text = re.sub(r'(\d+)時間', r'\1じかん', text)
            text = re.sub(r'(\d+)分', r'\1ふん', text)
        
        # 略語を展開
        if self.voice_settings['avoid_abbreviations']:
            text = text.replace('API', 'エーピーアイ')
            text = text.replace('UI', 'ユーアイ')
            text = text.replace('DB', 'データベース')
            text = text.replace('ToDo', 'やることリスト')
        
        # 助詞の調整（音声で聞きやすく）
        text = text.replace('は、', 'は')
        text = text.replace('を、', 'を')
        
        return text
    
    def _optimize_confirmation(self, text: str) -> str:
        """確認用の音声最適化"""
        # はい/いいえを先頭に
        if '?' in text or '？' in text or 'ますか' in text:
            # 質問の場合
            if not text.startswith(('はい', 'いいえ')):
                text = f"はい か いいえ で答えてください。{text}"
        
        # 末尾で要点を復唱
        if '更新' in text:
            text += "更新してよろしいですか。"
        elif '削除' in text:
            text += "削除してよろしいですか。"
        elif '作成' in text:
            text += "作成してよろしいですか。"
        
        return text
    
    def correct_voice_recognition(self, recognized_text: str) -> str:
        """音声認識の誤変換を修正"""
        try:
            corrected = recognized_text
            
            # よくある誤変換を修正
            for wrong, correct in self.common_misrecognitions.items():
                corrected = corrected.replace(wrong, correct)
            
            # AI による文脈修正
            if len(corrected) > 20:  # 長いテキストのみAI修正
                corrected = self._ai_correct_recognition(corrected)
            
            return corrected
            
        except Exception as e:
            print(f"❌ Voice correction error: {e}")
            return recognized_text
    
    async def _ai_correct_recognition(self, text: str) -> str:
        """AIで音声認識を修正"""
        try:
            prompt = f"""
以下の音声認識結果を修正してください。
ToDo管理、タスク管理、スケジュール管理の文脈です。

音声認識結果: {text}

修正のポイント:
- 専門用語の誤変換修正
- 自然な日本語に調整
- 文脈に合わない部分の修正

修正したテキストのみ回答してください。
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ AI correction error: {e}")
            return text
    
    async def process_voicemail_to_tasks(self, transcribed_text: str, 
                                        caller_info: Dict) -> Dict:
        """留守電の文字起こしからタスクを作成"""
        try:
            prompt = f"""
以下の留守電の内容からToDoとリマインダーを抽出してください：

【発信者情報】
名前: {caller_info.get('name', '不明')}
電話番号: {caller_info.get('phone', '不明')}
時刻: {caller_info.get('timestamp', datetime.now().strftime('%Y/%m/%d %H:%M'))}

【留守電内容】
{transcribed_text}

以下のJSON形式で回答：
{{
    "summary": "留守電の要約（50字以内）",
    "urgency": 1-5の緊急度,
    "todos": [
        {{
            "title": "タスク名",
            "description": "詳細説明",
            "priority": 1-5,
            "category": "communication/meeting/follow_up/other",
            "estimated_minutes": 推定時間（分）
        }}
    ],
    "reminders": [
        {{
            "title": "リマインダー名",
            "message": "内容",
            "remind_time": "推奨通知時刻（相対指定：1時間後/明日朝など）"
        }}
    ],
    "callback_required": true/false,
    "callback_priority": "high/medium/low"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return result
            
        except Exception as e:
            print(f"❌ Voicemail processing error: {e}")
            return {
                'summary': '留守電の処理に失敗',
                'urgency': 3,
                'todos': [],
                'reminders': [],
                'callback_required': True,
                'callback_priority': 'medium'
            }
    
    def create_voice_response_template(self, response_type: str, 
                                     data: Dict) -> str:
        """音声応答テンプレート生成"""
        templates = {
            'task_created': "タスクを作成しました。{title}。優先度は{priority}です。",
            'task_updated': "タスクを更新しました。{title}を{change}に変更しました。",
            'task_completed': "タスクが完了しました。{title}。お疲れ様でした。",
            'list_tasks': "現在{count}件のタスクがあります。最優先は{top_task}です。",
            'reminder_set': "リマインダーを設定しました。{time}に{title}をお知らせします。",
            'confirmation_needed': "確認します。{action}を実行してよろしいですか。はい か いいえ で答えてください。",
            'error': "申し訳ありません。エラーが発生しました。もう一度お試しください。",
            'not_understood': "すみません。よく聞こえませんでした。もう一度お話しください。"
        }
        
        template = templates.get(response_type, templates['not_understood'])
        
        try:
            return template.format(**data)
        except KeyError as e:
            print(f"❌ Template formatting error: {e}")
            return template
    
    def add_voice_pauses(self, text: str) -> str:
        """音声出力用の読み上げポーズを追加"""
        # 文末に pause
        text = re.sub(r'([。！？])', r'\1<pause time="0.5s"/>', text)
        
        # 重要な情報の前後に pause
        text = re.sub(r'(優先度|期限|担当)', r'<pause time="0.3s"/>\1', text)
        text = re.sub(r'(です|ます)([。！？])', r'\1<pause time="0.3s"/>\2', text)
        
        return text
    
    def format_for_tts(self, text: str, voice_settings: Dict = None) -> str:
        """TTS（Text-to-Speech）用のフォーマット"""
        if voice_settings:
            self.voice_settings.update(voice_settings)
        
        # 音声最適化を適用
        optimized = self.optimize_for_voice(text)
        
        # TTS向けのタグ追加
        if self.voice_settings.get('add_pauses', True):
            optimized = self.add_voice_pauses(optimized)
        
        # 読み上げ速度の調整
        speed = voice_settings.get('speed', 'medium')
        prosody_tag = f'<prosody rate="{speed}">{optimized}</prosody>'
        
        return prosody_tag