#!/usr/bin/env python3
"""
Student Data Scraper - Click on specific students and gather their data
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

class StudentDataScraper:
    def __init__(self):
        self.driver = None
        self.student_data = {}
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
            logger.info("Student data scraper initialized")
            
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
                
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                
                username_field.send_keys(username)
                password_field.send_keys(password)
                password_field.send_keys("\n")
                
                time.sleep(3)
                return True
                
            except NoSuchElementException:
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def read_students_list(self):
        """Read student names from students.txt"""
        try:
            with open('students.txt', 'r') as f:
                students = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Extract just the name (before any comma or tab)
                        name = line.split(',')[0].split('\t')[0].strip()
                        if name:
                            students.append(name)
                
            print(f"📚 Loaded {len(students)} students from students.txt:")
            for i, student in enumerate(students, 1):
                print(f"   {i}. {student}")
            
            return students
            
        except FileNotFoundError:
            print("❌ students.txt file not found!")
            return []
        except Exception as e:
            print(f"❌ Error reading students.txt: {e}")
            return []
    
    def navigate_to_dashboard(self):
        """Navigate directly to admin dashboard"""
        try:
            print("🚀 Navigating directly to admin dashboard...")
            self.driver.get("https://app.alphamath.school/admin")
            
            # Check for login
            if "login" in self.driver.page_source.lower():
                print("🔑 Login required, attempting authentication...")
                if not self.login_quick():
                    return False
                
                # Navigate again after login
                self.driver.get("https://app.alphamath.school/admin")
                print("✅ Login successful!")
                time.sleep(3)
            else:
                print("✅ Already logged in!")
            
            # Wait for dashboard to load
            time.sleep(5)
            
            print(f"📄 Dashboard loaded!")
            print(f"🔗 Current URL: {self.driver.current_url}")
            print(f"📄 Page Title: {self.driver.title}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to dashboard: {str(e)}")
            return False
    
    def _search_for_student_in_visible_area(self, student_name):
        """Search for student in currently visible area"""
        try:
            # Look for student name in visible table rows
            rows = self.driver.find_elements(By.XPATH, "//table//tr")
            for row in rows:
                try:
                    if student_name.lower() in row.text.lower():
                        # Found the student, now find clickable element
                        name_cell = row.find_element(By.XPATH, ".//td[1]//a | .//td[1]")
                        print(f"✅ Found {student_name} in visible area")
                        return name_cell
                except:
                    continue
            return None
        except:
            return None
    
    def _scroll_and_search_student(self, student_name):
        """Scroll through the page to find the student"""
        try:
            # Get the table container or body for scrolling
            table_container = self.driver.find_element(By.TAG_NAME, "table")
            
            # Track how far we've scrolled
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 20  # Prevent infinite scrolling
            
            while scroll_attempts < max_scrolls:
                print(f"   📜 Scrolling attempt {scroll_attempts + 1} looking for {student_name}...")
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Check if student is now visible
                student_element = self._search_for_student_in_visible_area(student_name)
                if student_element:
                    return student_element
                
                # Check if we've reached the bottom (no new content loaded)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print(f"   📜 Reached bottom of page, {student_name} not found")
                    break
                
                last_height = new_height
                scroll_attempts += 1
            
            # Try one more comprehensive search after scrolling
            print(f"   🔍 Final comprehensive search for {student_name}...")
            all_rows = self.driver.find_elements(By.XPATH, "//table//tr")
            print(f"   📋 Total rows found: {len(all_rows)}")
            
            for i, row in enumerate(all_rows):
                try:
                    row_text = row.text.strip()
                    if student_name.lower() in row_text.lower():
                        print(f"   ✅ Found {student_name} in row {i}: {row_text[:100]}")
                        # Scroll to this element
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                        time.sleep(1)
                        
                        # Find clickable element in this row
                        try:
                            clickable = row.find_element(By.XPATH, ".//a | .//td[1]")
                            return clickable
                        except:
                            return row
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error during scroll search: {e}")
            return None
    
    def find_and_click_student(self, student_name):
        """Find a specific student in the table and click on them"""
        try:
            print(f"\n🔍 Looking for student: {student_name}")
            
            # Wait for table to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # First, try to find the student in the currently visible area
            student_element = self._search_for_student_in_visible_area(student_name)
            
            # If not found, scroll down and search
            if not student_element:
                print(f"   Student not visible, scrolling to find {student_name}...")
                student_element = self._scroll_and_search_student(student_name)
            
            # Look for the student name in the table
            # Try different approaches to find the student
            student_selectors = [
                f"//td[contains(text(), '{student_name}')]",
                f"//a[contains(text(), '{student_name}')]",
                f"//tr[contains(., '{student_name}')]//a",
                f"//tr[contains(., '{student_name}')]//td[1]"
            ]
            
            if not student_element:
                for selector in student_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if student_name.lower() in element.text.lower():
                                student_element = element
                                print(f"✅ Found {student_name} using selector: {selector}")
                                break
                        if student_element:
                            break
                    except:
                        continue
            
            if student_element:
                # If it's a clickable element (like a link), click it
                if student_element.tag_name == 'a':
                    clickable = student_element
                else:
                    # Try to find a clickable element in the same row
                    try:
                        row = student_element.find_element(By.XPATH, "./ancestor::tr")
                        clickable = row.find_element(By.TAG_NAME, "a")
                    except:
                        clickable = student_element
                
                print(f"🎯 Clicking on {student_name}...")
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", clickable)
                time.sleep(1)
                
                # Click the element
                clickable.click()
                time.sleep(3)
                
                print(f"✅ Successfully clicked on {student_name}")
                return True
            else:
                print(f"❌ Could not find {student_name} in the table")
                
                # Debug: Show available student names
                try:
                    rows = self.driver.find_elements(By.XPATH, "//table//tr")
                    print(f"🔍 Available students in table:")
                    for i, row in enumerate(rows[1:6]):  # Skip header, show first 5
                        try:
                            name_cell = row.find_element(By.XPATH, ".//td[1]")
                            print(f"   - {name_cell.text.strip()}")
                        except:
                            pass
                except:
                    pass
                
                return False
                
        except Exception as e:
            print(f"❌ Error finding/clicking student {student_name}: {str(e)}")
            return False
    
    def scrape_student_page(self, student_name):
        """Scrape data from the current student page"""
        try:
            print(f"📊 Scraping data for {student_name}...")
            
            # Wait for page to load
            time.sleep(3)
            
            student_data = {
                'name': student_name,
                'timestamp': datetime.now().isoformat(),
                'url': self.driver.current_url,
                'page_title': self.driver.title,
                'status': 'success'
            }
            
            # Get page content
            print(f"   📄 Page title: {self.driver.title}")
            print(f"   🔗 URL: {self.driver.current_url}")
            
            # Collect various data elements
            
            # Get all text content
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                student_data['page_text'] = body.text[:2000]  # First 2000 chars
            except:
                pass
            
            # Get tables if any
            try:
                tables = []
                table_elements = self.driver.find_elements(By.TAG_NAME, "table")
                for i, table in enumerate(table_elements):
                    table_info = {
                        'index': i,
                        'rows': len(table.find_elements(By.TAG_NAME, "tr")),
                        'html_snippet': table.get_attribute("outerHTML")[:1000]
                    }
                    tables.append(table_info)
                student_data['tables'] = tables
                print(f"   📋 Found {len(tables)} tables")
            except:
                pass
            
            # Get progress/score information
            try:
                score_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'score') or contains(text(), 'Score') or contains(text(), 'points') or contains(text(), 'Points')]")
                scores = [elem.text.strip() for elem in score_elements[:5]]
                student_data['scores'] = scores
                if scores:
                    print(f"   🎯 Found score info: {scores}")
            except:
                pass
            
            # Get activity/progress information
            try:
                activity_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'activity') or contains(text(), 'Activity') or contains(text(), 'progress') or contains(text(), 'Progress')]")
                activities = [elem.text.strip() for elem in activity_elements[:5]]
                student_data['activities'] = activities
                if activities:
                    print(f"   📈 Found activity info: {activities}")
            except:
                pass
            
            # Get any charts or graphs
            try:
                chart_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'chart') or contains(@class, 'graph')]")
                student_data['charts_found'] = len(chart_elements)
                print(f"   📊 Found {len(chart_elements)} charts/graphs")
            except:
                pass
            
            # Screenshot for reference
            try:
                screenshot_filename = f"student_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_filename)
                student_data['screenshot'] = screenshot_filename
                print(f"   📸 Screenshot saved: {screenshot_filename}")
            except:
                pass
            
            print(f"✅ Data collection complete for {student_name}")
            
            # Wait a moment before going back
            time.sleep(2)
            
            return student_data
            
        except Exception as e:
            print(f"❌ Error scraping data for {student_name}: {str(e)}")
            return {
                'name': student_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
    
    def go_back_to_dashboard(self):
        """Navigate back to the dashboard"""
        try:
            print("🔙 Returning to dashboard...")
            
            # Try browser back button first
            self.driver.back()
            time.sleep(3)
            
            # If that doesn't work, navigate directly
            if "admin" not in self.driver.current_url or "downloads" in self.driver.current_url:
                self.driver.get("https://app.alphamath.school/admin")
                time.sleep(3)
            
            print("✅ Back on dashboard")
            return True
            
        except Exception as e:
            print(f"❌ Error returning to dashboard: {str(e)}")
            return False
    
    def process_all_students(self):
        """Main function to process all students"""
        try:
            # Read student list
            students = self.read_students_list()
            if not students:
                print("❌ No students to process")
                return
            
            # Navigate to dashboard
            if not self.navigate_to_dashboard():
                print("❌ Failed to reach dashboard")
                return
            
            print(f"\n🎯 Starting to process {len(students)} students...")
            
            # Process each student
            for i, student_name in enumerate(students, 1):
                print(f"\n{'='*50}")
                print(f"📚 Processing student {i}/{len(students)}: {student_name}")
                print(f"{'='*50}")
                
                # Find and click on the student
                if self.find_and_click_student(student_name):
                    # Scrape their data
                    student_data = self.scrape_student_page(student_name)
                    self.student_data[student_name] = student_data
                    
                    # Go back to dashboard for next student
                    self.go_back_to_dashboard()
                else:
                    # Record that we couldn't find this student
                    self.student_data[student_name] = {
                        'name': student_name,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'not_found',
                        'error': 'Student not found in table'
                    }
                
                # Small delay between students
                time.sleep(2)
            
            print(f"\n🎉 Completed processing all students!")
            self.save_results()
            
        except Exception as e:
            print(f"❌ Error processing students: {str(e)}")
            self.save_results()  # Save whatever we collected
    
    def save_results(self):
        """Save all collected student data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"student_data_{timestamp}.json"
            
            summary = {
                'collection_timestamp': datetime.now().isoformat(),
                'total_students_attempted': len(self.student_data),
                'successful_collections': len([d for d in self.student_data.values() if d.get('status') == 'success']),
                'failed_collections': len([d for d in self.student_data.values() if d.get('status') == 'failed']),
                'not_found': len([d for d in self.student_data.values() if d.get('status') == 'not_found']),
                'student_data': self.student_data
            }
            
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            print(f"📊 Summary:")
            print(f"   - Total students: {summary['total_students_attempted']}")
            print(f"   - Successful: {summary['successful_collections']}")
            print(f"   - Failed: {summary['failed_collections']}")
            print(f"   - Not found: {summary['not_found']}")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def close(self):
        if self.driver:
            print("\n👋 Closing browser...")
            time.sleep(3)  # Give time to see final results
            self.driver.quit()

def main():
    scraper = None
    try:
        print("🚀 Starting Student Data Scraper")
        print("📚 This will click on each student in students.txt and collect their data")
        
        scraper = StudentDataScraper()
        scraper.process_all_students()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()