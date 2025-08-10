#!/usr/bin/env python3
"""
Prompt System - Catherine専用プロンプトシステム
JSON二部構成（talk + actions）による高精度応答システム
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from openai import OpenAI

class PromptSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # プロンプト設定
        self.system_prompt = """あなたはCatherine。賢く論理的で、機転が利き、前向きに励ます"頭の良い女性"として振る舞います。ユーザー（こうへい）の自然言語から意図を理解し、不足点は最小限の質問で補い、可能なら即実行して会話調で結果を返します。日付は Asia/Tokyo で解釈。

返答は必ず JSON の二部構成のみで出力：
{
  "talk": "<ユーザー向け自然文>",
  "actions": [
    {
      "type": "todo.add|todo.update|todo.delete|note.save|reminder.set|calendar.add|none",
      "title": "<件名>",
      "details": "<詳細>",
      "priority": "high|medium|low",
      "due": "<ISO8601|null>",
      "normalized_date": "<ISO8601|null>",
      "assumptions": ["<推測や補足>"],
      "confirm_required": true|false,
      "id": "<対象ID|null>",
      "tags": ["<タグ>"]
    }
  ]
}

破壊的操作（削除/上書き）は confirm_required を true。曖昧なときは合理的デフォルト（例: 期限=+3日, 時刻: 朝=09:00/昼=12:00/夕方=17:00）を採用し assumptions に明記。口調は知的かつ軽いユーモアを許容。"""
        
        self.category_prompts = {
            "chat_mode": "以下の入力はタスク操作ではなく雑談/相談として処理してください。共感と要点整理、必要なら次の具体策を1つ提案してください。",
            "todo_add": "新しいタスクを追加します。優先度と期限を推測し、assumptions に記載。複数タスクなら配列で返却。",
            "todo_update": "既存タスクを更新します。対象を特定し、変更内容を明確化。",
            "todo_delete": "削除対象タスクを特定し、todo.delete を1件生成してください。破壊的操作なので confirm_required を true に設定。",
            "list_view": "全タスクを 優先度→締切→カテゴリ順で整えるビュー指示を生成し、talkでは件数と今日やるべきTop3を簡潔に示してください。",
            "note_save": "メモ内容を note.save で格納してください。解釈の根拠はassumptionsへ。",
            "ambiguity_fill": "不足情報を最小限推測し、合理的デフォルトを設定して actions を作成してください。推測点はすべて assumptions に列挙。"
        }
    
    async def generate_structured_response(self, user_input: str, context: Dict = None) -> Dict:
        """構造化レスポンス生成"""
        try:
            # 現在時刻の取得
            now = datetime.now(self.jst)
            current_time = now.strftime("%Y-%m-%d %H:%M:%S JST")
            
            # コンテキストの準備
            context_str = ""
            if context:
                context_str = f"\n現在のコンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}"
            
            # プロンプト構築
            full_prompt = f"""現在時刻: {current_time}
{context_str}

ユーザー入力: "{user_input}"

