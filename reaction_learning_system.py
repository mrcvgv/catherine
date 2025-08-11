#!/usr/bin/env python3
"""
Reaction-based Learning System
リアクションからフィードバックを学習し、応答を改善するシステム
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from firebase_config import firebase_manager
from openai import OpenAI

class ReactionLearningSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
        
        # リアクションの意味マッピング
        self.reaction_meanings = {
            # ポジティブフィードバック
            '👍': {'sentiment': 'positive', 'strength': 0.8, 'meaning': '良い応答'},
            '❤️': {'sentiment': 'positive', 'strength': 1.0, 'meaning': '素晴らしい応答'},
            '😊': {'sentiment': 'positive', 'strength': 0.7, 'meaning': '嬉しい応答'},
            '😄': {'sentiment': 'positive', 'strength': 0.8, 'meaning': '楽しい応答'},
            '🎉': {'sentiment': 'positive', 'strength': 0.9, 'meaning': '最高の応答'},
            '✅': {'sentiment': 'positive', 'strength': 0.8, 'meaning': '正確な応答'},
            '💯': {'sentiment': 'positive', 'strength': 1.0, 'meaning': '完璧な応答'},
            
            # ネガティブフィードバック
            '👎': {'sentiment': 'negative', 'strength': -0.8, 'meaning': '不適切な応答'},
            '😕': {'sentiment': 'negative', 'strength': -0.5, 'meaning': '混乱させる応答'},
            '😢': {'sentiment': 'negative', 'strength': -0.6, 'meaning': '悲しい応答'},
            '😠': {'sentiment': 'negative', 'strength': -0.8, 'meaning': '怒らせる応答'},
            '❌': {'sentiment': 'negative', 'strength': -0.9, 'meaning': '間違った応答'},
            '🤔': {'sentiment': 'neutral', 'strength': -0.3, 'meaning': '疑問を残す応答'},
            
            # ニュートラル/特殊
            '🔄': {'sentiment': 'neutral', 'strength': 0, 'meaning': 'もう一度'},
            '➕': {'sentiment': 'neutral', 'strength': 0.2, 'meaning': 'もっと詳しく'},
            '➖': {'sentiment': 'neutral', 'strength': -0.2, 'meaning': '簡潔に'},
            '🎯': {'sentiment': 'positive', 'strength': 0.7, 'meaning': '的確な応答'},
            '💡': {'sentiment': 'positive', 'strength': 0.6, 'meaning': '良いアイデア'}
        }
        
        # 学習パラメータ
        self.learning_rate = 0.1
        self.feedback_window = timedelta(minutes=5)  # 5分以内のリアクションを関連付け
        
    async def process_reaction(self, user_id: str, message_id: str, 
                              reaction: str, bot_response: str,
                              user_message: str) -> Dict:
        """リアクションを処理して学習"""
        try:
            # リアクションの意味を取得
            reaction_data = self.reaction_meanings.get(
                reaction, 
                {'sentiment': 'neutral', 'strength': 0, 'meaning': '不明なリアクション'}
            )
            
            # フィードバックデータを作成
            feedback = {
                'feedback_id': f"{message_id}_{reaction}_{datetime.now().timestamp()}",
                'user_id': user_id,
                'message_id': message_id,
                'reaction': reaction,
                'sentiment': reaction_data['sentiment'],
                'strength': reaction_data['strength'],
                'meaning': reaction_data['meaning'],
                'bot_response': bot_response,
                'user_message': user_message,
                'timestamp': datetime.now(),
                'learned': False
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('reaction_feedback').document(feedback['feedback_id'])
            doc_ref.set(feedback)
            
            # 即座に学習を実行
            learning_result = await self._learn_from_feedback(user_id, feedback)
            
            # 応答パターンを更新
            await self._update_response_patterns(user_id, feedback, learning_result)
            
            return {
                'success': True,
                'feedback': feedback,
                'learning_result': learning_result
            }
            
        except Exception as e:
            print(f"❌ Reaction processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _learn_from_feedback(self, user_id: str, feedback: Dict) -> Dict:
        """フィードバックから学習"""
        try:
            # 応答分析
            analysis_prompt = f"""
以下のフィードバックを分析して、今後の改善点を抽出してください。

【ユーザーメッセージ】
{feedback['user_message']}

【Catherineの応答】
{feedback['bot_response']}

【受け取ったリアクション】
{feedback['reaction']} - {feedback['meaning']}
感情: {feedback['sentiment']}
強度: {feedback['strength']}

