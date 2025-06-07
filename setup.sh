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

# Install Playwright browsers and system dependencies
echo "🌐 Installing Playwright browsers..."
playwright install chromium || echo "⚠️ Playwright browser installation failed."

echo "🔧 Installing system dependencies for headless browser..."
# Try to install playwright system dependencies
playwright install-deps || {
    echo "⚠️ Automatic dependency installation failed. Trying manual installation..."
    
    # Check if we have sudo access
    if command -v sudo &> /dev/null; then
        echo "📦 Installing browser dependencies manually..."
        sudo apt-get update
        sudo apt-get install -y \
            libatk1.0-0 \
            libatk-bridge2.0-0 \
            libatspi2.0-0 \
            libxcomposite1 \
            libxdamage1 \
            libxfixes3 \
            libxrandr2 \
            libgbm1 \
            libasound2 \
            libxss1 \
            libgtk-3-0 \
            libdrm2 \
            libxkbcommon0 \
            libgtk-4-1 || echo "⚠️ Some dependencies might not be available on this system."
    else
        echo "⚠️ No sudo access. Please run the following command manually:"
        echo "    sudo apt-get install libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2"
    fi
}

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
echo "To run in background:"
echo "  nohup ./run.sh > bot.log 2>&1 &"
echo ""
echo "To test the setup:"
echo "  source venv/bin/activate"
echo "  python wazebot.py" 