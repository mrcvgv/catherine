# Catherine Railway Deployment Guide

## Current Status
- ✅ GPT-5-mini model configured
- ✅ MCP integration (Notion + Google) implemented
- ✅ Google Drive folder connected
- ✅ Notion as primary TODO storage
- ✅ Google Calendar for reminders

## Pre-deployment Checklist

### 1. Environment Variables (.env)
All required variables are set:
- `DISCORD_BOT_TOKEN` ✅
- `OPENAI_API_KEY` ✅
- `NOTION_API_KEY` ✅
- `GOOGLE_SERVICE_ACCOUNT_KEY` ✅
- `GOOGLE_CALENDAR_ID` ✅
- `GOOGLE_DRIVE_FOLDER_ID` ✅
- `MCP_SERVERS` ✅

### 2. Dependencies
Required packages in requirements.txt:
```
discord.py>=2.3.2
openai>=1.2.0
python-dotenv>=1.0.0
PyYAML>=6.0.2
dacite>=1.8.0
firebase-admin>=6.5.0
pytz>=2023.3
python-dateutil>=2.8.0
```

### 3. MCP Servers
Node.js MCP servers ready:
- `mcp/notion/server.js` - Notion integration
- `mcp/google/server.js` - Google services (Calendar, Drive, Sheets, Gmail)

## Railway Deployment Steps

### 1. Push to GitHub
```bash
git add -A
git commit -m "✨ Complete MCP integration with Notion and Google services"
git push origin master
```

### 2. Railway Configuration
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Ensure Node.js buildpack is detected (for MCP servers)

### 3. Railway.json Configuration
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python src/main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### 4. Post-deployment Testing

Test these commands in Discord:
1. **TODO Creation**: `@Catherine TODO: テストタスク を作成`
2. **TODO List**: `@Catherine TODOリストを見せて`
3. **Calendar**: `@Catherine 今後の予定は？`
4. **Reminder**: `@Catherine 明日10時に会議をリマインドして`
5. **Drive**: `@Catherine Googleドライブのファイルを確認して`

## Monitoring

### Check Railway Logs
```bash
railway logs
```

### Expected Startup Logs
```
INFO: Starting Catherine Discord Bot...
INFO: MCP Bridge initialized
INFO: Started MCP server: notion
INFO: Started MCP server: google
INFO: Discord bot connected as Catherine#XXXX
INFO: Ready to serve!
```

## Troubleshooting

### Issue: MCP servers not starting
**Solution**: Check Node.js is installed in Railway environment
```bash
railway run node --version
```

### Issue: Google API errors
**Solution**: Verify Service Account permissions:
- Google Calendar API enabled
- Google Drive API enabled
- Google Sheets API enabled
- Gmail API enabled

### Issue: Notion API errors
**Solution**: Check Notion integration has access to workspace

## Features Summary

### 1. Enhanced Intelligence
- GPT-5-mini model for better understanding
- Optimized temperature (0.7) for balanced responses
- Simplified system prompt for clarity

### 2. TODO Management
- Primary storage in Notion database
- Automatic sync with Google Calendar for due dates
- Priority levels and status tracking

### 3. Calendar Integration
- Event creation with reminders
- Schedule viewing
- Time parsing (明日10時, 30分後, etc.)

### 4. Google Drive
- File upload/download
- Folder creation
- File listing from connected folder

### 5. Context Management
- User preferences stored in Firebase
- Conversation history tracking
- Important context preservation

## Success Indicators
✅ Bot responds to messages
✅ TODOs appear in Notion
✅ Calendar events are created
✅ Drive operations work
✅ Response time < 3 seconds

## Next Steps (Optional)
- Add voice channel support
- Implement advanced NLP patterns
- Create dashboard for analytics
- Add multi-language support