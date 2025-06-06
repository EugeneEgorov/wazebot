#!/bin/bash

echo "🤖 WazeBot Setup Script"
echo "======================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers (optional)
echo "🌐 Installing Playwright browsers (optional)..."
playwright install chromium || echo "⚠️ Playwright browser installation failed. The bot will work without headless browser support."

# Prompt for Telegram bot token
echo ""
echo "🔑 Telegram Bot Token Setup"
echo "============================="
echo "Please enter your Telegram bot token:"
echo "(Get it from @BotFather on Telegram)"
read -p "Token: " TELEGRAM_TOKEN

# Save token to .env file
echo "TELEGRAM_TOKEN=$TELEGRAM_TOKEN" > .env

# Make run script executable
chmod +x run.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the bot, run:"
echo "  ./run.sh"
echo ""
echo "To test the setup:"
echo "  source venv/bin/activate"
echo "  python wazebot.py" 