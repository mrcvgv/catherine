# Railway デプロイ手順

## 🚂 Catherine AI をRailwayにデプロイ

### ステップ1: Railway プロジェクト作成
1. https://railway.app/ にアクセス
2. GitHubアカウントでサインイン
3. 「New Project」→「Deploy from GitHub repo」
4. `mrcvgv/catherine` を選択

### ステップ2: 環境変数設定
Railway Dashboard > Variables で以下を設定：

#### 必須環境変数
```bash
# Discord Bot Token
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN

# OpenAI API Key  
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY

# Firebase Service Account Key (JSON形式 - 1行で)
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"catherine-9e862","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"firebase-adminsdk-xxxxx@catherine-9e862.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}

# ポート設定（Railway用）
PORT=8080
```

### ステップ3: 起動コマンド設定
Railway Dashboard > Settings > Deploy:
```bash
Start Command: python main_memory_focused.py
```

### ステップ4: デプロイ実行
1. 「Deploy」ボタンをクリック
2. ビルドログを確認
3. 成功すると緑色の「Active」表示

### ステップ5: 動作確認
ログで以下が表示されれば成功：
```
INFO: Using Firebase key from environment variable
SUCCESS: Firebase initialized successfully  
🧠 Catherine AI - 完全記録版 起動完了
📚 Firebase記録機能: ✅ 有効
👤 ログイン: Catherine#1234
```

## 🔧 トラブルシューティング

### よくあるエラー
1. **Discord Token エラー**: DISCORD_TOKEN の値を確認
2. **OpenAI エラー**: OPENAI_API_KEY の値を確認  
3. **Firebase エラー**: FIREBASE_SERVICE_ACCOUNT_KEY のJSON形式を確認

### Firebase Service Account Key の注意点
- JSONは1行で設定（改行なし）
- `"` や `\` はエスケープ不要
- private_key 内の `\n` は `\\n` にする

### ログ確認方法
Railway Dashboard > Deployments > View Logs

## 🎉 デプロイ成功後
Catherine AI がDiscordで利用可能になります！

### テストコマンド
```
C! hello          # 基本会話テスト
C! memory stats   # Firebase接続確認
C! todo test      # ToDo機能確認
```

---
🤖 **完全記録型AI秘書Catherine** - Railway上で24/7稼働中！