# Catherine AI - OpenAI GPT Discord Bot + Firebase Integration

## 🤖 Overview
Advanced Discord bot powered by OpenAI's GPT models with Firebase conversation logging. Based on OpenAI's official GPT Discord Bot with enhanced Firebase integration for persistent conversation storage.

## ✨ Features

### 🧠 **AI Conversation**
- **OpenAI GPT Integration**: Powered by GPT-3.5-turbo or GPT-4
- **Thread-based Conversations**: Each conversation runs in a dedicated Discord thread
- **Context Retention**: Maintains conversation history within threads
- **Intelligent Moderation**: Built-in content filtering and moderation
- **Customizable Personality**: Configure bot behavior via `config.yaml`

### 🔥 **Firebase Integration**
- **Conversation Logging**: All conversations automatically saved to Firestore
- **User History Tracking**: Track conversation patterns and usage
- **Persistent Storage**: Never lose conversation data
- **Structured Data**: Organized conversation data with timestamps and metadata

### 🛡️ **Moderation & Safety**
- **Content Filtering**: Automatic detection of inappropriate content
- **Server-specific Controls**: Configure moderation per Discord server
- **Admin Controls**: Manage allowed servers and moderation channels
- **Safe Conversations**: Blocked content is automatically removed

## 📋 Commands

### **Primary Commands**

#### `/chat [message] [model] [temperature] [max_tokens]`
Start a new AI conversation thread.

**Parameters:**
- `message` (required): Your initial message to the AI
- `model` (optional): AI model to use (default: gpt-3.5-turbo)
- `temperature` (optional): Creativity level 0.0-1.0 (default: 1.0)
- `max_tokens` (optional): Maximum response length (default: 512)

**Examples:**
```
/chat Hello, how are you today?
/chat Tell me a story model:gpt-4 temperature:0.8
/chat Explain quantum physics max_tokens:1000
```

**What happens:**
1. Creates a new public thread
2. Bot responds with an embed showing conversation details
3. Continue the conversation by sending messages in the thread
4. All messages are saved to Firebase automatically

### **Thread Conversations**
Once a `/chat` command creates a thread, you can:

- **Continue Chatting**: Just send messages normally in the thread
- **Context Preserved**: Bot remembers everything said in the thread
- **Auto-close**: Thread closes automatically after reaching message limit or inactivity
- **Moderation**: All messages are filtered for safety

**Thread Features:**
- Thread name starts with "🤖-chat" prefix
- Maximum of 100 messages per thread
- Automatic closure when limit reached
- Real-time typing indicators
- Message history preserved

## 🚀 Setup & Installation

### **1. Prerequisites**
- Python 3.9+ (tested with Python 3.12)
- Discord Bot Token
- OpenAI API Key
- Firebase Project (optional, for conversation logging)

### **2. Environment Configuration**

Copy `.env.example` to `.env` and configure:

```env
# Required Settings
OPENAI_API_KEY=sk-your-openai-api-key-here
DISCORD_BOT_TOKEN=your-discord-bot-token-here
DISCORD_CLIENT_ID=your-discord-client-id-here

# Server Configuration  
ALLOWED_SERVER_IDS=123456789,987654321
SERVER_TO_MODERATION_CHANNEL=server_id:channel_id

# AI Configuration
DEFAULT_MODEL=gpt-3.5-turbo
```

### **3. Discord Bot Setup**

1. **Create Application**: Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. **Create Bot**: Go to Bot tab → Add Bot
3. **Get Token**: Copy bot token to `.env`
4. **Enable Intents**: Turn ON "Message Content Intent"
5. **Get Client ID**: Copy from OAuth2 → General
6. **Bot Permissions**: 
   - Send Messages
   - Send Messages in Threads  
   - Create Public Threads
   - Manage Messages (for moderation)
   - Manage Threads
   - Read Message History
   - Use Application Commands

### **4. OpenAI API Setup**