【分析項目】
1. なぜこのリアクションを受けたか
2. 応答の良かった点/悪かった点
3. 改善すべき要素
4. 今後避けるべきパターン
5. 今後強化すべきパターン

JSON形式で回答してください：
{{
    "reaction_reason": "リアクションの理由",
    "positive_aspects": ["良かった点のリスト"],
    "negative_aspects": ["悪かった点のリスト"],
    "improvement_areas": {{
        "tone": "トーンの改善点",
        "content": "内容の改善点",
        "length": "長さの改善点",
        "empathy": "共感度の改善点"
    }},
    "patterns_to_avoid": ["避けるべきパターン"],
    "patterns_to_reinforce": ["強化すべきパターン"],
    "specific_learning": "この特定のケースから学んだこと"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": analysis_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            learning = json.loads(response.choices[0].message.content)
            
            # 学習結果を保存
            learning_doc = {
                'user_id': user_id,
                'feedback_id': feedback['feedback_id'],
                'learning': learning,
                'applied': False,
                'timestamp': datetime.now()
            }
            
            self.db.collection('learning_history').add(learning_doc)
            
            return learning
            
        except Exception as e:
            print(f"❌ Learning error: {e}")
            return {}
    
    async def _update_response_patterns(self, user_id: str, 
                                       feedback: Dict, 
                                       learning: Dict) -> None:
        """応答パターンを更新"""
        try:
            # ユーザー固有の応答パターンを取得/作成
            doc_ref = self.db.collection('response_patterns').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                patterns = doc.to_dict()
            else:
                patterns = {
                    'user_id': user_id,
                    'created_at': datetime.now(),
                    'successful_patterns': [],
                    'failed_patterns': [],
                    'preferences': {},
                    'adjustment_history': []
                }
            
            # パターンを更新
            if feedback['sentiment'] == 'positive':
                patterns['successful_patterns'].append({
                    'pattern': self._extract_pattern(feedback['bot_response']),
                    'context': feedback['user_message'],
                    'strength': feedback['strength'],
                    'timestamp': datetime.now()
                })
                
                # 成功パターンから好みを学習
                if 'tone' in learning.get('positive_aspects', []):
                    patterns['preferences']['preferred_tone'] = self._analyze_tone(feedback['bot_response'])
                    
            elif feedback['sentiment'] == 'negative':
                patterns['failed_patterns'].append({
                    'pattern': self._extract_pattern(feedback['bot_response']),
                    'context': feedback['user_message'],
                    'strength': feedback['strength'],
                    'timestamp': datetime.now(),
                    'avoid_reasons': learning.get('patterns_to_avoid', [])
                })
            
            # 調整履歴を記録
            patterns['adjustment_history'].append({
                'timestamp': datetime.now(),
                'reaction': feedback['reaction'],
                'adjustment': learning.get('specific_learning', ''),
                'strength': feedback['strength']
            })
            
            # 古いパターンをクリーンアップ（30日以上前）
            cutoff_date = datetime.now() - timedelta(days=30)
            patterns['successful_patterns'] = [
                p for p in patterns['successful_patterns']
                if p['timestamp'] > cutoff_date
            ]
            patterns['failed_patterns'] = [
                p for p in patterns['failed_patterns']
                if p['timestamp'] > cutoff_date
            ]
            
            # 保存
            doc_ref.set(patterns)
            
        except Exception as e:
            print(f"❌ Pattern update error: {e}")
    
    def _extract_pattern(self, response: str) -> Dict:
        """応答からパターンを抽出"""
        pattern = {
            'length': len(response),
            'has_emoji': any(ord(c) > 127 for c in response),
            'has_question': '？' in response or '?' in response,
            'has_exclamation': '！' in response or '!' in response,
            'starts_with_greeting': any(
                response.startswith(g) for g in 
                ['こんにちは', 'おはよう', 'こんばんは', 'お疲れ様']
            ),
            'ends_with_question': response.rstrip().endswith(('？', '?', 'か？', 'か?')),
            'formal_level': self._calculate_formality(response)
        }
        return pattern
    
    def _analyze_tone(self, response: str) -> str:
        """応答のトーンを分析"""
        if 'です' in response or 'ます' in response:
            if '!' in response or '！' in response:
                return 'polite_enthusiastic'
            return 'polite'
        elif any(casual in response for casual in ['だよ', 'だね', 'かな']):
            return 'casual_friendly'
        elif any(emoji in response for emoji in ['😊', '😄', '✨', '💪']):
            return 'friendly_with_emoji'
        else:
            return 'neutral'
    
    def _calculate_formality(self, text: str) -> float:
        """フォーマリティレベルを計算（0-1）"""
        formal_indicators = ['です', 'ます', 'ございます', 'いたします', 'おります']
        casual_indicators = ['だよ', 'だね', 'かな', 'っぽい', 'じゃん']
        
        formal_count = sum(1 for ind in formal_indicators if ind in text)
        casual_count = sum(1 for ind in casual_indicators if ind in text)
        
        if formal_count + casual_count == 0:
            return 0.5
        
        return formal_count / (formal_count + casual_count)
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """学習したユーザーの好みを取得"""
        try:
            # 応答パターンから好みを抽出
            doc_ref = self.db.collection('response_patterns').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return self._get_default_preferences()
            
            patterns = doc.to_dict()
            
            # 成功パターンから好みを分析
            successful = patterns.get('successful_patterns', [])
            if not successful:
                return self._get_default_preferences()
            
            # 最近の成功パターンを重視（重み付け）
            recent_patterns = sorted(
                successful, 
                key=lambda x: x['timestamp'], 
                reverse=True
            )[:20]
            
            preferences = {
                'preferred_length': sum(p['pattern']['length'] for p in recent_patterns) / len(recent_patterns),
                'likes_emoji': sum(1 for p in recent_patterns if p['pattern']['has_emoji']) > len(recent_patterns) / 2,
                'likes_questions': sum(1 for p in recent_patterns if p['pattern']['has_question']) > len(recent_patterns) / 3,
                'formality_preference': sum(p['pattern']['formal_level'] for p in recent_patterns) / len(recent_patterns),
                'preferred_tone': patterns.get('preferences', {}).get('preferred_tone', 'friendly'),
                'learning_count': len(patterns.get('adjustment_history', [])),
                'last_updated': datetime.now()
            }
            
            return preferences
            
        except Exception as e:
            print(f"❌ Preference retrieval error: {e}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict:
        """デフォルトの好み設定"""
        return {
            'preferred_length': 100,
            'likes_emoji': True,
            'likes_questions': False,
            'formality_preference': 0.5,
            'preferred_tone': 'friendly',
            'learning_count': 0,
            'last_updated': datetime.now()
        }
    
    async def apply_learning_to_response(self, user_id: str, 
                                        base_response: str) -> str:
        """学習結果を応答に適用"""
        try:
            preferences = await self.get_user_preferences(user_id)
            
            # 好みに基づいて応答を調整
            adjusted_response = base_response
            
            # 長さの調整
            if len(base_response) > preferences['preferred_length'] * 1.5:
                # 簡潔にする
                adjusted_response = await self._make_concise(base_response)
            
            # 絵文字の追加/削除
            if preferences['likes_emoji'] and '😊' not in adjusted_response:
                adjusted_response = await self._add_appropriate_emoji(adjusted_response)
            elif not preferences['likes_emoji']:
                adjusted_response = self._remove_emoji(adjusted_response)
            
            # フォーマリティの調整
            if preferences['formality_preference'] > 0.7:
                adjusted_response = await self._make_formal(adjusted_response)
            elif preferences['formality_preference'] < 0.3:
                adjusted_response = await self._make_casual(adjusted_response)
            
            return adjusted_response
            
        except Exception as e:
            print(f"❌ Response adjustment error: {e}")
            return base_response
    
    async def _make_concise(self, text: str) -> str:
        """テキストを簡潔にする"""
        prompt = f"以下のテキストを、意味を保ちながら簡潔にしてください：\n{text}"
        response = self.openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content
    
    async def _add_appropriate_emoji(self, text: str) -> str:
        """適切な絵文字を追加"""
        # シンプルなルールベースで追加
        if '嬉しい' in text or '楽しい' in text:
            return text + ' 😊'
        elif '頑張' in text:
            return text + ' 💪'
        elif 'ありがとう' in text:
            return text + ' ✨'
        return text
    
    def _remove_emoji(self, text: str) -> str:
        """絵文字を削除"""
        return ''.join(char for char in text if ord(char) < 127 or char in '。、！？')
    
    async def _make_formal(self, text: str) -> str:
        """よりフォーマルにする"""
        replacements = {
            'だよ': 'です',
            'だね': 'ですね',
            'かな': 'でしょうか',
            'うん': 'はい',
            'ちょっと': '少し'
        }
        for casual, formal in replacements.items():
            text = text.replace(casual, formal)
        return text
    
    async def _make_casual(self, text: str) -> str:
        """よりカジュアルにする"""
        replacements = {
            'です。': 'だよ。',
            'ですね。': 'だね。',
            'でしょうか': 'かな',
            'いたします': 'するね',
            'ございます': 'あります'
        }
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
        return text