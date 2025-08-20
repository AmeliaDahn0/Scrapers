#!/usr/bin/env python3
"""
Quick Download Scraper - Focused version for faster results
"""

import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickDownloadScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver in visible mode"""
        try:
            chrome_options = Options()
            # Remove headless mode to show browser
            # chrome_options.add_argument("--headless")  # Commented out
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Enable JavaScript and images for full page functionality
            # chrome_options.add_argument("--disable-images")  # Commented out
            # chrome_options.add_argument("--disable-javascript")  # Commented out
            chrome_options.add_argument("--window-size=1200,800")  # Set a good window size
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Quick scraper initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def login_quick(self):
        """Quick login function"""
        try:
            username = os.getenv('USERNAME')
            password = os.getenv('PASSWORD')
            
            if not username or not password:
                return False
                
            # Find and fill login form quickly
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                
                username_field.send_keys(username)
                password_field.send_keys(password)
                password_field.send_keys("\n")  # Submit
                
                time.sleep(2)  # Quick wait
                return True
                
            except NoSuchElementException:
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def get_page_source_and_links(self, url):
        """Get page source and extract links quickly"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Quick check for login
            if "login" in self.driver.page_source.lower():
                logger.info("Attempting login...")
                if not self.login_quick():
                    return {"error": "Login failed"}
                
                # Navigate again after login
                self.driver.get(url)
                print("✅ Login successful! Waiting for page to load...")
                time.sleep(5)  # Give more time for JavaScript to load
            
            # Get page info quickly
            title = self.driver.title
            current_url = self.driver.current_url
            
            print(f"📄 Page loaded: {title}")
            print(f"🔗 Current URL: {current_url}")
            print("🔍 Looking for download content... (you can see the page in the browser window)")
            
            # Wait for dynamic content and let user inspect the page
            print("\n⏳ Waiting for JavaScript content to load...")
            print("👀 You can now see the page in the Chrome browser window!")
            print("🔍 Look for any download links, files, or content on the page")
            
            # Wait longer for content and user inspection
            for i in range(10, 0, -1):
                print(f"⏰ Continuing scraping in {i} seconds... (page visible in browser)")
                time.sleep(1)
            
            # Extract download links fast
            download_links = []
            
            # Look for common download patterns
            selectors = [
                "a[href*='download']",
                "a[href*='.pdf']", 
                "a[href*='.zip']",
                "a[href*='.exe']",
                "a[href*='.dmg']",
                "a[download]",
                "[href*='file']",
                "[href*='asset']"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute('href')
                        text = elem.text.strip()
                        if href and href not in [link.get('href') for link in download_links]:
                            download_links.append({
                                'href': href,
                                'text': text,
                                'selector': selector
                            })
                except:
                    continue
            
            # Get all links as backup
            all_links = []
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links[:20]:  # Limit to first 20 links
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href:
                        all_links.append({'href': href, 'text': text})
            except:
                pass
            
            results = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'current_url': current_url,
                'title': title,
                'download_links': download_links,
                'all_links': all_links[:10],  # First 10 links
                'page_source_snippet': self.driver.page_source[:1000]  # First 1000 chars
            }
            
            return results
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
    
    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        scraper = QuickDownloadScraper()
        results = scraper.get_page_source_and_links("https://app.alphamath.school/admin/downloads")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Quick Scraper Results:")
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Title: {results.get('title', 'N/A')}")
        print(f"Download Links Found: {len(results.get('download_links', []))}")
        print(f"Total Links Found: {len(results.get('all_links', []))}")
        
        if results.get('download_links'):
            print(f"\n🔗 Download Links:")
            for i, link in enumerate(results['download_links'][:5], 1):
                print(f"{i}. {link['text']} -> {link['href']}")
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()