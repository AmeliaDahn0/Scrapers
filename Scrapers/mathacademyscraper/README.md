# Math Academy Scraper

A Python scraper for the Math Academy students page using Playwright.

## Setup

1. **Clone/setup the project:**
   ```bash
   cd mathacademyscraper
   ```

2. **Install dependencies:**
   ```bash
   python setup.py
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Math Academy username and password
   ```

4. **Run the scraper:**
   ```bash
   python scraper_simple.py
   ```

## Files

- `scraper_simple.py` - Main scraper script
- `requirements.txt` - Python dependencies
- `.env.example` - Template for environment variables
- `setup.py` - Setup script for easy installation

## Output

The scraper will:
1. Login to Math Academy using your credentials
2. Navigate to the students page
3. Save the page HTML for inspection
4. Take screenshots on errors for debugging

The output files will be timestamped for easy identification.

## Notes

- The scraper runs with `headless=False` by default so you can see what's happening
- Login selectors may need adjustment based on the actual Math Academy login form
- The script will save the full page HTML for manual inspection to help identify the correct selectors for student data