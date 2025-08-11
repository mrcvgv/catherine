#!/usr/bin/env python3
"""
Reminder System - 高度なリマインダー管理システム
定期実行、スマート通知、柔軟なスケジューリング機能
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class ReminderSystem:
    def __init__(self, openai_client: OpenAI, discord_client=None):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.discord_client = discord_client
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # リマインダータイプ
        self.reminder_types = {
            'once': '一回限り',
            'daily': '毎日',
            'weekly': '毎週',
            'monthly': '毎月',
            'custom': 'カスタム間隔'
        }
        
        # 実行中のリマインダー
        self.active_reminders = {}
    
    async def create_reminder(self, user_id: str, title: str, message: str, 
                            remind_at: datetime, reminder_type: str = 'once',
                            repeat_interval: Optional[timedelta] = None,
                            tags: List[str] = None) -> Dict:
        """リマインダー作成"""
        try:
            reminder_data = {
                'reminder_id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': title,
                'message': message,
                'remind_at': remind_at,
                'reminder_type': reminder_type,
                'repeat_interval_seconds': repeat_interval.total_seconds() if repeat_interval else None,
                'tags': tags or [],
                'status': 'active',
                'created_at': datetime.now(self.jst),
                'sent_count': 0,
                'next_reminder': remind_at,
                'metadata': await self._analyze_reminder_context(title, message)
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('reminders').document(reminder_data['reminder_id'])
            doc_ref.set(reminder_data)
            
            print(f"✅ Reminder created: {title} at {remind_at}")
            
            # アクティブリマインダーに追加
            await self._schedule_reminder(reminder_data)
            
            return reminder_data
            
        except Exception as e:
            print(f"❌ Reminder creation error: {e}")
            return {}
    
    async def create_smart_reminder(self, user_id: str, natural_input: str) -> Dict:
        """自然言語からスマートリマインダー作成"""
        try:
            analysis = await self._parse_reminder_request(natural_input)
            
            if not analysis.get('valid', False):
                return {"error": "リマインダーの内容を理解できませんでした"}
            
            # 日時の解析
            remind_at = await self._parse_reminder_time(
                analysis.get('when', ''), 
                user_id
            )
            
            if not remind_at:
                return {"error": "日時を特定できませんでした"}
            
            # リマインダー作成
            reminder = await self.create_reminder(
                user_id=user_id,
                title=analysis.get('title', ''),
                message=analysis.get('message', ''),
                remind_at=remind_at,
                reminder_type=analysis.get('type', 'once'),
                repeat_interval=analysis.get('interval'),
                tags=analysis.get('tags', [])
            )
            
            return reminder
            
        except Exception as e:
            print(f"❌ Smart reminder creation error: {e}")
            return {"error": str(e)}
    
    async def list_reminders(self, user_id: str, status: str = 'active') -> List[Dict]:
        """リマインダー一覧取得"""
        try:
            query = self.db.collection('reminders')\
                          .where('user_id', '==', user_id)\
                          .where('status', '==', status)
            
            docs = query.get()
            reminders = []
            
            for doc in docs:
                data = doc.to_dict()
                reminders.append(data)
            
            # 次回実行時刻でソート
            reminders.sort(key=lambda x: x.get('next_reminder', datetime.min))
            
            return reminders
            
        except Exception as e:
            print(f"❌ List reminders error: {e}")
            return []
    
    async def update_reminder(self, reminder_id: str, updates: Dict) -> bool:
        """リマインダー更新"""
        try:
            doc_ref = self.db.collection('reminders').document(reminder_id)
            
            # 更新データの準備
            update_data = {
                'updated_at': datetime.now(self.jst),
                **updates
            }
            
            doc_ref.update(update_data)
            
            # アクティブリマインダーの更新
            if reminder_id in self.active_reminders:
                await self._reschedule_reminder(reminder_id, updates)
            
            return True
            
        except Exception as e:
            print(f"❌ Update reminder error: {e}")
            return False
    
    async def delete_reminder(self, reminder_id: str) -> bool:
        """リマインダー削除"""
        try:
            # Firestoreから削除
            self.db.collection('reminders').document(reminder_id).delete()
            
            # アクティブリマインダーからも削除
            if reminder_id in self.active_reminders:
                task = self.active_reminders[reminder_id]
                task.cancel()
                del self.active_reminders[reminder_id]
            
            print(f"✅ Reminder deleted: {reminder_id}")
            return True
            
        except Exception as e:
            print(f"❌ Delete reminder error: {e}")
            return False
    
    async def snooze_reminder(self, reminder_id: str, snooze_minutes: int = 10) -> bool:
        """リマインダーのスヌーズ"""
        try:
            new_time = datetime.now(self.jst) + timedelta(minutes=snooze_minutes)
            
            success = await self.update_reminder(reminder_id, {
                'next_reminder': new_time,
                'snoozed_at': datetime.now(self.jst),
                'snooze_count': 1  # 実際の実装ではカウントを増やす
            })
            
            if success:
                print(f"⏰ Reminder snoozed for {snooze_minutes} minutes")
            
            return success
            
        except Exception as e:
            print(f"❌ Snooze reminder error: {e}")
            return False
    
    async def start_reminder_scheduler(self):
        """リマインダースケジューラー開始"""
        print("🔔 Starting reminder scheduler...")
        
        # 既存のアクティブリマインダーを読み込み
        await self._load_active_reminders()
        
        # 定期チェックタスクを開始
        asyncio.create_task(self._reminder_check_loop())
    
    async def _load_active_reminders(self):
        """アクティブなリマインダーを読み込み"""
        try:
            query = self.db.collection('reminders').where('status', '==', 'active')
            docs = query.get()
            
            for doc in docs:
                reminder_data = doc.to_dict()
                await self._schedule_reminder(reminder_data)
            
            print(f"📋 Loaded {len(self.active_reminders)} active reminders")
            
        except Exception as e:
            print(f"❌ Load active reminders error: {e}")
    
    async def _schedule_reminder(self, reminder_data: Dict):
        """個別リマインダーのスケジューリング"""
        try:
            reminder_id = reminder_data['reminder_id']
            remind_at = reminder_data['next_reminder']
            
            # 既存のタスクがあれば削除
            if reminder_id in self.active_reminders:
                self.active_reminders[reminder_id].cancel()
            
            # 新しいタスクを作成
            delay_seconds = (remind_at - datetime.now(self.jst)).total_seconds()
            
            if delay_seconds > 0:
                task = asyncio.create_task(
                    self._execute_reminder_after_delay(reminder_data, delay_seconds)
                )
                self.active_reminders[reminder_id] = task
            else:
                # 過去の時刻の場合は即座に実行
                await self._execute_reminder(reminder_data)
            
        except Exception as e:
            print(f"❌ Schedule reminder error: {e}")
    
    async def _execute_reminder_after_delay(self, reminder_data: Dict, delay_seconds: float):
        """遅延実行でリマインダーを送信"""
        try:
            await asyncio.sleep(delay_seconds)
            await self._execute_reminder(reminder_data)
            
        except asyncio.CancelledError:
            print(f"⏹️ Reminder cancelled: {reminder_data.get('title', 'Unknown')}")
        except Exception as e:
            print(f"❌ Execute reminder after delay error: {e}")
    
    async def _execute_reminder(self, reminder_data: Dict):
        """リマインダーの実行"""
        try:
            reminder_id = reminder_data['reminder_id']
            user_id = reminder_data['user_id']
            title = reminder_data['title']
            message = reminder_data['message']
            
            # Discord通知を送信
            if self.discord_client:
                await self._send_discord_notification(user_id, title, message)
            
            # 実行カウントを更新
            await self.update_reminder(reminder_id, {
                'sent_count': reminder_data.get('sent_count', 0) + 1,
                'last_sent': datetime.now(self.jst)
            })
            
            # 繰り返しリマインダーの場合は次回をスケジュール
            if reminder_data['reminder_type'] != 'once':
                await self._schedule_next_repeat(reminder_data)
            else:
                # 一回限りの場合は完了状態に
                await self.update_reminder(reminder_id, {'status': 'completed'})
                if reminder_id in self.active_reminders:
                    del self.active_reminders[reminder_id]
            
            print(f"🔔 Reminder executed: {title}")
            
        except Exception as e:
            print(f"❌ Execute reminder error: {e}")
    
    async def _send_discord_notification(self, user_id: str, title: str, message: str):
        """Discord通知送信"""
        try:
            # ユーザーを取得
            user = self.discord_client.get_user(int(user_id))
            if user:
                notification = f"🔔 **{title}**\n\n{message}"
                await user.send(notification)
            else:
                print(f"❌ User not found: {user_id}")
                
        except Exception as e:
            print(f"❌ Discord notification error: {e}")
    
    async def _schedule_next_repeat(self, reminder_data: Dict):
        """次回の繰り返しをスケジュール"""
        try:
            reminder_type = reminder_data['reminder_type']
            current_time = reminder_data['next_reminder']
            
            if reminder_type == 'daily':
                next_time = current_time + timedelta(days=1)
            elif reminder_type == 'weekly':
                next_time = current_time + timedelta(weeks=1)
            elif reminder_type == 'monthly':
                next_time = current_time + timedelta(days=30)  # 簡略化
            elif reminder_type == 'custom':
                interval_seconds = reminder_data.get('repeat_interval_seconds', 3600)
                next_time = current_time + timedelta(seconds=interval_seconds)
            else:
                return
            
            # 次回時刻を更新
            await self.update_reminder(reminder_data['reminder_id'], {
                'next_reminder': next_time
            })
            
            # 次回をスケジュール
            reminder_data['next_reminder'] = next_time
            await self._schedule_reminder(reminder_data)
            
        except Exception as e:
            print(f"❌ Schedule next repeat error: {e}")
    
    async def _reminder_check_loop(self):
        """定期的なリマインダーチェック"""
        while True:
            try:
                await asyncio.sleep(60)  # 1分ごとにチェック
                
                # 過去のリマインダーをチェックして実行
                current_time = datetime.now(self.jst)
                
                # シンプルなクエリに変更（インデックス不要）
                query = self.db.collection('reminders')\
                              .where('status', '==', 'active')
                
                docs = query.get()
                
                for doc in docs:
                    reminder_data = doc.to_dict()
                    reminder_time = reminder_data.get('next_reminder')
                    
                    # Pythonでフィルタリング
                    if (reminder_time and reminder_time <= current_time and
                        reminder_data['reminder_id'] not in self.active_reminders):
                        await self._execute_reminder(reminder_data)
                
            except Exception as e:
                print(f"❌ Reminder check loop error: {e}")
                await asyncio.sleep(300)  # エラー時は5分待機
    
    async def _parse_reminder_request(self, natural_input: str) -> Dict:
        """自然言語のリマインダーリクエストを解析"""
        try:
            prompt = f"""
            以下のリマインダーリクエストを解析してください：
            「{natural_input}」
            
            以下のJSONで返してください：
            {{
                "valid": true/false,
                "title": "リマインダーのタイトル",
                "message": "リマインダーメッセージ",
                "when": "いつ実行するか",
                "type": "once|daily|weekly|monthly|custom",
                "interval": "カスタム間隔（秒）",
                "tags": ["タグ1", "タグ2"],
                "priority": "high|medium|low",
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "リマインダー解析の専門家として、自然言語から正確な情報を抽出してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return result
            
        except Exception as e:
            print(f"❌ Parse reminder request error: {e}")
            return {"valid": False}
    
    async def _parse_reminder_time(self, when_str: str, user_id: str) -> Optional[datetime]:
        """リマインダー時刻を解析"""
        try:
            now = datetime.now(self.jst)
            
            # 基本的な時刻パターン
            time_patterns = {
                '今すぐ': now,
                '5分後': now + timedelta(minutes=5),
                '10分後': now + timedelta(minutes=10),
                '15分後': now + timedelta(minutes=15),
                '30分後': now + timedelta(minutes=30),
                '1時間後': now + timedelta(hours=1),
                '2時間後': now + timedelta(hours=2),
                '明日': now + timedelta(days=1),
                '明後日': now + timedelta(days=2),
                '来週': now + timedelta(days=7),
                '来月': now + timedelta(days=30)
            }
            
            # 完全一致チェック
            for pattern, time in time_patterns.items():
                if pattern in when_str:
                    return time
            
            # より複雑な解析（実装簡略化）
            # 実際にはより高度な日時解析を実装
            return now + timedelta(minutes=10)  # デフォルト
            
        except Exception as e:
            print(f"❌ Parse reminder time error: {e}")
            return None
    
    async def _analyze_reminder_context(self, title: str, message: str) -> Dict:
        """リマインダーのコンテキスト分析"""
        try:
            return {
                'category': 'general',
                'urgency': 'medium',
                'estimated_duration': '5_minutes',
                'related_tasks': [],
                'suggested_followups': []
            }
        except Exception as e:
            print(f"❌ Analyze reminder context error: {e}")
            return {}
    
    async def _reschedule_reminder(self, reminder_id: str, updates: Dict):
        """リマインダーの再スケジューリング"""
        try:
            # 現在のタスクをキャンセル
            if reminder_id in self.active_reminders:
                self.active_reminders[reminder_id].cancel()
            
            # 更新されたデータでリスケジュール
            doc = self.db.collection('reminders').document(reminder_id).get()
            if doc.exists:
                reminder_data = doc.to_dict()
                await self._schedule_reminder(reminder_data)
                
        except Exception as e:
            print(f"❌ Reschedule reminder error: {e}")