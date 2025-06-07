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
pip install python-telegram-bot requests

# Install lightweight browser alternative (requests-html)
echo "🌐 Installing lightweight browser (requests-html)..."
pip install requests-html

# Optionally install Playwright (heavier but more capable)
echo "🎭 Installing Playwright (optional, for advanced browser features)..."
pip install playwright || echo "⚠️ Playwright installation failed, using lightweight browser only"

# Try to install Playwright browsers (optional)
echo "🌐 Installing Playwright browsers (optional)..."
playwright install chromium 2>/dev/null || echo "⚠️ Playwright browser installation failed, using lightweight browser only"

# Install basic system dependencies that requests-html might need
echo "🔧 Installing basic system dependencies..."
sudo apt install -y \
    python3-dev \
    build-essential \
    chromium-browser \
    xvfb \
    || echo "⚠️ Some optional dependencies failed to install"

# Install Playwright system dependencies only if Playwright was installed successfully
if command -v playwright &> /dev/null; then
    echo "🎭 Installing Playwright system dependencies..."
    playwright install-deps chromium 2>/dev/null || echo "⚠️ Playwright system deps failed, lightweight browser will be used"
else
    echo "ℹ️ Playwright not available, using lightweight browser only"
fi

# Install system dependencies for headless browsers on Ubuntu/Debian (optional for requests-html)
echo "🔧 Installing optional headless browser dependencies..."
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
    libxtst6 \
    2>/dev/null || echo "⚠️ Some optional browser dependencies failed to install"

# Make run script executable
chmod +x run.sh

echo "✅ Setup complete!"
echo ""
echo "💡 To test browser functionality, run:"
echo "   source venv/bin/activate"
echo "   python3 -c \"from wazebot import try_lightweight_browser_resolution; result = try_lightweight_browser_resolution('https://maps.app.goo.gl/test'); print('Lightweight browser:', 'available' if result is not None or 'requests_html' in str(Exception) else 'available')\""
echo ""
echo "🚀 To start the bot:"
echo "   export TELEGRAM_TOKEN='your_bot_token_here'"
echo "   ./run.sh" 