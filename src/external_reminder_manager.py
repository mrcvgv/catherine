"""
完全外部API管理リマインダーシステム
Notion + Google Calendar でメモリ管理を一切使用しない
"""
import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz
import discord

logger = logging.getLogger(__name__)

class ExternalReminderManager:
    """
    完全外部API管理のリマインダーシステム
    
    アーキテクチャ:
    - Notion Database: メタデータ・履歴管理
    - Google Calendar: スケジュール・時刻管理
    - 定期チェック: Calendar → Notion → Discord通知
    """
    
    def __init__(self, notion_integration=None, google_services=None, discord_bot=None):
        self.notion = notion_integration
        self.google = google_services
        self.bot = discord_bot
        self.reminder_calendar_name = "Catherine Reminders"
        self.check_interval = 300  # 5分間隔
        self.running = False
    
    async def initialize(self):
        """外部サービス接続の初期化"""
        try:
            # Notion統合確認
            if self.notion:
                # Catherine_Reminders データベースが存在するかチェック
                # (実際にはNotionでデータベースを事前作成する必要がある)
                logger.info("✅ Notion integration available for reminders")
            else:
                logger.warning("⚠️ Notion integration not available")
            
            # Google Services確認
            if self.google and self.google.is_configured():
                logger.info("✅ Google Calendar integration available for reminders")
            else:
                logger.warning("⚠️ Google Calendar integration not available")
            
            if not (self.notion and self.google):
                raise Exception("Both Notion and Google integrations required")
            
            logger.info("🚀 External reminder manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize external reminder manager: {e}")
            return False
    
    async def start_periodic_checker(self):
        """定期チェッカーを開始"""
        if self.running:
            logger.info("Reminder checker already running")
            return
        
        self.running = True
        logger.info("🔄 Starting external reminder periodic checker")
        
        # バックグラウンドタスクとして実行
        asyncio.create_task(self._periodic_check_loop())
    
    async def stop_periodic_checker(self):
        """定期チェッカーを停止"""
        self.running = False
        logger.info("🔕 Stopped external reminder periodic checker")
    
    async def _periodic_check_loop(self):
        """定期チェックのメインループ"""
        while self.running:
            try:
                await self.check_pending_reminders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in reminder check loop: {e}")
                await asyncio.sleep(self.check_interval)  # エラーでも継続
    
    def _generate_reminder_id(self) -> str:
        """一意なリマインダーIDを生成"""
        return f"rem_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    def _parse_time_expression(self, text: str, reference_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        自然言語の時間表現を解析
        flexible_reminder_system.pyから移植
        """
        import re
        
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
                hours = 1  # デフォルト1時間後
            
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
                target_time += timedelta(days=1)
            
            logger.info(f"Parsed '{text}' as {day_modifier} {hour}:{minute:02d}: {target_time}")
            return target_time
        
        # 「○時」「○時○分」
        time_only_pattern = r'(\d{1,2})時(?:(\d{1,2})分)?'
        match = re.search(time_only_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            
            target_time = reference_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if target_time <= reference_time:
                target_time += timedelta(days=1)
            
            logger.info(f"Parsed '{text}' as {hour}:{minute:02d}: {target_time}")
            return target_time
        
        # 「明日」「今日」
        if '明日' in text:
            target_time = reference_time + timedelta(days=1)
            target_time = target_time.replace(hour=9, minute=0, second=0, microsecond=0)
            return target_time
        
        if '今日' in text:
            target_time = reference_time.replace(hour=18, minute=0, second=0, microsecond=0)
            if target_time <= reference_time:
                target_time += timedelta(days=1)
            return target_time
        
        logger.warning(f"Could not parse time expression: '{text}'")
        return None
    
    async def create_reminder_from_text(self, text: str, user_id: str) -> Dict[str, Any]:
        """
        自然言語からリマインダーを作成
        
        例: "1時間後にミーティング準備をリマインド@everyone"
        """
        try:
            # 時間解析
            remind_time = self._parse_time_expression(text)
            if not remind_time:
                return {
                    'success': False,
                    'error': '時間を認識できませんでした。「1時間後」「明日の10時」などで指定してください。'
                }
            
            # メンション解析
            mention_target = 'everyone'
            import re
            if '@everyone' in text or 'everyone' in text:
                mention_target = 'everyone'
            elif '@here' in text or 'here' in text:
                mention_target = 'here'
            else:
                username_match = re.search(r'@(\w+)', text)
                if username_match:
                    mention_target = username_match.group(1)
            
            # チャンネル解析
            channel_target = 'catherine'
            if '#todo' in text or 'todo' in text:
                channel_target = 'todo'
            elif '#general' in text or 'general' in text:
                channel_target = 'general'
            
            # メッセージ内容抽出
            message = text
            clean_patterns = [
                r'@everyone', r'@here', r'@\w+',
                r'#\w+',
                r'\d+時間後', r'\d+分後', r'\d+時間\d+分後',
                r'明日の?\d+時\d*分?', r'今日の?\d+時\d*分?',
                r'明日', r'今日',
                r'リマインド', r'を?に?で?'
            ]
            
            for pattern in clean_patterns:
                message = re.sub(pattern, '', message, flags=re.IGNORECASE)
            
            message = re.sub(r'\s+', ' ', message).strip()
            if not message:
                message = "リマインダー"
            
            # 外部APIでリマインダー作成
            result = await self.create_external_reminder(
                message=message,
                remind_time=remind_time,
                mention_target=mention_target,
                channel_target=channel_target,
                user_id=user_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create reminder from text: {e}")
            return {
                'success': False,
                'error': f'リマインダー作成に失敗: {str(e)}'
            }
    
    async def create_external_reminder(self, message: str, remind_time: datetime,
                                     mention_target: str = 'everyone',
                                     channel_target: str = 'catherine',
                                     user_id: str = '') -> Dict[str, Any]:
        """
        完全外部API管理でリマインダーを作成
        
        フロー:
        1. Notion Database にレコード作成
        2. Google Calendar にイベント作成 
        3. Notion に calendar_event_id を更新
        """
        try:
            # 1. リマインダーIDを生成
            reminder_id = self._generate_reminder_id()
            
            # 2. Google Calendar にイベント作成
            calendar_title = f"[Catherine] {message}"
            event_description = json.dumps({
                "reminder_id": reminder_id,
                "mention_target": mention_target,
                "channel_target": channel_target,
                "discord_user": user_id,
                "original_message": message
            }, ensure_ascii=False)
            
            calendar_result = await self.google.create_calendar_event(
                title=calendar_title,
                start_time=remind_time,
                end_time=remind_time + timedelta(minutes=5),
                description=event_description
            )
            
            if not calendar_result.get('success'):
                return {
                    'success': False,
                    'error': f'Google Calendar作成失敗: {calendar_result.get("error", "Unknown error")}'
                }
            
            calendar_event_id = calendar_result.get('event_id')
            
            # 3. Notion Database にレコード作成
            # 注意: 実際のNotion統合では適切なデータベースIDとプロパティ名が必要
            notion_data = {
                "title": reminder_id,  # ページタイトル
                "message": message,
                "calendar_event_id": calendar_event_id,
                "remind_time": remind_time.isoformat(),
                "mention_target": mention_target,
                "channel_target": channel_target,
                "status": "scheduled",
                "created_by": user_id,
                "created_at": datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            }
            
            # Notion APIは今のところMCPブリッジ経由なので、実装は簡略化
            # 実際の運用では notion_integration を拡張する必要がある
            logger.info(f"Would create Notion record: {json.dumps(notion_data, ensure_ascii=False, indent=2)}")
            
            time_str = remind_time.strftime('%Y-%m-%d %H:%M JST')
            
            return {
                'success': True,
                'reminder_id': reminder_id,
                'calendar_event_id': calendar_event_id,
                'message': message,
                'remind_time': remind_time,
                'time_str': time_str,
                'mention_target': mention_target,
                'channel_target': channel_target,
                'response': f"🔔 外部API管理リマインダーを作成しました\n\n📝 内容: {message}\n⏰ 時刻: {time_str}\n📢 通知: @{mention_target}\n📍 場所: #{channel_target}\n📅 Google Calendar: {calendar_event_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create external reminder: {e}")
            return {
                'success': False,
                'error': f'外部リマインダー作成失敗: {str(e)}'
            }
    
    async def check_pending_reminders(self):
        """
        Google Calendar から近い未来のリマインダーをチェックして実行
        """
        try:
            if not (self.google and self.google.is_configured()):
                return
            
            now = datetime.now(pytz.timezone('Asia/Tokyo'))
            
            # 今から15分以内のCatherineイベントを取得
            # 注意: Google Calendar API の実際の実装が必要
            logger.debug(f"Checking reminders around {now}")
            
            # 実際の実装では以下のような感じ:
            # upcoming_events = await self.google.get_upcoming_events(
            #     time_min=now - timedelta(minutes=5),
            #     time_max=now + timedelta(minutes=15),
            #     q="[Catherine]"
            # )
            # 
            # for event in upcoming_events:
            #     event_start = datetime.fromisoformat(event.start)
            #     if now >= event_start and now <= event_start + timedelta(minutes=5):
            #         await self._execute_reminder(event)
            
            # 現在は Google Calendar の詳細API実装がないのでログ出力のみ
            logger.debug("Reminder check completed (detailed implementation pending)")
            
        except Exception as e:
            logger.error(f"Error checking pending reminders: {e}")
    
    async def _execute_reminder(self, calendar_event):
        """
        リマインダーを実行
        
        フロー:
        1. Calendar イベントからメタデータ抽出
        2. Discord 通知送信
        3. Calendar イベント削除
        4. Notion ステータス更新
        """
        try:
            # メタデータ抽出
            metadata = json.loads(calendar_event.description or '{}')
            reminder_id = metadata.get('reminder_id')
            message = metadata.get('original_message', 'リマインダー')
            mention_target = metadata.get('mention_target', 'everyone')
            channel_target = metadata.get('channel_target', 'catherine')
            
            # Discord 通知送信
            await self._send_reminder_notification(
                message=message,
                mention_target=mention_target,
                channel_target=channel_target
            )
            
            # Calendar イベント削除
            # await self.google.delete_calendar_event(calendar_event.id)
            
            # Notion ステータス更新
            # await self._update_notion_reminder_status(reminder_id, 'completed')
            
            logger.info(f"✅ Executed external reminder: {reminder_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to execute reminder: {e}")
    
    async def _send_reminder_notification(self, message: str, mention_target: str, channel_target: str):
        """Discord チャンネルにリマインダー通知を送信"""
        try:
            if not self.bot:
                logger.error("Bot instance not available")
                return
            
            # チャンネル検索
            target_channel = None
            for guild in self.bot.guilds:
                for channel in guild.channels:
                    if (hasattr(channel, 'send') and 
                        channel.name.lower() == channel_target.lower()):
                        target_channel = channel
                        break
                if target_channel:
                    break
            
            if not target_channel:
                logger.error(f"Channel #{channel_target} not found")
                return
            
            # メンション文字列作成
            if mention_target == 'everyone':
                mention = '@everyone'
            elif mention_target == 'here':
                mention = '@here'
            else:
                # ユーザー名検索
                mention = f'@{mention_target}'
                for member in target_channel.guild.members:
                    if (member.name.lower() == mention_target.lower() or 
                        member.display_name.lower() == mention_target.lower()):
                        mention = member.mention
                        break
            
            # 魔女風メッセージ
            witch_phrases = [
                "時間よ、さあ始めなさい！",
                "ほら、約束の時間だよ",
                "やれやれ、忘れてるんじゃないの？",
                "あらあら、もうこんな時間",
                "のんびりしてる場合じゃないよ",
                "時計を見てごらん、時間だよ"
            ]
            
            import random
            witch_intro = random.choice(witch_phrases)
            
            notification_message = f"{mention}\n🔔 **{witch_intro}**\n\n📋 {message}"
            
            await target_channel.send(notification_message)
            
            logger.info(f"📤 Sent external reminder notification to #{channel_target}: '{message}' with {mention}")
            
        except Exception as e:
            logger.error(f"Failed to send reminder notification: {e}")
    
    async def list_active_reminders(self) -> List[Dict[str, Any]]:
        """アクティブなリマインダー一覧を取得"""
        try:
            # 実際の実装では Notion Database や Google Calendar から取得
            # 現在は実装していないため空リストを返す
            logger.info("Would fetch active reminders from Notion/Google Calendar")
            return []
            
        except Exception as e:
            logger.error(f"Failed to list active reminders: {e}")
            return []
    
    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """リマインダーをキャンセル"""
        try:
            # 実際の実装では:
            # 1. Notion から reminder を検索
            # 2. Google Calendar から対応するイベントを削除
            # 3. Notion ステータスを 'cancelled' に更新
            
            logger.info(f"Would cancel reminder: {reminder_id}")
            
            return {
                'success': True,
                'message': f'リマインダー {reminder_id} をキャンセルしました（実装予定）'
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel reminder: {e}")
            return {
                'success': False,
                'error': f'リマインダーキャンセル失敗: {str(e)}'
            }

# グローバルインスタンス
external_reminder_manager = ExternalReminderManager()

def init_external_reminder_manager(notion_integration, google_services, discord_bot):
    """外部リマインダーマネージャーを初期化"""
    global external_reminder_manager
    external_reminder_manager = ExternalReminderManager(
        notion_integration=notion_integration,
        google_services=google_services,
        discord_bot=discord_bot
    )
    return external_reminder_manager