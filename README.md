# WazeBot - Google Maps to Waze Converter

A Telegram bot that converts Google Maps share links to Waze navigation links, making it easy to switch between mapping services.

## 🚀 Features

- **Universal Link Support**: Handles both coordinate-based and place-based Google Maps links
- **Multiple Fallback Methods**: Uses 8 different strategies to extract coordinates
- **Smart Geocoding**: Falls back to OpenStreetMap geocoding when direct parsing fails
- **Headless Browser Support**: Can handle JavaScript-heavy pages and consent dialogs
- **Multi-language Support**: Works with Portuguese and English consent pages
- **Fast & Reliable**: Tries lightweight methods first, then more complex ones if needed

## 📋 Requirements

- Python 3.7+
- Telegram Bot Token
- Required Python packages (see `requirements.txt`)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd wazebot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (optional, for advanced fallback):
   ```bash
   playwright install chromium
   ```

4. **Set up your Telegram bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Copy your bot token

5. **Set environment variable**:
   ```bash
   export TELEGRAM_TOKEN="your_bot_token_here"
   ```

## 🚀 Usage

1. **Start the bot**:
   ```bash
   python wazebot.py
   ```

2. **Use the bot on Telegram**:
   - Start a chat with your bot
   - Send any Google Maps share link (`maps.app.goo.gl/...`)
   - Receive a Waze link in return!

### Example

**Input**: `https://maps.app.goo.gl/XodKRcb7kt53ne8d9`

**Output**: `Here's your Waze link: https://ul.waze.com/ul?ll=38.7711111,-9.0925`

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