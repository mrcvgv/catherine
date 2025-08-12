#!/usr/bin/env python3
"""
Memory & Learning System - Catherine AI の記憶・学習レイヤー
「勝手に賢くなる」「気を利かせる」パーソナライズエンジン
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import pytz
from collections import defaultdict, Counter
from firebase_config import firebase_manager

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ActionLog:
    """操作ログエントリ"""
    log_id: str
    user_id: str
    channel_id: str
    timestamp: datetime
    intent: str
    raw_input: str
    entities: Dict[str, Any]
    result: Dict[str, Any]
    confidence: float
    correction: Optional[Dict] = None  # 修正があった場合
    feedback: Optional[str] = None    # ユーザーフィードバック
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class UserPreference:
    """ユーザー好み設定"""
    user_id: str
    preference_type: str  # default_mention, default_time, shortcut, etc.
    key: str             # 'mention' or 'time:明日' or 'shortcut:うさぎ'
    value: Any           # '@everyone' or '09:00' or 'アイデア'
    confidence: float    # 確信度（使用頻度から算出）
    last_used: datetime
    created_at: datetime
    use_count: int = 1

@dataclass
class LearningPattern:
    """学習パターン"""
    pattern_id: str
    user_id: str
    pattern_type: str    # 'correction', 'disambiguation', 'shortcut'
    before_state: Dict   # 修正前/曖昧な状態
    after_state: Dict    # 修正後/確定状態  
    frequency: int       # 発生回数
    confidence: float    # パターン確信度
    created_at: datetime
    last_seen: datetime

class MemoryLayer:
    """記憶レイヤー - 操作履歴・好み・学習データの管理"""
    
    def __init__(self):
        self.db = firebase_manager.get_db()
        self.logs_collection = 'catherine_action_logs'
        self.preferences_collection = 'catherine_user_preferences'
        self.patterns_collection = 'catherine_learning_patterns'
        self.corrections_collection = 'catherine_corrections'
    
    async def save_action_log(self, user_id: str, channel_id: str, 
                             intent: str, raw_input: str, entities: Dict,
                             result: Dict, confidence: float) -> str:
        """操作ログ保存"""
        log_id = hashlib.md5(
            f"{user_id}:{channel_id}:{datetime.now()}:{raw_input}".encode()
        ).hexdigest()[:12]
        
        log_entry = ActionLog(
            log_id=log_id,
            user_id=user_id,
            channel_id=channel_id,
            timestamp=datetime.now(JST),
            intent=intent,
            raw_input=raw_input,
            entities=entities,
            result=result,
            confidence=confidence
        )
        
        try:
            self.db.collection(self.logs_collection).document(log_id).set(
                log_entry.to_dict()
            )
            print(f"[MEMORY] Action logged: {intent} | {confidence:.2f}")
            return log_id
        except Exception as e:
            print(f"[ERROR] Failed to save action log: {e}")
            return ""
    
    async def save_correction(self, log_id: str, before_intent: str, 
                             after_intent: str, user_feedback: str) -> bool:
        """修正記録保存"""
        try:
            # 元のログを更新
            log_ref = self.db.collection(self.logs_collection).document(log_id)
            log_ref.update({
                'correction': {
                    'before_intent': before_intent,
                    'after_intent': after_intent,
                    'corrected_at': datetime.now(JST).isoformat()
                },
                'feedback': user_feedback
            })
            
            # 学習パターンとして保存
            await self._extract_learning_pattern(log_id, before_intent, after_intent)
            
            print(f"[MEMORY] Correction saved: {before_intent} → {after_intent}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save correction: {e}")
            return False
    
    async def _extract_learning_pattern(self, log_id: str, before: str, after: str):
        """修正から学習パターンを抽出"""
        try:
            # 元のログを取得
            log_doc = self.db.collection(self.logs_collection).document(log_id).get()
            if not log_doc.exists:
                return
            
            log_data = log_doc.to_dict()
            user_id = log_data['user_id']
            raw_input = log_data['raw_input']
            
            # パターンID生成（類似の修正をグループ化）
            pattern_key = f"{before}→{after}:{hashlib.md5(raw_input.encode()).hexdigest()[:8]}"
            pattern_id = hashlib.md5(f"{user_id}:{pattern_key}".encode()).hexdigest()[:12]
            
            # 既存パターンチェック
            pattern_ref = self.db.collection(self.patterns_collection).document(pattern_id)
            pattern_doc = pattern_ref.get()
            
            if pattern_doc.exists:
                # 既存パターンの頻度を更新
                pattern_ref.update({
                    'frequency': pattern_doc.to_dict()['frequency'] + 1,
                    'last_seen': datetime.now(JST),
                    'confidence': min(0.95, pattern_doc.to_dict()['confidence'] + 0.1)
                })
            else:
                # 新規パターン作成
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    user_id=user_id,
                    pattern_type='correction',
                    before_state={'intent': before, 'raw_input': raw_input},
                    after_state={'intent': after},
                    frequency=1,
                    confidence=0.7,
                    created_at=datetime.now(JST),
                    last_seen=datetime.now(JST)
                )
                
                pattern_data = asdict(pattern)
                pattern_data['created_at'] = pattern.created_at.isoformat()
                pattern_data['last_seen'] = pattern.last_seen.isoformat()
                
                pattern_ref.set(pattern_data)
            
        except Exception as e:
            print(f"[ERROR] Failed to extract learning pattern: {e}")
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """ユーザー好み設定取得"""
        try:
            docs = self.db.collection(self.preferences_collection).where(
                'user_id', '==', user_id
            ).order_by('confidence', direction='DESCENDING').get()
            
            preferences = {}
            for doc in docs:
                pref = doc.to_dict()
                pref_type = pref['preference_type']
                key = pref['key']
                
                if pref_type not in preferences:
                    preferences[pref_type] = {}
                preferences[pref_type][key] = pref['value']
            
            return preferences
        except Exception as e:
            print(f"[ERROR] Failed to get preferences: {e}")
            return {}
    
    async def update_preference(self, user_id: str, pref_type: str, 
                               key: str, value: Any) -> bool:
        """好み設定更新（使用頻度ベース）"""
        try:
            pref_id = hashlib.md5(f"{user_id}:{pref_type}:{key}".encode()).hexdigest()[:12]
            pref_ref = self.db.collection(self.preferences_collection).document(pref_id)
            pref_doc = pref_ref.get()
            
            if pref_doc.exists:
                # 既存設定を更新
                existing = pref_doc.to_dict()
                new_count = existing['use_count'] + 1
                new_confidence = min(0.95, 0.5 + (new_count * 0.05))
                
                pref_ref.update({
                    'value': value,
                    'confidence': new_confidence,
                    'use_count': new_count,
                    'last_used': datetime.now(JST)
                })
            else:
                # 新規設定作成
                preference = UserPreference(
                    user_id=user_id,
                    preference_type=pref_type,
                    key=key,
                    value=value,
                    confidence=0.6,
                    last_used=datetime.now(JST),
                    created_at=datetime.now(JST)
                )
                
                pref_data = asdict(preference)
                pref_data['last_used'] = preference.last_used.isoformat()
                pref_data['created_at'] = preference.created_at.isoformat()
                
                pref_ref.set(pref_data)
            
            print(f"[MEMORY] Preference updated: {pref_type}:{key} = {value}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update preference: {e}")
            return False

class PersonalizationEngine:
    """パーソナライゼーションエンジン - 好みに基づく自動推測"""
    
    def __init__(self, memory_layer: MemoryLayer):
        self.memory = memory_layer
        self.user_cache = {}  # メモリ内キャッシュ
    
    async def enhance_entities(self, user_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """エンティティをユーザー好みで補完"""
        enhanced = entities.copy()
        preferences = await self._get_cached_preferences(user_id)
        
        # 宛先が未指定の場合のデフォルト適用
        if not enhanced.get('mention') and 'default_mention' in preferences:
            enhanced['mention'] = preferences['default_mention'].get('default', '@everyone')
            enhanced['_auto_filled'] = enhanced.get('_auto_filled', [])
            enhanced['_auto_filled'].append('mention')
        
        # 時刻の自動補完
        if enhanced.get('time') and 'default_time' in preferences:
            time_str = enhanced['time']
            for pattern, default_time in preferences['default_time'].items():
                if pattern in time_str and len(time_str) < 10:  # 曖昧な時刻
                    enhanced['time'] = f"{time_str} {default_time}"
                    enhanced['_auto_filled'] = enhanced.get('_auto_filled', [])
                    enhanced['_auto_filled'].append('time')
                    break
        
        # ショートカット展開
        if enhanced.get('what') and 'shortcut' in preferences:
            content = enhanced['what']
            for shortcut, expansion in preferences['shortcut'].items():
                if shortcut in content:
                    enhanced['what'] = content.replace(shortcut, expansion)
                    enhanced['_auto_filled'] = enhanced.get('_auto_filled', [])
                    enhanced['_auto_filled'].append('what')
        
        return enhanced
    
    async def suggest_corrections(self, user_id: str, intent: str, 
                                 raw_input: str) -> List[Dict]:
        """過去の修正パターンから推測候補提示"""
        try:
            docs = self.memory.db.collection(self.memory.patterns_collection).where(
                'user_id', '==', user_id
            ).where('pattern_type', '==', 'correction').where(
                'confidence', '>=', 0.8
            ).get()
            
            suggestions = []
            for doc in docs:
                pattern = doc.to_dict()
                before_state = pattern['before_state']
                
                # 類似入力パターンチェック
                if self._is_similar_input(raw_input, before_state.get('raw_input', '')):
                    suggestions.append({
                        'suggested_intent': pattern['after_state']['intent'],
                        'confidence': pattern['confidence'],
                        'reason': f"過去{pattern['frequency']}回の修正パターンから推測"
                    })
            
            return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)[:3]
        except Exception as e:
            print(f"[ERROR] Failed to get correction suggestions: {e}")
            return []
    
    async def learn_from_selection(self, user_id: str, context: Dict, 
                                  selected_option: str) -> bool:
        """選択肢から学習"""
        try:
            # 曖昧時の選択を記録
            if context.get('disambiguation_options'):
                await self.memory.update_preference(
                    user_id, 'disambiguation', 
                    context.get('context_key', 'general'),
                    selected_option
                )
            
            # 自動補完の確認
            if context.get('auto_filled_fields'):
                for field in context['auto_filled_fields']:
                    await self.memory.update_preference(
                        user_id, f'default_{field}',
                        'default', context.get(field)
                    )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to learn from selection: {e}")
            return False
    
    async def _get_cached_preferences(self, user_id: str) -> Dict:
        """キャッシュされた好み設定取得（5分キャッシュ）"""
        cache_key = f"prefs_{user_id}"
        now = datetime.now()
        
        if (cache_key in self.user_cache and 
            now - self.user_cache[cache_key]['timestamp'] < timedelta(minutes=5)):
            return self.user_cache[cache_key]['data']
        
        preferences = await self.memory.get_user_preferences(user_id)
        self.user_cache[cache_key] = {
            'data': preferences,
            'timestamp': now
        }
        
        return preferences
    
    def _is_similar_input(self, input1: str, input2: str, threshold=0.7) -> bool:
        """入力の類似度判定（簡易版）"""
        if not input1 or not input2:
            return False
        
        # 単純な文字重複度で判定
        set1 = set(input1.lower())
        set2 = set(input2.lower())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold

class LearningFeedbackSystem:
    """学習フィードバックシステム - Few-shot最適化＋確認フロー"""
    
    def __init__(self, memory_layer: MemoryLayer, personalization: PersonalizationEngine):
        self.memory = memory_layer
        self.personalization = personalization
    
    async def generate_few_shot_examples(self, user_id: str, intent_type: str = None) -> List[Dict]:
        """ユーザー専用Few-shot例文生成"""
        try:
            query = self.memory.db.collection(self.memory.logs_collection).where(
                'user_id', '==', user_id
            ).where('confidence', '>=', 0.9)
            
            if intent_type:
                query = query.where('intent', '==', intent_type)
            
            docs = query.order_by('timestamp', direction='DESCENDING').limit(10).get()
            
            examples = []
            for doc in docs:
                log = doc.to_dict()
                examples.append({
                    'input': log['raw_input'],
                    'intent': log['intent'],
                    'entities': log['entities'],
                    'confidence': log['confidence']
                })
            
            return examples
        except Exception as e:
            print(f"[ERROR] Failed to generate few-shot examples: {e}")
            return []
    
    async def suggest_learning_confirmation(self, user_id: str, 
                                          new_pattern: Dict) -> Dict[str, Any]:
        """学習確認提案生成"""
        pattern_type = new_pattern.get('type', 'unknown')
        
        if pattern_type == 'default_mention':
            return {
                'message': f"「{new_pattern['key']}」のときは毎回「{new_pattern['value']}」を使いますか？",
                'options': ['はい、次から自動で', 'いいえ、毎回聞いて', '今回だけ'],
                'learning_type': 'preference',
                'confidence_required': 0.8
            }
        
        elif pattern_type == 'time_pattern':
            return {
                'message': f"「{new_pattern['key']}」と言ったら「{new_pattern['value']}」の意味ですか？",
                'options': ['はい', 'いいえ', '場合による'],
                'learning_type': 'shortcut',
                'confidence_required': 0.9
            }
        
        elif pattern_type == 'intent_correction':
            return {
                'message': f"「{new_pattern['input']}」のような表現は「{new_pattern['correct_intent']}」として覚えますか？",
                'options': ['はい、学習して', 'いいえ', 'もう少し様子見'],
                'learning_type': 'correction',
                'confidence_required': 0.85
            }
        
        return {
            'message': "この操作パターンを学習しますか？",
            'options': ['はい', 'いいえ'],
            'learning_type': 'general',
            'confidence_required': 0.7
        }
    
    async def apply_confirmed_learning(self, user_id: str, confirmation: Dict) -> bool:
        """確認された学習の適用"""
        try:
            learning_type = confirmation.get('learning_type')
            pattern = confirmation.get('pattern')
            user_choice = confirmation.get('user_choice')
            
            if user_choice == 'はい、次から自動で' or user_choice == 'はい、学習して':
                if learning_type == 'preference':
                    await self.memory.update_preference(
                        user_id, pattern['pref_type'], 
                        pattern['key'], pattern['value']
                    )
                elif learning_type == 'correction':
                    # 修正パターンの確信度を上げる
                    pattern_id = pattern.get('pattern_id')
                    if pattern_id:
                        self.memory.db.collection(self.memory.patterns_collection).document(
                            pattern_id
                        ).update({
                            'confidence': min(0.95, pattern.get('confidence', 0.7) + 0.2),
                            'user_confirmed': True
                        })
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to apply confirmed learning: {e}")
            return False

# 統合クラス
class MemoryLearningSystem:
    """記憶・学習統合システム"""
    
    def __init__(self):
        self.memory = MemoryLayer()
        self.personalization = PersonalizationEngine(self.memory)
        self.feedback = LearningFeedbackSystem(self.memory, self.personalization)
        
        print("SUCCESS: Memory & Learning System initialized")
    
    async def process_with_memory(self, user_id: str, channel_id: str,
                                 raw_input: str, detected_intent: Dict) -> Dict:
        """記憶・学習を含めた総合処理"""
        
        # 1. 過去の学習からエンティティ補完
        enhanced_entities = await self.personalization.enhance_entities(
            user_id, detected_intent.get('entities', {})
        )
        
        # 2. 修正候補の提示（低信頼度の場合）
        suggestions = []
        if detected_intent.get('confidence', 0) < 0.8:
            suggestions = await self.personalization.suggest_corrections(
                user_id, detected_intent['intent'], raw_input
            )
        
        # 3. 結果をメモリに記録
        result = {
            'intent': detected_intent['intent'],
            'entities': enhanced_entities,
            'confidence': detected_intent.get('confidence', 0),
            'suggestions': suggestions,
            'auto_filled': enhanced_entities.get('_auto_filled', [])
        }
        
        log_id = await self.memory.save_action_log(
            user_id, channel_id, detected_intent['intent'], 
            raw_input, enhanced_entities, result, 
            detected_intent.get('confidence', 0)
        )
        
        result['log_id'] = log_id
        return result
    
    async def handle_correction(self, log_id: str, correct_intent: str, 
                               feedback: str) -> bool:
        """修正処理"""
        return await self.memory.save_correction(log_id, '', correct_intent, feedback)
    
    async def handle_learning_confirmation(self, user_id: str, 
                                          pattern: Dict) -> Dict:
        """学習確認処理"""
        return await self.feedback.suggest_learning_confirmation(user_id, pattern)

# テスト用
if __name__ == "__main__":
    import asyncio
    
    async def test_memory_system():
        system = MemoryLearningSystem()
        
        # テストデータ
        user_id = "test_user_123"
        channel_id = "test_channel_456"
        
        # 操作ログ保存テスト
        log_id = await system.memory.save_action_log(
            user_id, channel_id, "todo.add", "CCT作業を追加",
            {"title": "CCT作業", "mention": "@mrc"}, 
            {"success": True}, 0.95
        )
        
        print(f"Log saved: {log_id}")
        
        # 好み更新テスト
        await system.memory.update_preference(
            user_id, "default_mention", "default", "@mrc"
        )
        
        # 好み取得テスト
        prefs = await system.memory.get_user_preferences(user_id)
        print(f"User preferences: {prefs}")
        
        print("Memory system test completed!")
    
    # テスト実行
    try:
        asyncio.run(test_memory_system())
    except Exception as e:
        print(f"Test failed: {e}")