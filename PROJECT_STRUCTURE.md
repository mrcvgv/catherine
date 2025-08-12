# Catherine AI - Clean Project Structure

## Core Files

### Main Application
- `enhanced_main_v2.py` - Main Discord bot application
- `requirements.txt` - Python dependencies

### Firebase Integration  
- `firebase_config.py` - Firebase connection manager
- `firestore_schema.py` - Database schema definitions
- `firebase_todo_enhanced.py` - Firebase TODO system
- `cloud_functions.py` - Cloud Functions (TypeScript guide)
- `cloud_reminder_system.py` - Cloud reminder system

### AI & NLU
- `smart_intent_classifier.py` - Final LLM prompt intent classifier
- `hybrid_intent_detector.py` - Hybrid rule+LLM detector  
- `memory_learning_system.py` - Learning from interactions

### Deployment
- `railway_deployment.py` - Railway deployment manager
- `Procfile` - Railway process definition
- `railway.toml` - Railway configuration
- `Dockerfile` - Docker container setup
- `.env.example` - Environment variables template

## Architecture

```
User Input → Hybrid Intent Detector → Firebase Operations → Cloud Functions
     ↓              ↓                        ↓                  ↓
Smart Classifier → Pending Actions → Cloud Tasks → Discord Response
     ↓              ↓                        ↓                  ↓
Memory Learning → User Preferences → Scheduled Reminders → Confirmation
```

## Removed Files

The following redundant/outdated files were removed during cleanup:
- Multiple main.py variants (consolidated to enhanced_main_v2.py)
- Duplicate reminder systems (consolidated to cloud_reminder_system.py)
- Over-engineered AI systems (simplified to core functionality)
- Test and demo files (moved to production-ready code)

## Next Steps

1. Set environment variables using `.env.example` as template
2. Deploy to Railway using `railway_deployment.py`
3. Configure Cloud Functions using `cloud_functions.py`
4. Monitor and adjust using learning system
