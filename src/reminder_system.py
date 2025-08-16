"""
リマインダーシステム - TODO期限通知機能
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
import logging
from todo_manager import TodoManager
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

class ReminderSystem:
    """TODOリマインダーシステム"""
    
    def __init__(self, todo_manager: TodoManager, bot_instance=None):
        self.todo_manager = todo_manager
        self.bot = bot_instance
        self.running = False
        self.check_interval = 300  # 5分間隔でチェック
        
    async def start(self):
        """リマインダーシステムを開始"""
        if self.running:
            return
            
        self.running = True
        logger.info("リマインダーシステムを開始しました")
        
        while self.running:
            try:
                await self.check_reminders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"リマインダーチェック中にエラー: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """リマインダーシステムを停止"""
        self.running = False
        logger.info("リマインダーシステムを停止しました")
    
    async def check_reminders(self):
        """リマインダーが必要なTODOをチェック"""
        try:
            # 期限が近いTODOを取得
            reminders = await self.get_due_todos()
            
            for reminder in reminders:
                await self.send_reminder(reminder)
                
        except Exception as e:
            logger.error(f"リマインダーチェック失敗: {e}")
    
    async def get_due_todos(self) -> List[Dict[str, Any]]:
        """期限が近いTODOを取得"""
        try:
            # 全ユーザーのTODOから期限が近いものを検索
            now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            upcoming_threshold = now + timedelta(hours=1)  # 1時間以内
            overdue_threshold = now - timedelta(hours=1)   # 1時間前まで
            
            # Firestoreクエリで期限が近いTODOを取得
            query = self.todo_manager.db.collection('todos').where(
                filter=FieldFilter('status', 'in', ['pending', 'in_progress'])
            )
            
            due_todos = []
            for doc in query.stream():
                todo_data = doc.to_dict()
                todo_data['id'] = doc.id
                
                if 'due_date' in todo_data and todo_data['due_date']:
                    due_date = todo_data['due_date']
                    
                    # 期限が近い、または過ぎているTODOを検出
                    if overdue_threshold <= due_date <= upcoming_threshold:
                        # 最後の通知時間をチェック（重複通知を防ぐ）
                        if not self.was_recently_notified(todo_data):
                            due_todos.append(todo_data)
            
            return due_todos
            
        except Exception as e:
            logger.error(f"期限近のTODO取得失敗: {e}")
            return []
    
    def was_recently_notified(self, todo_data: Dict[str, Any]) -> bool:
        """最近通知されたかチェック"""
        if 'last_reminder' not in todo_data:
            return False
        
        last_reminder = todo_data['last_reminder']
        now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
        
        # 2時間以内に通知済みの場合はスキップ
        return (now - last_reminder).total_seconds() < 7200
    
    async def send_reminder(self, todo_data: Dict[str, Any]):
        """リマインダー通知を送信"""
        try:
            user_id = str(todo_data['user_id'])
            title = todo_data.get('title', '無題')
            due_date = todo_data['due_date']
            now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            
            # メッセージを作成
            if due_date < now:
                time_diff = now - due_date
                if time_diff.days > 0:
                    time_str = f"{time_diff.days}日"
                else:
                    time_str = f"{time_diff.seconds // 3600}時間"
                message = f"⚠️ **期限超過** ⚠️\n📝 {title}\n🕒 {time_str}前に期限が過ぎています"
            else:
                time_diff = due_date - now
                if time_diff.total_seconds() < 3600:
                    time_str = f"{int(time_diff.total_seconds() // 60)}分"
                else:
                    time_str = f"{int(time_diff.total_seconds() // 3600)}時間"
                message = f"🔔 **リマインダー** 🔔\n📝 {title}\n⏰ あと{time_str}で期限です"
            
            # チャンネル通知またはDM通知
            if self.bot:
                channel_target = todo_data.get('channel_target', 'dm')
                mention_target = todo_data.get('mention_target', 'everyone')
                
                if channel_target != 'dm':
                    await self.send_channel_reminder(channel_target, mention_target, message, user_id)
                else:
                    await self.send_discord_reminder(user_id, message)
            
            # 最後の通知時間を更新
            await self.update_last_reminder(todo_data['id'], user_id)
            
            logger.info(f"リマインダー送信: {user_id} - {title}")
            
        except Exception as e:
            logger.error(f"リマインダー送信失敗: {e}")
    
    async def send_channel_reminder(self, channel_name: str, mention_target: str, message: str, user_id: str):
        """チャンネルにメンション付きリマインダーを送信"""
        try:
            # チャンネルを検索
            channel = None
            for guild in self.bot.guilds:
                for ch in guild.channels:
                    if ch.name.lower() == channel_name.lower() and hasattr(ch, 'send'):
                        channel = ch
                        break
                if channel:
                    break
            
            if channel:
                # メンションを構築
                if mention_target == 'everyone':
                    mention = '@everyone'
                elif mention_target in ['mrc', 'supy']:
                    # 特定ユーザーを検索
                    target_user = None
                    for member in channel.guild.members:
                        if mention_target in member.name.lower() or mention_target in member.display_name.lower():
                            target_user = member
                            break
                    mention = target_user.mention if target_user else f'@{mention_target}'
                else:
                    mention = f'@{mention_target}'
                
                # メッセージを送信
                await channel.send(f"{mention}\n{message}")
                logger.info(f"チャンネル通知送信: #{channel_name} {mention}")
            else:
                logger.error(f"Channel '{channel_name}' not found, falling back to DM")
                await self.send_discord_reminder(user_id, message)
                
        except Exception as e:
            logger.error(f"チャンネル通知送信失敗: {e}")
            # フォールバックでDMを送信
            await self.send_discord_reminder(user_id, message)
    
    async def send_discord_reminder(self, user_id: str, message: str):
        """Discord経由でリマインダーを送信"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            if user:
                await user.send(message)
        except Exception as e:
            logger.error(f"Discord通知送信失敗: {e}")
    
    async def update_last_reminder(self, todo_id: str, user_id: str):
        """最後の通知時間を更新"""
        try:
            await self.todo_manager.update_todo(
                todo_id, 
                user_id, 
                last_reminder=datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            )
        except Exception as e:
            logger.error(f"最後の通知時間更新失敗: {e}")
    
    async def schedule_reminder(self, todo_data: Dict[str, Any], reminder_time: datetime):
        """特定の時間にリマインダーをスケジュール"""
        try:
            now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            delay = (reminder_time - now).total_seconds()
            
            if delay > 0:
                await asyncio.sleep(delay)
                await self.send_reminder(todo_data)
                
        except Exception as e:
            logger.error(f"スケジュールリマインダー失敗: {e}")

# グローバルインスタンス
reminder_system = None

def init_reminder_system(todo_manager: TodoManager, bot_instance=None):
    """リマインダーシステムを初期化"""
    global reminder_system
    reminder_system = ReminderSystem(todo_manager, bot_instance)
    return reminder_system