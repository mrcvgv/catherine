# Catherine AI 完全記録版起動スクリプト
Write-Host "🧠 Catherine AI - 完全記録版起動準備" -ForegroundColor Cyan

# 現在の環境変数確認
Write-Host "`n=== 環境変数チェック ===" -ForegroundColor Yellow

$discordToken = $env:DISCORD_TOKEN
$openaiKey = $env:OPENAI_API_KEY
$firebaseKey = $env:FIREBASE_SERVICE_ACCOUNT_KEY

if ($discordToken) {
    Write-Host "✓ DISCORD_TOKEN: 設定済み" -ForegroundColor Green
} else {
    Write-Host "✗ DISCORD_TOKEN: 未設定" -ForegroundColor Red
    Write-Host "設定方法: `$env:DISCORD_TOKEN='YOUR_TOKEN'" -ForegroundColor Yellow
}

if ($openaiKey) {
    Write-Host "✓ OPENAI_API_KEY: 設定済み" -ForegroundColor Green
} else {
    Write-Host "✗ OPENAI_API_KEY: 未設定" -ForegroundColor Red
    Write-Host "設定方法: `$env:OPENAI_API_KEY='sk-YOUR_KEY'" -ForegroundColor Yellow
}

if ($firebaseKey) {
    Write-Host "✓ FIREBASE_SERVICE_ACCOUNT_KEY: 設定済み" -ForegroundColor Green
} else {
    Write-Host "⚠️  FIREBASE_SERVICE_ACCOUNT_KEY: 未設定" -ForegroundColor Yellow
    Write-Host "Firebase機能は無効になります" -ForegroundColor Yellow
}

Write-Host "`n=== 起動可能バージョン ===" -ForegroundColor Yellow

if ($discordToken -and $openaiKey) {
    if ($firebaseKey) {
        Write-Host "✅ 完全記録版 (main_memory_focused.py) - 推奨" -ForegroundColor Green
        Write-Host "✅ 全機能版 (main_with_voice.py)" -ForegroundColor Green
    }
    Write-Host "✅ 基本版 (main_simple.py) - Firebase不要" -ForegroundColor Green
} else {
    Write-Host "❌ 環境変数の設定が必要です" -ForegroundColor Red
}

Write-Host "`n=== 起動コマンド ===" -ForegroundColor Yellow
Write-Host "python main_simple.py        # 基本版（Firebase不要）"
Write-Host "python main_memory_focused.py # 完全記録版（推奨）"
Write-Host "python main_with_voice.py     # 全機能版"

Write-Host "`n準備が完了したら上記コマンドで起動してください！" -ForegroundColor Cyan