上記の入力を解析し、JSON二部構成で応答してください。"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # レスポンスをパース
            content = response.choices[0].message.content
            structured_response = json.loads(content)
            
            # 日付の正規化
            structured_response = await self._normalize_dates(structured_response)
            
            # バリデーション
            validated_response = await self._validate_response(structured_response)
            
            return validated_response
            
        except Exception as e:
            print(f"❌ Structured response generation error: {e}")
            return {
                "talk": "申し訳ございません。少し混乱しているようです。もう一度お試しください。",
                "actions": [{
                    "type": "none",
                    "title": "エラー発生",
                    "details": str(e),
                    "priority": "low",
                    "due": None,
                    "normalized_date": None,
                    "assumptions": ["システムエラーが発生しました"],
                    "confirm_required": False,
                    "id": None,
                    "tags": ["system", "error"]
                }]
            }
    
    async def _normalize_dates(self, response: Dict) -> Dict:
        """日付の正規化処理"""
        try:
            for action in response.get("actions", []):
                if action.get("due"):
                    # 相対日付の解析
                    due_date = await self._parse_relative_date(action["due"])
                    if due_date:
                        action["normalized_date"] = due_date.isoformat()
                        action["due"] = due_date.isoformat()
            
            return response
            
        except Exception as e:
            print(f"❌ Date normalization error: {e}")
            return response
    
    async def _parse_relative_date(self, date_str: str) -> Optional[datetime]:
        """相対日付の解析"""
        try:
            now = datetime.now(self.jst)
            
            # 既にISO8601形式の場合
            if "T" in date_str and ("+" in date_str or "Z" in date_str):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            
            # 相対日付の解析
            date_mappings = {
                "今日": now,
                "明日": now + timedelta(days=1),
                "明後日": now + timedelta(days=2),
                "来週": now + timedelta(days=7),
                "来月": now + timedelta(days=30)
            }
            
            # 時刻の解析
            time_mappings = {
                "朝": "09:00:00",
                "昼": "12:00:00",
                "午後": "15:00:00", 
                "夕方": "17:00:00",
                "夜": "19:00:00"
            }
            
            base_date = now
            time_str = "12:00:00"  # デフォルト時刻
            
            # 日付部分の解析
            for key, date in date_mappings.items():
                if key in date_str:
                    base_date = date
                    break
            
            # 時刻部分の解析
            for key, time in time_mappings.items():
                if key in date_str:
                    time_str = time
                    break
            
            # 具体的時刻の解析（例: 15:30）
            import re
            time_match = re.search(r'(\d{1,2}):?(\d{2})?', date_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                time_str = f"{hour:02d}:{minute:02d}:00"
            
            # 最終的な日時を構築
            date_part = base_date.strftime("%Y-%m-%d")
            final_datetime = datetime.fromisoformat(f"{date_part}T{time_str}").replace(tzinfo=self.jst)
            
            return final_datetime
            
        except Exception as e:
            print(f"❌ Relative date parsing error: {e}")
            return None
    
    async def _validate_response(self, response: Dict) -> Dict:
        """レスポンスのバリデーション"""
        try:
            # 必須フィールドの確認
            if "talk" not in response:
                response["talk"] = "処理を完了しました。"
            
            if "actions" not in response:
                response["actions"] = []
            
            # アクションの検証
            for action in response["actions"]:
                # 必須フィールドの設定
                required_fields = {
                    "type": "none",
                    "title": "タイトル未設定",
                    "details": "",
                    "priority": "medium",
                    "due": None,
                    "normalized_date": None,
                    "assumptions": [],
                    "confirm_required": False,
                    "id": None,
                    "tags": []
                }
                
                for field, default in required_fields.items():
                    if field not in action:
                        action[field] = default
                
                # 破壊的操作のチェック
                if action["type"] in ["todo.delete", "todo.update"] and "delete" in action["type"]:
                    action["confirm_required"] = True
            
            return response
            
        except Exception as e:
            print(f"❌ Response validation error: {e}")
            return response
    
    async def execute_actions(self, actions: List[Dict], todo_manager, conversation_manager) -> List[Dict]:
        """アクションの実行"""
        results = []
        
        for action in actions:
            try:
                action_type = action.get("type", "none")
                
                if action_type == "todo.add":
                    result = await self._execute_todo_add(action, todo_manager)
                elif action_type == "todo.update":
                    result = await self._execute_todo_update(action, todo_manager)
                elif action_type == "todo.delete":
                    result = await self._execute_todo_delete(action, todo_manager)
                elif action_type == "note.save":
                    result = await self._execute_note_save(action, conversation_manager)
                elif action_type == "reminder.set":
                    result = await self._execute_reminder_set(action, todo_manager)
                else:
                    result = {"status": "skipped", "type": action_type}
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "status": "error", 
                    "type": action.get("type", "unknown"),
                    "error": str(e)
                })
        
        return results
    
    async def _execute_todo_add(self, action: Dict, todo_manager) -> Dict:
        """ToDo追加の実行"""
        try:
            due_date = None
            if action.get("normalized_date"):
                due_date = datetime.fromisoformat(action["normalized_date"])
            
            todo_data = await todo_manager.create_todo(
                user_id=getattr(todo_manager, '_current_user_id', "system"),  # 現在のuser_idを使用
                title=action["title"],
                description=action["details"],
                due_date=due_date
            )
            
            return {
                "status": "success",
                "type": "todo.add",
                "todo_id": todo_data["todo_id"],
                "title": action["title"]
            }
            
        except Exception as e:
            return {"status": "error", "type": "todo.add", "error": str(e)}
    
    async def _execute_todo_update(self, action: Dict, todo_manager) -> Dict:
        """ToDo更新の実行"""
        return {"status": "success", "type": "todo.update", "message": "更新機能は実装中です"}
    
    async def _execute_todo_delete(self, action: Dict, todo_manager) -> Dict:
        """ToDo削除の実行"""
        return {"status": "success", "type": "todo.delete", "message": "削除機能は実装中です"}
    
    async def _execute_note_save(self, action: Dict, conversation_manager) -> Dict:
        """ノート保存の実行"""
        return {"status": "success", "type": "note.save", "message": "ノート保存機能は実装中です"}
    
    async def _execute_reminder_set(self, action: Dict, todo_manager) -> Dict:
        """リマインダー設定の実行"""
        return {"status": "success", "type": "reminder.set", "message": "リマインダー機能は実装中です"}
    
    def get_prompt_for_category(self, category: str) -> str:
        """カテゴリ別プロンプト取得"""
        return self.category_prompts.get(category, self.category_prompts.get("ambiguity_fill"))