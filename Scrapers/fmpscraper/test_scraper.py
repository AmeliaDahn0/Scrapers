#!/usr/bin/env python3
"""
Test script to verify the scraper works with a known working website
"""

from scraper import FastMathProScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the scraper with a working website"""
    scraper = None
    
    try:
        # Initialize scraper in headless mode
        logger.info("Testing scraper with example.com...")
        scraper = FastMathProScraper(headless=True, timeout=15)
        
        # Test with a simple working website
        results = scraper.scrape_downloads_page("https://example.com")
        
        print(f"\n🎯 Scraper Test Results:")
        print(f"Status: {results['status']}")
        print(f"URL: {results['url']}")
        print(f"Page Title: {results.get('page_title', 'N/A')}")
        
        if results['status'] == 'success':
            print("✅ Scraper is working correctly!")
            print(f"Found {len(results.get('downloads', []))} potential download elements")
        else:
            print(f"❌ Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    test_scraper()