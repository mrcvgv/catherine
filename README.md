# Catherine AI - 完全記録型Discord秘書

🧠 **絶対に忘れない**AI秘書Catherineです。全ての会話・ToDo・設定を完全記録し、パーソナライズされたサポートを提供します。

## ✨ 機能

### 🤖 基本機能
- **Discord Bot**: `C!` コマンドで操作
- **AI会話**: OpenAI GPT-4o（最新モデル）との自然な対話
- **多言語対応**: 日本語メイン、英語対応
- **24時間稼働**: Railway デプロイで常時稼働

### 🧠 完全記録機能
- **全会話記録**: ユーザーとの全やり取りをFirebaseに永続保存
- **AI分析**: 感情・満足度・話題を自動分析
- **長期記憶**: 過去の会話を活用した個人化応答
- **会話統計**: 利用状況の詳細分析

### 📝 ToDo管理（強化版）
- **全ToDo表示**: すべてのタスクを一覧表示（制限なし）
- **AI分析付きタスク管理**: 優先度・カテゴリ自動設定
- **多様なソート機能**: 優先度/締切日/カテゴリ/作成日順
- **自然言語抽出**: 会話からToDoを自動検出
- **優先度表示**: 🔥高優先度 ⚡中優先度 📌通常優先度
- **締切日管理**: 📅マーク付きで期限を可視化
- **カテゴリ分類**: work/personal/health/finance/learning/other
- **リマインダー機能**: 期限前の自動通知
- **進捗追跡**: 完了までの履歴管理

### 🎯 パーソナライゼーション
- **ユーモアレベル調整**: 0-100%で会話スタイル制御
- **会話スタイル**: カジュアル～フォーマルまで
- **個人設定記憶**: ユーザーごとの好み保存
- **適応的応答**: 過去の反応を学習

### 🎤 音声機能
- **音声認識**: Whisper APIによる高精度認識
- **音声コマンド**: ハンズフリーでの操作
- **音声ToDo作成**: 話すだけでタスク追加

## 🚀 使用方法

### 基本コマンド
```
C! [質問・会話]     - 自然な会話
C! todo [内容]      - ToDo作成
C! list             - ToDoリスト表示（全件・優先度＋締切日順）
C! list priority    - 優先度順で表示
C! list due         - 締切日順で表示
C! list category    - カテゴリ別にグループ表示
C! list recent      - 作成日順（新しい順）で表示
C! done [番号]      - ToDo完了
C! help             - ヘルプ表示
```

### 音声コマンド
```
C! join             - ボイスチャンネル参加
C! listen           - 音声認識開始
C! stop             - 音声認識停止
C! leave            - ボイスチャンネル退出
```

### 設定コマンド
```
C! humor [0-100]    - ユーモアレベル調整
C! style [casual/friendly/polite/formal/business]
C! memory stats     - 会話統計表示
C! memory topics    - よく話す話題分析
```

## 🔧 セットアップ

### 必要な環境変数
```bash
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

### ローカル実行
```bash
# 依存関係インストール
pip install -r requirements.txt

# 基本版（Firebase不要）
python main_simple.py

# 完全記録版（Firebase必要）
python main_memory_focused.py

# 全機能版（音声機能含む）
python main_with_voice.py
```

### Railway デプロイ（24時間稼働）
1. GitHubリポジトリを作成・プッシュ
2. Railway（https://railway.app）でプロジェクト作成
3. GitHubリポジトリと連携
4. 環境変数を設定:
   - `DISCORD_TOKEN`: Discord Bot トークン
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase サービスアカウントJSON
5. Settings → Deploy → Start Command: `python main_memory_focused.py`
6. Pre-deploy Command: **空にする**（npm関連は不要）

## 📊 アーキテクチャ

### ファイル構成
```
├── main_simple.py              # 基本版（Firebase不要）
├── main_memory_focused.py      # 完全記録版（推奨）
├── main_with_voice.py         # 全機能版
├── firebase_config.py         # Firebase設定
├── todo_manager.py           # ToDo管理機能
├── conversation_manager.py   # 会話記録・分析
├── voice_manager.py          # 音声認識機能
└── requirements.txt          # 依存関係
```

### データベース構造（Firestore）
```
users/          # ユーザー情報・設定
todos/          # ToDo データ
conversations/  # 会話履歴
reminders/      # リマインダー
```

## 🛡️ セキュリティ

- Firebase認証による安全なデータアクセス
- 秘密鍵の環境変数管理
- ユーザー別データ分離
- セキュリティルール適用

## 🆕 最新アップデート

### v2.0 - 完全なToDo管理
- **全ToDo表示**: 5件制限を撤廃、すべてのタスクを表示
- **高度なソート機能**: 優先度/締切日/カテゴリ/作成日順
- **視覚的優先度表示**: 🔥⚡📌アイコンで一目瞭然
- **カテゴリグループ表示**: work/personal等で整理
- **Firebase最適化**: インデックス不要のシンプルクエリ
- **GPT-4o対応**: 最新モデルでより賢い応答

### 既知の問題と解決策
- **二重回答**: Railway再起動で解決
- **ToDo保存エラー**: Firebase権限を確認
- **インデックスエラー**: 最新版では解決済み

## 📈 パフォーマンス

- **レスポンス時間**: 平均1-2秒（GPT-4o使用時）
- **同時接続**: 複数サーバー対応
- **データ保存**: Firestore による自動スケーリング
- **音声認識**: リアルタイム処理
- **ToDo処理**: 1000件以上でも高速表示

## 🔄 継続的改善

Catherine AIは以下の方法で継続的に改善されます：
- 会話品質の自動分析
- ユーザー満足度のトラッキング
- 応答パターンの最適化
- 新機能の段階的導入

## 📞 サポート

技術的な質問や機能要望は Issues でお気軽にどうぞ！

---

**Catherine AI** - あなた専用の完全記録型AI秘書 🤖✨