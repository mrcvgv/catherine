#!/usr/bin/env python3
"""
Hybrid Intent Detection System - ルール＋LLMの二段構え
Catherine AI の精度優先自然言語理解エンジン
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import pytz
from openai import OpenAI
from memory_learning_system import MemoryLearningSystem

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class IntentSpec:
    """意図仕様 - 厳格型定義"""
    intent: str  # todo.add|todo.delete|todo.complete|todo.list|remind.*|chitchat
    confidence: float = 0.0
    what: Optional[str] = None  # タスク/リマインド内容
    indices: Optional[List[int]] = None  # リスト番号
    time: Optional[str] = None  # ISO8601形式
    repeat: Optional[str] = None  # RFC5545形式
    mention: Optional[str] = None  # @everyone|@mrc|@supy
    missing_fields: List[str] = field(default_factory=list)
    raw_text: str = ""
    rule_matched: bool = False
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass 
class PendingIntent:
    """保留中の意図 - 確認待ち管理"""
    pending_id: str
    user_id: str
    channel_id: str
    spec: IntentSpec
    missing_fields: List[str]
    created_at: datetime
    expires_at: datetime
    status: str = "waiting"  # waiting|completed|expired

class RuleBasedDetector:
    """ルール層 - 高速・確定判定"""
    
    def __init__(self):
        # 意図パターン（日本語強化版）
        self.patterns = {
            'todo.add': [
                r'(追加|入れて|登録|作って|新規|add|new|todo)',
                r'(やること|タスク|TODO|ToDo)',
                r'(.+を?(?:追加|入れて|登録))'
            ],
            'todo.delete': [
                r'(削除|消して?|けして?|取り消し|remove|delete)',
                r'(消す|消せ|消しとく?|消しといて)',
                r'(\d+[,、]?\d*\s*(?:削除|消|けし))'
            ],
            'todo.complete': [
                r'(完了|済み?|済ま|終わり|終了|チェック|done|finish)',
                r'(できた|やった|OK|ok)',
                r'(\d+[,、]?\d*\s*(?:完了|済み?))'
            ],
            'todo.list': [
                r'(一覧|リスト|list|show|見せて|出して)',
                r'(表示|確認|何がある|どんな)',
                r'(TODO|todo|タスク)\s*(?:一覧|リスト)'
            ],
            'remind.create': [
                r'(リマインド|通知|知らせて|教えて|remind|alert)',
                r'(思い出させて|忘れないで|お知らせ)',
                r'(\d+時|明日|来週|毎朝)'
            ]
        }
        
        # 数字抽出パターン
        self.number_patterns = [
            (r'(\d+)\s*[,、]\s*(\d+)', 'comma'),  # 1,3,5
            (r'(\d+)\s*[-〜～]\s*(\d+)', 'range'),  # 1-3
            (r'(\d+)\s*と\s*(\d+)', 'and'),  # 1と3
            (r'(\d+)', 'single')  # 単独数字
        ]
        
        # 宛先パターン
        self.mention_patterns = {
            '@everyone': ['@everyone', '全員', 'みんな', 'みな'],
            '@mrc': ['@mrc', 'MRC', 'エムアールシー'],
            '@supy': ['@supy', 'SUPY', 'スパイ']
        }
    
    def detect(self, text: str) -> IntentSpec:
        """ルールベース意図検出"""
        text_lower = text.lower()
        best_intent = None
        best_score = 0.0
        
        # 意図マッチング
        for intent, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # エンティティ抽出
        indices = self._extract_indices(text)
        mention = self._extract_mention(text)
        
        # 信頼度計算（ルールベースは0.6-0.9）
        confidence = min(0.9, 0.6 + best_score * 0.1) if best_score > 0 else 0.3
        
        return IntentSpec(
            intent=best_intent or 'unknown',
            confidence=confidence,
            indices=indices,
            mention=mention,
            raw_text=text,
            rule_matched=True if best_intent else False
        )
    
    def _extract_indices(self, text: str) -> Optional[List[int]]:
        """番号抽出（全角対応）"""
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        indices = []
        
        for pattern, ptype in self.number_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if ptype == 'single':
                    indices.append(int(match.group(1)))
                elif ptype == 'comma' or ptype == 'and':
                    indices.extend([int(g) for g in match.groups() if g])
                elif ptype == 'range':
                    start, end = int(match.group(1)), int(match.group(2))
                    indices.extend(range(start, end + 1))
        
        return sorted(list(set(indices))) if indices else None
    
    def _extract_mention(self, text: str) -> Optional[str]:
        """宛先抽出"""
        for mention, patterns in self.mention_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return mention
        return None

class LLMIntentDetector:
    """LLM層 - 汎用・曖昧対応"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.system_prompt = """あなたはDiscordの秘書Botの自然言語解析器です。
