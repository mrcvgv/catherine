# Firebase環境変数設定スクリプト (PowerShell)
# 使用方法: PowerShellでこのスクリプトを実行

Write-Host "Catherine AI - Firebase環境変数設定" -ForegroundColor Cyan

# 必要な環境変数をチェック
$discordToken = $env:DISCORD_TOKEN
$openaiKey = $env:OPENAI_API_KEY
$firebaseKey = $env:FIREBASE_SERVICE_ACCOUNT_KEY

Write-Host "`n=== 現在の環境変数状況 ===" -ForegroundColor Yellow

if ($discordToken) {
    Write-Host "✓ DISCORD_TOKEN: 設定済み" -ForegroundColor Green
} else {
    Write-Host "✗ DISCORD_TOKEN: 未設定" -ForegroundColor Red
}

if ($openaiKey) {
    Write-Host "✓ OPENAI_API_KEY: 設定済み" -ForegroundColor Green
} else {
    Write-Host "✗ OPENAI_API_KEY: 未設定" -ForegroundColor Red
}

if ($firebaseKey) {
    Write-Host "✓ FIREBASE_SERVICE_ACCOUNT_KEY: 設定済み" -ForegroundColor Green
} else {
    Write-Host "✗ FIREBASE_SERVICE_ACCOUNT_KEY: 未設定" -ForegroundColor Red
}

Write-Host "`n=== 設定手順 ===" -ForegroundColor Yellow
Write-Host "1. Discord Developer Portal でBot Tokenを取得"
Write-Host "2. OpenAI でAPI Keyを取得"
Write-Host "3. Firebase Console でService Account Keyを取得"

Write-Host "`n=== 環境変数設定例 ===" -ForegroundColor Yellow
Write-Host '$env:DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"'
Write-Host '$env:OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY"'
Write-Host '$env:FIREBASE_SERVICE_ACCOUNT_KEY=''{"type": "service_account", "project_id": "..."}'''

Write-Host "`n設定後、以下のコマンドでテスト:" -ForegroundColor Green
Write-Host "python test_firebase.py"