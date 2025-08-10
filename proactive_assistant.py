#!/usr/bin/env python3
"""
Proactive Assistant Module - 先読み・予測・提案システム
超優秀秘書の核心機能：ユーザーのニーズを予測し、能動的にサポート
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class ProactiveAssistant:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 予測モデル
        self.behavior_patterns = {}
        self.context_memory = {}
        self.predictive_cache = {}
    
    async def analyze_user_patterns(self, user_id: str) -> Dict:
        """ユーザーの行動パターンを深度分析"""
        try:
            # 過去30日間のデータを取得
            start_date = datetime.now(self.jst) - timedelta(days=30)
            
            # 会話履歴分析
            conversations = await self._get_user_conversations(user_id, start_date)
            todos = await self._get_user_todos(user_id, start_date)
            
            # AI分析でパターン抽出
            pattern_analysis = await self._ai_analyze_patterns(conversations, todos)
            
            # パターンをキャッシュ
            self.behavior_patterns[user_id] = {
                'patterns': pattern_analysis,
                'last_updated': datetime.now(self.jst),
                'confidence': pattern_analysis.get('confidence', 0.8)
            }
            
            return pattern_analysis
            
        except Exception as e:
            print(f"❌ Pattern analysis error: {e}")
            return {}
    
    async def predict_next_needs(self, user_id: str, current_context: str) -> List[Dict]:
        """次のニーズを予測"""
        try:
            # 行動パターンを取得/更新
            if user_id not in self.behavior_patterns or \
               (datetime.now(self.jst) - self.behavior_patterns[user_id]['last_updated']).total_seconds() / 3600 > 6:
                await self.analyze_user_patterns(user_id)
            
            patterns = self.behavior_patterns.get(user_id, {}).get('patterns', {})
            
            # AI予測
            prediction_prompt = f"""
            以下のユーザー行動パターンと現在の文脈から、次に必要になるであろうアクションを予測してください：
            
            【行動パターン】
            {patterns}
            
            【現在の文脈】
            {current_context}
            
            以下のJSON形式で予測結果を返してください：
            {{
                "predictions": [
                    {{
                        "action": "予測されるアクション",
                        "description": "詳細説明", 
                        "priority": 1-5,
                        "confidence": 0.0-1.0,
                        "suggested_timing": "今すぐ/1時間後/明日/来週",
                        "preparation_steps": ["準備ステップ1", "準備ステップ2"]
                    }}
                ],
                "reasoning": "予測の根拠"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは超優秀な予測分析専門家です。ユーザーの行動パターンから未来のニーズを正確に予測してください。"},
                    {"role": "user", "content": prediction_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            predictions = json.loads(content)
            return predictions.get('predictions', [])
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return []
    
    async def generate_proactive_suggestions(self, user_id: str, context: str) -> str:
        """プロアクティブな提案を生成"""
        try:
            predictions = await self.predict_next_needs(user_id, context)
            
            if not predictions:
                return ""
            
            # 高信頼度の予測のみを提案
            high_confidence_predictions = [
                p for p in predictions 
                if p.get('confidence', 0) > 0.7 and p.get('priority', 0) >= 3
            ]
            
            if not high_confidence_predictions:
                return ""
            
            # 提案文を生成
            suggestions = []
            for pred in high_confidence_predictions[:3]:  # 上位3件
                timing = pred.get('suggested_timing', '今すぐ')
                action = pred.get('action', '')
                desc = pred.get('description', '')
                
                suggestions.append(f"💡 **{timing}**: {action}\n   → {desc}")
            
            suggestion_text = "\n\n🔮 **私からの先読み提案**:\n" + "\n".join(suggestions)
            suggestion_text += "\n\n必要でしたら詳細をお聞かせください！"
            
            return suggestion_text
            
        except Exception as e:
            print(f"❌ Suggestion generation error: {e}")
            return ""
    
    async def prepare_resources(self, user_id: str, predicted_action: Dict) -> bool:
        """予測されたアクションのためにリソースを準備"""
        try:
            action_type = predicted_action.get('action', '')
            prep_steps = predicted_action.get('preparation_steps', [])
            
            # リソース準備の実行
            for step in prep_steps:
                await self._execute_preparation_step(user_id, step)
            
            # 準備完了をログ
            prep_log = {
                'user_id': user_id,
                'action': action_type,
                'prepared_at': datetime.now(self.jst),
                'steps_completed': prep_steps
            }
            
            self.db.collection('preparations').document().set(prep_log)
            return True
            
        except Exception as e:
            print(f"❌ Resource preparation error: {e}")
            return False
    
    async def _ai_analyze_patterns(self, conversations: List[Dict], todos: List[Dict]) -> Dict:
        """AI分析でユーザーパターンを抽出"""
        try:
            # データサマリー
            conv_summary = self._summarize_conversations(conversations)
            todo_summary = self._summarize_todos(todos)
            
            analysis_prompt = f"""
            以下のユーザーデータから行動パターンを分析してください：
            
            【会話履歴サマリー】
            {conv_summary}
            
            【ToDo履歴サマリー】
            {todo_summary}
            
            以下を分析して JSON で返してください：
            {{
                "daily_patterns": "日常的な行動パターン",
                "work_style": "仕事のスタイル",
                "communication_preferences": "コミュニケーション傾向",
                "peak_activity_times": ["活動的な時間帯"],
                "common_task_sequences": ["よくある作業の流れ"],
                "stress_indicators": ["ストレスのサイン"],
                "motivation_factors": ["モチベーション要因"],
                "prediction_confidence": 0.8,
                "recommended_support_style": "推奨サポート方法"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは優秀な行動分析心理学者です。データから深いインサイトを抽出してください。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ AI pattern analysis error: {e}")
            return {"confidence": 0.0}
    
    def _summarize_conversations(self, conversations: List[Dict]) -> str:
        """会話履歴をサマリー"""
        if not conversations:
            return "会話履歴なし"
        
        total_convs = len(conversations)
        topics = []
        sentiments = []
        
        for conv in conversations:
            analysis = conv.get('ai_analysis', {})
            if analysis.get('topics'):
                topics.extend(analysis['topics'])
            if analysis.get('sentiment'):
                sentiments.append(analysis['sentiment'])
        
        return f"総会話数: {total_convs}, 主要話題: {list(set(topics))[:5]}, 感情傾向: {sentiments}"
    
    def _summarize_todos(self, todos: List[Dict]) -> str:
        """ToDo履歴をサマリー"""
        if not todos:
            return "ToDo履歴なし"
        
        categories = {}
        priorities = []
        
        for todo in todos:
            cat = todo.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1
            priorities.append(todo.get('priority', 3))
        
        avg_priority = sum(priorities) / len(priorities) if priorities else 3
        
        return f"ToDo総数: {len(todos)}, カテゴリ分布: {categories}, 平均優先度: {avg_priority:.1f}"
    
    async def _get_user_conversations(self, user_id: str, since_date: datetime) -> List[Dict]:
        """ユーザーの会話履歴を取得"""
        try:
            query = self.db.collection('conversations').where('user_id', '==', user_id)
            docs = query.get()
            
            conversations = []
            for doc in docs:
                data = doc.to_dict()
                if data.get('created_at') and data['created_at'] >= since_date:
                    conversations.append(data)
            
            return conversations
        except Exception as e:
            print(f"❌ Get conversations error: {e}")
            return []
    
    async def _get_user_todos(self, user_id: str, since_date: datetime) -> List[Dict]:
        """ユーザーのToDo履歴を取得"""
        try:
            query = self.db.collection('todos').where('user_id', '==', user_id)
            docs = query.get()
            
            todos = []
            for doc in docs:
                data = doc.to_dict()
                if data.get('created_at') and data['created_at'] >= since_date:
                    todos.append(data)
            
            return todos
        except Exception as e:
            print(f"❌ Get todos error: {e}")
            return []
    
    async def _execute_preparation_step(self, user_id: str, step: str) -> bool:
        """準備ステップを実行"""
        try:
            # 準備ステップの種類に応じて処理
            if "リマインダー" in step:
                await self._create_smart_reminder(user_id, step)
            elif "資料準備" in step:
                await self._prepare_resources(user_id, step)
            elif "予定確認" in step:
                await self._check_schedule(user_id, step)
            
            return True
        except Exception as e:
            print(f"❌ Preparation step error: {e}")
            return False
    
    async def _create_smart_reminder(self, user_id: str, reminder_info: str):
        """スマートリマインダーを作成"""
        # 実装予定: 予測に基づいた自動リマインダー
        pass
    
    async def _prepare_resources(self, user_id: str, resource_info: str):
        """リソース準備"""
        # 実装予定: 必要なデータや情報の事前準備
        pass
    
    async def _check_schedule(self, user_id: str, schedule_info: str):
        """スケジュール確認"""
        # 実装予定: カレンダー連携や予定の確認
        pass