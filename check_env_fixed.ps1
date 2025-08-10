# 環境変数チェックスクリプト
Write-Host "Catherine AI - 環境変数確認" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Yellow

Write-Host "1. DISCORD_TOKEN:" -ForegroundColor White
if ($env:DISCORD_TOKEN) {
    Write-Host "   設定済み: $($env:DISCORD_TOKEN.Substring(0,20))..." -ForegroundColor Green
} else {
    Write-Host "   未設定" -ForegroundColor Red
}

Write-Host "2. OPENAI_API_KEY:" -ForegroundColor White  
if ($env:OPENAI_API_KEY) {
    Write-Host "   設定済み: $($env:OPENAI_API_KEY.Substring(0,20))..." -ForegroundColor Green
} else {
    Write-Host "   未設定" -ForegroundColor Red
}

Write-Host "3. FIREBASE_SERVICE_ACCOUNT_KEY:" -ForegroundColor White
if ($env:FIREBASE_SERVICE_ACCOUNT_KEY) {
    Write-Host "   設定済み: JSON形式データ" -ForegroundColor Green
} else {
    Write-Host "   未設定" -ForegroundColor Red
}

Write-Host "================================" -ForegroundColor Yellow