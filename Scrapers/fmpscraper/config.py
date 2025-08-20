"""
Configuration settings for the FastMath Pro scraper
"""

# Target URL
TARGET_URL = "https://app.alphamath.school/admin/downloads"

# Scraper settings
SCRAPER_CONFIG = {
    "headless": False,  # Set to True to run browser in headless mode
    "timeout": 30,      # Timeout in seconds for web elements
    "implicit_wait": 10 # Implicit wait time for elements
}

# Output settings
OUTPUT_CONFIG = {
    "save_json": True,
    "save_csv": True,
    "output_directory": "./output/"
}

# Browser settings
BROWSER_CONFIG = {
    "window_size": "1920,1080",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}