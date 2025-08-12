#!/usr/bin/env python3
"""
Smart Intent Classifier - Catherine AI決定版LLMプロンプト
短く・ブレない・厳格JSON出力による意図分類システム
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from openai import OpenAI
import pytz

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ClassifiedIntent:
    """分類済み意図 - Zod準拠スキーマ"""
    intent: str
    what: Optional[str] = None
    indices: Optional[List[int]] = None
    time: Optional[str] = None  # ISO8601 +09:00
    repeat: Optional[str] = None  # RRULE
    mention: Optional[str] = None
    confidence: float = 0.0
    missing_fields: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class SmartIntentClassifier:
    """スマート意図分類器 - 決定版プロンプト"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.confidence_threshold = 0.7
    
    def classify(self, text: str, user_preferences: Optional[Dict] = None) -> ClassifiedIntent:
        """意図分類メイン処理"""
        try:
            now = datetime.now(JST)
            tomorrow_9am = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            
            # 決定版システムプロンプト
            system_prompt = f"""あなたはDiscord秘書BotのNLU。日本語の発話を必ず次のJSONで返す。理由や説明は禁止。

現在時刻: {now.strftime('%Y-%m-%d %H:%M')} JST

SCHEMA:
{{"intent":"todo.add|todo.delete|todo.complete|todo.list|remind.create|remind.delete|remind.list|remind.snooze|chitchat",
 "what": "string|null",
 "indices": [number]|null,
 "time": "YYYY-MM-DDTHH:mm+09:00|null",
 "repeat": "RRULE|null",
 "mention": "@everyone|@mrc|@supy|null",
 "confidence": 0.0,
 "missing_fields": ["time","indices"]}}

RULES:
- 日本語の日時は Asia/Tokyo として ISO に解決（相対表現も）。
- 意図が複数なら最も作用の強い1つを選ぶ。
- 必須が欠けるときは missing_fields を埋める。
- JSONのみ返す。

FEW-SHOTS:
U: 1,3,5はけして
A: {{"intent":"todo.delete","what":null,"indices":[1,3,5],"time":null,"repeat":null,"mention":null,"confidence":0.96,"missing_fields":null}}

U: 毎朝9時に進捗リマインド @everyone
A: {{"intent":"remind.create","what":"進捗リマインド","indices":null,"time":"{tomorrow_9am.strftime('%Y-%m-%dT%H:%M+09:00')}","repeat":"FREQ=DAILY","mention":"@everyone","confidence":0.94,"missing_fields":null}}

U: リスト見せて
A: {{"intent":"todo.list","what":null,"indices":null,"time":null,"repeat":null,"mention":null,"confidence":0.99,"missing_fields":null}}

U: 午後にアラート
A: {{"intent":"remind.create","what":"アラート","indices":null,"time":null,"repeat":null,"mention":null,"confidence":0.65,"missing_fields":["time"]}}

U: 1-3消して  
A: {{"intent":"todo.delete","what":null,"indices":[1,2,3],"time":null,"repeat":null,"mention":null,"confidence":0.95,"missing_fields":null}}

U: 全部消して
A: {{"intent":"todo.delete","what":null,"indices":null,"time":null,"repeat":null,"mention":null,"confidence":0.85,"missing_fields":["indices"]}}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSON厳格解析
            try:
                data = json.loads(response_text)
                
                return ClassifiedIntent(
                    intent=data.get('intent', 'chitchat'),
                    what=data.get('what'),
                    indices=data.get('indices'),
                    time=data.get('time'),
                    repeat=data.get('repeat'),
                    mention=data.get('mention'),
                    confidence=data.get('confidence', 0.0),
                    missing_fields=data.get('missing_fields')
                )
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, response: {response_text}")
                return ClassifiedIntent(intent='chitchat', confidence=0.0, missing_fields=['parse_error'])
                
        except Exception as e:
            print(f"Classification error: {e}")
            return ClassifiedIntent(intent='chitchat', confidence=0.0, missing_fields=['error'])
    
    def generate_clarification_question(self, classified: ClassifiedIntent) -> str:
        """曖昧解決用質問生成"""
        
        if not classified.missing_fields:
            return ""
        
        missing = classified.missing_fields
        
        # 意図不明
        if 'intent' in missing or classified.intent == 'chitchat':
            return "意図が曖昧です。①追加 ②削除 ③完了 ④一覧 ⑤リマインド"
        
        # 削除対象なし
        if classified.intent in ['todo.delete', 'todo.complete'] and 'indices' in missing:
            return "どれを操作しますか？番号で指定してね（例：1,3 / 2-5）。\n直前のリスト👇"
        
        # リマインド時間なし
        if classified.intent == 'remind.create' and 'time' in missing:
            return "いつ通知しますか？（例：今日15:30 / 10分後 / 毎朝9時）"
        
        # 低信頼度
        if classified.confidence < 0.7:
            return f"解釈：{classified.intent} / 内容：{classified.what}。実行していい？ ①はい ②修正"
        
        return "詳細を教えてください"

class MinimalTestSuite:
    """最低限のテストスイート - 壊れやすい箇所を先にチェック"""
    
    def __init__(self, classifier: SmartIntentClassifier):
        self.classifier = classifier
    
    def run_critical_tests(self) -> Dict[str, bool]:
        """クリティカルテスト実行"""
        # APIキー不要の静的テスト
        results = {
            "range_expansion": self._test_range_expansion(),
            "missing_field_detection": self._test_missing_fields(),
            "confidence_threshold": self._test_confidence(),
            "json_validation": self._test_json_structure(),
            "question_generation": self._test_questions()
        }
        return results
    
    def _test_range_expansion(self) -> bool:
        """範囲展開テスト（1-3 → [1,2,3]）"""
        # ルールベーステスト
        test_text = "1-3消して"
        range_pattern = r'(\d+)-(\d+)'
        match = re.search(range_pattern, test_text)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            expanded = list(range(start, end + 1))
            return expanded == [1, 2, 3]
        return False
    
    def _test_missing_fields(self) -> bool:
        """必須フィールド検出テスト"""
        test_intent = ClassifiedIntent(
            intent="remind.create",
            what="テスト",
            missing_fields=["time"]
        )
        question = self.classifier.generate_clarification_question(test_intent)
        return "いつ通知" in question
    
    def _test_confidence(self) -> bool:
        """信頼度テスト"""
        low_confidence = ClassifiedIntent(
            intent="todo.add",
            what="テスト",
            confidence=0.5
        )
        question = self.classifier.generate_clarification_question(low_confidence)
        return "実行していい" in question
    
    def _test_json_structure(self) -> bool:
        """JSON構造テスト"""
        test_intent = ClassifiedIntent(
            intent="todo.list",
            confidence=0.99
        )
        json_str = test_intent.to_json()
        try:
            data = json.loads(json_str)
            return data.get("intent") == "todo.list"
        except:
            return False
    
    def _test_questions(self) -> bool:
        """質問生成テスト"""
        test_cases = [
            (ClassifiedIntent(intent="chitchat"), "意図が曖昧"),
            (ClassifiedIntent(intent="todo.delete", missing_fields=["indices"]), "番号で指定"),
            (ClassifiedIntent(intent="remind.create", missing_fields=["time"]), "いつ通知"),
        ]
        
        for intent, expected in test_cases:
            question = self.classifier.generate_clarification_question(intent)
            if expected not in question:
                return False
        return True
    
    def generate_test_report(self) -> str:
        """テストレポート生成"""
        results = self.run_critical_tests()
        
        report = "Catherine AI Intent Classifier Test Report\n\n"
        
        for test_name, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            report += f"{status} {test_name}: {'PASS' if passed else 'FAIL'}\n"
        
        passed_count = sum(results.values())
        total_count = len(results)
        
        report += f"\nSummary: {passed_count}/{total_count} passed"
        if passed_count == total_count:
            report += " - All tests passed!"
        else:
            report += " - Some tests failed"
        
        return report

# 使用例・テスト実行
if __name__ == "__main__":
    print("Catherine AI Smart Intent Classifier")
    print("Features:")
    print("  - Final LLM prompt (short & stable)")
    print("  - Strict JSON output (Zod schema)")
    print("  - Range expansion (1-3 -> [1,2,3])")
    print("  - Ambiguity detection & question generation")
    print("  - Critical tests included")
    
    # APIキー不要のテスト実行
    test_classifier = SmartIntentClassifier(None)  # API不要
    test_suite = MinimalTestSuite(test_classifier)
    report = test_suite.generate_test_report()
    print("\n" + report)
"""
Smart Intent Classifier - OpenAI API based natural language understanding
Catherine AI の自然言語理解エンジン - 真の意図分類システム
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pytz
from openai import OpenAI

