#!/usr/bin/env python3
"""
Cloud Reminder System - Firebase三点セット統合
Firebase + Cloud Functions + Cloud Tasks による堅牢なリマインドシステム
"""

import json
import requests
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pytz
from firebase_config import firebase_manager
from cloud_functions import CloudFunctionsClient

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class CloudReminder:
    """クラウドリマインダー"""
    reminder_id: str
    user_id: str
    what: str
    mention: str
    run_at: datetime
    channel_id: str
    rrule: Optional[str] = None
    status: str = "scheduled"
    task_name: Optional[str] = None

class CloudReminderSystem:
    """Cloud Functions + Cloud Tasks ベースのリマインドシステム"""
    
    def __init__(self, functions_url: str):
        self.db = firebase_manager.get_db()
        self.cloud_client = CloudFunctionsClient(functions_url)
        self.collection_name = 'reminders'
        
        print("SUCCESS: Cloud Reminder System initialized")
    
    async def create_reminder(self, user_id: str, what: str, run_at: datetime,
                             channel_id: str, mention: str = "@everyone",
                             rrule: Optional[str] = None) -> Dict[str, Any]:
        """リマインダー作成 - Cloud Functions経由"""
        try:
            # ISO8601形式に変換
            run_at_iso = run_at.isoformat()
            
            # Cloud Functions呼び出し
            result = await self.cloud_client.create_reminder(
                user_id=user_id,
                what=what,
                run_at=run_at_iso,
                channel_id=channel_id,
                mention=mention,
                rrule=rrule
            )
            
            if result['success']:
                data = result['data']
                return {
                    'success': True,
                    'reminder_id': data['reminderId'],
                    'scheduled_at': run_at_iso,
                    'task_name': data.get('taskName'),
                    'message': f'⏰ リマインド登録: {run_at.strftime("%m/%d %H:%M")} JST | 宛先: {mention}'
                }
            else:
                return {
                    'success': False,
                    'message': f'リマインド登録エラー: {result["error"]}',
                    'error': result['error']
                }
        
        except Exception as e:
            print(f"[ERROR] Cloud reminder creation failed: {e}")
            return {
                'success': False,
                'message': f'リマインド作成エラー: {str(e)}',
                'error': str(e)
            }
    
    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """リマインダー削除 - Cloud Functions経由"""
        try:
            result = await self.cloud_client.cancel_reminder(reminder_id)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'リマインダー「{reminder_id}」をキャンセルしました',
                    'cancelled_id': reminder_id
                }
            else:
                return {
                    'success': False,
                    'message': f'キャンセルエラー: {result["error"]}',
                    'error': result['error']
                }
        
        except Exception as e:
            print(f"[ERROR] Cloud reminder cancellation failed: {e}")
            return {
                'success': False,
                'message': f'キャンセルエラー: {str(e)}',
                'error': str(e)
            }
    
    async def list_user_reminders(self, user_id: str, 
                                 status: str = "scheduled") -> Dict[str, Any]:
        """ユーザーのリマインダー一覧取得"""
        try:
            query = self.db.collection(self.collection_name).where(
                'userId', '==', user_id
            ).where('status', '==', status).order_by(
                'runAt', direction='ASCENDING'
            ).limit(20)
            
            docs = query.get()
            
            reminders = []
            for doc in docs:
                data = doc.to_dict()
                reminders.append({
                    'id': doc.id,
                    'what': data.get('what'),
                    'mention': data.get('mention'),
                    'run_at': data.get('runAt').strftime('%m/%d %H:%M') if data.get('runAt') else 'Unknown',
                    'rrule': data.get('rrule'),
                    'status': data.get('status')
                })
            
            if not reminders:
                return {
                    'success': True,
                    'message': '予定されているリマインダーはありません',
                    'reminders': []
                }
            
            # フォーマット済みメッセージ生成
            message = f"📅 **リマインダー一覧** ({len(reminders)}件)\n\n"
            for i, reminder in enumerate(reminders, 1):
                rrule_info = f" (繰り返し)" if reminder['rrule'] else ""
                message += f"{i}. 🔔 {reminder['run_at']} - {reminder['what']} ({reminder['mention']}){rrule_info}\n"
            
            return {
                'success': True,
                'message': message,
                'reminders': reminders,
                'count': len(reminders)
            }
        
        except Exception as e:
            print(f"[ERROR] List reminders failed: {e}")
            return {
                'success': False,
                'message': f'リマインダー一覧取得エラー: {str(e)}',
                'error': str(e)
            }
    
    async def get_daily_reminders(self, user_id: str, date: datetime) -> Dict[str, Any]:
        """指定日のリマインダー取得"""
        try:
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            query = self.db.collection(self.collection_name).where(
                'userId', '==', user_id
            ).where('runAt', '>=', day_start).where(
                'runAt', '<', day_end
            ).where('status', '==', 'scheduled').order_by('runAt')
            
            docs = query.get()
            
            reminders = []
            for doc in docs:
                data = doc.to_dict()
                reminders.append({
                    'id': doc.id,
                    'what': data.get('what'),
                    'mention': data.get('mention'),
                    'time': data.get('runAt').strftime('%H:%M'),
                    'full_time': data.get('runAt')
                })
            
            return {
                'success': True,
                'reminders': reminders,
                'count': len(reminders),
                'date': date.strftime('%Y-%m-%d')
            }
        
        except Exception as e:
            print(f"[ERROR] Get daily reminders failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_rrule_from_japanese(self, text: str) -> Optional[str]:
        """日本語からRRULE生成"""
        text_lower = text.lower()
        
        # 毎日
        if '毎日' in text or 'daily' in text_lower:
            return 'FREQ=DAILY'
        
        # 毎週
        if '毎週' in text:
            weekdays = {
                '月': 'MO', '火': 'TU', '水': 'WE', '木': 'TH',
                '金': 'FR', '土': 'SA', '日': 'SU'
            }
            
            for jp_day, en_day in weekdays.items():
                if jp_day in text:
                    return f'FREQ=WEEKLY;BYDAY={en_day}'
            
            return 'FREQ=WEEKLY'
        
        # 毎月
        if '毎月' in text:
            return 'FREQ=MONTHLY'
        
        # 平日
        if '平日' in text:
            return 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'
        
        # 週末
        if '週末' in text:
            return 'FREQ=WEEKLY;BYDAY=SA,SU'
        
        return None
    
    async def parse_reminder_request(self, text: str, user_id: str, 
                                   channel_id: str) -> Dict[str, Any]:
        """自然言語リマインド要求の解析"""
        import re
        
        try:
            # 基本パターンマッチング
            result = {
                'what': '',
                'time': None,
                'mention': '@everyone',
                'rrule': None,
                'confidence': 0.0
            }
            
            # 時刻抽出パターン
            time_patterns = [
                (r'(\d{1,2}):(\d{2})', 'time_hhmm'),
                (r'(\d{1,2})時(\d{2})?分?', 'time_jp'),
                (r'明日(\d{1,2}時)?', 'tomorrow'),
                (r'来週(\w+)(\d{1,2}時)?', 'next_week'),
                (r'毎朝(\d{1,2}時)?', 'every_morning')
            ]
            
            # メンション抽出
            mention_patterns = {
                '@everyone': ['@everyone', '全員', 'みんな', 'みな'],
                '@mrc': ['@mrc', 'MRC', 'エムアール'],
                '@supy': ['@supy', 'SUPY', 'スーパー']
            }
            
            # メンション検出
            for mention, keywords in mention_patterns.items():
                if any(keyword in text for keyword in keywords):
                    result['mention'] = mention
                    break
            
            # 時刻解析
            now = datetime.now(JST)
            
            for pattern, ptype in time_patterns:
                match = re.search(pattern, text)
                if match:
                    if ptype == 'time_hhmm':
                        hour, minute = int(match.group(1)), int(match.group(2))
                        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # 過去の時刻なら翌日
                        if target_time <= now:
                            target_time += timedelta(days=1)
                        
                        result['time'] = target_time
                        result['confidence'] = 0.9
                        
                    elif ptype == 'time_jp':
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        if target_time <= now:
                            target_time += timedelta(days=1)
                        
                        result['time'] = target_time
                        result['confidence'] = 0.85
                        
                    elif ptype == 'tomorrow':
                        tomorrow = now + timedelta(days=1)
                        hour = int(match.group(1)[:-1]) if match.group(1) else 9  # デフォルト9時
                        result['time'] = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
                        result['confidence'] = 0.8
                        
                    elif ptype == 'every_morning':
                        hour = int(match.group(1)[:-1]) if match.group(1) else 9
                        tomorrow = now + timedelta(days=1)
                        result['time'] = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
                        result['rrule'] = 'FREQ=DAILY'
                        result['confidence'] = 0.8
                    
                    break
            
            # 内容抽出（時刻・メンション以外の部分）
            content_text = text
            for pattern, _ in time_patterns:
                content_text = re.sub(pattern, '', content_text)
            
            for mention, keywords in mention_patterns.items():
                for keyword in keywords:
                    content_text = content_text.replace(keyword, '')
            
            # クリーンアップ
            content_text = re.sub(r'(リマインド|通知|知らせて|教えて)', '', content_text)
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            result['what'] = content_text if content_text else 'リマインド'
            
            # RRULE検出
            if not result['rrule']:
                result['rrule'] = self.parse_rrule_from_japanese(text)
            
            return {
                'success': True,
                'parsed': result,
                'confidence': result['confidence']
            }
        
        except Exception as e:
            print(f"[ERROR] Parse reminder failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'confidence': 0.0
            }

# 統合リマインドシステム（ハイブリッド検出器と連携）
class IntegratedReminderSystem:
    """統合リマインドシステム - ハイブリッド検出器連携版"""
    
    def __init__(self, functions_url: str):
        self.cloud_system = CloudReminderSystem(functions_url)
    
    async def handle_reminder_from_spec(self, spec: Dict[str, Any], user_id: str,
                                      channel_id: str, message_id: str) -> Dict[str, Any]:
        """意図仕様からリマインダー処理"""
        try:
            what = spec.get('what')
            time_str = spec.get('time')  # ISO8601形式
            mention = spec.get('mention', '@everyone')
            rrule = spec.get('repeat')
            
            if not what:
                return {
                    'success': False,
                    'message': 'リマインドの内容を指定してください',
                    'response_type': 'missing_content'
                }
            
            if not time_str:
                return {
                    'success': False, 
                    'message': 'リマインドの時刻を指定してください',
                    'response_type': 'missing_time'
                }
            
            # 時刻パース
            try:
                if time_str.endswith('+09:00') or 'T' in time_str:
                    run_at = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if run_at.tzinfo is None:
                        run_at = run_at.replace(tzinfo=JST)
                else:
                    run_at = datetime.fromisoformat(time_str).replace(tzinfo=JST)
            except:
                return {
                    'success': False,
                    'message': f'時刻形式が不正です: {time_str}',
                    'response_type': 'invalid_time'
                }
            
            # リマインダー作成
            result = await self.cloud_system.create_reminder(
                user_id=user_id,
                what=what,
                run_at=run_at,
                channel_id=channel_id,
                mention=mention,
                rrule=rrule
            )
            
            return result
        
        except Exception as e:
            print(f"[ERROR] Handle reminder from spec failed: {e}")
            return {
                'success': False,
                'message': f'リマインド処理エラー: {str(e)}',
                'response_type': 'error'
            }

# 使用例とテスト
if __name__ == "__main__":
    async def test_cloud_reminder():
        """クラウドリマインドシステムテスト"""
        
        # テスト用Cloud Functions URL（実際のデプロイ後に変更）
        functions_url = "https://asia-northeast1-catherine-9e862.cloudfunctions.net"
        
        system = CloudReminderSystem(functions_url)
        integrated = IntegratedReminderSystem(functions_url)
        
        print("🧪 Cloud Reminder System Test")
        print("-" * 40)
        
        # 自然言語解析テスト
        test_texts = [
            "明日18時に@mrcでCCT送付リマインド",
            "毎朝9時に全員で朝会リマインド", 
            "15:30にミーティング準備",
            "来週月曜10時にレポート提出"
        ]
        
        for text in test_texts:
            result = await system.parse_reminder_request(text, "test_user", "test_channel")
            print(f"\n入力: {text}")
            print(f"解析: {result}")
        
        # 統合システムテスト
        spec = {
            'what': 'テストリマインド',
            'time': '2025-08-13T15:30:00+09:00',
            'mention': '@everyone'
        }
        
        integrated_result = await integrated.handle_reminder_from_spec(
            spec, "test_user", "test_channel", "msg123"
        )
        print(f"\n統合システム: {integrated_result}")
    
    print("☁️ Cloud Reminder System Ready!")
    print("🔥 Firebase + Cloud Functions + Cloud Tasks")
    print("📋 Features:")
    print("  - 時刻ぴったり発火（Cloud Tasks）")
    print("  - 自動再試行")
    print("  - RRULE繰り返し")
    print("  - 二重送信防止")
    print("  - 自然言語解析")
    
    # テスト実行
    try:
        # asyncio.run(test_cloud_reminder())
        print("\n✅ Cloud Reminder System ready (test requires deployed functions)")
    except Exception as e:
        print(f"Test requires Cloud Functions deployment: {e}")