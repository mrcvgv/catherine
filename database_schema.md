# Catherine AI秘書 - データベース設計

## Firebase Firestore Collections

### 1. `users` コレクション
```json
{
  "user_id": "discord_user_id",
  "username": "Discord表示名",
  "created_at": "2024-01-01T00:00:00Z",
  "last_active": "2024-01-01T12:00:00Z",
  "preferences": {
    "timezone": "Asia/Tokyo",
    "reminder_frequency": "daily",
    "ai_auto_categorize": true,
    "default_priority": 3
  }
}
```

### 2. `todos` コレクション
```json
{
  "todo_id": "auto_generated_uuid",
  "user_id": "discord_user_id",
  "title": "資料を作成する",
  "description": "来週のプレゼン用の資料を作成",
  "status": "pending", // pending, in_progress, completed, cancelled
  "priority": 4, // 1-5 (AI自動設定)
  "category": "work", // AI自動分類
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "due_date": "2024-01-08T23:59:59Z",
  "metadata": {
    "ai_confidence": 0.95,
    "extracted_entities": ["プレゼン", "資料"],
    "estimated_duration": "2 hours",
    "tags": ["urgent", "work"]
  }
}
```

### 3. `reminders` コレクション
```json
{
  "reminder_id": "auto_generated_uuid",
  "todo_id": "related_todo_id",
  "user_id": "discord_user_id",
  "remind_at": "2024-01-07T09:00:00Z",
  "type": "due_soon", // due_soon, overdue, weekly_review
  "sent": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 4. `conversations` コレクション
```json
{
  "conversation_id": "auto_generated_uuid",
  "user_id": "discord_user_id",
  "message": "明日までに資料作成しないと",
  "response": "承知いたしました。「資料作成」のToDoを優先度4で登録いたします。",
  "ai_analysis": {
    "intent": "create_todo",
    "entities": {
      "task": "資料作成",
      "deadline": "明日"
    },
    "confidence": 0.92
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 主要機能

### AI機能
- **自動ToDo抽出**: 自然言語から作業を抽出
- **自動分類**: work, personal, urgent, routine等
- **優先度自動設定**: 緊急度と重要度を分析
- **期限認識**: 「明日まで」「来週」等の時間表現を解析

### リマインダー機能
- **期限前通知**: 24時間前、1時間前
- **遅延アラート**: 期限超過時の警告
- **週次レビュー**: 未完了タスクの整理提案
