#!/bin/bash

echo "🚀 Starting WazeBot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Environment file not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Check if token is set
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ TELEGRAM_TOKEN not found in .env file."
    echo "Please run setup.sh again or manually add your token to .env file."
    exit 1
fi

echo "✅ Environment loaded"
echo "🤖 Starting bot..."
echo "Press Ctrl+C to stop"

# Run the bot
python wazebot.py 