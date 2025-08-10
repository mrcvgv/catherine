# FIREBASE_SERVICE_ACCOUNT_KEY 取得手順

## ステップ1: Firebaseプロジェクト作成

1. **Firebase Console にアクセス**
   - https://console.firebase.google.com/
   - Googleアカウントでログイン

2. **新しいプロジェクトを作成**
   - 「プロジェクトを追加」をクリック
   - プロジェクト名: `catherine-ai-bot` （任意）
   - Google Analytics: 「今は設定しない」でOK
   - 「プロジェクトを作成」

## ステップ2: Firestoreデータベース設定

1. **Firestoreを有効化**
   - プロジェクト画面で「Firestore Database」をクリック
   - 「データベースの作成」

2. **セキュリティルール選択**
   - 「テストモードで開始」を選択（開発時）
   - 「次へ」

3. **ロケーション選択**
   - `asia-northeast1 (Tokyo)` を選択
   - 「完了」

## ステップ3: サービスアカウントキー取得 ⭐

1. **プロジェクト設定に移動**
   - 左上の⚙️（歯車アイコン）をクリック
   - 「プロジェクトの設定」を選択

2. **サービスアカウントタブ**
   - 「サービスアカウント」タブをクリック
   - 下にスクロール

3. **新しい秘密鍵を生成**
   - 「新しい秘密鍵の生成」ボタンをクリック
   - 確認ダイアログで「キーを生成」

4. **JSONファイルダウンロード**
   - 自動的に `.json` ファイルがダウンロードされます
   - ファイル名例: `catherine-ai-bot-firebase-adminsdk-xxxxx-xxxxxxxxxx.json`

## ステップ4: JSONファイルの内容確認

ダウンロードしたJSONファイルを開くと、以下のような内容が含まれています：

```json
{
  "type": "service_account",
  "project_id": "catherine-ai-bot",
  "private_key_id": "abcd1234...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@catherine-ai-bot.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40catherine-ai-bot.iam.gserviceaccount.com"
}
```

## ステップ5: 環境変数に設定

### Windows PowerShell:
```powershell
# JSONファイル全体を1行にして設定
$env:FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "catherine-ai-bot", "private_key_id": "abcd1234...", "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----\n", "client_email": "firebase-adminsdk-xxxxx@catherine-ai-bot.iam.gserviceaccount.com", ...}'
```

### より簡単な方法 - .envファイル:
```bash
# プロジェクトフォルダに .env ファイルを作成
FIREBASE_SERVICE_ACCOUNT_KEY={"type": "service_account", "project_id": "catherine-ai-bot", ...}
```

## ⚠️ 重要な注意点

1. **秘密鍵の取り扱い**
   - JSONファイルは秘密情報です
   - GitHubなどにアップロードしないでください
   - .gitignore に追加推奨

2. **改行の処理**
   - private_key内の `\n` は改行文字として保持
   - 環境変数設定時に改行を削除しないでください

3. **特殊文字のエスケープ**
   - JSON内の `"` や `\` に注意
   - PowerShellでは `'` (シングルクォート) で囲むと安全

## テスト実行

設定完了後、以下でテスト：
```bash
python test_firebase.py
```

成功すると：
```
SUCCESS: Firebase connection established!
SUCCESS: Firestore database accessible
SUCCESS: Data write test passed
SUCCESS: Data read test passed: {'message': 'Hello from Catherine!', 'timestamp': 'test'}
SUCCESS: Test data cleanup completed
```