1. **Get API Key**: Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. **Create Key**: Generate new secret key
3. **Add to .env**: `OPENAI_API_KEY=sk-your-key-here`
4. **Set Model**: Choose `gpt-3.5-turbo` or `gpt-4`

### **5. Firebase Setup (Optional)**

Firebase enables conversation logging and history tracking.

1. **Create Project**: [Firebase Console](https://console.firebase.google.com)
2. **Enable Firestore**: Create Firestore database
3. **Service Account**: Project Settings → Service Accounts → Generate Key
4. **Add JSON File**: Place service account JSON in project root as `firebase-key.json`

**Firebase Collections Created:**
- `conversations`: Stores all chat interactions
  ```json
  {
    "user_id": "123456789",
    "channel_id": "987654321", 
    "user_message": "Hello!",
    "bot_response": "Hi there! How can I help?",
    "timestamp": "2024-01-01T12:00:00Z",
    "message_type": "chat_completion"
  }
  ```

### **6. Installation & Running**

**Local Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python -m src.main
```

**Docker:**
```bash
# Build image
docker build -t catherine-ai .

# Run container  
docker run -d --env-file .env catherine-ai
```

## 🌐 Deployment

### **Railway (Recommended)**

Railway deployment is fully configured and ready.

1. **Connect Repository**: Link your GitHub repo to Railway
2. **Set Environment Variables**: Configure in Railway dashboard
3. **Deploy**: Automatic deployment on git push

**Required Railway Environment Variables:**
```
OPENAI_API_KEY=sk-your-key-here
DISCORD_BOT_TOKEN=your-token-here
DISCORD_CLIENT_ID=your-client-id-here
ALLOWED_SERVER_IDS=your-server-ids
```

**Files for Railway:**
- `railway.toml`: Deployment configuration
- `Procfile`: Start command
- `requirements.txt`: Dependencies

### **Other Platforms**

The bot can be deployed to any platform supporting Python:
- **Heroku**: Use `Procfile`
- **Google Cloud**: Use `runtime.txt` 
- **AWS**: Use Lambda or EC2
- **DigitalOcean**: App Platform or Droplets

## ⚙️ Configuration

### **Bot Personality (`src/config.yaml`)**

Customize the AI's behavior and personality:

```yaml
name: Catherine AI
instructions: |
  You are Catherine AI, a helpful and friendly assistant.
  You provide thoughtful, accurate responses.
  You maintain a warm and supportive tone.
  You can discuss any topic but keep conversations appropriate.
  
example_conversations:
  - messages:
      - user: Hello!
        text: Hi there! I'm Catherine AI. How can I help you today?
      - user: What can you do?
        text: I can help with questions, have conversations, provide explanations, and much more! What would you like to talk about?
```

### **Moderation Settings (`src/constants.py`)**

Fine-tune content moderation:

```python
# Moderation thresholds (0.0 = strict, 1.0 = permissive)
HATE_THRESHOLD = 0.7
HATE_THREATENING_THRESHOLD = 0.7  
HARASSMENT_THRESHOLD = 0.7
SELF_HARM_THRESHOLD = 0.7
SEXUAL_THRESHOLD = 0.7
SEXUAL_MINORS_THRESHOLD = 0.7
VIOLENCE_THRESHOLD = 0.7
VIOLENCE_GRAPHIC_THRESHOLD = 0.7
```

### **Advanced Settings**

Modify behavior in `src/constants.py`:

```python
# Thread settings
MAX_THREAD_MESSAGES = 100        # Messages before auto-close
SECONDS_DELAY_RECEIVING_MSG = 2  # Delay before processing
ACTIVATE_THREAD_PREFX = "🤖-chat"  # Thread name prefix

# AI settings  
AVAILABLE_MODELS = ["gpt-3.5-turbo", "gpt-4"]
DEFAULT_MODEL = "gpt-3.5-turbo"
```

## 📊 Usage Examples

### **Basic Conversation**
```
User: /chat Hello, what's the weather like today?
Catherine: I don't have access to real-time weather data, but I'd be happy to help you in other ways! Is there something specific you'd like to know or discuss?

User: Tell me about artificial intelligence
Catherine: [Continues conversation in thread with detailed AI explanation...]
```

### **Creative Writing**
```
User: /chat Write a short story about a robot temperature:0.9 max_tokens:800
Catherine: [Creates thread and writes creative story...]
```

### **Technical Help**
```  
User: /chat Explain how to use Python decorators model:gpt-4
Catherine: [Provides detailed Python decorator explanation...]
```

### **Conversation Management**
- **New Topic**: Start new `/chat` command
- **Continue**: Keep chatting in existing thread  
- **History**: All conversations saved to Firebase
- **Moderation**: Inappropriate content automatically handled

## 🔧 Advanced Features

### **Multi-Server Support**
- Configure different servers with `ALLOWED_SERVER_IDS`
- Per-server moderation channels
- Server-specific conversation logging

### **Firebase Data Structure**
```
conversations/
  ├── {document_id}/
      ├── user_id: "123456789"
      ├── channel_id: "thread_id"  
      ├── user_message: "User's message"
      ├── bot_response: "AI response"
      ├── timestamp: "ISO timestamp"
      └── message_type: "chat_completion"
```

### **Monitoring & Analytics**
- Track conversation patterns in Firebase
- Monitor user engagement
- Analyze popular topics and usage

### **Error Handling**
- Automatic retry for API failures
- Graceful handling of rate limits
- Comprehensive error logging
- Failed message recovery

## 🚨 Troubleshooting

### **Common Issues**

**Bot doesn't respond to `/chat`:**
- Check `DISCORD_BOT_TOKEN` is correct
- Verify bot has required permissions
- Ensure server ID is in `ALLOWED_SERVER_IDS`

**OpenAI API errors:**
- Verify `OPENAI_API_KEY` is valid
- Check API usage/billing limits
- Try different model (gpt-3.5-turbo vs gpt-4)

**Firebase connection issues:**
- Confirm service account JSON file is present
- Check Firestore database is enabled
- Verify Firebase project configuration

**Moderation too strict/loose:**
- Adjust threshold values in `constants.py`
- Configure `SERVER_TO_MODERATION_CHANNEL`

### **Debug Mode**

Enable detailed logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance & Limits

### **Rate Limits**
- **OpenAI API**: 3,500 requests/minute (varies by plan)
- **Discord API**: 50 requests/second globally
- **Thread Limit**: 100 messages per conversation

### **Optimization Tips**
- Use `gpt-3.5-turbo` for faster, cheaper responses
- Set appropriate `max_tokens` limits
- Configure `temperature` based on use case
- Monitor Firebase usage costs

### **Scaling**
- Deploy multiple instances for high traffic
- Use Redis for shared session storage
- Implement conversation archiving
- Set up load balancing

## 🤝 Contributing

This bot is based on OpenAI's official GPT Discord Bot template with Firebase integration enhancements.

**Development:**
1. Fork the repository
2. Create feature branch
3. Add tests for new features  
4. Submit pull request

**Bug Reports:**
- Use GitHub Issues
- Include error logs
- Provide reproduction steps

## 📝 License

MIT License - Use freely for personal and commercial projects.

## 🙏 Acknowledgments

- **OpenAI**: GPT Discord Bot template
- **Firebase**: Conversation storage and analytics
- **Discord.py**: Discord API wrapper
- **Railway**: Deployment platform

---

## 💡 Pro Tips

1. **Conversation Management**: Use descriptive `/chat` messages to set context
2. **Model Selection**: Use GPT-4 for complex tasks, GPT-3.5-turbo for casual chat
3. **Temperature Control**: Lower values (0.3) for factual answers, higher (0.8) for creativity
4. **Firebase Analytics**: Query conversation data for insights and improvements
5. **Moderation Tuning**: Start strict, then relax based on your community needs

**Happy chatting with Catherine AI! 🤖✨**