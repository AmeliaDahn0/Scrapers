# FastMath Pro Downloads Scraper

A Python web scraper built with Selenium to extract download information from the FastMath Pro admin downloads page.

## Features

- **Selenium WebDriver**: Uses Chrome WebDriver for reliable web scraping
- **Automatic Driver Management**: ChromeDriverManager handles driver installation
- **Error Handling**: Comprehensive error handling and logging
- **Multiple Output Formats**: Saves results in JSON and CSV formats
- **Login Detection**: Detects if authentication is required
- **Configurable**: Easy to configure headless mode, timeouts, and other settings

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome browser** (if not already installed):
   - The scraper uses Chrome WebDriver
   - ChromeDriverManager will automatically download the appropriate driver version

3. **Set up authentication credentials**:
   ```bash
   # Copy the environment template
   cp env_template .env
   
   # Edit .env and add your login credentials
   nano .env  # or use any text editor
   ```

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python scraper.py
```

### Configuration

Edit `config.py` to customize scraper behavior:
- `headless`: Run browser in headless mode (True/False)
- `timeout`: Timeout for web elements (seconds)
- Target URL and other settings

### Output

The scraper generates:
- **JSON file**: Complete scraped data with metadata
- **CSV file**: Download links in tabular format
- **Log file**: Detailed scraping logs (`scraper.log`)

## Target URL

The scraper is configured to scrape:
```
https://app.fastmath.pro/admin/downloads
```

## What It Scrapes

The scraper extracts:
- Download links and buttons
- File information (PDFs, ZIPs, executables, etc.)
- Page metadata (title, headings, tables)
- Data attributes from download elements

## Authentication

The scraper now includes automatic login functionality:

### Setting up credentials:
1. **Edit the `.env` file** with your login credentials:
   ```bash
   USERNAME=your_actual_username
   PASSWORD=your_actual_password
   ```

2. **Optional settings** in `.env`:
   ```bash
   HEADLESS_MODE=true          # Run browser without GUI
   TIMEOUT_SECONDS=30          # Page load timeout
   RETRY_ATTEMPTS=3           # Login retry attempts
   ```

### How authentication works:
- **Automatic detection**: Detects if login is required
- **Smart form finding**: Automatically finds username/password fields
- **Multiple selectors**: Tries various common field selectors
- **Auto-submit**: Submits login form automatically
- **Success verification**: Confirms login worked before proceeding

### Supported login forms:
- Email/password combinations
- Username/password combinations  
- Common field names (email, username, password)
- Standard submit buttons

## Error Handling

The scraper includes robust error handling for:
- Network timeouts
- Missing elements
- Authentication requirements
- WebDriver issues

## Files Structure

```
fmpscraper/
├── scraper.py          # Main scraper script
├── test_scraper.py     # Test version for debugging
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── env_template        # Environment variable template
├── .env               # Your credentials (create from template)
├── .gitignore         # Git ignore file (protects .env)
├── setup.sh           # Installation script
├── README.md          # This file
├── scraper.log        # Generated log file
└── fastmath_downloads_YYYYMMDD_HHMMSS.json  # Generated results
```

## Troubleshooting

1. **Chrome not found**: Install Google Chrome browser
2. **Permission errors**: Run with appropriate permissions
3. **Network issues**: Check internet connection and URL accessibility
4. **Authentication required**: The target page may require login

## Dependencies

- `selenium`: Web automation framework
- `webdriver-manager`: Automatic WebDriver management
- `beautifulsoup4`: HTML parsing (optional enhancement)
- `requests`: HTTP library (optional enhancement)
- `pandas`: Data manipulation (optional enhancement)