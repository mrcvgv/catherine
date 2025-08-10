import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class TodoManager:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.firebase_available = firebase_manager.is_available()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
        self.memory_todos = {}  # Firebase無効時のメモリストレージ
    
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
        try:
            doc_ref = self.db.collection('todos').document(todo_data['todo_id'])
            doc_ref.set(todo_data)
            print(f"✅ Todo saved successfully: {todo_data['todo_id']} - {title}")
            
            # 保存確認
            saved_doc = doc_ref.get()
            if saved_doc.exists:
                print(f"✅ Todo verified in Firebase: {saved_doc.id}")
            else:
                print(f"❌ Todo not found in Firebase after save!")
                
        except Exception as e:
            print(f"❌ Firebase save error: {e}")
            raise e
        
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
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error in priority analysis: {e}")
                print(f"📄 Raw response: {response.choices[0].message.content}")
                return {
                    'priority': 3,
                    'category': 'general',
                    'estimated_duration': 'unknown',
                    'tags': [],
                    'confidence': 0.0,
                    'parse_error': True
                }
            
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
        # シンプルなクエリ（インデックス不要）
        query = self.db.collection('todos').where('user_id', '==', user_id)
        
        docs = query.get()
        todos = [doc.to_dict() for doc in docs]
        
        # Pythonでフィルタリング・ソート
        if status:
            todos = [t for t in todos if t.get('status') == status]
        
        # 優先度でソート（降順）、次に作成日時（昇順）
        todos.sort(key=lambda x: (-x.get('priority', 3), x.get('created_at')))
        
        return todos
    
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
    
    async def list_todos_formatted(self, user_id: str, sort_by: str = "priority_due") -> str:
        """フォーマット済みToDoリストを取得（全ToDo表示、ソート対応）"""
        try:
            print(f"📋 Fetching todos for user: {user_id}")
            todos = await self.get_user_todos(user_id)
            print(f"📋 Found {len(todos)} todos")
            
            if not todos:
                return "Catherine: 現在、登録されているToDoはありません。\n\n新しいToDoを追加するには `C! todo [内容]` を使用してください。"
            
            # ステータス別に分類
            pending = [t for t in todos if t.get('status') == 'pending']
            in_progress = [t for t in todos if t.get('status') == 'in_progress']
            completed = [t for t in todos if t.get('status') == 'completed']
            
            # ソート処理（優先度と締切日を最優先）
            def sort_todos(todo_list):
                return sorted(todo_list, key=lambda x: (
                    # 締切日がある場合は最優先
                    0 if x.get('due_date') else 1,
                    # 締切日（早い順）
                    x.get('due_date') if x.get('due_date') else datetime.max.replace(tzinfo=self.jst),
                    # 優先度（高い順）
                    -x.get('priority', 3),
                    # 作成日（新しい順）
                    -x.get('created_at', datetime.min).timestamp() if hasattr(x.get('created_at', datetime.min), 'timestamp') else 0
                ))
            
            pending = sort_todos(pending)
            in_progress = sort_todos(in_progress)
            
            result = "Catherine: 📋 **あなたのToDoリスト** （全" + str(len(todos)) + "件）\n\n"
            
            # 進行中タスク（全て表示）
            if in_progress:
                result += "🚀 **進行中** (" + str(len(in_progress)) + "件)\n"
                for i, todo in enumerate(in_progress, 1):
                    priority_mark = "🔥" if todo.get('priority', 3) >= 4 else "⚡" if todo.get('priority', 3) >= 3 else "📌"
                    due_date_str = ""
                    if todo.get('due_date'):
                        due_date_str = f" 📅{todo['due_date'].strftime('%m/%d')}"
                    result += f"{priority_mark} {i}. {todo.get('title', 'タイトル不明')}{due_date_str}\n"
                result += "\n"
            
            # 未着手タスク（全て表示）
            if pending:
                result += "⏰ **未着手** (" + str(len(pending)) + "件)\n"
                for i, todo in enumerate(pending, 1):
                    priority_mark = "🔥" if todo.get('priority', 3) >= 4 else "⚡" if todo.get('priority', 3) >= 3 else "📌"
                    due_date_str = ""
                    if todo.get('due_date'):
                        due_date_str = f" 📅{todo['due_date'].strftime('%m/%d')}"
                    category_str = f" [{todo.get('category', 'general')}]"
                    result += f"{priority_mark} {i}. {todo.get('title', 'タイトル不明')}{due_date_str}{category_str}\n"
                result += "\n"
            
            # 完了済み（件数のみ）
            if completed:
                result += f"✅ **完了済み** ({len(completed)}件)\n\n"
            
            result += "📊 **表示オプション:**\n"
            result += "• `C! list priority` - 優先度順\n"
            result += "• `C! list due` - 締切日順\n"
            result += "• `C! list category` - カテゴリ別\n"
            result += "• `C! list recent` - 作成日順（新しい順）\n\n"
            
            result += "💡 ToDoの追加: `C! todo [内容]`\n"
            result += "📝 完了報告: `C! done [番号]`"
            
            return result
            
        except Exception as e:
            print(f"❌ List todos error: {e}")
            return "Catherine: ToDoリストの取得でエラーが発生しました。しばらくしてからお試しください。"
    
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
            # ```json ブロックを除去
            content = response.choices[0].message.content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            result = json.loads(content)
            
            # 期限の日時変換
            if result.get('due_date'):
                from dateutil import parser
                result['due_date'] = parser.parse(result['due_date']).replace(tzinfo=self.jst)
            
            return result
            
        except Exception as e:
            print(f"❌ Natural language parsing error: {e}")
            return {'has_todo': False, 'confidence': 0.0}
