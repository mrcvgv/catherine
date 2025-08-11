#!/usr/bin/env python3
"""
Fast Greeting System - Catherine AI 高速挨拶応答システム
シンプルな挨拶に瞬時に応答するための軽量システム
"""

import random
import re
from typing import Dict, Optional, List
from datetime import datetime

class FastGreetingSystem:
    def __init__(self):
        self.greeting_patterns = {
            # カジュアル挨拶
            'よう': ['よう！', 'よ！', 'おっす！', 'やあ！'],
            'おっす': ['おっす！', 'よう！', 'やあ！'],
            'おい': ['なに？', 'おう！', 'どうした？'],
            'やあ': ['やあ！', 'よう！', 'おっす！'],
            'はい': ['はい！', 'なに？', 'うん？'],
            'うん': ['うん！', 'そうそう', 'はい'],
            'そう': ['そうだね', 'うん', 'そうそう'],
            'へー': ['へー', 'なるほど', 'そうなんだ'],
            
            # 一般的な挨拶
            'こんにちは': ['こんにちは！', 'お疲れさま！', 'よろしく！'],
            'こんばんは': ['こんばんは！', 'お疲れさま！'],
            'おはよう': ['おはよう！', 'おはようございます！'],
            
            # 英語挨拶
            'hi': ['Hi!', 'Hello!', 'Hey!'],
            'hello': ['Hello!', 'Hi!', 'Hey there!'],
            'hey': ['Hey!', 'Hi!', 'Hello!']
        }
        
        # 時間帯による挨拶調整
        self.time_greetings = {
            'morning': ['おはよう！', 'おはようございます！', 'いい朝だね！'],
            'afternoon': ['こんにちは！', 'お疲れさま！', '調子どう？'],
            'evening': ['こんばんは！', 'お疲れさま！', '今日もお疲れ！']
        }
    
    def get_time_period(self) -> str:
        """現在の時間帯を取得"""
        hour = datetime.now().hour
        if 5 <= hour < 11:
            return 'morning'
        elif 11 <= hour < 17:
            return 'afternoon'
        else:
            return 'evening'
    
    def is_simple_greeting(self, text: str) -> bool:
        """シンプルな挨拶かどうかを判定"""
        if len(text) > 15:
            return False
        
        text_lower = text.lower().strip()
        
        # 挨拶パターンをチェック
        for pattern in self.greeting_patterns.keys():
            if pattern in text_lower:
                return True
        
        return False
    
    def generate_fast_response(self, text: str) -> str:
        """高速挨拶応答を生成"""
        text_lower = text.lower().strip()
        
        # 完全一致チェック
        for pattern, responses in self.greeting_patterns.items():
            if pattern in text_lower:
                return random.choice(responses)
        
        # 時間帯に応じた挨拶
        time_period = self.get_time_period()
        return random.choice(self.time_greetings[time_period])
    
    def should_use_fast_response(self, text: str) -> bool:
        """高速応答を使うべきかどうかを判定"""
        return (
            len(text.strip()) <= 10 and
            self.is_simple_greeting(text) and
            not any(word in text.lower() for word in ['todo', 'タスク', 'リスト', 'やること'])
        )