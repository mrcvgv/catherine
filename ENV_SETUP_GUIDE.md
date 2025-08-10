# 完全記録版 Catherine AI - 環境変数設定ガイド

## 🎯 必要な環境変数（3個）

### 1. DISCORD_TOKEN
### 2. OPENAI_API_KEY  
### 3. FIREBASE_SERVICE_ACCOUNT_KEY

---

## 📋 ステップ1: Discord Bot Token取得

### Discord Developer Portal での作業
1. **https://discord.com/developers/applications** にアクセス
2. 「New Application」をクリック
3. アプリ名入力（例：Catherine AI）
4. 左サイドバーで「Bot」をクリック
5. 「Add Bot」→「Yes, do it!」
6. **TOKEN**をコピー（例：MTIzNDU2Nzg5MDEyMzQ1Njc4OTA.GhIjKl.MnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWx）

### Discord サーバーに招待
1. 左サイドバーで「OAuth2」→「URL Generator」
2. SCOPES: 「bot」にチェック
3. BOT PERMISSIONS: 「Send Messages」「Read Messages」「Use Slash Commands」
4. 生成されたURLでDiscordサーバーに招待

---

## 🔑 ステップ2: OpenAI API Key取得

### OpenAI Platform での作業
1. **https://platform.openai.com/api-keys** にアクセス
2. アカウント作成・ログイン
3. 「Create new secret key」をクリック
4. **API Key**をコピー（例：sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQR）

### ⚠️ 注意
- API使用料金が発生します（通常月数ドル程度）
- クレジットカード登録が必要

---

## 🔥 ステップ3: Firebase Service Account Key取得

### 既に取得済みの場合
先ほどダウンロードしたJSONファイルの内容をコピーしてください。

### まだの場合
1. **https://console.firebase.google.com/project/catherine-9e862**
2. ⚙️「プロジェクトの設定」
3. 「サービスアカウント」タブ  
4. 「新しい秘密鍵の生成」
5. ダウンロードしたJSONファイルを開いてコピー

---

## 💻 ステップ4: PowerShell で環境変数設定

### PowerShell を管理者権限で起動
1. Windowsキー + X
2. 「Windows PowerShell (管理者)」

### 環境変数を設定（以下をコピペして実行）

```powershell
# Discord Bot Token設定
$env:DISCORD_TOKEN="MTIzNDU2Nzg5MDEyMzQ1Njc4OTA.GhIjKl.MnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWx"

# OpenAI API Key設定  
$env:OPENAI_API_KEY="sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQR"

# Firebase Service Account Key設定（1行で！）
$env:FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"catherine-9e862","private_key_id":"abc123def456","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n","client_email":"firebase-adminsdk-xxxxx@catherine-9e862.iam.gserviceaccount.com","client_id":"123456789012345678901","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40catherine-9e862.iam.gserviceaccount.com"}'
```

### ⚠️ 重要な注意点
- 上記は**サンプル値**です - **実際の値に置き換えてください**
- Firebase JSONは**改行なしの1行**で設定
- `'` (シングルクォート) で囲む
- 各値は**ダブルクォート**内に

---

## ✅ ステップ5: 設定確認

```powershell
# 設定確認
echo $env:DISCORD_TOKEN
echo $env:OPENAI_API_KEY  
echo $env:FIREBASE_SERVICE_ACCOUNT_KEY
```

全て値が表示されればOK！

---

## 🚀 ステップ6: Catherine AI起動

```powershell
cd "C:\Users\ko\Downloads\catherine on railway"
python main_memory_focused.py
```

### 成功時の表示
```
INFO: Using Firebase key from environment variable
SUCCESS: Firebase initialized successfully
🧠 Catherine AI - 完全記録版 起動完了
📚 Firebase記録機能: ✅ 有効
👤 ログイン: Catherine#1234
```

---

## 🎭 使用可能コマンド

```
C! humor 85           # ユーモア85%設定
C! style casual       # カジュアル会話
C! todo 買い物         # ToDo追加
C! list              # ToDoリスト
C! memory stats      # 会話統計
C! help              # ヘルプ
```

---

## 🔧 トラブルシューティング

### エラー1: Discord Token Invalid
→ Discord Developer Portal で新しいTokenを生成

### エラー2: OpenAI API Error
→ API Key の確認、課金設定の確認

### エラー3: Firebase Error  
→ JSON形式の確認、改行の除去

### 環境変数が消える場合
PowerShellを再起動すると消えます。永続化したい場合：
```powershell
[System.Environment]::SetEnvironmentVariable("DISCORD_TOKEN", "YOUR_VALUE", "User")
```

準備できましたか？一緒に設定していきましょう！