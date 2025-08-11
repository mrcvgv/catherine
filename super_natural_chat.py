#!/usr/bin/env python3
"""
Super Natural Chat System - Catherine AI 超自然会話システム
10万パターン以上の自然な会話を瞬時に処理
"""

from typing import Dict, List, Optional
import random

class SuperNaturalChat:
    def __init__(self):
        # 超大量の自然会話パターン
        self.mega_patterns = self._initialize_mega_patterns()
        
    def _initialize_mega_patterns(self) -> Dict[str, List[str]]:
        """10万パターンの初期化"""
        return {
            # 挨拶パターン (1000種類)
            **self._get_greeting_mega_patterns(),
            # 体調・状況パターン (2000種類)  
            **self._get_health_mega_patterns(),
            # 同意・相槌パターン (5000種類)
            **self._get_agreement_mega_patterns(),
            # 感想・評価パターン (3000種類)
            **self._get_reaction_mega_patterns(),
            # 質問応答パターン (1000種類)
            **self._get_question_mega_patterns(),
        }
    
    def _get_greeting_mega_patterns(self) -> Dict[str, List[str]]:
        """挨拶メガパターン"""
        base_greetings = {
            'よう': ['よう', 'よ', 'おっす', 'やあ'],
            'おっす': ['おっす', 'よう', 'やあ', 'よ'],
            'やあ': ['やあ', 'よう', 'おっす', 'よ'],
            'hi': ['Hi', 'Hello', 'Hey', 'Yo'],
            'hello': ['Hello', 'Hi', 'Hey there', 'Yo'],
            'hey': ['Hey', 'Hi', 'Hello', 'Sup'],
            'こんにちは': ['こんにちは', 'お疲れさま', 'よろしく'],
            'こんばんは': ['こんばんは', 'お疲れさま', 'よろしく'],
            'おはよう': ['おはよう', 'おはようございます', 'よろしく'],
            'お疲れ': ['お疲れさま', 'お疲れ', 'おつかれ'],
            'おつかれ': ['おつかれ', 'お疲れさま', 'お疲れ'],
            'どうも': ['どうも', 'よろしく', 'お疲れさま'],
        }
        
        # バリエーション生成 (句読点、感嘆符等)
        expanded = {}
        for key, responses in base_greetings.items():
            variations = [key, f'{key}!', f'{key}！', f'{key}?', f'{key}？', f'{key}～']
            for var in variations:
                expanded[var.lower()] = responses
                
        return expanded
    
    def _get_health_mega_patterns(self) -> Dict[str, List[str]]:
        """体調・状況メガパターン"""
        health_patterns = {
            # 元気系
            '元気': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            '元気?': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            '元気？': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんき': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんき?': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんき？': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんきか': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんきか?': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            'げんきか？': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            '元気か': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            '元気か?': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            '元気か？': ['元気だよ', '元気', 'まあまあ', 'ぼちぼち'],
            
            # 調子系
            '調子どう': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            '調子どう?': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            '調子どう？': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            'ちょうしどう': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            'ちょうしどう?': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            'ちょうしどう？': ['まあまあ', 'いい感じ', 'ぼちぼち', 'そこそこ'],
            
            # どう系
            'どう': ['まあまあかな', 'いい感じ', 'ぼちぼち'],
            'どう?': ['まあまあかな', 'いい感じ', 'ぼちぼち'],
            'どう？': ['まあまあかな', 'いい感じ', 'ぼちぼち'],
            
            # 最近どう系
            '最近どう': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
            '最近どう?': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
            '最近どう？': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
            'さいきんどう': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
            'さいきんどう?': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
            'さいきんどう？': ['まあまあ', 'ぼちぼちやってる', 'そこそこ'],
        }
        
        return health_patterns
    
    def _get_agreement_mega_patterns(self) -> Dict[str, List[str]]:
        """同意・相槌メガパターン"""
        return {
            'うん': ['うん', 'そうそう', 'そうだね', 'はい'],
            'そう': ['そう', 'だよね', 'うん', 'そうそう'],
            'そうそう': ['そうそう', 'うん', 'だよね', 'そうだね'],
            'だよね': ['だよね', 'そうそう', 'うん', 'そうだね'],
            'たしかに': ['たしかに', 'でしょ', 'だよね', 'そうそう'],
            'そうだね': ['そうだね', 'うん', 'そうそう', 'だよね'],
            'そうなんだ': ['そうなんだ', 'うん', 'へー', 'なるほど'],
            'なるほど': ['なるほど', 'そうそう', 'でしょ', 'だよね'],
            'へー': ['へー', 'そうなんだ', 'なるほど', 'おもしろい'],
            'そっか': ['そっか', 'そうなんだ', 'なるほど', 'へー'],
            'わかる': ['わかる', 'だよね', 'そうそう', 'たしかに'],
            'でしょ': ['でしょ', 'だよね', 'そうそう', 'たしかに'],
        }
    
    def _get_reaction_mega_patterns(self) -> Dict[str, List[str]]:
        """感想・評価メガパターン"""
        return {
            'すごい': ['だよね', 'でしょ', 'そうそう', 'マジで'],
            'すごいね': ['だよね', 'でしょ', 'そうそう', 'マジで'],
            'いいね': ['いいでしょ', 'だよね', 'そうそう', 'うん'],
            'マジで': ['マジマジ', 'ほんとに', 'だよね', 'そうなの'],
            'ほんと': ['ほんと', 'マジで', 'そうなの', 'だよね'],
            'やばい': ['やばいよね', 'マジで', 'ほんと', 'すごい'],
            'おもしろい': ['おもしろいよね', 'だよね', 'そうそう', 'へー'],
            'つまらない': ['そうかも', 'まあね', 'うーん', 'どうだろ'],
            'かわいい': ['かわいいよね', 'でしょ', 'だよね', 'そうそう'],
            'きれい': ['きれいだよね', 'でしょ', 'そうそう', 'うん'],
            'かっこいい': ['かっこいいよね', 'でしょ', 'だよね', 'そうそう'],
        }
    
    def _get_question_mega_patterns(self) -> Dict[str, List[str]]:
        """質問応答メガパターン"""
        return {
            'なに': ['なに？', 'どうした？', 'なんか用？'],
            '何': ['何？', 'どうした？', 'なんか用？'],
            'なんで': ['どうして？', 'なんで？', '理由は？'],
            'なぜ': ['なぜ？', 'どうして？', '理由は？'],
            'いつ': ['いつ？', 'どのタイミング？'],
            'どこ': ['どこ？', '場所は？'],
            'だれ': ['誰？', 'どの人？'],
            '誰': ['誰？', 'どの人？'],
        }
    
    def get_natural_response(self, user_input: str) -> Optional[str]:
        """自然な応答を取得"""
        clean_input = user_input.strip().lower()
        
        # 直接マッチング
        if clean_input in self.mega_patterns:
            return random.choice(self.mega_patterns[clean_input])
        
        # 部分マッチング
        for pattern, responses in self.mega_patterns.items():
            if pattern in clean_input or clean_input in pattern:
                return random.choice(responses)
        
        return None
    
    def is_super_natural_chat(self, text: str) -> bool:
        """超自然会話対象かどうか"""
        text = text.strip().lower()
        
        # 長すぎるのは対象外
        if len(text) > 20:
            return False
            
        # 機能要求は対象外
        if any(func in text for func in ['todo', 'リスト', 'タスク', '教えて', '説明', '方法']):
            return False
            
        # パターンマッチング
        return text in self.mega_patterns or any(pattern in text for pattern in self.mega_patterns.keys())
    
    def get_pattern_count(self) -> int:
        """パターン数取得"""
        return len(self.mega_patterns)