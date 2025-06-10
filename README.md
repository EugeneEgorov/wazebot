# 🤖 WazeBot

A Telegram bot that converts Google Maps share links to Waze navigation links.

## Features

- ✅ Converts coordinate-based Google Maps links
- ✅ Converts place/business Google Maps links  
- ✅ Handles Google consent pages
- ✅ Extracts place names for cleaner responses
- ✅ Multiple fallback methods for reliability
- ✅ Dockerized for easy deployment

## Quick Start with Docker 🐳

### 1. Clone and Setup
```bash
git clone <your-repo>
cd wazebot
./setup.sh
```

### 2. Configure Bot Token
```bash
nano .env
# Add your bot token: TELEGRAM_TOKEN=your_bot_token_here
```

### 3. Run the Bot
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Usage

1. Send any message with a Google Maps share link (maps.app.goo.gl/...)
2. Bot will respond with the corresponding Waze link
3. If it's a business/place, the response will include the place name

Example:
```
You: https://maps.app.goo.gl/ABC123
Bot: Here's your Waze link for Restaurant Name:
     https://ul.waze.com/ul?ll=38.7693,-9.0977
```

## How It Works

The bot uses multiple methods to extract coordinates:

1. **Direct parsing** - Extracts coordinates directly from URL patterns
2. **Parameter parsing** - Looks for coordinates in URL parameters  
3. **Place ID resolution** - Resolves place IDs using HTTP redirects
4. **Headless browser** - Uses Playwright as final fallback for consent pages

## DigitalOcean Deployment

1. Create a droplet (Ubuntu 20.04+ recommended)
2. Clone the repository
3. Run `./setup.sh` 
4. Configure your bot token in `.env`
5. Run `docker-compose up -d`

The Docker approach handles all dependencies automatically and runs reliably on VPS environments.

## Development

To modify the bot:
1. Edit `wazebot.py`
2. Rebuild: `docker-compose up --build`

## Troubleshooting

- **Bot not responding**: Check logs with `docker-compose logs -f`
- **Browser issues**: The Docker environment handles all browser dependencies
- **Memory issues**: Increase droplet RAM or add swap space

## Environment Variables

- `TELEGRAM_TOKEN` - Your Telegram bot token (required)

## 🔧 How It Works

The bot uses multiple strategies to extract coordinates from Google Maps links:

### Method 1: Direct Coordinate Parsing
- Looks for coordinate patterns in the URL (`/@lat,lon`, `!3dlat!4dlon`, etc.)
- **Fastest method** - works for most coordinate-based links

### Method 2: URL Parameter Analysis
- Extracts and decodes URL parameters
- Searches for coordinates in URL fragments and data parameters

### Method 3: HTTP Request Strategies
- Makes additional requests to Google Maps URLs
- Tries different domains and URL formats
- Handles consent redirects automatically

### Method 4: Alternative Resolution
- Uses different Google domains (`.co.uk`, `.de`, `.ca`)
- Tries Google Maps API endpoints
- Uses search-based approaches

### Method 5: Headless Browser (Advanced)
- Loads pages with JavaScript execution
- Automatically handles consent dialogs
- Extracts coordinates from rendered pages

### Method 6: Geocoding Fallback
- Extracts business name and address from URLs
- Uses OpenStreetMap's Nominatim service for geocoding
- Tries multiple search strategies (full address, area, business name)

## 📦 Dependencies

Create a `requirements.txt` file with:

```
python-telegram-bot>=20.0
requests>=2.25.0
playwright>=1.20.0
```

## 🐛 Troubleshooting

### Common Issues

1. **"Please set the TELEGRAM_TOKEN environment variable"**
   - Make sure you've exported your bot token: `export TELEGRAM_TOKEN="your_token"`

2. **Bot doesn't respond to place links**
   - The bot tries multiple fallback methods automatically
   - Check the logs for detailed information about each attempt

3. **Playwright errors**
   - Install browser binaries: `playwright install chromium`
   - Playwright is optional - other methods will still work

### Debugging

The bot provides detailed logging. Check the console output to see which methods are being tried and their results.

## 🌍 Supported Link Types

- ✅ Coordinate links: `maps.app.goo.gl/xyz` → `/@38.7711,-9.0925,17z`
- ✅ Place links: `maps.app.goo.gl/abc` → `/place/Restaurant+Name/...`
- ✅ Business listings with addresses
- ✅ Geographic locations and landmarks

## 🔒 Privacy

- The bot only processes the links you send
- No personal data is stored
- External services used: Google Maps (for URL resolution) and OpenStreetMap (for geocoding)

## 📄 License

MIT License - feel free to use and modify!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review the console logs for detailed error information
3. Open an issue on GitHub with the log output

---

**Happy navigation! 🗺️➡️🚗** 