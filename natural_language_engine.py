#!/usr/bin/env python3
"""
Natural Language Engine - 完全自然言語理解エンジン
コマンド不要、普通の会話で全機能を実行
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import re

JST = pytz.timezone('Asia/Tokyo')

class NaturalLanguageEngine:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        
        # 意図パターンの定義（学習により改善される）
        self.intent_patterns = {
            'todo_add': [
                r'(.+?)をやる',
                r'(.+?)する',
                r'(.+?)しなきゃ',
                r'(.+?)しないと',
                r'(.+?)やらなきゃ',
                r'todo.*(.+)',
                r'タスク.*(.+)',
                r'(.+?)を?追加',
                r'(.+?)を?登録'
            ],
            'todo_list': [
                r'やること.*見せて',
                r'タスク.*表示',
                r'todo.*list',
                r'list',
                r'一覧',
                r'リスト',
                r'何があったっけ',
                r'やることある？',
                r'タスクは？'
            ],
            'todo_complete': [
                r'(\d+).*終わった',
                r'(\d+).*完了',
                r'(\d+).*done',
                r'(.+?)終わった',
                r'(.+?)できた',
                r'(.+?)完了した',
                r'(.+?)おわり'
            ],
            'todo_delete': [
                r'(\d+).*消して',
                r'(\d+).*削除',
                r'(\d+).*いらない',
                r'(.+?)消して',
                r'(.+?)削除',
                r'(.+?)やめる',
                r'(.+?)キャンセル'
            ],
            'reminder_add': [
                r'(.+?)リマインド',
                r'(.+?)思い出させて',
                r'(.+?)忘れないように',
                r'(.+?)通知して',
                r'明日.*(.+)',
                r'(\d+)時.*(.+)',
                r'(\d+)分後.*(.+)'
            ],
            'greeting': [
                r'おはよう',
                r'こんにちは',
                r'こんばんは',
                r'hello',
                r'hi',
                r'やっほー',
                r'よう',
                r'元気？',
                r'調子どう'
            ],
            'help': [
                r'help',
                r'ヘルプ',
                r'使い方',
                r'どうやって',
                r'できること',
                r'何ができる'
            ],
            'growth': [
                r'成長',
                r'レベル',
                r'ステータス',
                r'進化',
                r'学習状況'
            ],
            'briefing': [
                r'ブリーフィング',
                r'朝の.*報告',
                r'今日の.*予定',
                r'今日.*何',
                r'朝会'
            ]
        }
    
    async def understand_intent(self, message: str, context: Dict = None) -> Dict:
        """自然言語から意図を完全理解"""
        try:
            # GPT-4oによる高度な意図理解
            intent_result = await self._analyze_with_gpt(message, context)
            
            # パターンマッチングによる補強
            pattern_intent = self._pattern_based_intent(message)
            
            # 両方の結果を統合
            final_intent = self._merge_intents(intent_result, pattern_intent)
            
            return final_intent
            
        except Exception as e:
            print(f"❌ Intent understanding error: {e}")
            return {
                'primary_intent': 'chat',
                'confidence': 0.3,
                'parameters': {},
                'natural_response': True
            }
    
    async def _analyze_with_gpt(self, message: str, context: Dict = None) -> Dict:
        """GPT-4oによる意図分析"""
        try:
            context_info = ""
            if context:
                context_info = f"""
最近の会話文脈:
- 前回の話題: {context.get('last_topic', '不明')}
- ユーザーの状態: {context.get('user_state', '通常')}
- 時刻: {datetime.now(JST).strftime('%H:%M')}
"""
            
            prompt = f"""
以下のメッセージから、ユーザーの意図を正確に分析してください。
コマンドを使わずに、自然な会話から何をしたいのかを理解します。

メッセージ: "{message}"
{context_info}

以下のJSON形式で返してください：
{{
    "primary_intent": "意図カテゴリ",
    "specific_action": "具体的なアクション",
    "confidence": 0.0-1.0,
    "parameters": {{
        "content": "内容",
        "target": "対象",
        "timing": "タイミング",
        "priority": "優先度",
        "additional": "その他パラメータ"
    }},
    "emotional_context": "感情的文脈",
    "suggested_response_style": "casual/formal/friendly",
    "requires_confirmation": true/false,
    "natural_response": true/false
}}

意図カテゴリ例:
- todo_management: ToDoの追加、表示、完了、削除など
- reminder: リマインダー設定
- information_query: 情報を求める質問
- casual_conversation: 雑談
- greeting: 挨拶
- status_check: ステータス確認
- help_request: ヘルプ要求
- emotional_support: 感情的サポート
- planning: 計画立案
- review: 振り返り、サマリー
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは自然言語理解の専門家です。ユーザーの真の意図を正確に把握します。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"❌ GPT analysis error: {e}")
            return {
                'primary_intent': 'chat',
                'confidence': 0.5,
                'parameters': {},
                'natural_response': True
            }
    
    def _pattern_based_intent(self, message: str) -> Dict:
        """パターンベースの意図検出（フォールバック）"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    match = re.search(pattern, message_lower)
                    
                    # パラメータ抽出
                    parameters = {}
                    if match.groups():
                        parameters['content'] = match.group(1) if match.group(1) else message
                    
                    return {
                        'primary_intent': intent,
                        'confidence': 0.7,
                        'parameters': parameters,
                        'pattern_matched': pattern
                    }
        
        return {
            'primary_intent': 'chat',
            'confidence': 0.3,
            'parameters': {'content': message}
        }
    
    def _merge_intents(self, gpt_intent: Dict, pattern_intent: Dict) -> Dict:
        """GPTとパターンの意図を統合"""
        # GPTの信頼度が高い場合はGPTを優先
        if gpt_intent.get('confidence', 0) > 0.7:
            final = gpt_intent.copy()
            
            # パターンマッチの情報で補強
            if pattern_intent.get('parameters'):
                final['parameters'].update(pattern_intent['parameters'])
            
            return final
        
        # パターンマッチが明確な場合
        if pattern_intent.get('confidence', 0) > 0.6:
            final = pattern_intent.copy()
            
            # GPTの追加情報で補強
            final['emotional_context'] = gpt_intent.get('emotional_context', '')
            final['suggested_response_style'] = gpt_intent.get('suggested_response_style', 'friendly')
            
            return final
        
        # 両方の情報を統合
        return {
            'primary_intent': gpt_intent.get('primary_intent', 'chat'),
            'specific_action': gpt_intent.get('specific_action', ''),
            'confidence': max(gpt_intent.get('confidence', 0), pattern_intent.get('confidence', 0)),
            'parameters': {**pattern_intent.get('parameters', {}), **gpt_intent.get('parameters', {})},
            'emotional_context': gpt_intent.get('emotional_context', ''),
            'suggested_response_style': gpt_intent.get('suggested_response_style', 'friendly'),
            'requires_confirmation': gpt_intent.get('requires_confirmation', False),
            'natural_response': True
        }
    
    async def generate_action_response(self, intent: Dict, action_result: any) -> str:
        """アクション結果を自然な言葉で返す"""
        try:
            prompt = f"""
