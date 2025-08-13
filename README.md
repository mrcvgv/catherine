# Catherine Task Manager Bot

## 📋 Simple Discord Task Management

A minimal task management bot for Discord based on Discord Task Manager Bot design principles.

## ✨ Commands

### Slash Commands
- `/add [task] [@user]` - Add a new task (optionally assign to user)
- `/list` - Show all pending tasks
- `/done [ID]` - Mark task as completed
- `/done-list` - Show completed tasks
- `/undo [ID]` - Mark completed task as pending
- `/delete [ID]` - Delete a task
- `/clear` - Clear all tasks
- `/help` - Show help

### Text Commands (Alternative)
- `t!add [task] [@user]` - Add a task
- `t!list` - List pending tasks
- `t!done [ID]` - Mark as done
- `t!done-list` - Show completed
- `t!undo [ID]` - Undo completion

## 🚀 Quick Start

1. **Setup**:
   ```bash
   cp .env.example .env
   # Add your Discord bot token to .env
   ```

2. **Install**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run**:
   ```bash
   python catherine_task_manager.py
   ```

## 💡 Usage Example

```
/add Write documentation
> ✅ Task #1 added: Write documentation

/add Review code @username
> ✅ Task #2 added: Review code (assigned to @username)

/list
> 📋 Pending Tasks:
> 1. Write documentation - ID: 1
> 2. Review code - ID: 2 - @username

/done 1
> ✅ Task #1 marked as done!
```

## 🗂️ Features
- Server-specific tasks (isolated per Discord server)
- Task assignment with user mentions
- Persistent storage in JSON file
- Simple ID-based task management
- Health check endpoint for deployment

## 🚀 Deploy to Railway
1. Set `DISCORD_TOKEN` environment variable
2. Deploy - health checks are built-in at `/health`

## 📝 License
MIT License