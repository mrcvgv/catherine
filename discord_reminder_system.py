#!/usr/bin/env python3
"""
Discord Reminder System - 自然文リマインド機能
こうへい最終仕様対応版
"""

import uuid
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pytz
from dataclasses import dataclass, asdict
from firebase_config import firebase_manager
from todo_nlu_enhanced import RelativeDateParser

# 日本時間
JST = pytz.timezone('Asia/Tokyo')

@dataclass
class Reminder:
    id: Optional[str] = None
    message: str = ""
    remind_at: Optional[datetime] = None
    mentions: List[str] = None
    created_by: str = ""
    channel_id: str = ""
    status: str = "scheduled"  # scheduled, sent, cancelled
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now(JST)

class ReminderSystem:
    """Discord リマインドシステム"""
    
    def __init__(self):
        self.db = firebase_manager.get_db()
        self.collection_name = 'reminders'
        self.date_parser = RelativeDateParser()
        
        # メンション正規化マップ
        self.mention_map = {
            'everyone': '@everyone',
            'みんな': '@everyone',
            '全員': '@everyone',
            'all': '@everyone',
            'mrc': '@mrc',
            'supy': '@supy',
            'こうへい': '@kouhei',
            'kohei': '@kouhei'
        }
        
        # リマインドパターン
        self.remind_patterns = [
            r'(?:リマインド|remind|通知|お知らせ)',
            r'(?:思い出させて|忘れないで)',
            r'(?:アラーム|時報)',
            r'(?:知らせて|教えて)'
        ]
        
        # 日付パターン（強化版）
        self.date_patterns = {
            # 標準形式
            r'(\d{1,2})/(\d{1,2})': self._parse_md_format,
            r'(\d{4})/(\d{1,2})/(\d{1,2})': self._parse_ymd_format,
            r'(\d{1,2})月(\d{1,2})日': self._parse_month_day,
            r'(\d{1,2})日': self._parse_day_only,
            
            # 相対日付
            r'今日|きょう': lambda: self.date_parser.now.date(),
            r'明日|あした|あす': lambda: (self.date_parser.now + timedelta(days=1)).date(),
            r'明後日|あさって': lambda: (self.date_parser.now + timedelta(days=2)).date(),
            
            # 曜日
            r'月曜|月曜日': lambda: self._next_weekday(0),
            r'火曜|火曜日': lambda: self._next_weekday(1),
            r'水曜|水曜日': lambda: self._next_weekday(2),
            r'木曜|木曜日': lambda: self._next_weekday(3),
            r'金曜|金曜日': lambda: self._next_weekday(4),
            r'土曜|土曜日': lambda: self._next_weekday(5),
            r'日曜|日曜日': lambda: self._next_weekday(6),
        }
        
        # 時刻パターン
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})',  # 18:30
            r'(\d{1,2})時(\d{1,2})分',  # 18時30分
            r'(\d{1,2})時',  # 18時
            r'午前(\d{1,2})時',  # 午前9時
            r'午後(\d{1,2})時',  # 午後6時
            r'朝(\d{1,2})時',  # 朝9時
            r'夜(\d{1,2})時',  # 夜8時
        ]
    
    def _parse_md_format(self, match) -> datetime.date:
        """M/D形式をパース"""
        month, day = int(match.group(1)), int(match.group(2))
        year = self.date_parser.now.year
        try:
            date = datetime(year, month, day).date()
            if date < self.date_parser.now.date():
                date = datetime(year + 1, month, day).date()
            return date
        except ValueError:
            return None
    
    def _parse_ymd_format(self, match) -> datetime.date:
        """Y/M/D形式をパース"""
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return datetime(year, month, day).date()
        except ValueError:
            return None
    
    def _parse_month_day(self, match) -> datetime.date:
        """X月Y日形式をパース"""
        month, day = int(match.group(1)), int(match.group(2))
        year = self.date_parser.now.year
        try:
            date = datetime(year, month, day).date()
            if date < self.date_parser.now.date():
                date = datetime(year + 1, month, day).date()
            return date
        except ValueError:
            return None
    
    def _parse_day_only(self, match) -> datetime.date:
        """X日形式をパース（今月または来月）"""
        day = int(match.group(1))
        now = self.date_parser.now
        try:
            # 今月
            date = datetime(now.year, now.month, day).date()
            if date < now.date():
                # 来月
                if now.month == 12:
                    date = datetime(now.year + 1, 1, day).date()
                else:
                    date = datetime(now.year, now.month + 1, day).date()
            return date
        except ValueError:
            return None
    
    def _next_weekday(self, target_weekday: int) -> datetime.date:
        """次の指定曜日を取得"""
        now = self.date_parser.now
        days_ahead = target_weekday - now.weekday()
        if days_ahead <= 0:  # 今日以前なら来週
            days_ahead += 7
        return (now + timedelta(days=days_ahead)).date()
    
    def parse_reminder_text(self, text: str) -> Dict[str, Any]:
        """自然文からリマインド情報を抽出"""
        result = {
            'intent': 'reminder',
            'message': '',
            'remind_at': None,
            'mentions': [],
            'confidence': 0.0,
            'error': None
        }
        
        # リマインド意図の検出
        is_reminder = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.remind_patterns)
        if not is_reminder:
            result['confidence'] = 0.0
            return result
        
        result['confidence'] = 0.7
        
        # メンション抽出
        mentions = self._extract_mentions(text)
        result['mentions'] = mentions
        
        # 日時抽出
        remind_at = self._extract_datetime(text)
        result['remind_at'] = remind_at
        
        # メッセージ抽出
        message = self._extract_message(text)
        result['message'] = message
        
        # 必須項目チェック
        if not message:
            result['error'] = {
                'type': 'missing_message',
                'message': 'リマインドする内容を教えてください',
                'suggestion': '例: 18:30に@mrcで『在庫チェック』リマインド'
            }
            result['confidence'] = 0.3
        elif not remind_at:
            result['error'] = {
                'type': 'missing_time',
                'message': 'いつ通知しますか？',
                'suggestion': '例: 明日9:00、8/15 18:30、月曜日の朝9時'
            }
            result['confidence'] = 0.5
        else:
            result['confidence'] = 0.9
        
        return result
    
    def _extract_mentions(self, text: str) -> List[str]:
        """メンション抽出"""
        mentions = []
        
        # @形式のメンション
        at_mentions = re.findall(r'@(\w+)', text)
        for mention in at_mentions:
            normalized = self.mention_map.get(mention.lower(), f'@{mention}')
            mentions.append(normalized)
        
        # 自然言語でのメンション
        for key, value in self.mention_map.items():
            if key in text.lower() and value not in mentions:
                mentions.append(value)
        
        return list(set(mentions))  # 重複除去
    
    def _extract_datetime(self, text: str) -> Optional[datetime]:
        """日時抽出"""
        target_date = None
        target_time = None
        
        # 日付抽出
        for pattern, parser in self.date_patterns.items():
            match = re.search(pattern, text)
            if match:
                if callable(parser):
                    target_date = parser()
                else:
                    target_date = parser(match)
                if target_date:
                    break
        
        # 時刻抽出
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '午後' in match.group(0):
                        hour = int(match.group(1))
                        if hour != 12:
                            hour += 12
                        minute = 0
                    elif '午前' in match.group(0):
                        hour = int(match.group(1))
                        minute = 0
                    elif '朝' in match.group(0):
                        hour = int(match.group(1))
                        if hour < 12:  # 朝は午前として扱う
                            pass
                        minute = 0
                    elif '夜' in match.group(0):
                        hour = int(match.group(1))
                        if hour < 12:  # 夜は午後として扱う
                            hour += 12
                        minute = 0
                    elif len(match.groups()) == 2:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                    else:
                        hour = int(match.group(1))
                        minute = 0
                    
                    target_time = datetime.min.time().replace(hour=hour, minute=minute)
                    break
                except (ValueError, IndexError):
                    continue
        
        # デフォルト値設定
        if not target_date:
            target_date = self.date_parser.now.date()
        
        if not target_time:
            # 時刻が指定されていない場合は18:00をデフォルト
            target_time = datetime.min.time().replace(hour=18, minute=0)
        
        # 結合
        try:
            result = datetime.combine(target_date, target_time)
            result = JST.localize(result)
            
            # 過去の時刻なら翌日
            if result <= self.date_parser.now:
                result += timedelta(days=1)
            
            return result
        except Exception:
            return None
    
    def _extract_message(self, text: str) -> str:
        """リマインドメッセージ抽出"""
        # 「」『』で囲まれたメッセージを優先
        quote_match = re.search(r'[「『]([^」』]+)[」』]', text)
        if quote_match:
            return quote_match.group(1).strip()
        
        # リマインド系の語句を除去して残りを抽出
        message = text
        
        # 日時・メンション・リマインド語句を除去
        message = re.sub(r'\d{1,2}[:/]\d{1,2}', '', message)
        message = re.sub(r'\d{1,2}時\d{0,2}分?', '', message)
        message = re.sub(r'@\w+', '', message)
        message = re.sub(r'(?:リマインド|remind|通知|お知らせ)', '', message)
        message = re.sub(r'(?:明日|今日|明後日)', '', message)
        message = re.sub(r'(?:午前|午後|朝|夜)', '', message)
        message = re.sub(r'[で|に|を|と|は|が|の]+', ' ', message)
        
        # 余分な空白を除去
        message = re.sub(r'\s+', ' ', message).strip()
        
        # 短すぎる場合は元のテキストから推測
        if len(message) < 3:
            # 動詞を含む部分を抽出
            verb_match = re.search(r'(\w+(?:チェック|確認|会議|ミーティング|作業|提出|締切))', text)
            if verb_match:
                return verb_match.group(1)
            
            # 最後の手段：元テキストの一部
            clean_text = re.sub(r'(?:リマインド|remind|@\w+|\d{1,2}:\d{2})', '', text).strip()
            if clean_text:
                return clean_text[:50]
        
        return message[:100] if message else ""
    
    async def register_reminder(self, reminder: Reminder) -> Dict[str, Any]:
        """リマインド登録"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            # Firestoreに保存
            reminder_doc = {
                'id': reminder.id,
                'message': reminder.message,
                'remind_at': reminder.remind_at,
                'mentions': reminder.mentions,
                'created_by': reminder.created_by,
                'channel_id': reminder.channel_id,
                'status': reminder.status,
                'created_at': reminder.created_at
            }
            
            self.db.collection(self.collection_name).document(reminder.id).set(reminder_doc)
            
            # スケジューラに登録（実装は別途必要）
            # await self._schedule_reminder(reminder)
            
            # 成功レスポンス
            remind_time = reminder.remind_at.strftime('%Y-%m-%d %H:%M JST')
            mentions_str = ', '.join(reminder.mentions) if reminder.mentions else '@everyone'
            
            return {
                'success': True,
                'message': f"⏰ リマインド登録：{remind_time} ｜宛先: {mentions_str}",
                'reminder_id': reminder.id,
                'response_type': 'reminder_registered'
            }
            
        except Exception as e:
            print(f"Error registering reminder: {e}")
            return {'success': False, 'message': f'リマインド登録エラー: {str(e)}'}
    
    async def get_daily_schedule(self, date: datetime.date, channel_id: str) -> str:
        """指定日の予定を取得（毎朝8:00用）"""
        try:
            if not self.db:
                return "データベース接続エラー"
            
            # その日のリマインドを取得
            start_dt = datetime.combine(date, datetime.min.time())
            end_dt = datetime.combine(date, datetime.max.time())
            start_dt = JST.localize(start_dt)
            end_dt = JST.localize(end_dt)
            
            reminders = self.db.collection(self.collection_name).where(
                'channel_id', '==', channel_id
            ).where(
                'status', '==', 'scheduled'
            ).where(
                'remind_at', '>=', start_dt
            ).where(
                'remind_at', '<=', end_dt
            ).order_by('remind_at').get()
            
            if not reminders:
                return "📅 **本日の予定**\n\n予定はありません。良い一日を！"
            
            message = f"📅 **本日の予定** ({date.strftime('%m/%d')})\n\n"
            for reminder in reminders:
                data = reminder.to_dict()
                time_str = data['remind_at'].strftime('%H:%M')
                mentions_str = ', '.join(data.get('mentions', ['@everyone']))
                message += f"🔔 {time_str} - {data['message']} ({mentions_str})\n"
            
            message += "\n良い一日をお過ごしください！"
            return message
            
        except Exception as e:
            print(f"Error getting daily schedule: {e}")
            return f"予定取得エラー: {str(e)}"
    
    async def execute_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """リマインド実行"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            # リマインド取得
            doc = self.db.collection(self.collection_name).document(reminder_id).get()
            if not doc.exists:
                return {'success': False, 'message': 'リマインドが見つかりません'}
            
            data = doc.to_dict()
            
            # 実行
            mentions_str = ' '.join(data.get('mentions', ['@everyone']))
            message = f"{mentions_str} 🔔 リマインド: {data['message']}"
            
            # ステータス更新
            self.db.collection(self.collection_name).document(reminder_id).update({
                'status': 'sent',
                'sent_at': datetime.now(JST)
            })
            
            return {
                'success': True,
                'message': message,
                'channel_id': data['channel_id'],
                'response_type': 'reminder_executed'
            }
            
        except Exception as e:
            print(f"Error executing reminder: {e}")
            return {'success': False, 'message': f'リマインド実行エラー: {str(e)}'}

if __name__ == "__main__":
    # テスト実行
    reminder_system = ReminderSystem()
    
    test_cases = [
        "18:30に@mrcで『在庫チェック』リマインド",
        "明日9:00に会議リマインド",
        "8/15 18:00にみんなで締切のお知らせ",
        "月曜日の朝9時にミーティング通知",
        "今夜8時に@supyで作業完了確認",
    ]
    
    for test in test_cases:
        print(f"\n📝 Input: {test}")
        result = reminder_system.parse_reminder_text(test)
        print(f"Intent: {result['intent']}")
        print(f"Message: {result['message']}")
        print(f"Remind at: {result['remind_at']}")
        print(f"Mentions: {result['mentions']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result['error']:
            print(f"Error: {result['error']}")