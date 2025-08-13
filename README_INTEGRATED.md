# Catherine AI Integrated Version 2.0

## 🌟 Overview
Catherine AI Integrated combines the best features from multiple open-source Discord bots with advanced TODO management, creating a powerful and versatile Discord assistant.

## ✨ Features

### 🤖 AI Conversation
- **Multiple AI Providers**: OpenAI (GPT-4o), Claude, Gemini support
- **Context Management**: Maintains conversation history per user/channel
- **Smart Responses**: Natural conversation in English and Japanese
- **Slash Commands**: Modern Discord slash command support

### 📋 TODO Management
- **Natural Language**: "todoいれて", "リスト出して", "3削除して"
- **Bulk Operations**: Delete/complete multiple items at once
- **Edit Support**: "3の内容は、新しいタスクです。変更して"
- **Firebase Integration**: Persistent storage across sessions

### 🎯 Intent Detection
- **Japanese Support**: Full Japanese command recognition
- **Number Parsing**: Handles various number formats (1,2,3 or 1.2.3)
- **Context Aware**: Understands intent from natural conversation

### 🔧 System Features
- **Health Check**: Railway-compatible health endpoints
- **Session Management**: Per-user conversation sessions
- **Error Handling**: Robust error recovery
- **Logging**: Comprehensive logging system

## 📦 Installation

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/catherine-ai.git
cd catherine-ai
pip install -r requirements_integrated.txt
```

### 2. Configure Environment
```bash
cp .env.integrated .env
# Edit .env with your API keys and settings
```

### 3. Firebase Setup (Optional for TODO features)
- Place your Firebase service account JSON in the project root
- Update `firebase_config.py` with your credentials

### 4. Run the Bot
```bash
python catherine_integrated.py
```

## 🎮 Usage

### Slash Commands
- `/chat [message]` - Start a conversation with Catherine
- `/clear` - Clear conversation history
- `/todo list` - Show TODO list
- `/todo add [content]` - Add a TODO item

### Natural Language Commands
```
# TODO Management
"発注リストをtodoいれて"
"リスト出して"
"3削除して"
"1,2,3完了"
"3の内容は、新しいタスクです。変更して"
"ぜんぶ消して"

# Conversation
@Catherine こんにちは
@Catherine 今日の天気はどう？
```

### TODO Examples
```
User: 発注
・サイズハンコ
・平箱
・60サイズ箱
todoいれて

Catherine: 📝 TODO追加完了:
• 発注
• サイズハンコ
• 平箱
• 60サイズ箱
```

## 🚀 Deployment

### Railway
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy with automatic health checks

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements_integrated.txt .
RUN pip install -r requirements_integrated.txt
COPY . .
CMD ["python", "catherine_integrated.py"]
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DISCORD_TOKEN | Discord bot token | ✅ |
| OPENAI_API_KEY | OpenAI API key | ✅ |
| DEFAULT_MODEL | AI model to use (gpt-4o-mini) | ❌ |
| MAX_TOKENS | Max response tokens (2000) | ❌ |
| TEMPERATURE | AI creativity (0.7) | ❌ |
| CLAUDE_API_KEY | Claude API key | ❌ |
| GEMINI_API_KEY | Gemini API key | ❌ |
| PORT | Health check port (8080) | ❌ |

## 🏗️ Architecture

```
catherine_integrated.py
├── Configuration (Config class)
├── AI Providers (OpenAI, Claude, Gemini)
├── Conversation Management
├── Firebase Integration
├── Intent Detection
├── Discord Bot Commands
└── Health Check Server
```

## 🔄 Version History

### v2.0 (Current)
- Integrated multiple AI providers
- Enhanced conversation management
- Improved TODO operations
- Added slash command support

### v1.0
- Basic TODO management
- Simple chat responses
- Firebase integration

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License
MIT License - feel free to use and modify as needed.

## 🙏 Credits
Based on:
- OpenAI GPT Discord Bot
- ChatGPT Discord Bot (Zero6992)
- Original Catherine AI

## 💬 Support
For issues or questions, please open an issue on GitHub or contact the maintainers.