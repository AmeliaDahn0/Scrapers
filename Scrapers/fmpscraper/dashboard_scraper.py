#!/usr/bin/env python3
"""
Dashboard Data Scraper - Navigate to admin dashboard and gather data
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

class DashboardScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver in visible mode"""
        try:
            chrome_options = Options()
            # Keep browser visible
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1400,1000")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Dashboard scraper initialized")
            
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
                
                time.sleep(3)  # Wait for login
                return True
                
            except NoSuchElementException:
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def navigate_to_dashboard(self):
        """Navigate to downloads page, then click back to dashboard"""
        try:
            # Start at downloads page
            logger.info("Navigating to downloads page...")
            self.driver.get("https://app.alphamath.school/admin/downloads")
            
            # Check for login
            if "login" in self.driver.page_source.lower():
                logger.info("Attempting login...")
                if not self.login_quick():
                    return {"error": "Login failed"}
                
                # Navigate again after login
                self.driver.get("https://app.alphamath.school/admin/downloads")
                print("✅ Login successful!")
                time.sleep(3)
            else:
                print("✅ Already logged in!")
            
            print("📄 On downloads page, looking for back button...")
            print(f"🔍 Page title: {self.driver.title}")
            print(f"🔍 Current URL: {self.driver.current_url}")
            
            # Wait a bit for page to fully load
            time.sleep(5)
            
            # Look for the back button
            back_button_selectors = [
                "a[href='/admin']",
                "a[href*='admin']",
                "a:contains('Back')",
                "a:contains('Dashboard')",
                ".back-button",
                "[href*='admin']:not([href*='downloads'])"
            ]
            
            back_button = None
            for selector in back_button_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text content
                        xpath = f"//a[contains(text(), 'Back')]"
                        back_button = self.driver.find_element(By.XPATH, xpath)
                        break
                    else:
                        back_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                except NoSuchElementException:
                    continue
            
            if not back_button:
                # Try to find any link with "admin" in href that's not downloads
                print("🔍 Searching all links on the page...")
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    print(f"📋 Found {len(all_links)} total links:")
                    
                    for i, link in enumerate(all_links[:10]):  # Show first 10 links
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        print(f"   {i+1}. '{text}' -> {href}")
                        
                        if href and 'admin' in href and 'downloads' not in href:
                            back_button = link
                            print(f"🎯 This looks like our back button!")
                            break
                    
                    if len(all_links) > 10:
                        print(f"   ... and {len(all_links) - 10} more links")
                        
                except Exception as e:
                    print(f"❌ Error getting links: {e}")
                    pass
            
            if back_button:
                print(f"🎯 Found back button! Clicking it...")
                print(f"   Text: '{back_button.text.strip()}'")
                print(f"   URL: {back_button.get_attribute('href')}")
                
                # Wait a moment for user to see
                time.sleep(2)
                
                # Click the back button
                back_button.click()
                
                # Wait for dashboard to load
                time.sleep(5)
                print("✅ Clicked back button, now on dashboard!")
                
                return True
            else:
                print("❌ Could not find back button")
                return False
                
        except Exception as e:
            print(f"❌ Error navigating to dashboard: {str(e)}")
            return False
    
    def scrape_dashboard_data(self):
        """Scrape data from the admin dashboard"""
        try:
            current_url = self.driver.current_url
            title = self.driver.title
            
            print(f"\n📊 DASHBOARD DATA COLLECTION")
            print(f"🔗 Current URL: {current_url}")
            print(f"📄 Page Title: {title}")
            print(f"⏰ Waiting for dashboard content to load...")
            
            # Wait longer for dynamic content
            time.sleep(10)
            
            # Collect various types of data
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'url': current_url,
                'title': title,
                'status': 'success'
            }
            
            # Get all links
            print("🔗 Collecting all links...")
            links = []
            try:
                link_elements = self.driver.find_elements(By.TAG_NAME, "a")
                for link in link_elements:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text:
                        links.append({'href': href, 'text': text})
                print(f"   Found {len(links)} links")
            except:
                pass
            
            dashboard_data['links'] = links
            
            # Get all buttons
            print("🔘 Collecting all buttons...")
            buttons = []
            try:
                button_elements = self.driver.find_elements(By.TAG_NAME, "button")
                for button in button_elements:
                    text = button.text.strip()
                    onclick = button.get_attribute('onclick')
                    classes = button.get_attribute('class')
                    if text:
                        buttons.append({
                            'text': text,
                            'onclick': onclick,
                            'classes': classes
                        })
                print(f"   Found {len(buttons)} buttons")
            except:
                pass
            
            dashboard_data['buttons'] = buttons
            
            # Get tables if any
            print("📋 Looking for tables...")
            tables = []
            try:
                table_elements = self.driver.find_elements(By.TAG_NAME, "table")
                for i, table in enumerate(table_elements):
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    table_data = {
                        'index': i,
                        'rows': len(rows),
                        'headers': [],
                        'sample_data': []
                    }
                    
                    # Get headers
                    try:
                        header_cells = table.find_elements(By.TAG_NAME, "th")
                        table_data['headers'] = [cell.text.strip() for cell in header_cells]
                    except:
                        pass
                    
                    # Get first few rows of data
                    try:
                        for row in rows[:3]:  # First 3 rows
                            cells = row.find_elements(By.TAG_NAME, "td")
                            row_data = [cell.text.strip() for cell in cells]
                            if row_data:
                                table_data['sample_data'].append(row_data)
                    except:
                        pass
                    
                    tables.append(table_data)
                print(f"   Found {len(tables)} tables")
            except:
                pass
            
            dashboard_data['tables'] = tables
            
            # Get headings
            print("📝 Collecting page headings...")
            headings = []
            try:
                for level in range(1, 7):
                    h_elements = self.driver.find_elements(By.TAG_NAME, f"h{level}")
                    for h in h_elements:
                        text = h.text.strip()
                        if text:
                            headings.append({'level': level, 'text': text})
                print(f"   Found {len(headings)} headings")
            except:
                pass
            
            dashboard_data['headings'] = headings
            
            # Get forms
            print("📝 Looking for forms...")
            forms = []
            try:
                form_elements = self.driver.find_elements(By.TAG_NAME, "form")
                for i, form in enumerate(form_elements):
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    selects = form.find_elements(By.TAG_NAME, "select")
                    textareas = form.find_elements(By.TAG_NAME, "textarea")
                    
                    form_data = {
                        'index': i,
                        'action': form.get_attribute('action'),
                        'method': form.get_attribute('method'),
                        'inputs': len(inputs),
                        'selects': len(selects),
                        'textareas': len(textareas)
                    }
                    forms.append(form_data)
                print(f"   Found {len(forms)} forms")
            except:
                pass
            
            dashboard_data['forms'] = forms
            
            # Get page source snippet
            dashboard_data['page_source_snippet'] = self.driver.page_source[:2000]
            
            print(f"\n✅ Dashboard data collection complete!")
            print(f"📊 Summary:")
            print(f"   - Links: {len(dashboard_data.get('links', []))}")
            print(f"   - Buttons: {len(dashboard_data.get('buttons', []))}")
            print(f"   - Tables: {len(dashboard_data.get('tables', []))}")
            print(f"   - Headings: {len(dashboard_data.get('headings', []))}")
            print(f"   - Forms: {len(dashboard_data.get('forms', []))}")
            
            # Keep browser open for a bit so user can see
            print(f"\n👀 Browser will stay open for 15 seconds for you to inspect...")
            for i in range(15, 0, -1):
                print(f"⏰ Closing in {i} seconds...")
                time.sleep(1)
            
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Error collecting dashboard data: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def save_results(self, data):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        return filename
    
    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        print("🚀 Starting Dashboard Data Scraper")
        scraper = DashboardScraper()
        
        # Navigate to dashboard via downloads page
        if scraper.navigate_to_dashboard():
            # Scrape dashboard data
            data = scraper.scrape_dashboard_data()
            
            # Save results
            scraper.save_results(data)
        else:
            print("❌ Failed to navigate to dashboard")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()