#!/usr/bin/env python3
"""
Natural Conversation System - Catherine AI 自然会話システム
普通の人間みたいに自然で短い会話を実現
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class NaturalConversationSystem:
    def __init__(self):
        # 短くて自然な応答パターン
        self.casual_responses = {
            # 質問への答え
            'どう': ['まあまあかな', 'ぼちぼち', 'そこそこ', 'まずまず'],
            '元気': ['元気だよ', 'まあまあ', 'ぼちぼち', 'おかげさまで'],
            '調子': ['いい感じ', 'まあまあ', 'ぼちぼち', 'そこそこかな'],
            
            # 感想・相槌
            'すごい': ['だよね', 'そうそう', 'うん', 'たしかに'],
            'いいね': ['でしょ', 'うん', 'そうだね', 'だよね'],
            'そうなんだ': ['うん', 'そう', 'だよね', 'でしょ'],
            'なるほど': ['そうそう', 'でしょ', 'だよね', 'うん'],
            
            # 同意・共感
            'うん': ['そうそう', 'だよね', 'うん', 'そう'],
            'そう': ['だよね', 'うん', 'そうそう', 'でしょ'],
            'たしかに': ['でしょ', 'だよね', 'そうそう', 'うん'],
            
            # 疑問・困惑
            'えー': ['まあね', 'そうかも', 'どうだろ', 'うーん'],
            'マジで': ['マジマジ', 'そうなの', 'だよね', 'ほんとに'],
            'ほんと': ['ほんと', 'マジで', 'だよね', 'そうなの'],
        }
        
        # 話を広げるパターン
        self.conversation_extenders = [
            'それで？', 'どうなった？', 'へー', 'そうなんだ', 
            'なるほど', 'いいね', 'それはいいね', 'おもしろい'
        ]
        
        # 短い返答パターン
        self.short_responses = [
            'うん', 'そうだね', 'なるほど', 'へー', 'そうなんだ',
            'いいね', 'おもしろい', 'そっか', 'マジで', 'すごい'
        ]
        
        # 終了・区切りのパターン
        self.ending_phrases = [
            'そっか', 'なるほどね', 'そうなんだ', 'いいね', 'おもしろいね'
        ]

    def is_casual_conversation(self, text: str) -> bool:
        """カジュアルな会話かどうか判定"""
        text = text.strip().lower()
        
        # 長すぎる文は除外
        if len(text) > 30:
            return False
            
        # 機能的な要求は除外
        if any(keyword in text for keyword in [
            'todo', 'リスト', 'タスク', 'やること', '教えて', '説明', 
            'どうやって', 'どうすれば', 'help', 'ヘルプ'
        ]):
            return False
            
        # カジュアルな会話の特徴
        casual_indicators = [
            'どう', '元気', '調子', 'すごい', 'いいね', 'そうなんだ',
            'なるほど', 'うん', 'そう', 'たしかに', 'えー', 'マジで',
            'ほんと', 'へー', 'そっか', 'おもしろい'
        ]
        
        return any(indicator in text for indicator in casual_indicators)

    def generate_natural_response(self, text: str, context: Dict = None) -> str:
        """自然な会話応答を生成"""
        text = text.strip().lower()
        
        # 直接マッチするパターンを探す
        for pattern, responses in self.casual_responses.items():
            if pattern in text:
                return random.choice(responses)
        
        # 疑問文かどうか判定
        if '?' in text or '？' in text or text.endswith(('どう', 'かな', 'だっけ')):
            return random.choice(['そうだね', 'どうだろ', 'うーん', 'まあまあかな'])
        
        # 感嘆符があるか
        if '!' in text or '！' in text:
            return random.choice(['だよね！', 'そうそう！', 'いいね！', 'すごい！'])
        
        # 短い相槌的な応答
        if len(text) <= 10:
            return random.choice(self.short_responses)
        
        # デフォルトの共感的応答
        return random.choice(['そうなんだ', 'なるほど', 'へー', 'いいね', 'おもしろい'])

    def should_use_natural_conversation(self, text: str) -> bool:
        """自然会話システムを使うべきかどうか"""
        return (
            len(text.strip()) <= 30 and
            self.is_casual_conversation(text) and
            not any(keyword in text.lower() for keyword in [
                'todo', 'リスト', 'タスク', 'やること', '教えて', '説明してください',
                'どうやって', 'どうすれば', 'help', 'ヘルプ', '方法', '手順'
            ])
        )

    def get_conversation_mood(self, text: str) -> str:
        """会話のムードを判定"""
        text = text.lower()
        
        if any(word in text for word in ['すごい', 'いいね', '最高', '素晴らしい']):
            return 'positive'
        elif any(word in text for word in ['大変', '困った', '疲れた', 'つらい']):
            return 'concern'
        elif '?' in text or '？' in text:
            return 'question'
        else:
            return 'neutral'