#!/bin/bash

echo "🐳 WazeBot Docker Setup"
echo "======================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    
    # Update package database
    sudo apt update
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Clean up
    rm get-docker.sh
    
    echo "✅ Docker installed successfully!"
    echo "⚠️  Please log out and log back in to use Docker without sudo"
    echo "   Or run: newgrp docker"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo "✅ Docker Compose installed successfully!"
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        cp env.example .env
        echo "📝 Created .env file from example"
        echo "⚠️  Please edit .env and add your TELEGRAM_TOKEN"
    else
        echo "TELEGRAM_TOKEN=your_bot_token_here" > .env
        echo "📝 Created .env file"
        echo "⚠️  Please edit .env and add your TELEGRAM_TOKEN"
    fi
fi

# Create logs directory
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your Telegram bot token:"
echo "   nano .env"
echo ""
echo "2. Build and run the bot:"
echo "   docker-compose up --build"
echo ""
echo "3. Run in background:"
echo "   docker-compose up --build -d"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop the bot:"
echo "   docker-compose down" 