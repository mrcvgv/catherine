# 完全外部API管理システム設計

## 基本方針
**メモリ/ローカル管理を完全廃止し、全てをNotion + Google APIで管理**

## アーキテクチャ

### 🗂️ **データストレージ**

#### **Notion Database: "Catherine_Reminders"**
```
- reminder_id (タイトル): 一意ID
- message (リッチテキスト): リマインダーメッセージ
- calendar_event_id (テキスト): Google Calendar Event ID
- remind_time (日付): リマインド時刻
- mention_target (セレクト): everyone, here, username
- channel_target (テキスト): catherine, todo, general
- status (セレクト): scheduled, completed, cancelled
- created_by (テキスト): Discord User ID
- created_at (作成日時): 作成日時
- executed_at (日付): 実行日時
```

#### **Google Calendar: "Catherine Reminders"**
```
- イベントタイトル: [Catherine] {message}
- 開始時間: remind_time
- 終了時間: remind_time + 5分
- 説明: JSON形式でメタデータ保存
  {
    "reminder_id": "rem_12345",
    "mention_target": "everyone", 
    "channel_target": "catherine",
    "discord_user": "123456789"
  }
```

### 🔄 **処理フロー**

#### **1. リマインダー作成**
```python
async def create_external_reminder(message, remind_time, mention_target, channel_target, user_id):
    # 1. Notion Database にレコード作成
    notion_record = await notion.create_reminder_record(
        message=message,
        remind_time=remind_time,
        mention_target=mention_target,
        channel_target=channel_target,
        created_by=user_id,
        status="scheduled"
    )
    
    # 2. Google Calendar にイベント作成
    calendar_event = await google_calendar.create_event(
        title=f"[Catherine] {message}",
        start_time=remind_time,
        end_time=remind_time + timedelta(minutes=5),
        description=json.dumps({
            "reminder_id": notion_record.id,
            "mention_target": mention_target,
            "channel_target": channel_target,
            "discord_user": user_id
        })
    )
    
    # 3. Notion に calendar_event_id を更新
    await notion.update_reminder_record(
        notion_record.id,
        calendar_event_id=calendar_event.id
    )
    
    return notion_record.id
```

#### **2. 定期チェック (5分間隔)**
```python
async def check_pending_reminders():
    # 1. Google Calendar から近い未来のCatherineイベント取得
    now = datetime.now()
    upcoming_events = await google_calendar.get_events(
        time_min=now,
        time_max=now + timedelta(minutes=15),
        q="[Catherine]"
    )
    
    # 2. 実行時刻に到達したものを処理
    for event in upcoming_events:
        if event.start <= now <= event.start + timedelta(minutes=5):
            await execute_reminder(event)
```

#### **3. リマインダー実行**
```python
async def execute_reminder(calendar_event):
    # 1. イベントからメタデータ抽出
    metadata = json.loads(calendar_event.description)
    reminder_id = metadata["reminder_id"]
    
    # 2. Notion からフル情報取得
    notion_record = await notion.get_reminder(reminder_id)
    
    # 3. Discord通知送信
    await send_discord_notification(
        message=notion_record.message,
        mention_target=notion_record.mention_target,
        channel_target=notion_record.channel_target
    )
    
    # 4. 後処理
    # Calendar イベント削除
    await google_calendar.delete_event(calendar_event.id)
    
    # Notion ステータス更新
    await notion.update_reminder_record(
        reminder_id,
        status="completed",
        executed_at=datetime.now()
    )
```

### 🛠️ **実装コンポーネント**

#### **ExternalReminderManager**
```python
class ExternalReminderManager:
    """完全外部API管理のリマインダーシステム"""
    
    def __init__(self, notion_integration, google_services, discord_bot):
        self.notion = notion_integration
        self.google = google_services  
        self.bot = discord_bot
        
    async def create_reminder(self, ...): # 上記フロー実装
    async def check_reminders(self): # 定期チェック
    async def execute_reminder(self, ...): # 実行
    async def list_active_reminders(self): # 一覧
    async def cancel_reminder(self, reminder_id): # キャンセル
```

### 📊 **メリット**

#### **✅ 完全な永続化**
- Railway再起動、サーバークラッシュ無関係
- データ消失リスク完全排除

#### **✅ 可視化・管理性**
- Notion: リマインダー一覧、履歴、編集
- Google Calendar: 時系列表示、通知設定

#### **✅ 冗長性**
- Notion停止 → Google Calendarから復元可能
- Google停止 → Notion Databaseから状況確認

#### **✅ 拡張性**
- 新機能追加がデータベーススキーマ変更のみ
- 複数Botインスタンスでの共有可能

#### **✅ デバッグ性**
- 全履歴がNotionに残る
- Calendar UIでリアルタイム確認

### 🔄 **移行計画**

#### **Phase 1: 外部システム構築**
1. Notion Database "Catherine_Reminders" 作成
2. ExternalReminderManager 実装
3. Google Calendar統合

#### **Phase 2: 統合**
1. unified_message_handler を外部システムに切り替え
2. テスト・デバッグ

#### **Phase 3: 旧システム削除**  
1. flexible_reminder_system.py 削除
2. scheduler_system.py 削除
3. reminder_system.py 削除
4. メモリベースコード完全削除

## 実装優先度: 🔥 HIGH
現在のメモリベースは本格運用には不適切