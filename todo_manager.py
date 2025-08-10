import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class TodoManager:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
    
    async def create_todo(self, user_id: str, title: str, description: str = "", 
                         due_date: Optional[datetime] = None) -> Dict:
        """新しいToDoを作成"""
        # AI分析で優先度とカテゴリを設定
        ai_analysis = await self._analyze_todo_with_ai(title, description)
        
        todo_data = {
            'todo_id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'description': description,
            'status': 'pending',
            'priority': ai_analysis.get('priority', 3),
            'category': ai_analysis.get('category', 'general'),
            'created_at': datetime.now(self.jst),
            'updated_at': datetime.now(self.jst),
            'due_date': due_date,
            'metadata': ai_analysis
        }
        
        # Firestoreに保存
        doc_ref = self.db.collection('todos').document(todo_data['todo_id'])
        doc_ref.set(todo_data)
        
        # リマインダーを設定
        if due_date:
            await self._create_reminders(todo_data)
        
        return todo_data
    
    async def _analyze_todo_with_ai(self, title: str, description: str) -> Dict:
        """AIでToDoを分析（優先度、カテゴリ、タグ等）"""
        try:
            prompt = f"""
            以下のToDoを分析して、JSON形式で返してください：
            
            タイトル: {title}
            説明: {description}
            
            以下の項目を分析してください：
            - priority: 1-5の優先度（5が最高）
            - category: work, personal, health, finance, learning, other のいずれか
            - estimated_duration: 推定所要時間（文字列）
            - tags: 関連するタグの配列
            - confidence: 分析の信頼度（0-1）
            
            例：
            {{"priority": 4, "category": "work", "estimated_duration": "2 hours", "tags": ["urgent", "presentation"], "confidence": 0.9}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは優秀な秘書です。ToDoを分析して構造化された情報を返してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"❌ AI analysis error: {e}")
            return {
                'priority': 3,
                'category': 'general',
                'estimated_duration': 'unknown',
                'tags': [],
                'confidence': 0.0
            }
    
    async def get_user_todos(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """ユーザーのToDoリストを取得"""
        query = self.db.collection('todos').where('user_id', '==', user_id)
        
        if status:
            query = query.where('status', '==', status)
        
        # 優先度でソート（降順）、次に作成日時（昇順）
        query = query.order_by('priority', direction=firestore.Query.DESCENDING)
        query = query.order_by('created_at', direction=firestore.Query.ASCENDING)
        
        docs = query.get()
        return [doc.to_dict() for doc in docs]
    
    async def update_todo_status(self, todo_id: str, status: str) -> bool:
        """ToDoのステータスを更新"""
        try:
            doc_ref = self.db.collection('todos').document(todo_id)
            doc_ref.update({
                'status': status,
                'updated_at': datetime.now(self.jst)
            })
            return True
        except Exception as e:
            print(f"❌ Todo update error: {e}")
            return False
    
    async def _create_reminders(self, todo_data: Dict):
        """ToDoのリマインダーを作成"""
        due_date = todo_data['due_date']
        if not due_date:
            return
        
        # 24時間前のリマインダー
        remind_24h = due_date - timedelta(hours=24)
        if remind_24h > datetime.now(self.jst):
            reminder_data = {
                'reminder_id': str(uuid.uuid4()),
                'todo_id': todo_data['todo_id'],
                'user_id': todo_data['user_id'],
                'remind_at': remind_24h,
                'type': 'due_soon',
                'sent': False,
                'created_at': datetime.now(self.jst)
            }
            self.db.collection('reminders').document(reminder_data['reminder_id']).set(reminder_data)
        
        # 1時間前のリマインダー
        remind_1h = due_date - timedelta(hours=1)
        if remind_1h > datetime.now(self.jst):
            reminder_data = {
                'reminder_id': str(uuid.uuid4()),
                'todo_id': todo_data['todo_id'],
                'user_id': todo_data['user_id'],
                'remind_at': remind_1h,
                'type': 'urgent',
                'sent': False,
                'created_at': datetime.now(self.jst)
            }
            self.db.collection('reminders').document(reminder_data['reminder_id']).set(reminder_data)
    
    async def parse_natural_language_todo(self, user_input: str) -> Dict:
        """自然言語からToDoを抽出"""
        try:
            prompt = f"""
            以下のメッセージからToDoを抽出してください：
            「{user_input}」
            
            以下のJSON形式で返してください：
            {{
                "has_todo": true/false,
                "title": "抽出したタスクのタイトル",
                "description": "詳細説明",
                "due_date": "期限（YYYY-MM-DD HH:MM形式、または null）",
                "confidence": 0.0-1.0
            }}
            
            期限の表現例：
            - "明日まで" → 明日の23:59
            - "来週" → 来週金曜日の23:59
            - "3日後" → 3日後の23:59
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは優秀な秘書です。自然言語からToDoを正確に抽出してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # 期限の日時変換
            if result.get('due_date'):
                from dateutil import parser
                result['due_date'] = parser.parse(result['due_date']).replace(tzinfo=self.jst)
            
            return result
            
        except Exception as e:
            print(f"❌ Natural language parsing error: {e}")
            return {'has_todo': False, 'confidence': 0.0}
