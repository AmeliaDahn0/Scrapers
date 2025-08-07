# Acely Authentication Base

A clean, robust authentication foundation for accessing the Acely admin console at `https://app.acely.ai/team/admin-console`. This base provides reliable Google OAuth authentication that you can use to build your own custom scrapers.

## 🔧 What's Included

- **🔐 Robust Google OAuth Authentication** - Bypasses 2FA using "Continue with Google"
- **🚀 Enhanced Error Handling** - Detailed logging and retry logic with Chrome dialog dismissal
- **⚙️ Configurable Setup** - Headless/headful mode, timeouts, and delays
- **🪵 Professional Logging** - Comprehensive logging with rotation
- **🧹 Clean Architecture** - Modular base class for easy extension

## 🎯 Purpose

This codebase has been cleaned up to provide **only the authentication logic**. The previous data collection methods have been removed so you can implement your own scraping logic from scratch.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Credentials

Create a `.env` file with your Google account credentials:

```env
ACELY_EMAIL=your_gmail@gmail.com
ACELY_PASSWORD=your_google_password
HEADLESS_MODE=True
WAIT_TIMEOUT=10
```

### 3. Test Authentication

```bash
# Test that authentication works
python3 acely_auth_base.py
```

### 4. Build Your Custom Scraper

```bash
# See the example implementation
python3 example_new_scraper.py
```

## 🏗️ Building Your Own Scraper

### Basic Pattern

```python
from acely_auth_base import AcelyAuthenticator, AuthConfig

class MyCustomScraper(AcelyAuthenticator):
    def __init__(self, config: AuthConfig = None):
        super().__init__(config)
        # Your custom initialization
    
    def scrape_data(self):
        # Authenticate first
        if not self.is_authenticated:
            if not self.login():
                return None
        
        # Now implement your data collection logic
        # self.driver is available for Selenium operations
        # self.wait is available for WebDriverWait operations
        
        return your_collected_data
```

### Example Usage

```python
import os
from dotenv import load_dotenv

load_dotenv()

config = AuthConfig(
    email=os.getenv("ACELY_EMAIL"),
    password=os.getenv("ACELY_PASSWORD"),
    headless=True,
    wait_timeout=10
)

scraper = MyCustomScraper(config)
try:
    scraper.setup_driver()
    data = scraper.scrape_data()
    # Process your data
finally:
    scraper.close()
```

## 🔧 Available Methods

### Authentication Methods
- `login()` - Perform complete authentication flow
- `setup_driver()` - Initialize Chrome browser with anti-detection
- `verify_admin_access()` - Ensure admin console access
- `close()` - Clean up browser resources

### Chrome Dialog Handling
- `dismiss_chrome_dialog_aggressively()` - Handle Chrome sign-in prompts

### Configuration
- `AuthConfig` dataclass for authentication settings
- Environment variable support for easy deployment

## 📁 File Structure

```
acelyscraper/
├── acely_auth_base.py          # Core authentication class
├── example_new_scraper.py      # Example implementation
├── requirements.txt            # Python dependencies
├── student_emails.txt          # Email list for targeting
├── .env                        # Your credentials (create this)
└── README.md                   # This file
```

## ⚙️ Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `ACELY_EMAIL` | Your Google email for OAuth | Required |
| `ACELY_PASSWORD` | Your Google password | Required |
| `HEADLESS_MODE` | Run browser in headless mode | `True` |
| `WAIT_TIMEOUT` | Selenium wait timeout (seconds) | `10` |

## 🛠️ Database Integration (Optional)

The Supabase integration components are still available if you want to store your scraped data:

- `supabase_setup.sql` - Database schema
- `supabase_uploader.py` - Upload utilities  
- `enhanced_supabase_uploader.py` - Advanced upload features
- SQL example files for querying

## 🚀 Advanced Features

### Anti-Detection
- Fresh Chrome profiles per authentication attempt
- Custom user agents and browser flags
- Aggressive Chrome dialog dismissal
- Enhanced stealth mode

### Error Handling
- Multiple authentication retry attempts
- Detailed logging of each step
- Graceful failure handling
- Clean resource cleanup

### Extensibility
- Clean inheritance pattern
- Configurable via dataclass or environment
- Modular design for easy customization

## 🔒 Security Notes

- Store credentials in `.env` file (never commit to version control)
- Use your own Google account that has access to Acely
- Only access data you have permission to view
- Be respectful of rate limits

## 🆘 Troubleshooting

### Authentication Issues

1. **Login Failed**
   - Verify Google credentials in `.env` file
   - Try running in non-headless mode (`HEADLESS_MODE=False`)
   - Ensure you have permission to access Acely admin console

2. **Chrome Dialogs Blocking**
   - The base class handles most Chrome dialogs automatically
   - Try running with fresh profile (restart your script)
   - Check logs for specific dialog dismissal attempts

3. **Timeout Issues**
   - Increase `WAIT_TIMEOUT` in your configuration
   - Check your internet connection
   - Monitor logs for specific bottlenecks

### Debug Mode

Run in visible mode to see what's happening:

```bash
# In .env file
HEADLESS_MODE=False
```

## System Requirements

- **Python 3.8+**
- **Google Chrome browser**
- **ChromeDriver** (automatically managed)
- **macOS/Linux/Windows** (tested on macOS)

## Dependencies

- `selenium`: Web automation
- `undetected-chromedriver`: Anti-detection browser automation  
- `python-dotenv`: Environment variable management
- `loguru`: Enhanced logging

## Legal Considerations

- Ensure you have permission to access the data
- Respect privacy and data protection laws
- Follow your organization's data handling policies
- Don't overload servers with too many requests

## License

This project is for educational and authorized use only. Make sure you have proper authorization before accessing any website. 