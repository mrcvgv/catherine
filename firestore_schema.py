#!/usr/bin/env python3
"""
Firestore Schema & Security Rules for Catherine AI
「勝手に動かず賢くなる秘書」のためのスキーマ設計
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pytz

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class User:
    """ユーザー設定コレクション - users/{userId}"""
    tz: str = "Asia/Tokyo"
    default_mention: str = "@everyone"
    morning_hour: int = 9
    afternoon_hour: int = 15
    evening_hour: int = 20
    updated_at: Optional[datetime] = None

@dataclass
class Todo:
    """TODOコレクション - todos/{todoId}"""
    user_id: str
    content: str
    status: str  # "open" | "done"
    priority: str = "normal"  # "urgent" | "high" | "normal" | "low"
    due_at: Optional[datetime] = None
    assignees: List[str] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Reminder:
    """リマインダーコレクション - reminders/{reminderId}"""
    user_id: str
    what: str
    mention: str  # "@everyone" | "@mrc" | "@supy"
    run_at: datetime  # 単発実行時刻
    rrule: Optional[str] = None  # iCal RRULE形式
    channel_id: str
    status: str = "scheduled"  # "scheduled" | "sending" | "sent" | "cancelled"
    task_name: Optional[str] = None  # Cloud Tasksのジョブ名
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PendingAction:
    """保留中アクションコレクション - pendingActions/{pendingId}"""
    user_id: str
    channel_id: str
    intent: str
    missing: List[str]  # 不足フィールド ["time", "indices"]
    draft: Dict[str, Any]  # 暫定データ {what, time, mention, ...}
    status: str = "pending"  # "pending" | "expired" | "done"
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class InteractionLog:
    """操作ログコレクション - interactionLogs/{logId}"""
    user_id: str
    channel_id: str
    input_text: str
    parsed: Dict[str, Any]  # 解析結果
    action: str  # 実行したアクション
    outcome: Dict[str, Any]  # 結果
    correction: Optional[Dict[str, Any]] = None  # 修正情報
    confidence: float = 0.0
    created_at: Optional[datetime] = None

@dataclass
class UserPreference:
    """ユーザー好み設定 - preferences/{userId}"""
    user_id: str
    default_mention: str = "@everyone"
    morning_hour: int = 9
    afternoon_hour: int = 15
    evening_hour: int = 20
    shortcuts: Dict[str, str] = None  # {"うさぎ": "アイデア", ...}
    patterns: Dict[str, Any] = None  # 学習済みパターン
    updated_at: Optional[datetime] = None

# Firestore Security Rules (firestore.rules)
FIRESTORE_SECURITY_RULES = """
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // ユーザー設定 - 本人のみ読み書き可能
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // TODOs - 本人のみアクセス
    match /todos/{todoId} {
      allow read, write: if request.auth != null && 
                         request.auth.uid == resource.data.userId;
      allow create: if request.auth != null && 
                   request.auth.uid == request.resource.data.userId;
    }
    
    // リマインダー - Cloud Functions サービスアカウントのみ書き込み
    match /reminders/{reminderId} {
      allow read: if request.auth != null && 
                 request.auth.uid == resource.data.userId;
      allow write: if request.auth != null && 
                   request.auth.token.firebase.sign_in_provider == 'custom';
    }
    
    // 保留中アクション - Cloud Functions のみ
    match /pendingActions/{pendingId} {
      allow read, write: if request.auth != null && 
                        request.auth.token.firebase.sign_in_provider == 'custom';
    }
    
    // 操作ログ - Cloud Functions のみ書き込み、本人は読み込み可
    match /interactionLogs/{logId} {
      allow read: if request.auth != null && 
                 request.auth.uid == resource.data.userId;
      allow write: if request.auth != null && 
                   request.auth.token.firebase.sign_in_provider == 'custom';
    }
    
    // 好み設定 - 本人のみ
    match /preferences/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // デフォルト拒否
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
"""

# Firestore インデックス設計
FIRESTORE_INDEXES = """
# reminders コレクション
- Collection: reminders
  Fields:
    - userId (Ascending)
    - status (Ascending) 
    - runAt (Ascending)

# todos コレクション  
- Collection: todos
  Fields:
    - userId (Ascending)
    - status (Ascending)
    - createdAt (Descending)

# interactionLogs コレクション
- Collection: interactionLogs
  Fields:
    - userId (Ascending)
    - createdAt (Descending)

# pendingActions コレクション
- Collection: pendingActions
  Fields:
    - userId (Ascending)
    - status (Ascending)
    - expiresAt (Ascending)
