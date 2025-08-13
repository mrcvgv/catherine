#!/bin/bash

echo "🚀 Deploying Catherine AI Integrated Version"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.integrated .env
    echo "📝 Please edit .env with your API keys before running the bot"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_integrated.txt

# Test Firebase connection
echo "🔥 Testing Firebase connection..."
python -c "from firebase_config import firebase_manager; print('Firebase OK')" 2>/dev/null || echo "⚠️  Firebase not configured (TODO features will be limited)"

# For Railway deployment
if [ "$RAILWAY_ENVIRONMENT" ]; then
    echo "🚂 Railway environment detected"
    cp railway_integrated.toml railway.toml
    cp Procfile.integrated Procfile
fi

# Start the bot
echo "✨ Starting Catherine AI Integrated..."
python catherine_integrated.py