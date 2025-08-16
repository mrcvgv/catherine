# Catherine AI - Witch of the Waste Style TODO Management Discord Bot

## 🧙‍♀️ Overview

Catherine is an AI secretary with the personality of an elegant yet slightly mischievous elderly witch, reminiscent of the Witch of the Waste.  
She manages TODOs, sets reminders, and engages in natural conversations on Discord.

## ✨ Key Features

### 📝 **TODO Management System**
- **Natural Language TODO Operations**: Add TODOs with natural phrases like "Add acrylic keychain production"
- **Priority System**: 4-level priority system with ⚫Urgent, 🔴High, 🟡Normal, 🟢Low
- **Auto-Sort**: Automatic sorting by priority (Urgent → High → Normal → Low)
- **Batch Delete**: Delete multiple TODOs at once with "Delete 1.2.3.5"
- **Priority Change**: Easily change priorities with "Change 5 to urgent priority"
- **Rename**: Change TODO names with "Change 1 to shopping list"

### ⏰ **Reminder System**
- **Individual Reminders**: "Remind me about 1 in 1 minute" for specific TODO notifications
- **Daily Reminders**: "Remind all list every morning at 8:30" for regular notifications
- **Channel Targeting**: Send notifications to specific channels like #todo
- **Mention Features**: Mention @everyone or specific users

### 🎭 **Witch of the Waste Personality**
- **Witch-style Speech**: Elegant yet mischievous dialogue like "Oh my, adding more work again?"
- **Random Comments**: Different witch-like remarks each time you view the TODO list
- **Time-based Greetings**: Morning, afternoon, and evening greetings in witch style
- **Priority Comments**: Witch-style advice based on priority levels

## 🗣️ Usage

### **Basic TODO Operations**

#### Adding TODOs
```
Add acrylic keychain production
Create "shopping list"
Finish report by tomorrow (urgent priority)
```

#### Displaying TODO List
```
list
show all
give me todos
```

#### Deleting TODOs
```
delete 1
remove 2.3.5
delete 1 and 4
```

#### Changing Priority
```
change 5 to urgent priority
set 3 to high priority
make 1 normal
```

#### Renaming TODOs
```
change 1 to shopping list
rename 2 to meeting prep
```

### **Setting Reminders**

#### Individual Reminders
```
remind me about 1 in 1 minute
remind 3 tomorrow
remind 5 now
```

#### Daily Reminders
```
remind all list every morning at 8:30
notify list every evening at 22:00
```

### **Conversations with Catherine**
Besides TODO commands, you can have natural conversations with Catherine. She uses OpenAI GPT-4o for high-quality dialogue.

## 🎯 Priority System

### Priority Levels
- **⚫ Urgent**: Highest priority, emergency, critical, immediate response needed
- **🔴 High**: Important, significant, priority, urgent tasks
- **🟡 Normal**: Regular, standard, default (when no priority specified)
- **🟢 Low**: Later, whenever, low priority, when you have time

### Auto-Sort Feature
- TODO list always displays in priority order
- Automatic reordering when priority changes
- Within same priority, sorted by creation date

## ⚙️ Setup

### 1. Environment Variables
```env
# Discord Configuration
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CLIENT_ID=your-client-id
ALLOWED_SERVER_IDS=your-server-ids

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key

# Firebase Configuration (for TODO management)
# Place firebase-key.json file in project root
```

### 2. Discord Bot Permissions
- Send Messages
- Read Message History
- Use Application Commands
- Mention @everyone

### 3. Firebase Setup
- Enable Firestore database
- Save service account key as `firebase-key.json`

## 🚀 Deployment

### Railway (Recommended)
```bash
# Connect repository to Railway
# Set environment variables
# Auto-deploy
```

### Local Execution
```bash
pip install -r requirements.txt
python -m src.main
```

## 🤖 Catherine's Personality

### Basic Speech Patterns
- "Fufu, ○○ isn't it?" "Oh my, ○○ you know"
- "Oh dear" "My my" "Really now"
- Elegant yet slightly mischievous elderly lady

### TODO Comments Examples
- "Hmm, 'acrylic keychain production' is it? I'll remember that for you"
- "Adding more work again? My, you're a busy person indeed"
- "Changing priority, are we? Well, important things should come first"

### Random Remarks Collection
- "Now then, do your best today"
- "Take it one step at a time"
- "You have quite a pile of things to do"
- "My, what a busy person you are"

## 📊 Data Management

### Firebase Structure
```
todos/
  ├── user_id: "Discord User ID"
  ├── title: "TODO Title"
  ├── priority: "urgent|high|normal|low"
  ├── status: "pending|completed"
  ├── created_at: "Creation date (JST)"
  └── due_date: "Due date (if set)"

conversations/
  ├── user_id: "User ID"
  ├── user_message: "User Message"
  ├── bot_response: "Catherine's Response"
  └── timestamp: "Timestamp (JST)"
```

## 🔧 Customization

### Adjusting Witch Personality
Customize speech and personality in `src/personality_system.py`:
- Basic speech patterns
- Situational response variations
- Time-based greetings

### NLU (Natural Language Understanding) Adjustments
Customize command recognition in `src/todo_nlu.py`:
- Add priority keywords
- Add new action patterns
- Extend time expressions

## 🚨 Troubleshooting

### Common Issues

**Catherine doesn't respond**
- Check if Discord Bot Token is correct
- Verify server ID is included in ALLOWED_SERVER_IDS

**TODOs not saving**
- Check if firebase-key.json file exists
- Verify Firestore is enabled

**Reminders not working**
- Check if scheduler system is running
- Verify time specification is recognized correctly

## 💡 Usage Tips

1. **Natural language is fine**: Talk naturally like "Add ○○" or "Delete ○○"
2. **Priority can be changed later**: Add TODOs first, then adjust priorities
3. **Use numbers for operations**: Use displayed numbers for easy deletion and changes
4. **Daily reminders are convenient**: Use as a morning routine to check all TODOs
5. **Enjoy chatting with Catherine**: She can discuss topics beyond TODOs

---

**Start efficient TODO management with Catherine, the Witch of the Waste! 🧙‍♀️✨**