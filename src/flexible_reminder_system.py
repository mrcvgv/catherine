"""
柔軟なリマインダーシステム - カスタムメッセージ・メンション指定対応
"""
import asyncio
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import pytz
import logging
import discord

logger = logging.getLogger(__name__)

class FlexibleReminderSystem:
    """
    柔軟なリマインダーシステム
    
    機能:
    - カスタムメッセージリマインダー
    - TODO項目リマインダー
    - メンション指定 (@everyone, @here, @username)
    - チャンネル指定
    - 自然言語時間解析
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.scheduled_reminders = {}  # reminder_id -> reminder_info
        self.running = False
        self.counter = 0
    
    async def start(self):
        """リマインダーシステム開始"""
        if self.running:
            logger.info("Flexible reminder system already running")
            return
        
        self.running = True
        logger.info("🔔 Flexible reminder system started")
    
    async def stop(self):
        """リマインダーシステム停止"""
        self.running = False
        
        # 実行中のタスクをキャンセル
        for reminder_id, info in self.scheduled_reminders.items():
            if 'task' in info:
                info['task'].cancel()
        
        self.scheduled_reminders.clear()
        logger.info("🔕 Flexible reminder system stopped")
    
    def parse_time_expression(self, text: str, reference_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        自然言語の時間表現を解析
        
        対応例:
        - 1時間後, 30分後, 2時間30分後
        - 明日の10時, 今日の15時
        - 明日, 今日, 来週
        - 10時, 15:30
        """
        if not reference_time:
            reference_time = datetime.now(pytz.timezone('Asia/Tokyo'))
        
        text = text.lower().strip()
        
        # 「○時間○分後」「○分後」「○時間後」
        time_after_pattern = r'(?:(\d+)時間)?(?:(\d+)分)?後'
        match = re.search(time_after_pattern, text)
        if match:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            
            if hours == 0 and minutes == 0:
                # 「後」だけの場合は1時間後
                hours = 1
            
            delta = timedelta(hours=hours, minutes=minutes)
            result_time = reference_time + delta
            logger.info(f"Parsed '{text}' as {hours}h{minutes}m later: {result_time}")
            return result_time
        
        # 「明日の○時」「今日の○時」
        day_time_pattern = r'(明日|今日).*?(\d{1,2})時(?:(\d{1,2})分)?'
        match = re.search(day_time_pattern, text)
        if match:
            day_modifier = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3)) if match.group(3) else 0
            
            target_time = reference_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if day_modifier == '明日':
                target_time += timedelta(days=1)
            elif day_modifier == '今日' and target_time <= reference_time:
                # 今日の時刻が既に過ぎている場合は明日に
                target_time += timedelta(days=1)
            
            logger.info(f"Parsed '{text}' as {day_modifier} {hour}:{minute:02d}: {target_time}")
            return target_time
        
        # 「○時」「○時○分」（今日または明日）
        time_only_pattern = r'(\d{1,2})時(?:(\d{1,2})分)?'
        match = re.search(time_only_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            
            target_time = reference_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 時刻が過ぎている場合は明日に
            if target_time <= reference_time:
                target_time += timedelta(days=1)
            
            logger.info(f"Parsed '{text}' as {hour}:{minute:02d}: {target_time}")
            return target_time
        
        # 「明日」「今日」
        if '明日' in text:
            target_time = reference_time + timedelta(days=1)
            target_time = target_time.replace(hour=9, minute=0, second=0, microsecond=0)  # デフォルト9時
            logger.info(f"Parsed '明日' as tomorrow 9:00: {target_time}")
            return target_time
        
        if '今日' in text:
            target_time = reference_time.replace(hour=18, minute=0, second=0, microsecond=0)  # デフォルト18時
            if target_time <= reference_time:
                target_time += timedelta(days=1)  # 過ぎていたら明日の18時
            logger.info(f"Parsed '今日' as today 18:00: {target_time}")
            return target_time
        
        logger.warning(f"Could not parse time expression: '{text}'")
        return None
    
    def parse_mention_target(self, text: str) -> Dict[str, Any]:
        """
        メンション対象を解析
        
        対応例:
        - @everyone, @here
        - @username, @ユーザー名
        - everyone, here (@ なしでも対応)
        """
        mention_info = {
            'type': 'everyone',  # 'everyone', 'here', 'user'
            'target': 'everyone',
            'mention_string': '@everyone'
        }
        
        text_lower = text.lower()
        
        # @everyone or everyone
        if '@everyone' in text_lower or 'everyone' in text_lower:
            mention_info.update({
                'type': 'everyone',
                'target': 'everyone', 
                'mention_string': '@everyone'
            })
            return mention_info
        
        # @here or here
        if '@here' in text_lower or 'here' in text_lower:
            mention_info.update({
                'type': 'here',
                'target': 'here',
                'mention_string': '@here'
            })
            return mention_info
        
        # @username pattern
        username_match = re.search(r'@(\w+)', text)
        if username_match:
            username = username_match.group(1)
            mention_info.update({
                'type': 'user',
                'target': username,
                'mention_string': f'@{username}'
            })
            return mention_info
        
        # デフォルトは@everyone
        return mention_info
    
    def parse_channel_target(self, text: str) -> str:
        """
        チャンネル対象を解析
        
        対応例:
        - #general, #todo, #catherine
        - general, todo (# なしでも対応)
        """
        # #channel pattern
        channel_match = re.search(r'#(\w+)', text)
        if channel_match:
            return channel_match.group(1)
        
        # キーワードベース
        text_lower = text.lower()
        if 'todo' in text_lower:
            return 'todo'
        elif 'general' in text_lower:
            return 'general'
        elif 'catherine' in text_lower:
            return 'catherine'
        
        # デフォルトは現在のチャンネル（catherine）
        return 'catherine'
    
    async def create_reminder(self, message: str, remind_time: datetime, 
                            mention_target: str = 'everyone', 
                            channel_target: str = 'catherine',
                            user_id: str = '', is_todo_reminder: bool = False,
                            todo_number: Optional[int] = None) -> str:
        """
        リマインダーを作成
        
        Args:
            message: リマインダーメッセージ
            remind_time: リマインド時刻
            mention_target: メンション対象
            channel_target: チャンネル名
            user_id: 作成者ID
            is_todo_reminder: TODO項目のリマインダーか
            todo_number: TODO番号（TODO項目の場合）
        
        Returns:
            reminder_id: リマインダーID
        """
        self.counter += 1
        reminder_id = f"reminder_{self.counter}_{uuid.uuid4().hex[:6]}"
        
        # メンション情報を解析
        mention_info = self.parse_mention_target(mention_target)
        
        reminder_info = {
            'id': reminder_id,
            'message': message,
            'remind_time': remind_time,
            'mention_info': mention_info,
            'channel_target': channel_target,
            'user_id': user_id,
            'is_todo_reminder': is_todo_reminder,
            'todo_number': todo_number,
            'created_at': datetime.now(pytz.timezone('Asia/Tokyo')),
            'status': 'scheduled'
        }
        
        # 非同期タスクを作成
        task = asyncio.create_task(self._execute_reminder(reminder_id))
        reminder_info['task'] = task
        
        self.scheduled_reminders[reminder_id] = reminder_info
        
        time_str = remind_time.strftime('%Y-%m-%d %H:%M JST')
        logger.info(f"🔔 Created reminder {reminder_id}: '{message}' at {time_str} with {mention_info['mention_string']}")
        
        return reminder_id
    
    async def _execute_reminder(self, reminder_id: str):
        """リマインダーを実行"""
        try:
            reminder_info = self.scheduled_reminders.get(reminder_id)
            if not reminder_info:
                logger.error(f"Reminder {reminder_id} not found")
                return
            
            remind_time = reminder_info['remind_time']
            
            # 指定時間まで待機
            now = datetime.now(pytz.timezone('Asia/Tokyo'))
            if remind_time > now:
                wait_seconds = (remind_time - now).total_seconds()
                logger.info(f"⏳ Waiting {wait_seconds:.0f}s for reminder {reminder_id}")
                await asyncio.sleep(wait_seconds)
            
            # リマインダーを送信
            await self._send_reminder_message(reminder_info)
            
            # 完了としてマーク
            reminder_info['status'] = 'completed'
            reminder_info['executed_at'] = datetime.now(pytz.timezone('Asia/Tokyo'))
            
        except asyncio.CancelledError:
            logger.info(f"❌ Reminder {reminder_id} was cancelled")
        except Exception as e:
            logger.error(f"❌ Error executing reminder {reminder_id}: {e}")
    
    async def _send_reminder_message(self, reminder_info: Dict[str, Any]):
        """リマインダーメッセージを送信"""
        try:
            if not self.bot:
                logger.error("Bot instance not available for sending reminders")
                return
            
            channel_name = reminder_info['channel_target']
            mention_info = reminder_info['mention_info']
            message = reminder_info['message']
            
            # チャンネルを検索
            target_channel = None
            for guild in self.bot.guilds:
                for channel in guild.channels:
                    if (hasattr(channel, 'send') and 
                        channel.name.lower() == channel_name.lower()):
                        target_channel = channel
                        break
                if target_channel:
                    break
            
            if not target_channel:
                logger.error(f"Channel '{channel_name}' not found")
                return
            
            # メンション文字列を作成
            mention_string = mention_info['mention_string']
            if mention_info['type'] == 'user':
                # ユーザー名からメンション作成を試行
                username = mention_info['target']
                user_member = None
                for member in target_channel.guild.members:
                    if member.name.lower() == username.lower() or member.display_name.lower() == username.lower():
                        user_member = member
                        break
                
                if user_member:
                    mention_string = user_member.mention
                else:
                    mention_string = f"@{username} (ユーザーが見つかりません)"
            
            # 魔女風リマインダーメッセージ
            witch_reminders = [
                "時間よ！",
                "ほら、約束の時間だよ",
                "忘れてるんじゃないの？",
                "やれやれ、リマインダーの時間だ",
                "あらあら、もうこんな時間",
                "さあ、やることがあるでしょう？",
                "時計を見てごらん",
                "のんびりしてる場合じゃないよ"
            ]
            
            import random
            witch_intro = random.choice(witch_reminders)
            
            # TODO項目リマインダーの場合は追加情報
            extra_info = ""
            if reminder_info.get('is_todo_reminder') and reminder_info.get('todo_number'):
                extra_info = f"\n📋 TODO #{reminder_info['todo_number']}"
            
            full_message = f"{mention_string}\n🔔 **{witch_intro}**\n\n{message}{extra_info}"
            
            await target_channel.send(full_message)
            
            logger.info(f"✅ Sent reminder to #{channel_name}: '{message}' with {mention_string}")
            
        except Exception as e:
            logger.error(f"Failed to send reminder message: {e}")
    
    async def create_custom_reminder(self, text: str, user_id: str = '') -> Dict[str, Any]:
        """
        自然言語からカスタムリマインダーを作成
        
        例:
        - "1時間後にミーティング準備をリマインド@everyone"
        - "明日の10時に買い物リストを#todo で@here にリマインド"
        - "30分後に休憩"
        """
        try:
            # 時間表現を抽出
            remind_time = self.parse_time_expression(text)
            if not remind_time:
                return {
                    'success': False,
                    'error': '時間を認識できませんでした。「1時間後」「明日の10時」などの形式で指定してください。'
                }
            
            # メンション対象を抽出
            mention_target = 'everyone'  # デフォルト
            if '@everyone' in text or 'everyone' in text:
                mention_target = 'everyone'
            elif '@here' in text or 'here' in text:
                mention_target = 'here'
            else:
                # @username を検索
                username_match = re.search(r'@(\w+)', text)
                if username_match:
                    mention_target = username_match.group(1)
            
            # チャンネル対象を抽出
            channel_target = self.parse_channel_target(text)
            
            # メッセージ内容を抽出（「リマインド」より前の部分）
            message_content = text
            
            # 不要な部分を除去
            clean_patterns = [
                r'@everyone', r'@here', r'@\w+',  # メンション
                r'#\w+',  # チャンネル
                r'\d+時間後', r'\d+分後', r'\d+時間\d+分後',  # 時間表現
                r'明日の?\d+時\d*分?', r'今日の?\d+時\d*分?',
                r'明日', r'今日',
                r'リマインド', r'を?に?で?'
            ]
            
            for pattern in clean_patterns:
                message_content = re.sub(pattern, '', message_content, flags=re.IGNORECASE)
            
            message_content = re.sub(r'\s+', ' ', message_content).strip()
            
            if not message_content:
                message_content = "リマインダー"
            
            # リマインダーを作成
            reminder_id = await self.create_reminder(
                message=message_content,
                remind_time=remind_time,
                mention_target=mention_target,
                channel_target=channel_target,
                user_id=user_id,
                is_todo_reminder=False
            )
            
            # 結果を返す
            time_str = remind_time.strftime('%Y-%m-%d %H:%M JST')
            mention_info = self.parse_mention_target(mention_target)
            
            return {
                'success': True,
                'reminder_id': reminder_id,
                'message': message_content,
                'remind_time': remind_time,
                'time_str': time_str,
                'mention_target': mention_info['mention_string'],
                'channel_target': f'#{channel_target}',
                'response': f"🔔 リマインダーを設定しました\n\n📝 内容: {message_content}\n⏰ 時刻: {time_str}\n📢 通知: {mention_info['mention_string']}\n📍 場所: #{channel_target}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create custom reminder: {e}")
            return {
                'success': False,
                'error': f'リマインダー作成に失敗しました: {str(e)}'
            }
    
    async def create_todo_reminder(self, todo_number: int, remind_time: datetime,
                                 user_id: str = '', mention_target: str = 'everyone',
                                 channel_target: str = 'catherine') -> Dict[str, Any]:
        """TODO項目のリマインダーを作成"""
        try:
            # 統合TODOマネージャーから該当TODOを取得
            from src.unified_todo_manager import unified_todo_manager
            
            todos_result = await unified_todo_manager.list_todos(user_id, include_completed=False)
            if not todos_result.get('success') or not todos_result.get('todos'):
                return {'success': False, 'error': 'TODOが見つかりません'}
            
            todos = todos_result['todos']
            if todo_number < 1 or todo_number > len(todos):
                return {'success': False, 'error': f'番号{todo_number}のTODOは存在しません'}
            
            todo = todos[todo_number - 1]
            todo_title = todo.get('title', f'TODO #{todo_number}')
            
            # リマインダーを作成
            reminder_id = await self.create_reminder(
                message=f"TODO: {todo_title}",
                remind_time=remind_time,
                mention_target=mention_target,
                channel_target=channel_target,
                user_id=user_id,
                is_todo_reminder=True,
                todo_number=todo_number
            )
            
            time_str = remind_time.strftime('%Y-%m-%d %H:%M JST')
            mention_info = self.parse_mention_target(mention_target)
            
            return {
                'success': True,
                'reminder_id': reminder_id,
                'todo_title': todo_title,
                'remind_time': remind_time,
                'time_str': time_str,
                'mention_target': mention_info['mention_string'],
                'channel_target': f'#{channel_target}',
                'response': f"🔔 TODO #{todo_number}のリマインダーを設定しました\n\n📝 内容: {todo_title}\n⏰ 時刻: {time_str}\n📢 通知: {mention_info['mention_string']}\n📍 場所: #{channel_target}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create todo reminder: {e}")
            return {
                'success': False,
                'error': f'TODOリマインダー作成に失敗しました: {str(e)}'
            }
    
    def get_scheduled_reminders(self) -> List[Dict[str, Any]]:
        """スケジュール済みリマインダー一覧を取得"""
        active_reminders = []
        for reminder_id, info in self.scheduled_reminders.items():
            if info.get('status') == 'scheduled':
                active_reminders.append({
                    'id': reminder_id,
                    'message': info['message'],
                    'remind_time': info['remind_time'],
                    'mention_target': info['mention_info']['mention_string'],
                    'channel_target': info['channel_target']
                })
        
        # 時間順にソート
        active_reminders.sort(key=lambda x: x['remind_time'])
        return active_reminders

# グローバルインスタンス
flexible_reminder_system = FlexibleReminderSystem()

def init_flexible_reminder_system(bot_instance) -> FlexibleReminderSystem:
    """リマインダーシステムを初期化"""
    global flexible_reminder_system
    flexible_reminder_system = FlexibleReminderSystem(bot_instance)
    return flexible_reminder_system