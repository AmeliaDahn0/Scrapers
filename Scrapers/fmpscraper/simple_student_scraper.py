#!/usr/bin/env python3
"""
Simple Student Scraper - One student at a time with robust scrolling
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

class SimpleStudentScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver in visible mode"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1400,1000")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            print("✅ Browser initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {str(e)}")
            raise
    
    def login_and_navigate(self):
        """Login and navigate to dashboard"""
        try:
            print("🚀 Navigating to admin dashboard...")
            self.driver.get("https://app.alphamath.school/admin")
            
            # Check for login
            time.sleep(3)
            if "login" in self.driver.page_source.lower():
                print("🔑 Login required...")
                username = os.getenv('USERNAME')
                password = os.getenv('PASSWORD')
                
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                
                username_field.send_keys(username)
                password_field.send_keys(password)
                password_field.send_keys("\n")
                
                time.sleep(5)
                print("✅ Login completed")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            print(f"📄 Dashboard loaded: {self.driver.title}")
            print(f"🔗 URL: {self.driver.current_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during login/navigation: {str(e)}")
            return False
    
    def scroll_and_find_all_students(self):
        """Scroll through the entire page and collect all visible student names"""
        try:
            print("📜 Scrolling through page to find all students...")
            
            all_students_found = []
            scroll_position = 0
            
            # Start from top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            while True:
                # Get currently visible students
                current_students = self.get_visible_students()
                
                # Add new students to our list
                for student in current_students:
                    if student not in all_students_found:
                        all_students_found.append(student)
                        print(f"   📚 Found: {student}")
                
                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                
                # Check if we've reached the bottom
                new_scroll_position = self.driver.execute_script("return window.pageYOffset;")
                if new_scroll_position == scroll_position:
                    # Try one more bigger scroll
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(2)
                    final_position = self.driver.execute_script("return window.pageYOffset;")
                    if final_position == new_scroll_position:
                        print("📜 Reached bottom of page")
                        break
                
                scroll_position = new_scroll_position
            
            print(f"📋 Total students found: {len(all_students_found)}")
            
            # Show all found students
            for i, student in enumerate(all_students_found, 1):
                print(f"   {i}. {student}")
            
            return all_students_found
            
        except Exception as e:
            print(f"❌ Error during scrolling: {str(e)}")
            return []
    
    def get_visible_students(self):
        """Get student names currently visible on screen"""
        students = []
        try:
            # Look for table rows
            rows = self.driver.find_elements(By.XPATH, "//table//tr")
            
            for row in rows:
                try:
                    # Get the first cell which should contain the student name
                    first_cell = row.find_element(By.XPATH, ".//td[1]")
                    student_name = first_cell.text.strip()
                    
                    # Filter out headers and empty cells
                    if student_name and student_name not in ['NAME', 'Name', ''] and len(student_name) > 3:
                        students.append(student_name)
                        
                except:
                    continue
                    
        except Exception as e:
            pass
            
        return students
    
    def find_and_click_student(self, student_name):
        """Find and click on a specific student"""
        try:
            print(f"\n🎯 Looking for: {student_name}")
            
            # Scroll to top first
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Search while scrolling
            max_scrolls = 50
            scroll_count = 0
            
            while scroll_count < max_scrolls:
                # Check current visible area
                rows = self.driver.find_elements(By.XPATH, "//table//tr")
                
                for row in rows:
                    try:
                        row_text = row.text.strip()
                        if student_name.lower() in row_text.lower():
                            print(f"✅ Found {student_name}!")
                            
                            # Scroll the row into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", row)
                            time.sleep(2)
                            
                            # Try to find clickable element
                            try:
                                # Look for link in first cell
                                clickable = row.find_element(By.XPATH, ".//td[1]//a")
                            except:
                                try:
                                    # Try the first cell itself
                                    clickable = row.find_element(By.XPATH, ".//td[1]")
                                except:
                                    clickable = row
                            
                            # Click it
                            print(f"🖱️  Clicking on {student_name}...")
                            self.driver.execute_script("arguments[0].click();", clickable)
                            time.sleep(3)
                            
                            print(f"✅ Successfully clicked {student_name}")
                            return True
                            
                    except Exception as e:
                        continue
                
                # Scroll down and try again
                self.driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(0.5)
                scroll_count += 1
            
            print(f"❌ Could not find {student_name} after scrolling")
            return False
            
        except Exception as e:
            print(f"❌ Error finding {student_name}: {str(e)}")
            return False
    
    def scrape_current_page(self, student_name):
        """Scrape data from current student page"""
        try:
            print(f"📊 Scraping data for {student_name}...")
            
            # Wait for page to load
            time.sleep(3)
            
            data = {
                'student_name': student_name,
                'url': self.driver.current_url,
                'title': self.driver.title,
                'timestamp': datetime.now().isoformat(),
                'page_text': self.driver.find_element(By.TAG_NAME, "body").text[:1500],
                'status': 'success'
            }
            
            print(f"   📄 Page: {data['title']}")
            print(f"   🔗 URL: {data['url']}")
            
            # Take screenshot
            screenshot_name = f"student_{student_name.replace(' ', '_')}.png"
            self.driver.save_screenshot(screenshot_name)
            data['screenshot'] = screenshot_name
            print(f"   📸 Screenshot: {screenshot_name}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error scraping {student_name}: {str(e)}")
            return {'student_name': student_name, 'status': 'failed', 'error': str(e)}
    
    def go_back(self):
        """Go back to dashboard"""
        try:
            print("🔙 Returning to dashboard...")
            self.driver.back()
            time.sleep(3)
            
            # Wait for table to be visible
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            return True
        except:
            # If back doesn't work, navigate directly
            self.driver.get("https://app.alphamath.school/admin")
            time.sleep(5)
            return True
    
    def process_target_students(self):
        """Process only the students from students.txt"""
        try:
            # Read target students
            target_students = []
            with open('students.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name = line.split(',')[0].split('\t')[0].strip()
                        if name:
                            target_students.append(name)
            
            print(f"🎯 Target students: {len(target_students)}")
            for i, student in enumerate(target_students, 1):
                print(f"   {i}. {student}")
            
            # Login and navigate
            if not self.login_and_navigate():
                return
            
            # First, let's see all available students
            print(f"\n📋 Discovering all students on dashboard...")
            all_available = self.scroll_and_find_all_students()
            
            print(f"\n🔍 Checking which target students are available...")
            available_targets = []
            for target in target_students:
                found = False
                for available in all_available:
                    if target.lower() in available.lower() or available.lower() in target.lower():
                        available_targets.append((target, available))
                        print(f"   ✅ {target} → Found as: {available}")
                        found = True
                        break
                if not found:
                    print(f"   ❌ {target} → Not found")
            
            print(f"\n🎯 Processing {len(available_targets)} available target students...")
            
            results = {}
            
            # Process each available target student
            for i, (target_name, found_name) in enumerate(available_targets, 1):
                print(f"\n{'='*60}")
                print(f"📚 Processing {i}/{len(available_targets)}: {target_name}")
                print(f"{'='*60}")
                
                if self.find_and_click_student(found_name):
                    # Scrape the student's page
                    student_data = self.scrape_current_page(target_name)
                    results[target_name] = student_data
                    
                    # Go back to dashboard
                    self.go_back()
                    
                    # Small delay between students
                    time.sleep(2)
                else:
                    results[target_name] = {
                        'student_name': target_name,
                        'status': 'not_found',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"student_results_{timestamp}.json"
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_targets': len(target_students),
                'found_and_processed': len([r for r in results.values() if r.get('status') == 'success']),
                'results': results
            }
            
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\n🎉 Processing complete!")
            print(f"📊 Summary:")
            print(f"   - Target students: {summary['total_targets']}")
            print(f"   - Successfully processed: {summary['found_and_processed']}")
            print(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error processing students: {str(e)}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            print("\n👋 Closing browser in 5 seconds...")
            time.sleep(5)
            self.driver.quit()

def main():
    scraper = None
    try:
        print("🚀 Starting Simple Student Scraper")
        scraper = SimpleStudentScraper()
        scraper.process_target_students()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()