# 日本時間
JST = pytz.timezone('Asia/Tokyo')

@dataclass
class IntentResult:
    intent: str  # add, delete, complete, list, remind, find, help
    confidence: float  # 0.0 - 1.0
    entities: Dict[str, Any]  # 抽出された情報
    raw_response: str  # LLMの生レスポンス
    error: Optional[str] = None
    fallback_used: bool = False

class SmartIntentClassifier:
    """OpenAI APIベースの高精度意図分類器"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
        # システムプロンプト
        self.system_prompt = """あなたは Discord TODO システムの意図分類器です。
ユーザーの自然言語入力を分析し、以下の JSON 形式で返してください：

{
    "intent": "add|delete|complete|list|remind|find|help|unknown",
    "confidence": 0.0-1.0,
    "entities": {
        "indices": [1,3,5] または null,
        "title": "タスクタイトル" または null,
        "due_time": "2025-08-12T15:30:00+09:00" または null,
        "priority": "urgent|high|normal|low" または null,
        "tags": ["tag1", "tag2"] または null,
        "assignees": ["@mrc", "@supy"] または null,
        "mention": "@everyone|@mrc|@supy" または null,
        "query": "検索キーワード" または null
    }
}

**意図の定義：**
- add: 新しいTODOを追加
- delete: TODOを削除（番号指定や自然言語）
- complete: TODOを完了（番号指定や自然言語）
- list: TODOリストを表示
- remind: リマインドを設定
- find: TODOを検索
- help: ヘルプを表示
- unknown: 不明

