#!/usr/bin/env python3
"""
Instant Response System - Catherine AI 瞬間応答システム
0.001秒以内で即座に返事をする最高速システム
"""

import time
from typing import Dict, Optional

class InstantResponseSystem:
    def __init__(self):
        # 超高速直接マッピング - ハッシュテーブルで即座にアクセス
        self.instant_responses = {
            # 基本挨拶 - 0.001秒応答
            'よう': 'よう',
            'おっす': 'おっす',
            'やあ': 'やあ',
            'おい': 'よう',
            'hi': 'Hi',
            'hello': 'Hello',
            'hey': 'Hey',
            'sup': 'Sup',
            
            # 元気系 - 0.001秒応答
            '元気？': '元気だよ',
            '元気': '元気だよ',
            'げんき？': '元気だよ',
            'げんき': '元気だよ',
            'げんきか？': '元気だよ',
            'げんきか': '元気だよ',
            '元気か？': '元気だよ',
            '元気か': '元気だよ',
            
            # 調子系 - 0.001秒応答
            '調子どう？': 'まあまあ',
            '調子どう': 'まあまあ',
            'どう？': 'まあまあかな',
            'どう': 'まあまあかな',
            
            # 相槌系 - 0.001秒応答
            'うん': 'そうそう',
            'そう': 'だよね',
            'そうそう': 'うん',
            'だよね': 'そうそう',
            'たしかに': 'でしょ',
            'でしょ': 'だよね',
            'なるほど': 'そうそう',
            'そうなんだ': 'うん',
            'へー': 'そうなんだ',
            'そっか': 'そうなんだ',
            'わかる': 'だよね',
            
            # 感嘆系 - 0.001秒応答
            'すごい': 'でしょ',
            'すごいね': 'だよね',
            'いいね': 'でしょ',
            'やばい': 'やばいよね',
            'マジで': 'マジマジ',
            'ほんと': 'ほんと',
            'えー': 'まじで？',
            'うそ': 'うそでしょ',
            
            # 時間系 - 0.001秒応答
            'おはよう': 'おはよう',
            'こんにちは': 'こんにちは',
            'こんばんは': 'こんばんは',
            'おやすみ': 'おやすみ',
            'お疲れ': 'お疲れさま',
            'おつかれ': 'お疲れさま',
            
            # 状態系 - 0.001秒応答
            '疲れた': 'お疲れさま',
            '眠い': '眠いね',
            '忙しい': 'お疲れさま',
            '暇': '何しよう',
            '暇だ': '何しよう',
            
            # 食べ物系 - 0.001秒応答
            'お腹すいた': '何食べる？',
            '美味しい': 'いいね',
            'うまい': 'うまそう',
            
            # 天気系 - 0.001秒応答
            '暑い': '暑いね',
            '寒い': '寒いね',
            '雨': '雨だね',
            'いい天気': 'いい天気だね',
            
            # その他カジュアル - 0.001秒応答
            'ありがとう': 'どういたしまして',
            'サンキュー': 'どういたしまして',
            'thanks': 'You\'re welcome',
            'ごめん': '大丈夫だよ',
            'すまん': '大丈夫',
            'sorry': 'No problem',
        }
        
        # バリエーション追加（句読点対応）
        self._add_variations()
        
    def _add_variations(self):
        """句読点バリエーション追加"""
        base_patterns = dict(self.instant_responses)
        
        for pattern, response in base_patterns.items():
            # 句読点バリエーション
            variations = [
                f"{pattern}!",
                f"{pattern}！", 
                f"{pattern}?",
                f"{pattern}？",
                f"{pattern}~",
                f"{pattern}～",
                f"{pattern}.",
                f"{pattern}。"
            ]
            
            for var in variations:
                self.instant_responses[var.lower()] = response
    
    def get_instant_response(self, user_input: str) -> Optional[str]:
        """瞬間応答取得 - 0.001秒以内"""
        clean_input = user_input.strip().lower()
        
        # 直接マッピング検索（最高速）
        if clean_input in self.instant_responses:
            return self.instant_responses[clean_input]
        
        return None
    
    def is_instant_response_target(self, text: str) -> bool:
        """瞬間応答対象判定"""
        clean_text = text.strip().lower()
        
        # 短い文章のみ対象（10文字以下）
        if len(clean_text) > 10:
            return False
            
        # 機能要求は除外
        if any(keyword in clean_text for keyword in ['todo', 'リスト', 'タスク']):
            return False
            
        # 直接マッピング存在チェック
        return clean_text in self.instant_responses
    
    def get_response_count(self) -> int:
        """応答パターン数取得"""
        return len(self.instant_responses)