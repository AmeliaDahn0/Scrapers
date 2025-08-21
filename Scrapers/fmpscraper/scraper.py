#!/usr/bin/env python3
"""
FastMath Pro Downloads Scraper
A Selenium-based web scraper for app.fastmath.pro/admin/downloads
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
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FastMathProScraper:
    def __init__(self, headless=True, timeout=30):
        """
        Initialize the scraper with Chrome WebDriver
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default timeout for web elements
        """
        self.timeout = timeout
        self.driver = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use ChromeDriverManager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(self.timeout)
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def login(self, username=None, password=None):
        """
        Attempt to login to the admin panel
        
        Args:
            username (str): Username (if None, reads from environment)
            password (str): Password (if None, reads from environment)
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Get credentials from environment if not provided
            if username is None:
                username = os.getenv('USERNAME')
            if password is None:
                password = os.getenv('PASSWORD')
            
            if not username or not password:
                logger.error("No credentials provided. Please set USERNAME and PASSWORD in .env file")
                logger.error(f"USERNAME env var: {'SET' if os.getenv('USERNAME') else 'NOT SET'}")
                logger.error(f"PASSWORD env var: {'SET' if os.getenv('PASSWORD') else 'NOT SET'}")
                return False
            
            logger.info("Attempting to login...")
            
            # Look for common login form elements
            login_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[name='username']", 
                "input[id='email']",
                "input[id='username']"
            ]
            
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[id='password']"
            ]
            
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign in')",
                ".login-button",
                ".submit-button"
            ]
            
            # Find username field
            username_field = None
            for selector in login_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not username_field:
                logger.error("Could not find username/email field")
                return False
            
            # Find password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Fill in credentials
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Find and click submit button
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                submit_button.click()
            else:
                # Try submitting the form by pressing Enter
                password_field.send_keys("\n")
            
            # Wait for login to process
            time.sleep(3)
            
            # Check if login was successful by looking for login indicators
            if self.is_login_required():
                logger.error("Login appears to have failed - still seeing login page")
                return False
            else:
                logger.info("Login appears successful")
                return True
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def scrape_downloads_page(self, url="https://app.alphamath.school/admin/downloads"):
        """
        Scrape the FastMath Pro admin downloads page
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            dict: Scraped data
        """
        scraped_data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "data": [],
            "error": None
        }
        
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if login is required and attempt login
            if self.is_login_required():
                logger.warning("Login page detected. Attempting authentication...")
                if self.login():
                    logger.info("Login successful, proceeding with scraping...")
                    # Navigate to the downloads page again after login
                    self.driver.get(url)
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Check if still on login page
                    if self.is_login_required():
                        scraped_data["error"] = "Authentication failed - still on login page"
                        return scraped_data
                else:
                    scraped_data["error"] = "Authentication failed - could not login"
                    return scraped_data
            
            # Get page title
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Look for and click "Back to Admin Dashboard" button to navigate to student dashboard
            logger.info("Looking for 'Back to Admin Dashboard' button...")
            try:
                back_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Back to Admin Dashboard')]")
                logger.info(f"Found back button: {back_button.text}")
                logger.info("Clicking 'Back to Admin Dashboard' button...")
                back_button.click()
                time.sleep(5)  # Wait for navigation
                
                # Wait for dashboard to load
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                logger.info("Successfully navigated to admin dashboard")
                
                # Now scrape dashboard student data
                logger.info("Scraping dashboard student data...")
                student_data = self.extract_dashboard_students()
                
            except Exception as e:
                logger.error(f"Could not navigate to dashboard: {str(e)}")
                student_data = []
            
            # Scrape download links and information (if still on downloads page)
            downloads = self.extract_download_data()
            
            # Scrape general page information
            page_info = self.extract_page_info()
            
            scraped_data.update({
                "status": "success",
                "page_title": page_title,
                "page_info": page_info,
                "downloads": downloads,
                "total_downloads": len(downloads),
                "students": student_data if 'student_data' in locals() else [],
                "total_students": len(student_data) if 'student_data' in locals() else 0
            })
            
            logger.info(f"Successfully scraped {len(downloads)} download items")
            
        except TimeoutException:
            error_msg = f"Timeout waiting for page to load: {url}"
            logger.error(error_msg)
            scraped_data["error"] = error_msg
            
        except Exception as e:
            error_msg = f"Error scraping page: {str(e)}"
            logger.error(error_msg)
            scraped_data["error"] = error_msg
            
        return scraped_data
    
    def is_login_required(self):
        """Check if the page requires login"""
        login_indicators = [
            "login", "sign in", "username", "password", 
            "authentication", "access denied", "unauthorized"
        ]
        
        page_text = self.driver.page_source.lower()
        return any(indicator in page_text for indicator in login_indicators)
    
    def extract_download_data(self):
        """Extract download links and related information"""
        downloads = []
        
        try:
            # Common selectors for download links
            download_selectors = [
                "a[href*='download']",
                "a[href*='.pdf']",
                "a[href*='.zip']",
                "a[href*='.exe']",
                "a[href*='.dmg']",
                ".download-link",
                ".download-item",
                "[data-download]"
            ]
            
            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        download_info = {
                            "text": element.text.strip(),
                            "href": element.get_attribute("href"),
                            "title": element.get_attribute("title"),
                            "data_attrs": self.get_data_attributes(element)
                        }
                        if download_info["href"] and download_info not in downloads:
                            downloads.append(download_info)
                except NoSuchElementException:
                    continue
            
            # Also look for buttons or divs that might contain download information
            button_selectors = [
                "button[class*='download']",
                ".btn-download",
                "[role='button'][aria-label*='download']"
            ]
            
            for selector in button_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        download_info = {
                            "text": element.text.strip(),
                            "type": "button",
                            "onclick": element.get_attribute("onclick"),
                            "data_attrs": self.get_data_attributes(element)
                        }
                        downloads.append(download_info)
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting download data: {str(e)}")
        
        return downloads
    
    def extract_page_info(self):
        """Extract general page information"""
        page_info = {}
        
        try:
            # Get all headings
            headings = []
            for level in range(1, 7):
                h_elements = self.driver.find_elements(By.TAG_NAME, f"h{level}")
                for h in h_elements:
                    if h.text.strip():
                        headings.append({
                            "level": level,
                            "text": h.text.strip()
                        })
            
            page_info["headings"] = headings
            
            # Get all tables if any
            tables = []
            table_elements = self.driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(table_elements):
                table_data = {
                    "index": i,
                    "rows": len(table.find_elements(By.TAG_NAME, "tr")),
                    "html": table.get_attribute("outerHTML")[:500] + "..." if len(table.get_attribute("outerHTML")) > 500 else table.get_attribute("outerHTML")
                }
                tables.append(table_data)
            
            page_info["tables"] = tables
            
            # Get meta information
            page_info["url"] = self.driver.current_url
            page_info["title"] = self.driver.title
            
        except Exception as e:
            logger.error(f"Error extracting page info: {str(e)}")
        
        return page_info
    
    def get_data_attributes(self, element):
        """Extract data-* attributes from an element"""
        data_attrs = {}
        try:
            # Get all attributes
            attrs = self.driver.execute_script(
                "var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;",
                element
            )
            
            # Filter data attributes
            data_attrs = {k: v for k, v in attrs.items() if k.startswith('data-')}
        except Exception as e:
            logger.error(f"Error getting data attributes: {str(e)}")
        
        return data_attrs
    
    def extract_dashboard_students(self):
        """Extract student information from the admin dashboard"""
        students = []
        
        try:
            logger.info("Extracting student data from dashboard...")
            
            # Scroll to load all students
            logger.info("Scrolling to load all students...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            
            while scroll_count < 20:  # Limit scrolls to prevent infinite loop
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1
            
            logger.info(f"Completed {scroll_count} scrolls to load content")
            
            # Find the table with student data
            table = self.driver.find_element(By.TAG_NAME, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            logger.info(f"Found table with {len(rows)} rows")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:  # Make sure we have at least name and some data
                        student_name = cells[0].text.strip()
                        
                        # Skip empty names or header rows
                        if student_name and not student_name.isdigit() and len(student_name) > 2:
                            student_info = {
                                "index": i,
                                "name": student_name,
                                "row_data": [cell.text.strip() for cell in cells]
                            }
                            students.append(student_info)
                            
                except Exception as e:
                    logger.debug(f"Error processing row {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(students)} students from dashboard")
            
        except Exception as e:
            logger.error(f"Error extracting dashboard students: {str(e)}")
        
        return students
    
    def save_results(self, data, format='json'):
        """Save scraped results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filename = f"fastmath_downloads_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filename}")
            
        elif format == 'csv' and data.get('downloads'):
            filename = f"fastmath_downloads_{timestamp}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if data['downloads']:
                    writer = csv.DictWriter(f, fieldnames=data['downloads'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['downloads'])
            logger.info(f"Downloads saved to {filename}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def main():
    """Main function to run the scraper"""
    scraper = None
    
    try:
        # Get configuration from environment
        headless_mode = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
        timeout_seconds = int(os.getenv('TIMEOUT_SECONDS', '30'))
        
        # Initialize scraper
        logger.info("Starting FastMath Pro Downloads Scraper")
        logger.info(f"Configuration: Headless={headless_mode}, Timeout={timeout_seconds}s")
        
        # Debug environment variables
        logger.info(f"Environment check - USERNAME: {'SET' if os.getenv('USERNAME') else 'NOT SET'}")
        logger.info(f"Environment check - PASSWORD: {'SET' if os.getenv('PASSWORD') else 'NOT SET'}")
        logger.info(f"Environment check - SUPABASE_URL: {'SET' if os.getenv('SUPABASE_URL') else 'NOT SET'}")
        logger.info(f"Environment check - CI: {os.getenv('CI', 'NOT SET')}")
        scraper = FastMathProScraper(headless=headless_mode, timeout=timeout_seconds)
        
        # Scrape the downloads page
        results = scraper.scrape_downloads_page()
        
        # Print results
        print(f"\nScraping Results:")
        print(f"Status: {results['status']}")
        print(f"URL: {results['url']}")
        print(f"Timestamp: {results['timestamp']}")
        
        if results['status'] == 'success':
            print(f"Page Title: {results.get('page_title', 'N/A')}")
            print(f"Total Downloads Found: {results.get('total_downloads', 0)}")
            
            if results.get('downloads'):
                print("\nDownload Items Found:")
                for i, download in enumerate(results['downloads'][:5], 1):  # Show first 5
                    print(f"{i}. {download.get('text', 'N/A')} - {download.get('href', 'N/A')}")
                
                if len(results['downloads']) > 5:
                    print(f"... and {len(results['downloads']) - 5} more items")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        # Save results
        scraper.save_results(results, 'json')
        if results.get('downloads'):
            scraper.save_results(results, 'csv')
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()