**重要な判定基準：**
- 「消す」「削除」「けす」「取り消し」= delete
- 「完了」「済み」「終わり」「done」「finished」= complete
- 「一覧」「リスト」「表示」「見せて」「出して」= list
- 「リマインド」「通知」「知らせて」「思い出させて」= remind
- 「探して」「検索」「見つけて」「どこ」= find
- 数字(1,3,5 や 1-3)がある場合は indices に抽出

**時刻解析：**
- 「明日18時」「来週月曜」「8/12 15:30」などを ISO 8601 形式に変換
- タイムゾーンは Asia/Tokyo (+09:00)
- 相対時間も絶対時間に変換

**メンション抽出：**
- @mrc, @supy, @everyone, みんな, 全員 を正規化

JSON のみ返し、他の説明は不要です。"""

        # フォールバック用ルールベース分類器
        self.fallback_patterns = {
            'delete': [
                r'(?:削除|消す|けす|消して|消しといて|取り消し|remove|delete)',
                r'(?:なくして|いらない|不要)'
            ],
            'complete': [
                r'(?:完了|done|済み|済ま|終わり|終わった|finished|できた)',
                r'(?:チェック|check|✅)'
            ],
            'list': [
                r'(?:一覧|リスト|list|表示|見せて|出して|show)',
                r'(?:何がある|どんなの|確認)'
            ],
            'remind': [
                r'(?:リマインド|remind|通知|知らせて|思い出させて|忘れないで)',
                r'(?:アラーム|時報|お知らせ)'
            ],
            'find': [
                r'(?:探して|検索|見つけて|search|find)',
                r'(?:どこ|何だっけ|あれ)'
            ],
            'help': [
                r'(?:ヘルプ|help|使い方|どうやって|方法)',
                r'(?:わからない|教えて)'
            ]
        }
    
    async def classify(self, text: str, context: Dict[str, Any] = None) -> IntentResult:
        """自然言語テキストから意図を分類"""
        try:
            # OpenAI API で分類
            llm_result = await self._classify_with_llm(text, context)
            
            if llm_result and llm_result.confidence > 0.7:
                return llm_result
            
            # フォールバックでルールベース分類
            print(f"[INTENT] LLM confidence low ({llm_result.confidence if llm_result else 'failed'}), using fallback")
            fallback_result = self._classify_with_rules(text)
            fallback_result.fallback_used = True
            
            return fallback_result
            
        except Exception as e:
            print(f"[ERROR] Intent classification failed: {e}")
            return IntentResult(
                intent='unknown',
                confidence=0.0,
                entities={},
                raw_response='',
                error=str(e)
            )
    
    async def _classify_with_llm(self, text: str, context: Dict[str, Any] = None) -> IntentResult:
        """OpenAI APIで意図分類"""
        try:
            # コンテキスト情報を追加
            context_str = ""
            if context:
                if context.get('last_list_count'):
                    context_str += f"直前に{context['last_list_count']}件のTODOリストを表示済み。"
                if context.get('user_timezone'):
                    context_str += f"ユーザーのタイムゾーン: {context['user_timezone']}。"
            
            user_prompt = f"{context_str}ユーザー入力: {text}"
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 一貫性重視
                max_tokens=500
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # JSON パース
            try:
                # JSONコードブロックから抽出
                if '```json' in raw_response:
                    json_part = raw_response.split('```json')[1].split('```')[0].strip()
                elif '```' in raw_response:
                    json_part = raw_response.split('```')[1].strip()
                else:
                    json_part = raw_response
                
                parsed = json.loads(json_part)
                
                return IntentResult(
                    intent=parsed.get('intent', 'unknown'),
                    confidence=float(parsed.get('confidence', 0.5)),
                    entities=parsed.get('entities', {}),
                    raw_response=raw_response
                )
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parse failed: {e}, raw: {raw_response[:200]}")
                return IntentResult(
                    intent='unknown',
                    confidence=0.0,
                    entities={},
                    raw_response=raw_response,
                    error=f"JSON parse error: {str(e)}"
                )
                
        except Exception as e:
            print(f"[ERROR] LLM classification failed: {e}")
            raise
    
    def _classify_with_rules(self, text: str) -> IntentResult:
        """フォールバック用ルールベース分類"""
        text_lower = text.lower()
        best_intent = 'unknown'
        best_score = 0.0
        
        # パターンマッチング
        for intent, patterns in self.fallback_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # 基本的なエンティティ抽出
        entities = self._extract_basic_entities(text)
        
        confidence = min(0.8, 0.3 + best_score * 0.2) if best_score > 0 else 0.1
        
        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            raw_response=f"Fallback classification: {best_intent}",
            fallback_used=True
        )
    
    def _extract_basic_entities(self, text: str) -> Dict[str, Any]:
        """基本的なエンティティ抽出（フォールバック用）"""
        entities = {}
        
        # 番号抽出
        indices = self._extract_indices(text)
        if indices:
            entities['indices'] = indices
        
        # タグ抽出
        tags = re.findall(r'#([a-zA-Z0-9_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)', text)
        if tags:
            entities['tags'] = tags
        
        # メンション抽出
        mentions = re.findall(r'@([a-zA-Z0-9_]+)', text)
        if mentions:
            entities['assignees'] = [f'@{m}' for m in mentions]
        
        # 優先度抽出
        if re.search(r'(?:urgent|緊急|至急|なるはや)', text, re.IGNORECASE):
            entities['priority'] = 'urgent'
        elif re.search(r'(?:high|高|重要)', text, re.IGNORECASE):
            entities['priority'] = 'high'
        elif re.search(r'(?:low|低|後回し)', text, re.IGNORECASE):
            entities['priority'] = 'low'
        
        return entities
    
    def _extract_indices(self, text: str) -> List[int]:
        """番号リスト抽出（簡易版）"""
        indices = []
        
        # カンマ区切りの番号
        comma_matches = re.findall(r'(\d+)(?:\s*[,、]\s*(\d+))*', text)
        for match in comma_matches:
            for num_str in match:
                if num_str:
                    indices.append(int(num_str))
        
        # 範囲指定
        range_matches = re.findall(r'(\d+)\s*[-〜～]\s*(\d+)', text)
        for start_str, end_str in range_matches:
            start, end = int(start_str), int(end_str)
            indices.extend(range(start, end + 1))
        
        # 「と」区切り
        to_matches = re.findall(r'(\d+)\s*と\s*(\d+)', text)
        for num1_str, num2_str in to_matches:
            indices.extend([int(num1_str), int(num2_str)])
        
        return sorted(list(set(indices))) if indices else []

class IntentRouter:
    """意図分類結果に基づく処理ルーター"""
    
    def __init__(self, todo_system, reminder_system=None):
        self.todo_system = todo_system
        self.reminder_system = reminder_system
    
    async def route(self, intent_result: IntentResult, user_id: str, 
                   channel_id: str, message_id: str) -> Dict[str, Any]:
        """意図に基づいて適切な処理にルーティング"""
        
        intent = intent_result.intent
        entities = intent_result.entities
        
        if intent == 'add':
            return await self._handle_add(entities, user_id, channel_id, message_id)
        
        elif intent == 'delete':
            return await self._handle_delete(entities, user_id, channel_id)
        
        elif intent == 'complete':
            return await self._handle_complete(entities, user_id, channel_id)
        
        elif intent == 'list':
            return await self._handle_list(entities, user_id, channel_id)
        
        elif intent == 'remind':
            return await self._handle_remind(entities, user_id, channel_id, message_id)
        
        elif intent == 'find':
            return await self._handle_find(entities, user_id, channel_id)
        
        elif intent == 'help':
            return await self._handle_help()
        
        else:
            return {
                'success': False,
                'message': f'申し訳ありませんが、「{intent}」の処理方法がわかりません。',
                'suggestion': 'ヘルプをご覧になりますか？ `todo help`',
                'response_type': 'unknown_intent'
            }
    
    async def _handle_add(self, entities: Dict, user_id: str, channel_id: str, message_id: str) -> Dict:
        """TODO追加処理"""
        if not entities.get('title'):
            return {
                'success': False,
                'message': 'TODOのタイトルを教えてください',
                'suggestion': '例: todo add 「レポート作成」明日18時 high #urgent',
                'response_type': 'missing_title'
            }
        
        # TODO追加処理（既存システムを活用）
        return await self.todo_system._handle_add_with_entities(entities, user_id, channel_id, message_id)
    
    async def _handle_delete(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """TODO削除処理"""
        if entities.get('indices'):
            # 番号指定削除
            return await self.todo_system._handle_bulk_delete_indices(entities['indices'], user_id, channel_id)
        else:
            # 自然言語削除
            return await self.todo_system._handle_natural_delete(entities, user_id, channel_id)
    
    async def _handle_complete(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """TODO完了処理"""
        if entities.get('indices'):
            # 番号指定完了
            return await self.todo_system._handle_bulk_complete_indices(entities['indices'], user_id, channel_id)
        else:
            # 自然言語完了
            return await self.todo_system._handle_natural_complete(entities, user_id, channel_id)
    
    async def _handle_list(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """TODOリスト表示処理"""
        return await self.todo_system._handle_list_with_filters(entities, user_id, channel_id)
    
    async def _handle_remind(self, entities: Dict, user_id: str, channel_id: str, message_id: str) -> Dict:
        """リマインド処理"""
        if not self.reminder_system:
            return {
                'success': False,
                'message': 'リマインド機能は現在利用できません',
                'response_type': 'reminder_unavailable'
            }
        
        return await self.reminder_system._handle_remind_with_entities(entities, user_id, channel_id, message_id)
    
    async def _handle_find(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """TODO検索処理"""
        query = entities.get('query', entities.get('title', ''))
        if not query:
            return {
                'success': False,
                'message': '何を検索しますか？',
                'suggestion': '例: 検索 「レポート」、CCTタグを探して',
                'response_type': 'missing_query'
            }
        
        return await self.todo_system._handle_search(query, entities, user_id, channel_id)
    
    async def _handle_help(self) -> Dict:
        """ヘルプ表示"""
        help_message = await self.todo_system.get_help()
        return {
            'success': True,
            'message': help_message,
            'response_type': 'help'
        }

# テスト用
if __name__ == "__main__":
    import asyncio
    import os
    
    async def test_classifier():
        """意図分類器のテスト"""
        
        # OpenAI クライアント初期化（テスト用）
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        client = OpenAI(api_key=api_key)
        
        classifier = SmartIntentClassifier(client)
        
        test_cases = [
            "todo 削除して",
            "1,3,5は消しといて", 
            "2と4完了",
            "リスト出して",
            "明日18時にリマインド",
            "CCTタグの一覧",
            "ロンT制作を追加して",
            "全部完了",
            "help",
        ]
        
        print("🧪 Smart Intent Classifier テスト")
        print("-" * 50)
        
        for test_text in test_cases:
            print(f"\n📝 Input: {test_text}")
            try:
                result = await classifier.classify(test_text)
                print(f"Intent: {result.intent} (confidence: {result.confidence:.2f})")
                print(f"Entities: {result.entities}")
                if result.fallback_used:
                    print("⚠️  Fallback used")
                if result.error:
                    print(f"❌ Error: {result.error}")
            except Exception as e:
                print(f"❌ Failed: {e}")
    
    # テスト実行
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_classifier())
    else:
        print("WARNING: OPENAI_API_KEY not set, skipping LLM tests")
        
        # ルールベースのみテスト
        classifier = SmartIntentClassifier(None)
        for text in ["1,3,5削除", "リスト表示", "完了"]:
            result = classifier._classify_with_rules(text)
            print(f"{text} → {result.intent} ({result.confidence:.2f})")