ユーザー発話から意図とエンティティを抽出し、必ずJSON形式のみで返します。

出力スキーマ：
{
  "intent": "todo.add|todo.delete|todo.complete|todo.list|remind.create|remind.delete|remind.list|remind.snooze|chitchat",
  "what": "タスクやリマインドの内容（あれば）",
  "indices": [1,3,5],  // 番号リスト（あれば）
  "time": "2025-08-12T10:00:00+09:00",  // ISO8601形式（あれば）
  "repeat": "FREQ=DAILY;BYHOUR=9",  // RFC5545形式（あれば）
  "mention": "@everyone|@mrc|@supy",  // 宛先（あれば）
  "confidence": 0.95,  // 0.0〜1.0の確信度
  "missing_fields": ["time", "mention"]  // 不足している項目
}

判定ルール：
- 「追加/入れて/登録」→ todo.add
- 「削除/消して/けして」→ todo.delete  
- 「完了/済み/done」→ todo.complete
- 「一覧/リスト/見せて」→ todo.list
- 「リマインド/通知/知らせて」→ remind.create
- 数字は半角に統一、範囲は展開
- 日時は日本時間(+09:00)でISO8601形式に変換
- 宛先が不明なら"missing_fields"に含める

JSONのみ返し、他の説明は不要です。"""
    
    async def detect(self, text: str, context: Dict[str, Any] = None) -> IntentSpec:
        """LLMによる意図検出"""
        try:
            # コンテキスト情報を追加
            context_info = ""
            if context:
                if context.get('last_list'):
                    context_info += f"直前のリスト: {len(context['last_list'])}件表示済み\n"
                if context.get('current_time'):
                    context_info += f"現在時刻: {context['current_time']}\n"
            
            user_prompt = f"{context_info}ユーザー発話: {text}"
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # JSON抽出
            json_str = self._extract_json(raw_response)
            parsed = json.loads(json_str)
            
            return IntentSpec(
                intent=parsed.get('intent', 'unknown'),
                confidence=float(parsed.get('confidence', 0.5)),
                what=parsed.get('what'),
                indices=parsed.get('indices'),
                time=parsed.get('time'),
                repeat=parsed.get('repeat'),
                mention=parsed.get('mention'),
                missing_fields=parsed.get('missing_fields', []),
                raw_text=text
            )
            
        except Exception as e:
            print(f"[ERROR] LLM detection failed: {e}")
            return IntentSpec(
                intent='unknown',
                confidence=0.0,
                raw_text=text,
                missing_fields=['all']
            )
    
    def _extract_json(self, text: str) -> str:
        """JSONブロック抽出"""
        if '```json' in text:
            return text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            return text.split('```')[1].strip()
        elif '{' in text and '}' in text:
            start = text.index('{')
            end = text.rindex('}') + 1
            return text[start:end]
        return text

class HybridIntentDetector:
    """ハイブリッド意図検出器 - 記憶・学習対応版"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.rule_detector = RuleBasedDetector()
        self.llm_detector = LLMIntentDetector(openai_client) if openai_client else None
        self.pending_intents: Dict[str, PendingIntent] = {}
        
        # 記憶・学習システム
        self.memory_system = MemoryLearningSystem()
        
        # 設定値
        self.confidence_threshold = 0.8
        self.pending_timeout_minutes = 15
        
        # 必須フィールド定義
        self.required_fields = {
            'todo.add': ['what'],
            'todo.delete': ['indices'],  # or 'what'
            'todo.complete': ['indices'],  # or 'what'
            'remind.create': ['what', 'time'],
            'remind.delete': ['indices'],
            'remind.snooze': ['indices', 'time']
        }
    
    async def detect(self, text: str, user_id: str, channel_id: str, 
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """ハイブリッド意図検出 - 記憶・学習対応メインエントリポイント"""
        
        # 保留中の意図があるかチェック
        pending_key = f"{user_id}:{channel_id}"
        if pending_key in self.pending_intents:
            return await self._handle_pending_response(text, pending_key)
        
        # 1. ルール層で高速判定
        rule_spec = self.rule_detector.detect(text)
        
        # 2. LLM層で詳細解析（利用可能な場合）
        if self.llm_detector and (rule_spec.confidence < 0.7 or not rule_spec.rule_matched):
            llm_spec = await self.llm_detector.detect(text, context)
            
            # マージ（LLM優先、ただしルールが確実な場合は尊重）
            if llm_spec.confidence > rule_spec.confidence:
                spec = llm_spec
            else:
                spec = rule_spec
                # LLMのエンティティで補完
                if llm_spec.what and not spec.what:
                    spec.what = llm_spec.what
                if llm_spec.time and not spec.time:
                    spec.time = llm_spec.time
        else:
            spec = rule_spec
        
        # 3. 記憶・学習システムでの処理
        memory_result = await self.memory_system.process_with_memory(
            user_id, channel_id, text, {
                'intent': spec.intent,
                'entities': spec.to_dict(),
                'confidence': spec.confidence
            }
        )
        
        # エンティティを学習済みで補完
        for key, value in memory_result['entities'].items():
            if not key.startswith('_'):
                setattr(spec, key, value)
        
        # 修正候補がある場合
        if memory_result.get('suggestions'):
            spec.missing_fields.append('intent_verification')
        
        # 4. バリデーション＆確認フロー
        result = await self._validate_and_confirm(spec, user_id, channel_id)
        
        # 記憶システムの情報を追加
        result['memory_info'] = {
            'log_id': memory_result.get('log_id'),
            'auto_filled': memory_result.get('auto_filled', []),
            'suggestions': memory_result.get('suggestions', [])
        }
        
        return result
    
    async def _validate_and_confirm(self, spec: IntentSpec, user_id: str, 
                                   channel_id: str) -> Dict[str, Any]:
        """仕様検証と確認フロー"""
        
        # 信頼度チェック
        if spec.confidence < self.confidence_threshold:
            return self._create_clarification_response(spec, user_id, channel_id)
        
        # 必須フィールドチェック
        if spec.intent in self.required_fields:
            required = self.required_fields[spec.intent]
            missing = []
            
            for field in required:
                value = getattr(spec, field, None)
                if not value:
                    missing.append(field)
            
            if missing:
                spec.missing_fields = missing
                return self._create_missing_fields_response(spec, user_id, channel_id)
        
        # デフォルト値適用
        if spec.intent.startswith('remind.') and not spec.mention:
            spec.mention = '@everyone'
        
        # 実行可能
        return {
            'action': 'execute',
            'spec': spec.to_dict(),
            'message': self._build_execution_summary(spec)
        }
    
    def _create_clarification_response(self, spec: IntentSpec, user_id: str, 
                                      channel_id: str) -> Dict[str, Any]:
        """曖昧時の確認レスポンス生成"""
        pending_id = self._save_pending(spec, user_id, channel_id)
        
        options = [
            "📝 TODO追加",
            "🗑️ TODO削除", 
            "✅ TODO完了",
            "📋 TODO一覧",
            "⏰ リマインド設定"
        ]
        
        return {
            'action': 'clarify',
            'pending_id': pending_id,
            'message': f"意図が不明確です。何をしますか？\n" + "\n".join(options),
            'spec': spec.to_dict()
        }
    
    def _create_missing_fields_response(self, spec: IntentSpec, user_id: str,
                                       channel_id: str) -> Dict[str, Any]:
        """不足フィールドの確認レスポンス生成"""
        pending_id = self._save_pending(spec, user_id, channel_id)
        
        questions = {
            'what': "内容を教えてください",
            'indices': "番号を指定してください（例: 1,3,5）",
            'time': "いつですか？（例: 明日18時、毎朝9時）",
            'mention': "誰に通知しますか？（@everyone/@mrc/@supy）"
        }
        
        missing_questions = [questions.get(f, f"「{f}」を指定してください") 
                           for f in spec.missing_fields]
        
        intent_name = self._get_intent_display_name(spec.intent)
        
        return {
            'action': 'confirm',
            'pending_id': pending_id,
            'message': f"**{intent_name}** を実行します。\n\n" + 
                      "\n".join(f"❓ {q}" for q in missing_questions),
            'spec': spec.to_dict()
        }
    
    def _save_pending(self, spec: IntentSpec, user_id: str, channel_id: str) -> str:
        """保留中の意図を保存"""
        pending_id = hashlib.md5(f"{user_id}:{channel_id}:{datetime.now()}".encode()).hexdigest()[:8]
        pending_key = f"{user_id}:{channel_id}"
        
        self.pending_intents[pending_key] = PendingIntent(
            pending_id=pending_id,
            user_id=user_id,
            channel_id=channel_id,
            spec=spec,
            missing_fields=spec.missing_fields,
            created_at=datetime.now(JST),
            expires_at=datetime.now(JST) + timedelta(minutes=self.pending_timeout_minutes)
        )
        
        return pending_id
    
    async def _handle_pending_response(self, text: str, pending_key: str) -> Dict[str, Any]:
        """保留中の意図への返答処理"""
        pending = self.pending_intents[pending_key]
        
        # タイムアウトチェック
        if datetime.now(JST) > pending.expires_at:
            del self.pending_intents[pending_key]
            return {
                'action': 'expired',
                'message': "前回の操作はタイムアウトしました。最初からやり直してください。"
            }
        
        # 返答を解析してフィールドを埋める
        spec = pending.spec
        
        # 簡易的なフィールド埋め込み
        if 'what' in pending.missing_fields and text:
            spec.what = text
            pending.missing_fields.remove('what')
        
        if 'indices' in pending.missing_fields:
            indices = self.rule_detector._extract_indices(text)
            if indices:
                spec.indices = indices
                pending.missing_fields.remove('indices')
        
        if 'mention' in pending.missing_fields:
            mention = self.rule_detector._extract_mention(text)
            if mention:
                spec.mention = mention
                pending.missing_fields.remove('mention')
        
        # まだ不足があるか確認
        if pending.missing_fields:
            return self._create_missing_fields_response(spec, pending.user_id, pending.channel_id)
        
        # 完了 - 実行可能
        del self.pending_intents[pending_key]
        return {
            'action': 'execute',
            'spec': spec.to_dict(),
            'message': self._build_execution_summary(spec)
        }
    
    def _build_execution_summary(self, spec: IntentSpec) -> str:
        """実行内容のサマリー生成"""
        intent_name = self._get_intent_display_name(spec.intent)
        
        parts = [f"**{intent_name}**"]
        
        if spec.what:
            parts.append(f"内容: {spec.what}")
        if spec.indices:
            parts.append(f"番号: {', '.join(map(str, spec.indices))}")
        if spec.time:
            parts.append(f"時刻: {spec.time}")
        if spec.mention:
            parts.append(f"宛先: {spec.mention}")
        
        return " | ".join(parts)
    
    def _get_intent_display_name(self, intent: str) -> str:
        """意図の表示名取得"""
        names = {
            'todo.add': 'TODO追加',
            'todo.delete': 'TODO削除',
            'todo.complete': 'TODO完了',
            'todo.list': 'TODO一覧',
            'remind.create': 'リマインド作成',
            'remind.delete': 'リマインド削除',
            'remind.list': 'リマインド一覧',
            'remind.snooze': 'リマインドスヌーズ',
            'chitchat': '雑談'
        }
        return names.get(intent, intent)
    
    async def handle_correction(self, log_id: str, correct_intent: str, 
                               user_feedback: str = "修正") -> Dict[str, Any]:
        """修正処理 - 学習システム連携"""
        try:
            success = await self.memory_system.handle_correction(
                log_id, correct_intent, user_feedback
            )
            
            if success:
                return {
                    'action': 'correction_saved',
                    'message': f"修正を学習しました。次回から「{correct_intent}」として理解します。",
                    'learning_applied': True
                }
            else:
                return {
                    'action': 'correction_failed', 
                    'message': "修正の保存に失敗しました",
                    'learning_applied': False
                }
        except Exception as e:
            print(f"[ERROR] Correction handling failed: {e}")
            return {
                'action': 'error',
                'message': f"修正処理エラー: {str(e)}"
            }
    
    async def suggest_learning_improvement(self, user_id: str, 
                                         interaction_history: List[Dict]) -> Dict[str, Any]:
        """学習改善提案"""
        try:
            # 最近の低信頼度操作を分析
            low_confidence_patterns = []
            for interaction in interaction_history[-10:]:  # 直近10件
                if interaction.get('confidence', 1.0) < 0.8:
                    low_confidence_patterns.append({
                        'input': interaction.get('raw_input', ''),
                        'intent': interaction.get('intent', ''),
                        'confidence': interaction.get('confidence', 0)
                    })
            
            if len(low_confidence_patterns) >= 3:
                # 学習提案生成
                pattern_analysis = await self.memory_system.feedback.suggest_learning_confirmation(
                    user_id, {
                        'type': 'pattern_improvement',
                        'patterns': low_confidence_patterns,
                        'suggestion': '類似表現の学習強化'
                    }
                )
                
                return {
                    'action': 'learning_suggestion',
                    'message': f"最近曖昧な表現が{len(low_confidence_patterns)}件ありました。",
                    'suggestion': pattern_analysis,
                    'can_improve': True
                }
            
            return {
                'action': 'no_suggestion',
                'message': "現在の理解度は良好です",
                'can_improve': False
            }
            
        except Exception as e:
            print(f"[ERROR] Learning suggestion failed: {e}")
            return {
                'action': 'error',
                'message': f"学習提案エラー: {str(e)}"
            }

# テスト
if __name__ == "__main__":
    import asyncio
    import os
    
    async def test_hybrid():
        # テスト用OpenAIクライアント（実際のAPIキーが必要）
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key) if api_key else None
        
        detector = HybridIntentDetector(client)
        
        test_cases = [
            ("1,3,5削除して", "user1", "ch1"),
            ("明日18時にリマインド", "user1", "ch1"),
            ("CCT作業を追加", "user1", "ch1"),
            ("リスト見せて", "user1", "ch1"),
            ("2と4完了", "user1", "ch1"),
            ("全部消して", "user1", "ch1"),
            ("うさぎかわいい", "user1", "ch1")
        ]
        
        print("Hybrid Intent Detection Test")
        print("-" * 50)
        
        for text, user_id, channel_id in test_cases:
            print(f"\nInput: {text}")
            result = await detector.detect(text, user_id, channel_id)
            print(f"Action: {result['action']}")
            if 'spec' in result:
                print(f"Intent: {result['spec'].get('intent')} ({result['spec'].get('confidence', 0):.2f})")
            print(f"Message: {result['message'][:100]}...")
    
    asyncio.run(test_hybrid())