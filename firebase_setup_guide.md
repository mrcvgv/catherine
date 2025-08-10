# Firebase設定ガイド

## ステップ1: Firebaseプロジェクト作成

1. [Firebase Console](https://console.firebase.google.com/) にアクセス
2. 「プロジェクトを追加」をクリック
3. プロジェクト名を入力（例: `catherine-ai-secretary`）
4. 「続行」をクリックして作成

## ステップ2: Firestoreデータベース作成

1. Firebase Console > 「Firestore Database」
2. 「データベースの作成」をクリック
3. **テストモードで開始**を選択（開発時）
4. ロケーション: `asia-northeast1 (Tokyo)` を選択
5. 「完了」

## ステップ3: サービスアカウント設定

1. Firebase Console > 「プロジェクトの設定」（⚙️アイコン）
2. 「サービスアカウント」タブをクリック
3. 「新しい秘密鍵の生成」をクリック
4. JSONファイルがダウンロードされます

## ステップ4: 環境変数設定

### Windowsの場合:
```powershell
# PowerShellで実行
$env:FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "YOUR_PROJECT_ID", ...}'
```

### より簡単な方法 - .envファイル:
```bash
# .envファイルを作成
FIREBASE_SERVICE_ACCOUNT_KEY={"type": "service_account", "project_id": "catherine-ai-secretary", "private_key_id": "...", "private_key": "...", "client_email": "...", "client_id": "...", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}
```

## ステップ5: テスト実行

```bash
python test_firebase.py
```

## Railway等でのデプロイ時

1. Railway Dashboard > Variables
2. Add Variable:
   - Key: `FIREBASE_SERVICE_ACCOUNT_KEY`
   - Value: （ダウンロードしたJSONファイルの内容全体）

## セキュリティルール（推奨）

Firestore > Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true; // 開発時のみ
      // 本番環境では認証付きルールに変更
    }
  }
}
```

## トラブルシューティング

### 文字化けエラー
- Windows環境では文字エンコーディングの問題が発生する場合があります
- 環境変数設定時に特殊文字を避けてください

### 接続エラー
- プロジェクトIDが正しいか確認
- サービスアカウントJSONが完全か確認
- ネットワーク接続を確認