以下のアクション結果を、自然で親しみやすい日本語で伝えてください。
コマンド的な応答ではなく、友人に話すような自然な表現を使ってください。

意図: {intent.get('primary_intent')}
アクション: {intent.get('specific_action', '')}
結果: {action_result}
感情文脈: {intent.get('emotional_context', '')}
スタイル: {intent.get('suggested_response_style', 'friendly')}

応答の方針:
1. 結果を簡潔に伝える
2. 次のアクションの提案があれば自然に含める
3. 励ましや共感を適切に含める
4. 絵文字は控えめに（ユーザーが使っている場合のみ）
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは親しみやすい友人のような話し方をするAI秘書です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_completion_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            return "わかりました！処理完了です。"
    
    def extract_todo_info(self, message: str, intent: Dict) -> Dict:
        """ToDoに関する情報を抽出"""
        parameters = intent.get('parameters', {})
        
        # 優先度の判定
        priority = 3  # デフォルト
        if any(word in message for word in ['緊急', '急ぎ', 'すぐ', '今すぐ', 'ASAP']):
            priority = 5
        elif any(word in message for word in ['重要', '大事', '大切']):
            priority = 4
        elif any(word in message for word in ['いつでも', 'そのうち', '暇なとき']):
            priority = 2
        
        # 期限の抽出
        due_date = None
        today = datetime.now(JST)
        
        if '明日' in message:
            due_date = today + timedelta(days=1)
        elif '明後日' in message:
            due_date = today + timedelta(days=2)
        elif '来週' in message:
            due_date = today + timedelta(days=7)
        elif '今週' in message:
            # 今週の金曜日
            days_until_friday = (4 - today.weekday()) % 7
            due_date = today + timedelta(days=days_until_friday if days_until_friday > 0 else 7)
        
        # 日付パターン
        date_match = re.search(r'(\d{1,2})[月/](\d{1,2})', message)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year = today.year
            if month < today.month:
                year += 1
            try:
                due_date = datetime(year, month, day, tzinfo=JST)
            except:
                pass
        
        return {
            'title': parameters.get('content', message)[:100],
            'priority': priority,
            'due_date': due_date,
            'category': self._detect_category(message)
        }
    
    def _detect_category(self, message: str) -> str:
        """カテゴリ自動検出"""
        categories = {
            'work': ['仕事', '会議', 'ミーティング', '資料', 'レポート', 'プレゼン'],
            'personal': ['買い物', '家', 'プライベート', '個人'],
            'study': ['勉強', '学習', '本', '読書', '調べる'],
            'health': ['運動', 'ジム', '病院', '健康'],
            'finance': ['支払い', '振込', 'お金', '請求'],
            'communication': ['連絡', 'メール', '電話', '返信']
        }
        
        message_lower = message.lower()
        for category, keywords in categories.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def extract_reminder_info(self, message: str, intent: Dict) -> Dict:
        """リマインダー情報を抽出"""
        parameters = intent.get('parameters', {})
        now = datetime.now(JST)
        
        # 時間の抽出
        remind_at = now + timedelta(minutes=30)  # デフォルト30分後
        
        # 相対時間
        if match := re.search(r'(\d+)分後', message):
            minutes = int(match.group(1))
            remind_at = now + timedelta(minutes=minutes)
        elif match := re.search(r'(\d+)時間後', message):
            hours = int(match.group(1))
            remind_at = now + timedelta(hours=hours)
        elif '明日' in message:
            # 明日の同じ時刻
            remind_at = now + timedelta(days=1)
            if match := re.search(r'(\d{1,2})時', message):
                hour = int(match.group(1))
                remind_at = remind_at.replace(hour=hour, minute=0)
        
        # 絶対時間
        elif match := re.search(r'(\d{1,2})時(\d{0,2})', message):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            remind_at = now.replace(hour=hour, minute=minute, second=0)
            if remind_at < now:
                remind_at += timedelta(days=1)
        
        # リマインダータイプ
        reminder_type = 'once'
        if '毎日' in message:
            reminder_type = 'daily'
        elif '毎週' in message:
            reminder_type = 'weekly'
        elif '毎月' in message:
            reminder_type = 'monthly'
        
        return {
            'title': parameters.get('content', message)[:50],
            'message': parameters.get('content', message),
            'remind_at': remind_at,
            'reminder_type': reminder_type
        }