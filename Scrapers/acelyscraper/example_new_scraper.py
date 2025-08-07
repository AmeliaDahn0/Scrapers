#!/usr/bin/env python3
"""
Example: How to build a new scraper using the AcelyAuthenticator base class

This example shows how to inherit from AcelyAuthenticator to create your own
custom scraper with proper authentication handling.
"""

import time
from acely_auth_base import AcelyAuthenticator, AuthConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger


class MyCustomScraper(AcelyAuthenticator):
    """Custom scraper that inherits authentication capabilities"""
    
    def __init__(self, config: AuthConfig = None):
        super().__init__(config)
        # Add any custom initialization here
        self.scraped_data = {}
    
    def scrape_data(self):
        """Main scraping method - implement your data collection logic here"""
        try:
            # First, authenticate
            if not self.is_authenticated:
                logger.info("🔐 Authenticating to Acely...")
                if not self.login():
                    logger.error("❌ Authentication failed")
                    return None
            
            # Now you can implement your custom scraping logic
            logger.info("🚀 Starting custom data scraping...")
            
            # Example: Navigate to a specific page
            logger.info("📍 Navigating to admin console...")
            self.driver.get("https://app.acely.ai/team/admin-console")
            time.sleep(5)
            
            # Example: Extract page title
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            logger.info(f"📄 Page title: {page_title}")
            logger.info(f"📍 Current URL: {current_url}")
            
            # Store basic data
            self.scraped_data = {
                "timestamp": time.time(),
                "url": current_url,
                "title": page_title,
                "authenticated": self.is_authenticated
            }
            
            # TODO: Add your custom data extraction logic here
            # For example:
            # - Find specific elements on the page
            # - Extract text, attributes, or other data
            # - Navigate to different sections
            # - Process and structure the data
            
            logger.info("✅ Custom scraping completed successfully")
            return self.scraped_data
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return None
    
    def save_data(self, data):
        """Save scraped data to a file"""
        if not data:
            logger.warning("⚠️ No data to save")
            return None
        
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custom_scraped_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return None


def main():
    """Example usage of the custom scraper"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Create configuration
    config = AuthConfig(
        email=os.getenv("ACELY_EMAIL"),
        password=os.getenv("ACELY_PASSWORD"),
        headless=os.getenv("HEADLESS_MODE", "True").lower() == "true",
        wait_timeout=int(os.getenv("WAIT_TIMEOUT", "10"))
    )
    
    # Create and run scraper
    scraper = MyCustomScraper(config)
    
    try:
        # Setup the browser
        scraper.setup_driver()
        
        # Run scraping
        data = scraper.scrape_data()
        
        if data:
            # Save the data
            filename = scraper.save_data(data)
            print(f"✅ Scraping completed! Data saved to: {filename}")
        else:
            print("❌ Scraping failed - no data collected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always clean up
        scraper.close()


if __name__ == "__main__":
    main() 