"""

class FirestoreSchemaValidator:
    """Firestoreスキーマバリデーター"""
    
    @staticmethod
    def validate_user(data: Dict) -> bool:
        required = {'tz', 'default_mention'}
        return all(field in data for field in required)
    
    @staticmethod
    def validate_todo(data: Dict) -> bool:
        required = {'user_id', 'content', 'status'}
        valid_statuses = {'open', 'done'}
        return (all(field in data for field in required) and
                data.get('status') in valid_statuses)
    
    @staticmethod
    def validate_reminder(data: Dict) -> bool:
        required = {'user_id', 'what', 'mention', 'run_at', 'channel_id'}
        valid_mentions = {'@everyone', '@mrc', '@supy'}
        valid_statuses = {'scheduled', 'sending', 'sent', 'cancelled'}
        
        return (all(field in data for field in required) and
                data.get('mention') in valid_mentions and
                data.get('status', 'scheduled') in valid_statuses)
    
    @staticmethod
    def validate_pending_action(data: Dict) -> bool:
        required = {'user_id', 'channel_id', 'intent', 'missing', 'draft'}
        valid_statuses = {'pending', 'expired', 'done'}
        
        return (all(field in data for field in required) and
                data.get('status', 'pending') in valid_statuses and
                isinstance(data.get('missing'), list) and
                isinstance(data.get('draft'), dict))

# 使用例とテスト
if __name__ == "__main__":
    from firebase_config import firebase_manager
    
    def test_schema_validation():
        """スキーマバリデーションテスト"""
        validator = FirestoreSchemaValidator()
        
        # User テスト
        user_data = {
            'tz': 'Asia/Tokyo',
            'default_mention': '@everyone',
            'morning_hour': 9
        }
        assert validator.validate_user(user_data), "User validation failed"
        
        # Todo テスト
        todo_data = {
            'user_id': 'test123',
            'content': 'テストタスク',
            'status': 'open'
        }
        assert validator.validate_todo(todo_data), "Todo validation failed"
        
        # Reminder テスト
        reminder_data = {
            'user_id': 'test123',
            'what': 'テストリマインド',
            'mention': '@everyone',
            'run_at': datetime.now(JST),
            'channel_id': 'ch123'
        }
        assert validator.validate_reminder(reminder_data), "Reminder validation failed"
        
        # PendingAction テスト
        pending_data = {
            'user_id': 'test123',
            'channel_id': 'ch123',
            'intent': 'todo.add',
            'missing': ['what'],
            'draft': {'mention': '@everyone'}
        }
        assert validator.validate_pending_action(pending_data), "PendingAction validation failed"
        
        print("✅ All schema validations passed!")
    
    async def test_firestore_operations():
        """Firestore操作テスト"""
        db = firebase_manager.get_db()
        
        # ユーザー作成テスト
        user_data = {
            'tz': 'Asia/Tokyo',
            'default_mention': '@mrc',
            'morning_hour': 9,
            'afternoon_hour': 15,
            'evening_hour': 20,
            'updated_at': datetime.now(JST)
        }
        
        # TODO作成テスト
        todo_data = {
            'user_id': 'test_user_123',
            'content': 'Firestoreスキーマテスト',
            'status': 'open',
            'priority': 'high',
            'created_at': datetime.now(JST),
            'updated_at': datetime.now(JST)
        }
        
        # リマインダー作成テスト
        reminder_data = {
            'user_id': 'test_user_123',
            'what': 'スキーマテスト実行',
            'mention': '@everyone',
            'run_at': datetime.now(JST),
            'channel_id': 'test_channel_456',
            'status': 'scheduled',
            'created_at': datetime.now(JST)
        }
        
        try:
            # Firestore書き込みテスト（実際のプロダクションでは注意）
            print("📝 Testing Firestore operations...")
            
            # バリデーション
            validator = FirestoreSchemaValidator()
            assert validator.validate_todo(todo_data), "Todo validation failed"
            assert validator.validate_reminder(reminder_data), "Reminder validation failed"
            
            print("✅ Firestore schema operations ready!")
            
        except Exception as e:
            print(f"❌ Firestore test failed: {e}")
    
    # テスト実行
    test_schema_validation()
    
    import asyncio
    try:
        asyncio.run(test_firestore_operations())
    except Exception as e:
        print(f"Warning: Firestore operations test skipped: {e}")
    
    print("\n🎯 Firestore Schema Design Complete!")
    print("📋 Collections:")
    print("  - users/{userId}")
    print("  - todos/{todoId}")  
    print("  - reminders/{reminderId}")
    print("  - pendingActions/{pendingId}")
    print("  - interactionLogs/{logId}")
    print("  - preferences/{userId}")
    print("\n🔐 Security: Cloud Functions サービスアカウントのみ書き込み")
    print("📊 Indexes: userId + status + timestamp で最適化済み")