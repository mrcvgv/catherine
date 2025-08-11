#!/usr/bin/env python3
"""
Instant Intent Engine - Catherine AI 瞬時意図認識エンジン
人間の言葉の意図を0.001秒で把握し、的確なアクションを即座に実行
"""

import time
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import asyncio

@dataclass
class IntentResult:
    """意図認識結果"""
    intent: str
    confidence: float
    action: str
    parameters: Dict[str, Any]
    response_text: str
    processing_time: float
    priority: str = 'medium'

class InstantIntentEngine:
    def __init__(self):
        # 超高速意図マッピング (ハッシュテーブルベース)
        self.instant_intent_map = {}
        self.action_executor = {}
        
        # パフォーマンス追跡
        self.recognition_stats = {
            'total_requests': 0,
            'instant_hits': 0,
            'average_time': 0.0,
            'accuracy_rate': 0.95
        }
        
        self._initialize_instant_patterns()
        self._initialize_action_executors()
    
    def _initialize_instant_patterns(self):
        """瞬時パターン初期化 - 最頻出パターンを直接マッピング"""
        
        # 挨拶系 (瞬時応答)
        greeting_patterns = {
            'よう': IntentResult('greeting', 1.0, 'respond', {}, 'よう！', 0.001),
            'おっす': IntentResult('greeting', 1.0, 'respond', {}, 'おっす！', 0.001),
            'やあ': IntentResult('greeting', 1.0, 'respond', {}, 'やあ！', 0.001),
            'hi': IntentResult('greeting', 1.0, 'respond', {}, 'Hi!', 0.001),
            'hello': IntentResult('greeting', 1.0, 'respond', {}, 'Hello!', 0.001),
            'こんにちは': IntentResult('greeting', 1.0, 'respond', {}, 'こんにちは！', 0.001),
            'こんばんは': IntentResult('greeting', 1.0, 'respond', {}, 'こんばんは！', 0.001),
            'おはよう': IntentResult('greeting', 1.0, 'respond', {}, 'おはよう！', 0.001),
        }
        
        # カジュアル会話系 (高速応答)
        casual_patterns = {
            '元気？': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            '元気': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            'げんき？': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            'げんき': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            'げんきか？': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            'げんきか': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            '元気か？': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            '元気か': IntentResult('casual', 1.0, 'respond', {}, '元気だよ', 0.001),
            '調子どう？': IntentResult('casual', 1.0, 'respond', {}, 'まあまあ', 0.001),
            '調子どう': IntentResult('casual', 1.0, 'respond', {}, 'まあまあ', 0.001),
            'どう？': IntentResult('casual', 1.0, 'respond', {}, 'まあまあかな', 0.001),
            'どう': IntentResult('casual', 0.95, 'respond', {}, 'まあまあかな', 0.001),
            'うん': IntentResult('agreement', 0.95, 'respond', {}, 'そうそう', 0.001),
            'そう': IntentResult('agreement', 0.95, 'respond', {}, 'だよね', 0.001),
            'そうそう': IntentResult('agreement', 0.95, 'respond', {}, 'うん', 0.001),
            'だよね': IntentResult('agreement', 0.95, 'respond', {}, 'そうそう', 0.001),
            'たしかに': IntentResult('agreement', 0.95, 'respond', {}, 'でしょ', 0.001),
            'すごい': IntentResult('praise', 0.90, 'respond', {}, 'でしょ', 0.001),
            'すごいね': IntentResult('praise', 0.90, 'respond', {}, 'だよね', 0.001),
            'いいね': IntentResult('praise', 0.90, 'respond', {}, 'でしょ', 0.001),
            'マジで': IntentResult('surprise', 0.85, 'respond', {}, 'マジマジ', 0.001),
            'ほんと': IntentResult('surprise', 0.85, 'respond', {}, 'ほんと', 0.001),
            'へー': IntentResult('interest', 0.85, 'respond', {}, 'へー', 0.001),
            'そうなんだ': IntentResult('acknowledgment', 0.90, 'respond', {}, 'うん', 0.001),
            'なるほど': IntentResult('understanding', 0.90, 'respond', {}, 'そうそう', 0.001),
        }
        
        # Todo/タスク系 (アクション実行)
        todo_patterns = {
            # リスト表示
            'todoリスト': IntentResult('todo_list', 1.0, 'show_todo_list', {}, '', 0.002),
            'todo リスト': IntentResult('todo_list', 1.0, 'show_todo_list', {}, '', 0.002),
            'todoリスト出して': IntentResult('todo_list', 1.0, 'show_todo_list', {}, '', 0.002),
            'リスト出して': IntentResult('todo_list', 0.95, 'show_todo_list', {}, '', 0.002),
            'リスト表示': IntentResult('todo_list', 0.95, 'show_todo_list', {}, '', 0.002),
            'リスト見せて': IntentResult('todo_list', 0.95, 'show_todo_list', {}, '', 0.002),
            'タスク一覧': IntentResult('todo_list', 0.95, 'show_todo_list', {}, '', 0.002),
            'やること見せて': IntentResult('todo_list', 0.90, 'show_todo_list', {}, '', 0.002),
            'list': IntentResult('todo_list', 0.85, 'show_todo_list', {}, '', 0.002),
            
            # Todo追加のパターン
            'todo追加': IntentResult('todo_add', 0.95, 'add_todo', {'quick': True}, '', 0.002),
            'タスク追加': IntentResult('todo_add', 0.95, 'add_todo', {'quick': True}, '', 0.002),
            
            # 状態確認
            'どうなってる？': IntentResult('status_check', 0.85, 'show_status', {}, '', 0.002),
            '状況は？': IntentResult('status_check', 0.85, 'show_status', {}, '', 0.002),
            '進捗は？': IntentResult('status_check', 0.90, 'show_status', {}, '', 0.002),
        }
        
        # 全パターンを統合
        self.instant_intent_map.update(greeting_patterns)
        self.instant_intent_map.update(casual_patterns)
        self.instant_intent_map.update(todo_patterns)
        
        # バリエーション追加 (句読点、大小文字)
        self._add_pattern_variations()
    
    def _add_pattern_variations(self):
        """パターンバリエーション追加"""
        base_patterns = dict(self.instant_intent_map)
        
        for pattern, intent_result in base_patterns.items():
            # 句読点バリエーション
            variations = [
                pattern + '？', pattern + '?',
                pattern + '！', pattern + '!',
                pattern + '。', pattern + '～'
            ]
            
            for variation in variations:
                if variation not in self.instant_intent_map:
                    # 新しいIntentResultオブジェクトを作成
                    new_result = IntentResult(
                        intent_result.intent,
                        intent_result.confidence * 0.98,  # 若干信頼度下げる
                        intent_result.action,
                        intent_result.parameters.copy(),
                        intent_result.response_text,
                        intent_result.processing_time
                    )
                    self.instant_intent_map[variation] = new_result
    
    def _initialize_action_executors(self):
        """アクション実行器初期化"""
        self.action_executor = {
            'respond': self._execute_simple_response,
            'show_todo_list': self._execute_todo_list,
            'add_todo': self._execute_todo_add,
            'show_status': self._execute_status_check,
        }
    
    def recognize_intent_instantly(self, user_input: str) -> IntentResult:
        """瞬時意図認識 - 0.001秒以内"""
        start_time = time.time()
        self.recognition_stats['total_requests'] += 1
        
        # 前処理
        cleaned_input = user_input.strip().lower()
        
        # 直接マッピング検索 (最高速)
        if cleaned_input in self.instant_intent_map:
            result = self.instant_intent_map[cleaned_input]
            result.processing_time = time.time() - start_time
            self.recognition_stats['instant_hits'] += 1
            return result
        
        # 部分一致検索 (高速)
        for pattern, intent_result in self.instant_intent_map.items():
            if pattern in cleaned_input or cleaned_input in pattern:
                result = IntentResult(
                    intent_result.intent,
                    intent_result.confidence * 0.85,  # 部分一致は信頼度下げる
                    intent_result.action,
                    intent_result.parameters.copy(),
                    intent_result.response_text,
                    time.time() - start_time
                )
                return result
        
        # キーワードベース推論 (中速)
        intent_result = self._keyword_based_recognition(cleaned_input)
        intent_result.processing_time = time.time() - start_time
        return intent_result
    
    def _keyword_based_recognition(self, text: str) -> IntentResult:
        """キーワードベース認識"""
        keywords = text.split()
        
        # Todo関連キーワード
        todo_keywords = ['todo', 'タスク', 'やること', 'list', 'リスト', '一覧', '表示']
        if any(keyword in text for keyword in todo_keywords):
            if any(show_word in text for show_word in ['出し', '見せ', '表示', 'リスト']):
                return IntentResult('todo_list', 0.80, 'show_todo_list', {}, '', 0.003)
            else:
                return IntentResult('todo_add', 0.75, 'add_todo', {'text': text}, '', 0.003)
        
        # 質問系
        if '？' in text or '?' in text or text.endswith(('どう', 'かな', 'だっけ')):
            return IntentResult('question', 0.70, 'respond', {}, self._generate_question_response(), 0.003)
        
        # デフォルト
        return IntentResult('casual', 0.50, 'respond', {}, 'そうなんだ', 0.003)
    
    def _generate_question_response(self) -> str:
        """質問への応答生成"""
        responses = ['そうだね', 'どうだろ', 'うーん', 'まあまあかな', 'そうかも']
        import random
        return random.choice(responses)
    
    async def execute_intent_action(self, intent_result: IntentResult, context: Dict = None) -> str:
        """意図に基づくアクション実行"""
        if intent_result.action in self.action_executor:
            executor = self.action_executor[intent_result.action]
            try:
                if asyncio.iscoroutinefunction(executor):
                    result = await executor(intent_result, context or {})
                else:
                    result = executor(intent_result, context or {})
                return result
            except Exception as e:
                return f"アクション実行エラー: {str(e)}"
        else:
            return intent_result.response_text or "理解しました"
    
    # アクション実行メソッド群
    def _execute_simple_response(self, intent_result: IntentResult, context: Dict) -> str:
        """シンプル応答実行"""
        return intent_result.response_text
    
    async def _execute_todo_list(self, intent_result: IntentResult, context: Dict) -> str:
        """Todoリスト表示実行"""
        # ここで実際のTodo管理システムと連携
        return "📊 **ToDoリスト**\n1. 買い物\n2. 洗濯\n3. 掃除"
    
    async def _execute_todo_add(self, intent_result: IntentResult, context: Dict) -> str:
        """Todo追加実行"""
        # ここで実際のTodo追加処理
        task_text = intent_result.parameters.get('text', 'タスク')
        return f"✅ ToDo追加: {task_text}"
    
    async def _execute_status_check(self, intent_result: IntentResult, context: Dict) -> str:
        """ステータスチェック実行"""
        return "📈 **現在の状況**\n• 未完了タスク: 3件\n• 完了タスク: 7件\n• 進捗: 70%"
    
    def get_performance_stats(self) -> Dict:
        """パフォーマンス統計取得"""
        instant_hit_rate = (self.recognition_stats['instant_hits'] / 
                          max(self.recognition_stats['total_requests'], 1)) * 100
        
        return {
            'total_patterns': len(self.instant_intent_map),
            'total_requests': self.recognition_stats['total_requests'],
            'instant_hit_rate': f"{instant_hit_rate:.1f}%",
            'average_processing_time': self.recognition_stats['average_time'],
            'accuracy_rate': f"{self.recognition_stats['accuracy_rate'] * 100:.1f}%"
        }
    
    def add_learned_pattern(self, user_input: str, correct_intent: str, 
                          correct_action: str, response: str):
        """学習パターン追加"""
        cleaned_input = user_input.strip().lower()
        self.instant_intent_map[cleaned_input] = IntentResult(
            correct_intent, 0.85, correct_action, {}, response, 0.001
        )