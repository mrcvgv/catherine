# Firestore API 有効化手順

## 🔑 認証成功！
JSONファイルからの秘密鍵読み込みは成功しました。

## 🔧 次に必要な作業
Firestore APIを有効化してください：

### 方法1: Firebase Console（推奨）
1. https://console.firebase.google.com/project/catherine-9e862 にアクセス
2. 「Firestore Database」をクリック
3. 「データベースの作成」
4. **「テストモードで開始」**を選択（重要！）
5. ロケーション: 「asia-southeast1 (Singapore)」を選択
6. 「完了」

### 方法2: 直接API有効化
https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=catherine-9e862

## ✅ 完了後のテスト
```bash
python test_firebase.py
```

成功すると以下が表示されます：
```
SUCCESS: Firebase connection established!
SUCCESS: Firestore database accessible
SUCCESS: Data write test passed
SUCCESS: Data read test passed
SUCCESS: Test data cleanup completed
```

## 🗑️ セキュリティ対策
APIが有効になったら、JSONファイルは削除推奨：
```bash
del catherine-9e862-firebase-adminsdk-fbsvc-28368629ce.json
```
（削除前にバックアップを取っておくことをお勧めします）