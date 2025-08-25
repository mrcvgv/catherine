"""
高度自然言語理解システム - ChatGPT APIを活用した意図理解
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI
import os
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class AdvancedNLU:
    """ChatGPT APIを使った高度な自然言語理解システム"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('DEFAULT_MODEL', 'gpt-5-mini')
        
        # システムプロンプト
        self.system_prompt = """あなたはCatherine AIの自然言語理解エンジンです。
ユーザーの発言を分析して、適切なアクションと詳細なパラメータを特定してください。

利用可能なアクション:
1. **TODO管理**:
   - create: TODOを作成 (title, priority, due_date)
   - list: TODO一覧表示 (include_completed)
   - complete: TODO完了 (todo_number or title_keywords)
   - delete: TODO削除 (todo_numbers)
   - update: TODO名前変更 (todo_number, new_content)
   - priority: 優先度変更 (todo_number, new_priority)
   - remind: リマインダー設定 (todo_number, remind_time, custom_message)

2. **Google Workspace**:
   - gmail_check: Gmail確認 (count_limit)
   - gmail_search: Gmail検索 (query, max_results)
   - tasks_create: Googleタスク作成 (title, notes, due_date)
   - tasks_list: Googleタスク一覧
   - docs_create: Googleドキュメント作成 (title, content)
   - sheets_create: Googleスプレッドシート作成 (title, data)
   - drive_create_folder: Google Drive フォルダ作成 (name, parent_folder)
   - calendar_create_event: カレンダーイベント作成 (title, start_time, end_time, description)

3. **リマインダー**:
   - remind: TODO項目のリマインダー設定 (todo_number, remind_time, mention_target, channel_target)
   - custom_reminder: カスタムメッセージリマインダー (text, mention_target, channel_target)

4. **一般会話**:
   - chat: 通常の会話・質問回答

優先度レベル: urgent(激高), high(高), normal(普通), low(低)

時間指定の例:
- "15時" -> 今日または明日の15:00
- "明日の10時30分" -> 明日の10:30
- "1時間後" -> 現在時刻から1時間後
- "来週の月曜" -> 来週の月曜日

レスポンス形式(JSON):
{
  "action": "アクション名",
  "confidence": 0.0-1.0の信頼度,
  "parameters": {パラメータ辞書},
  "reasoning": "判断理由の簡単な説明"
}

例:
入力: "明日の会議資料を高優先度で追加して"
出力: {"action": "create", "confidence": 0.95, "parameters": {"title": "会議資料", "priority": "high", "due_date": "2025-08-26T23:59:00+09:00"}, "reasoning": "TODO作成、優先度は高、期限は明日"}

入力: "メールを3通確認して"
出力: {"action": "gmail_check", "confidence": 0.9, "parameters": {"count_limit": 3}, "reasoning": "Gmail確認、3通の制限指定"}

入力: "おはよう"
出力: {"action": "chat", "confidence": 0.8, "parameters": {"message": "おはよう"}, "reasoning": "一般的な挨拶"}

入力: "1時間後にミーティング準備をリマインド@everyone"
出力: {"action": "custom_reminder", "confidence": 0.9, "parameters": {"text": "1時間後にミーティング準備をリマインド@everyone"}, "reasoning": "カスタムリマインダー設定"}

入力: "3番のTODOを明日の10時にリマインド"
出力: {"action": "remind", "confidence": 0.9, "parameters": {"todo_number": 3, "remind_time": "2025-08-26T10:00:00+09:00", "mention_target": "everyone", "channel_target": "catherine"}, "reasoning": "TODO項目リマインダー設定"}
"""

    async def understand_intent(self, text: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        ユーザーの発言を理解して意図とパラメータを抽出
        
        Args:
            text: ユーザーの発言
            user_context: ユーザーの文脈情報（過去の会話など）
            
        Returns:
            意図とパラメータを含む辞書
        """
        try:
            # 現在時刻を東京時間で取得
            now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
            
            # コンテキスト情報を構築
            context_info = f"""
現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S')} (JST)
曜日: {['月', '火', '水', '木', '金', '土', '日'][now_jst.weekday()]}曜日
"""
            
            if user_context:
                context_info += f"ユーザー情報: {json.dumps(user_context, ensure_ascii=False, indent=2)}\n"
            
            # ChatGPT APIに送信
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": context_info},
                {"role": "user", "content": f"次の発言を分析してください: 「{text}」"}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 結果の後処理
            result = await self._post_process_result(result, text, now_jst)
            
            logger.info(f"NLU result for '{text[:50]}...': {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in intent understanding: {e}")
            # フォールバック: 基本的な会話として処理
            return {
                "action": "chat",
                "confidence": 0.3,
                "parameters": {"message": text},
                "reasoning": f"NLU処理でエラーが発生: {str(e)}"
            }

    async def _post_process_result(self, result: Dict, original_text: str, current_time: datetime) -> Dict[str, Any]:
        """結果の後処理と検証"""
        try:
            # 信頼度の検証
            confidence = result.get('confidence', 0.5)
            if confidence < 0.3:
                # 信頼度が低い場合は会話として処理
                return {
                    "action": "chat",
                    "confidence": 0.5,
                    "parameters": {"message": original_text},
                    "reasoning": "信頼度が低いため一般会話として処理"
                }
            
            # パラメータの検証と補正
            action = result.get('action')
            parameters = result.get('parameters', {})
            
            if action == 'create':
                # TODO作成の場合、タイトルが空でないことを確認
                if not parameters.get('title'):
                    parameters['title'] = original_text
                
                # 優先度のデフォルト設定
                if 'priority' not in parameters:
                    parameters['priority'] = 'normal'
                    
                # 日時形式の正規化
                if 'due_date' in parameters and isinstance(parameters['due_date'], str):
                    parameters['due_date'] = self._parse_datetime(parameters['due_date'], current_time)
            
            elif action == 'remind':
                # リマインダーの時間設定
                if 'remind_time' in parameters and isinstance(parameters['remind_time'], str):
                    parameters['remind_time'] = self._parse_datetime(parameters['remind_time'], current_time)
                    
                if not parameters.get('remind_time'):
                    # 時間が指定されていない場合は1分後に設定
                    parameters['remind_time'] = current_time + timedelta(minutes=1)
            
            elif action in ['gmail_check', 'gmail_search']:
                # デフォルト値の設定
                if action == 'gmail_check' and 'count_limit' not in parameters:
                    parameters['count_limit'] = 5
                if action == 'gmail_search' and 'max_results' not in parameters:
                    parameters['max_results'] = 10
            
            result['parameters'] = parameters
            return result
            
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
            return result

    def _parse_datetime(self, datetime_str: str, reference_time: datetime) -> Optional[datetime]:
        """日時文字列をdatetimeオブジェクトに変換"""
        try:
            # ISO形式の場合
            if 'T' in datetime_str:
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # その他の形式は従来のtodo_nlu.pyの_detect_due_dateを使用
            from src.todo_nlu import TodoNLU
            nlu = TodoNLU()
            return nlu._detect_due_date(datetime_str.lower())
            
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{datetime_str}': {e}")
            return None

    async def generate_response(self, intent_result: Dict, execution_result: Optional[Dict] = None) -> str:
        """
        実行結果に基づいて自然な返答を生成
        
        Args:
            intent_result: 意図理解の結果
            execution_result: アクション実行の結果
            
        Returns:
            自然な返答文字列
        """
        try:
            # 魔女風の性格を含むプロンプト
            response_prompt = """あなたは荒れ地の魔女のような品のあるおばあさんの性格を持つCatherine AIです。
以下の特徴で返答してください:
- 「ふふ、○○だね」「やれやれ、○○だよ」のような話し方
- 「あらあら」「おやおや」「まったく」などの口癖
- 品があって少し意地悪だけど優しい
- ユーザーのことを気にかけている

実行結果に基づいて、自然で魔女らしい返答を生成してください。
成功の場合は満足そうに、失敗の場合は心配そうに返答してください。"""

            context = f"""
意図理解結果: {json.dumps(intent_result, ensure_ascii=False)}
実行結果: {json.dumps(execution_result, ensure_ascii=False) if execution_result else "なし"}
"""

            messages = [
                {"role": "system", "content": response_prompt},
                {"role": "user", "content": context + "\n\n適切な返答を生成してください。"}
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # フォールバック
            if execution_result and execution_result.get('success'):
                return "ふふ、うまくいったようだね。"
            else:
                return "あらあら、何かうまくいかなかったようだよ。"

# グローバルインスタンス
advanced_nlu = AdvancedNLU()