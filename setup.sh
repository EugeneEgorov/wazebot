#!/bin/bash

echo "🚀 Setting up WazeBot environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install Python and pip if not already installed
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install python-telegram-bot requests playwright

# Install Playwright browsers and system dependencies
echo "🌐 Installing browser dependencies..."
playwright install chromium

# Install system dependencies for headless browsers on Ubuntu/Debian
echo "🔧 Installing system dependencies for headless browsers..."
sudo apt install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgconf-2-4 \
    fonts-liberation \
    libappindicator3-1 \
    libu2f-udev \
    xdg-utils \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6

# Install Playwright system dependencies (this handles missing deps automatically)
echo "🎭 Installing Playwright system dependencies..."
playwright install-deps chromium

# Make run script executable
chmod +x run.sh

echo "✅ Setup complete!"
echo ""
echo "💡 To test browser functionality, run:"
echo "   source venv/bin/activate"
echo "   python3 -c \"import asyncio; from wazebot import check_browser_health; print('Browser healthy:', asyncio.run(check_browser_health()))\""
echo ""
echo "🚀 To start the bot:"
echo "   export TELEGRAM_TOKEN='your_bot_token_here'"
echo "   ./run.sh" 