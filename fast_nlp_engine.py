#!/usr/bin/env python3
"""
Fast NLP Engine - YAML駆動の高速自然言語処理
決め打ち正規表現 + LLM補完の二段構え
"""

from __future__ import annotations
import re
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Pattern
from datetime import datetime, timedelta
import pytz

try:
    import yaml
except ImportError:
    yaml = None

from openai import OpenAI

JST = pytz.timezone('Asia/Tokyo')

# 正規化テーブル
NORMALIZE_TABLE = {
    "　": " ",  # 全角スペース → 半角
    "！": "!",
    "？": "?",
    "（": "(",
    "）": ")",
    "［": "[",
    "］": "]",
}

# ストップワード
STOPWORDS = ["じゃあ", "えっと", "あの", "とりま", "ちなみに", "てか", "まあ"]

@dataclass
class PatternRule:
    intent: str
    pattern: Pattern
    weight: float = 1.0

class FastNLPEngine:
    def __init__(self, registry_path: str, openai_client: Optional[OpenAI] = None):
        self.rules: List[PatternRule] = []
        self.slot_filters: Dict[str, List[Pattern]] = {}
        self.openai_client = openai_client
        self.unmatched_log = []
        
        if os.path.exists(registry_path):
            self._load_registry(registry_path)
        else:
            print(f"⚠️ Registry file not found: {registry_path}")
            # フォールバック用の基本ルール
            self._load_fallback_rules()

    def _normalize(self, text: str) -> str:
        """テキスト正規化"""
        t = text.strip()
        
        # 文字正規化
        for k, v in NORMALIZE_TABLE.items():
            t = t.replace(k, v)
        
        # ストップワード除去
        for sw in STOPWORDS:
            t = t.replace(sw, "")
        
        return t.strip()

    def _compile(self, s: str) -> Pattern:
        """正規表現コンパイル"""
        try:
            return re.compile(s, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"❌ Regex compile error: {s} -> {e}")
            return re.compile(r"(?P<fallback>.*)")

    def _load_registry(self, path: str):
        """YAML レジストリ読み込み"""
        if not yaml:
            raise RuntimeError("PyYAML が必要です: pip install pyyaml")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            intents_loaded = 0
            patterns_loaded = 0
            
            for intent_data in data.get("intents", []):
                intent_name = intent_data["name"]
                weight = float(intent_data.get("weight", 1.0))
                
                # メインパターン
                for pattern_str in intent_data.get("patterns", []):
                    pattern = self._compile(pattern_str)
                    self.rules.append(PatternRule(
                        intent=intent_name,
                        pattern=pattern,
                        weight=weight
                    ))
                    patterns_loaded += 1
                
                # スロットフィルター
                slot_filters = intent_data.get("slot_filters", {})
                if slot_filters:
                    self.slot_filters[intent_name] = []
                    for filter_name, filter_patterns in slot_filters.items():
                        for fp in filter_patterns:
                            self.slot_filters[intent_name].append(self._compile(fp))
                
                intents_loaded += 1
            
            print(f"✅ Registry loaded: {intents_loaded} intents, {patterns_loaded} patterns")
            
        except Exception as e:
            print(f"❌ Failed to load registry: {e}")
            self._load_fallback_rules()

    def _load_fallback_rules(self):
        """フォールバック用基本ルール"""
        fallback_rules = [
            ("todo_add", r"(?P<task>.+?)(?:する|つくる|作る|やる|todo)", 2.0),
            ("todo_list", r"(?:list|リスト|一覧|やること)", 1.5),
            ("todo_done", r"(?P<task>.+?)(?:完了|終わった|できた)", 1.8),
            ("greeting", r"(?:おはよう|こんにちは|こんばんは|元気)", 1.0),
            ("help_request", r"(?:help|ヘルプ|使い方)", 1.0),
        ]
        
        for intent, pattern, weight in fallback_rules:
            self.rules.append(PatternRule(
                intent=intent,
                pattern=self._compile(pattern),
                weight=weight
            ))
        
        print("⚠️ Using fallback rules")

    def parse(self, text: str) -> Dict[str, Any]:
        """メイン解析関数"""
        normalized = self._normalize(text)
        matches: List[Dict[str, Any]] = []
        
        print(f"🔍 Fast NLP parsing: '{text}' -> '{normalized}'")
        
        # 正規表現マッチング
        for rule in self.rules:
            match = rule.pattern.search(normalized)
            if match:
                slots = {k: v.strip() for k, v in match.groupdict().items() if v}
                score = rule.weight + len(slots) * 0.1
                
                print(f"✅ Pattern matched: {rule.intent} (score: {score:.2f}) - slots: {slots}")
                
                matches.append({
                    "intent": rule.intent,
                    "slots": slots,
                    "score": score,
                    "method": "regex"
                })
        
        if not matches:
            print(f"❌ No regex match for: '{normalized}'")
            self.unmatched_log.append({
                "text": text,
                "normalized": normalized,
                "timestamp": datetime.now(JST).isoformat()
            })
            return {"intent": "UNKNOWN", "slots": {}, "score": 0.0, "method": "none"}
        
        # 最高スコアを選択
        best = sorted(matches, key=lambda x: x["score"], reverse=True)[0]
        
        # 追加スロット抽出
        if best["intent"] in self.slot_filters:
            for filter_pattern in self.slot_filters[best["intent"]]:
                for slot_match in filter_pattern.finditer(normalized):
                    for k, v in slot_match.groupdict().items():
                        if v and k not in best["slots"]:
                            best["slots"][k] = v.strip()
        
        print(f"🎯 Final result: {best['intent']} (score: {best['score']:.2f})")
        return best

    async def llm_fallback(self, text: str, threshold: float = 0.8) -> Dict[str, Any]:
        """LLM による補完解析"""
        if not self.openai_client:
            return {"intent": "chat", "slots": {"text": text}, "score": 0.5, "method": "fallback"}
        
        try:
            print(f"🤖 LLM fallback for: '{text}'")
            
            prompt = f"""
以下のメッセージから意図を分析してJSONで返してください。

メッセージ: "{text}"

可能な意図:
- todo_add: タスク追加
- todo_list: リスト表示  
- todo_done: タスク完了
- todo_delete: タスク削除
- reminder_set: リマインダー設定
- greeting: 挨拶
- help_request: ヘルプ要求
- chat: 雑談

JSON形式:
{{
    "intent": "意図名",
    "slots": {{
        "task": "タスク内容",
        "due": "期限",
        "priority": "優先度"
    }},
    "confidence": 0.0-1.0
}}
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは意図分析の専門家です。正確なJSONを返してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["method"] = "llm"
            result["score"] = result.get("confidence", 0.5)
            
            print(f"🧠 LLM result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ LLM fallback error: {e}")
            return {"intent": "chat", "slots": {"text": text}, "score": 0.3, "method": "error"}

    async def understand_intent(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """統合意図理解（regex優先 → LLM補完）"""
        # まず高速正規表現で試す
        result = self.parse(text)
        
        # 不確実な場合はLLMで補完
        if result["intent"] == "UNKNOWN" or result["score"] < 0.8:
            llm_result = await self.llm_fallback(text)
            
            # LLMの方が確信度が高い場合は採用
            if llm_result["score"] > result["score"]:
                return llm_result
        
        return result

    def save_unmatched_log(self, path: str = "unmatched.jsonl"):
        """マッチしなかった文を保存"""
        try:
            with open(path, "a", encoding="utf-8") as f:
                for entry in self.unmatched_log:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.unmatched_log.clear()
            print(f"📝 Unmatched log saved to {path}")
        except Exception as e:
            print(f"❌ Failed to save log: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報"""
        intent_counts = {}
        for rule in self.rules:
            intent_counts[rule.intent] = intent_counts.get(rule.intent, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "intents": len(set(rule.intent for rule in self.rules)),
            "intent_distribution": intent_counts,
            "unmatched_count": len(self.unmatched_log)
        }

# 使用例
if __name__ == "__main__":
    engine = FastNLPEngine("intent_registry.yaml")
    
    # テスト
    test_cases = [
        "スタンプつくる",
        "todoいれたいんだけど全リストだして",
        "やることある？",
        "1番終わった",
        "元気？"
    ]
    
    for text in test_cases:
        result = engine.parse(text)
        print(f"'{text}' -> {result}")
    
    print("\nStats:", engine.get_stats())