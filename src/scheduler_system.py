"""
スケジューラーシステム - 指定時間にリマインダーを実行
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz
import logging
from src.mention_utils import DiscordMentionHandler, get_mention_string

logger = logging.getLogger(__name__)

class SchedulerSystem:
    """スケジューラーシステム"""
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.scheduled_tasks = {}  # task_id -> task_info
        self.running = False
        self.task_counter = 0
        self.mention_handler: Optional[DiscordMentionHandler] = None
        
        if bot_instance:
            self.mention_handler = DiscordMentionHandler(bot_instance)
        
    async def start(self):
        """スケジューラーを開始"""
        if self.running:
            logger.info("スケジューラーシステムは既に実行中です")
            return
            
        self.running = True
        logger.info("スケジューラーシステムを開始しました")
        
        # メインループを開始（すでにリマインダーシステムで動作中なのでここでは軽量化）
        
    async def stop(self):
        """スケジューラーを停止"""
        self.running = False
        # 実行中のタスクをキャンセル
        for task_id, task_info in self.scheduled_tasks.items():
            if 'task' in task_info:
                task_info['task'].cancel()
        self.scheduled_tasks.clear()
        logger.info("スケジューラーシステムを停止しました")
    
    async def schedule_reminder(self, remind_time: datetime, todo_data: Dict[str, Any], is_recurring: bool = False) -> str:
        """リマインダーをスケジュール"""
        self.task_counter += 1
        task_id = f"reminder_{self.task_counter}"
        
        # タスク情報を保存
        self.scheduled_tasks[task_id] = {
            'remind_time': remind_time,
            'todo_data': todo_data,
            'is_recurring': is_recurring,
            'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
        }
        
        # 非同期タスクを作成
        task = asyncio.create_task(self._execute_scheduled_reminder(task_id))
        self.scheduled_tasks[task_id]['task'] = task
        
        logger.info(f"リマインダーをスケジュール: {task_id} at {remind_time}")
        return task_id
    
    async def _execute_scheduled_reminder(self, task_id: str):
        """スケジュールされたリマインダーを実行"""
        try:
            task_info = self.scheduled_tasks.get(task_id)
            if not task_info:
                logger.error(f"Task {task_id} not found in scheduled_tasks")
                return
            
            remind_time = task_info['remind_time']
            todo_data = task_info['todo_data']
            is_recurring = task_info.get('is_recurring', False)
            
            logger.info(f"Executing reminder task {task_id} scheduled for {remind_time}")
            
            # 指定時間まで待機
            now = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC)
            if remind_time > now:
                wait_seconds = (remind_time - now).total_seconds()
                logger.info(f"Waiting {wait_seconds} seconds until {remind_time}")
                await asyncio.sleep(wait_seconds)
            else:
                logger.info(f"Reminder time has passed, executing immediately")
            
            # リマインダーを送信
            logger.info(f"Sending scheduled reminder for task {task_id}")
            await self._send_scheduled_reminder(todo_data)
            
            # 繰り返しタスクの場合は次回をスケジュール
            if is_recurring:
                next_remind_time = remind_time + timedelta(days=1)  # 毎日繰り返し
                logger.info(f"Scheduling next recurring reminder for {next_remind_time}")
                await self.schedule_reminder(next_remind_time, todo_data, is_recurring=True)
            
            # タスクを削除
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
                logger.info(f"Completed and removed task {task_id}")
                
        except asyncio.CancelledError:
            logger.info(f"スケジュールされたリマインダーがキャンセルされました: {task_id}")
        except Exception as e:
            logger.error(f"スケジュールリマインダー実行エラー: {e}")
            
    async def _send_scheduled_reminder(self, todo_data: Dict[str, Any]):
        """スケジュールされたリマインダーを送信"""
        try:
            if not self.bot:
                logger.error("Bot instance not available")
                return
            
            # チャンネルを取得
            channel_name = todo_data.get('channel_target', 'todo')
            channel = None
            
            for guild in self.bot.guilds:
                for ch in guild.channels:
                    if ch.name.lower() == channel_name.lower() and hasattr(ch, 'send'):
                        channel = ch
                        break
                if channel:
                    break
            
            if not channel:
                logger.error(f"Channel '{channel_name}' not found")
                return
            
            # 新しいメンションハンドラーを使用
            mention_target = todo_data.get('mention_target', 'everyone')
            logger.info(f"Building mention for target: {mention_target}")
            
            if self.mention_handler:
                mention_data = self.mention_handler.parse_mention_text(mention_target, channel.guild)
                mention = mention_data.get('mention_string', '@everyone')
                logger.info(f"Built mention using handler: {mention} for target: {mention_target}")
            else:
                # フォールバック
                mention = get_mention_string(mention_target, channel.guild, self.bot)
                logger.info(f"Built mention using fallback: {mention} for target: {mention_target}")
            
            # メッセージを送信
            if todo_data.get('is_list_reminder'):
                # 全リスト通知（チーム全体）
                from todo_manager import todo_manager
                user_id = str(todo_data['user_id'])
                todos = await todo_manager.get_todos()
                
                if todos:
                    list_text = todo_manager.format_todo_list(todos)
                    witch_daily_greetings = [
                        f"**定時リマインダー** {mention}\\n\\n{list_text}\\n\\nさあ、今日も頑張るんだよ",
                        f"**定時リマインダー** {mention}\\n\\n{list_text}\\n\\n一つずつ片付けていきな",
                        f"**定時リマインダー** {mention}\\n\\n{list_text}\\n\\nやることが山積みだねぇ",
                        f"**定時リマインダー** {mention}\\n\\n{list_text}\\n\\n優先度順になってるから、上から順にやりな"
                    ]
                    import random
                    message = random.choice(witch_daily_greetings)
                else:
                    witch_empty_list = [
                        f"**定時リマインダー** {mention}\\nTODOリストは空っぽだよ。珍しいねぇ",
                        f"**定時リマインダー** {mention}\\nやることが何もないね。のんびりしてるのかい？",
                        f"**定時リマインダー** {mention}\\nリストは空だよ。全部片付いたのかな？",
                        f"**定時リマインダー** {mention}\\n何もないじゃないか。サボってるのかい？"
                    ]
                    import random
                    message = random.choice(witch_empty_list)
            else:
                # 個別TODO通知またはカスタムメッセージ
                if todo_data.get('custom_message'):
                    # カスタムメッセージがある場合
                    custom_msg = todo_data['custom_message']
                    message = f"{mention}\n{custom_msg}"
                else:
                    # 通常のTODOリマインダー
                    title = todo_data.get('title', 'TODO')
                    witch_reminders = [
                        "時間だよ、忘れてないかい？",
                        "ほら、やる時間が来たよ",
                        "約束の時間だねぇ",
                        "さあ、取り掛かる時間だよ",
                        "忘れんぼうさん、時間だよ",
                        "やれやれ、またお知らせの時間かい",
                        "ふふ、私が教えてあげるよ"
                    ]
                    import random
                    witch_comment = random.choice(witch_reminders)
                    message = f"{mention}\n{title}\n{witch_comment}"
            
            await channel.send(message)
            logger.info(f"スケジュールリマインダー送信完了: {channel_name}")
            
        except Exception as e:
            logger.error(f"スケジュールリマインダー送信失敗: {e}")

# グローバルインスタンス
scheduler_system = None

def init_scheduler_system(bot_instance=None):
    """スケジューラーシステムを初期化"""
    global scheduler_system
    scheduler_system = SchedulerSystem(bot_instance)
    return scheduler_system