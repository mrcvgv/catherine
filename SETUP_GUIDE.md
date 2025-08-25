# 🚀 Catherine AI - 完全セットアップガイド

## 📋 現在の状況

**✅ 完全に動作している機能:**
- 基本TODO管理・リマインダー
- Gmail・Google Tasks
- 高度自然言語理解 (GPT-5-mini)
- エラー回復システム
- チャンネル制御

**⚠️ 設定が必要な機能:**
- Google Sheets・Docs・Drive・Calendar
- Notion統合

---

## 🔧 問題の修正手順

### 1. Google Service Account権限の修正

**現在のエラー**: `The caller does not have permission`

#### 方法A: OAuth認証に統一（推奨）

現在Gmail・TasksはOAuth認証で動作しているため、他のサービスもOAuthに統一するのが最も確実です。

```bash
# 1. 現在の認証情報を確認
grep -E "GOOGLE_(OAUTH|ACCESS|REFRESH)" .env

# 2. Google Cloud Consoleで追加のスコープを有効化
# https://console.cloud.google.com/apis/credentials にアクセス
# OAuth 2.0 クライアントIDを選択
# 承認済みのリダイレクトURIを確認: http://localhost:3000/oauth2/callback
```

**必要なスコープ**:
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/calendar`

#### 方法B: Service Account権限の修正

```bash
# 1. Google Cloud Console > IAM
# https://console.cloud.google.com/iam-admin/iam?project=catherine-470022

# 2. Service Account: catherine@catherine-470022.iam.gserviceaccount.com に以下を追加:
#    - Editor role
#    - Google Sheets API Service Agent
#    - Google Docs API Service Agent
#    - Google Drive API Service Agent

# 3. Domain-wide delegationを有効化
# Google Admin Console（管理者アクセスが必要）
# セキュリティ > API制御 > ドメイン全体の委任
# クライアントID: 105021529703540857114
# スコープ:
#   https://www.googleapis.com/auth/spreadsheets,
#   https://www.googleapis.com/auth/documents,
#   https://www.googleapis.com/auth/drive,
#   https://www.googleapis.com/auth/calendar
```

### 2. Notion統合の設定

**現在のエラー**: データベースが存在しない

```bash
# 1. Notionワークスペースにアクセス
# https://notion.so にログイン

# 2. 新しいデータベースを作成
# 「+ 新しいページ」→「データベース」→「テーブル」を選択

# 3. データベース名: "Catherine TODOs"

# 4. プロパティを以下に設定:
# | プロパティ名 | タイプ | オプション |
# |-------------|--------|------------|
# | Title | タイトル | - |
# | Status | 選択 | pending, completed, cancelled |
# | Priority | 選択 | urgent, high, normal, low |
# | Created By | テキスト | - |
# | Due Date | 日付 | - |

# 5. APIキー権限の確認
# Notionインテグレーション設定:
# https://www.notion.so/my-integrations

# 6. 作成したデータベースにインテグレーションを招待
# データベースページで「共有」→「招待」→Catherineインテグレーションを選択
```

---

## 🚀 即座に使える機能

### Gmail & Google Tasks
```
# メール確認
「メール確認して」
「メールを3通見せて」

# タスク作成  
「Googleタスクで会議準備を追加」
「タスクリストを確認して」
```

### TODO管理
```
# TODO作成
「明日までに資料作成（高優先度）」
「買い物リストを追加」

# TODO管理
「リスト」                     # 一覧表示
「1番削除」                   # 削除
「2は激高優先度に変更」        # 優先度変更
```

### リマインダー
```
「1を15時にリマインドして」
「明日の10時に会議の件で教えて」
「毎朝8:30に全リストをリマインドして」
```

---

## 🔍 動作確認方法

### Google統合テスト
```bash
# テストスクリプトを実行
node test-full-integration.js

# 期待される出力:
# ✅ Gmail接続成功 - X通のメールを確認
# ✅ Google Tasks接続成功 - タスクID: xxx
# ⚠️ Google Sheets接続失敗 - 権限エラー (設定後は✅に変わる)
```

### Discord内テスト
```
# #catherineチャンネルで
「メール確認して」
「タスクを1つ作成して」

# 成功例:
Catherine: ふふ、メールが3通あるよ
Catherine: やれやれ、Googleタスク「テスト」を作成したよ
```

---

## 🆘 トラブルシューティング

### Google API エラー
```bash
# エラー: "The caller does not have permission"
# 解決策: 上記「方法A: OAuth認証に統一」を実行

# エラー: "invalid_grant"  
# 解決策: OAuth認証を再実行
python src/google_oauth_setup.py
```

### Notion API エラー
```bash
# エラー: "Could not find database"
# 解決策: 上記Notion設定手順を実行

# エラー: "Unauthorized"
# 解決策: APIキーの権限を確認、データベースへのインテグレーション招待を確認
```

### Discord応答なし
```bash
# チャンネル設定を確認
grep CHANNEL .env

# ログを確認
railway logs --follow

# BOTの権限を確認（Discord側）
# - メッセージ送信権限
# - メッセージ履歴読み取り権限
# - メンション許可
```

---

## 🎯 設定完了後の完全機能

設定完了後、Catherineは以下の全機能を使用可能になります:

### Google Workspace完全統合
- 📧 Gmail: メール確認・検索・送信
- 📋 Tasks: タスク作成・管理・同期
- 📄 Docs: ドキュメント作成・共有・編集
- 📊 Sheets: スプレッドシート作成・データ管理
- 📁 Drive: フォルダ作成・ファイル管理
- 📅 Calendar: イベント作成・予定確認

### Notion統合
- 📝 Notion TODO同期
- 🔍 Notion検索機能
- 📊 進捗トラッキング

### 高度自然言語理解
```
# 複雑な依頼の例
「明日14時の会議用に資料をGoogleドキュメントで作成して、
共有設定にしてから、高優先度のTODOに追加して、
15分前にリマインドして」

→ Catherine が自動的に:
1. Googleドキュメント作成
2. 共有設定
3. 高優先度TODO追加  
4. リマインダー設定
5. 魔女らしいコメントで結果報告
```

---

## 📞 サポート

問題が発生した場合:
1. ログを確認: `railway logs --follow`
2. テストスクリプトを実行: `node test-full-integration.js`
3. 環境変数を確認: `cat .env | grep -E "(GOOGLE|NOTION)"`

Catherine は設定完了後、真に実用的なAIアシスタントとして機能します！