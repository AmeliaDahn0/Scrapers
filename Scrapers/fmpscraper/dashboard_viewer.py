#!/usr/bin/env python3
"""
Dashboard Viewer - Show students on the admin dashboard
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

class DashboardViewer:
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
            logger.info("Dashboard viewer initialized")
            
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
                password_field.send_keys("\n")  # Submit
                
                time.sleep(2)  # Quick wait
                return True
                
            except NoSuchElementException:
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def view_dashboard_and_students(self):
        """Navigate to dashboard and show students"""
        try:
            logger.info("Navigating to admin dashboard...")
            self.driver.get("https://app.alphamath.school/admin")
            
            # Quick check for login
            if "login" in self.driver.page_source.lower():
                logger.info("Attempting login...")
                if not self.login_quick():
                    return {"error": "Login failed"}
                
                # Navigate again after login
                self.driver.get("https://app.alphamath.school/admin")
                print("✅ Login successful! Waiting for dashboard to load...")
                time.sleep(5)
            else:
                print("✅ Already logged in!")
            
            # Get page info
            title = self.driver.title
            current_url = self.driver.current_url
            
            print(f"📄 Dashboard loaded: {title}")
            print(f"🔗 Current URL: {current_url}")
            print("🔍 Looking for students in the table...")
            
            # Wait for table to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                print("📋 Table found!")
            except:
                print("❌ No table found on page")
                return {"error": "No table found"}
            
            # Collect students by scrolling
            print("\n📜 Scrolling through page to collect all students...")
            all_students = []
            scroll_count = 0
            
            # Start from top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            while scroll_count < 20:  # Limit scrolling
                # Get current students
                rows = self.driver.find_elements(By.XPATH, "//table//tr")
                
                current_visible = []
                for row in rows:
                    try:
                        first_cell = row.find_element(By.XPATH, ".//td[1]")
                        name = first_cell.text.strip()
                        
                        # Filter valid student names
                        if name and len(name) > 2 and name not in ['NAME', 'Name', 'CAMPUS']:
                            if name not in all_students:
                                all_students.append(name)
                                current_visible.append(name)
                    except:
                        continue
                
                if current_visible:
                    print(f"   Found {len(current_visible)} new students in scroll {scroll_count + 1}")
                    for student in current_visible:
                        print(f"      📚 {student}")
                
                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(1)
                scroll_count += 1
                
                # Check if we hit bottom
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                current_scroll = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                
                if current_scroll >= scroll_height - 100:
                    print("📜 Reached bottom of page")
                    break
            
            print(f"\n🎉 Student Discovery Complete!")
            print(f"📊 Total students found: {len(all_students)}")
            
            # Show all students
            print(f"\n📋 All Students on Dashboard:")
            for i, student in enumerate(all_students, 1):
                print(f"   {i:2d}. {student}")
            
            # Compare with target students
            print(f"\n🎯 Checking your target students...")
            try:
                with open('students.txt', 'r') as f:
                    target_students = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            name = line.split(',')[0].split('\t')[0].strip()
                            if name:
                                target_students.append(name)
                
                print(f"📚 Your target students ({len(target_students)}):")
                matches = []
                
                for target in target_students:
                    found = False
                    for available in all_students:
                        if target.lower() in available.lower() or available.lower() in target.lower():
                            matches.append((target, available))
                            print(f"   ✅ '{target}' → FOUND as '{available}'")
                            found = True
                            break
                    if not found:
                        print(f"   ❌ '{target}' → NOT FOUND")
                
                print(f"\n📊 Summary:")
                print(f"   - Students on dashboard: {len(all_students)}")
                print(f"   - Your target students: {len(target_students)}")
                print(f"   - Successful matches: {len(matches)}")
                
            except Exception as e:
                print(f"❌ Error reading students.txt: {e}")
            
            # Keep browser open for inspection
            print(f"\n👀 Browser will stay open for 20 seconds for you to inspect the dashboard...")
            print(f"   You can scroll through and see all the students!")
            
            for i in range(20, 0, -1):
                print(f"⏰ Closing in {i} seconds...", end='\r')
                time.sleep(1)
            
            results = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'url': current_url,
                'title': title,
                'total_students': len(all_students),
                'students': all_students
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    viewer = None
    try:
        viewer = DashboardViewer()
        results = viewer.view_dashboard_and_students()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_students_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if viewer:
            viewer.close()

if __name__ == "__main__":
    main()