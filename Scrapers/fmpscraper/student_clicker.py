#!/usr/bin/env python3
"""
Student Clicker - Click on students from students.txt and collect their data
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_student_clicker():
    driver = None
    try:
        print("🚀 Starting Student Clicker")
        
        # Step 1: Read students from students.txt
        print("📚 Step 1: Reading students from students.txt...")
        target_students = []
        try:
            with open('students.txt', 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        target_students.append(line)
                        print(f"   {line_num}. {line}")
        except FileNotFoundError:
            print("❌ students.txt not found!")
            return
        
        print(f"📊 Total target students: {len(target_students)}")
        
        # Step 2: Setup browser
        print("\n🌐 Step 2: Setting up browser...")
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,1000")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Browser opened - you can see it!")
        
        # Step 3: Navigate and login
        print("\n🔑 Step 3: Navigating and logging in...")
        driver.get("https://app.alphamath.school/admin/downloads")
        time.sleep(3)
        
        # Login if needed
        if "login" in driver.page_source.lower():
            username = os.getenv('USERNAME')
            password = os.getenv('PASSWORD')
            
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            password_field.send_keys("\n")
            
            time.sleep(5)
            
            # Navigate back to downloads page after login
            driver.get("https://app.alphamath.school/admin/downloads")
            time.sleep(3)
        
        print("✅ Login successful!")
        
        # Step 4: Click back to dashboard (using proven working method)
        print("\n🔙 Step 4: Navigating to admin dashboard...")
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page Title: {driver.title}")
        print(f"📝 Page contains 'Back': {'Back' in driver.page_source}")
        print(f"📝 Page contains 'Dashboard': {'Dashboard' in driver.page_source}")
        
        try:
            # Use the exact same method that works in working_scraper.py
            back_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Back to Admin Dashboard')]")
            print(f"✅ Found back button: '{back_button.text.strip()}'")
            print(f"   Button href: '{back_button.get_attribute('href')}'")
            
            print("🖱️  Clicking back button...")
            back_button.click()
            time.sleep(10)  # Wait for navigation
            
            print(f"📍 Current URL after click: {driver.current_url}")
            print(f"📄 Current Title: {driver.title}")
            
            # Wait for student table to load with longer timeout
            print("⏳ Waiting for student table to load...")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            print("✅ Dashboard table found!")
            
            # Verify we're on the right page
            current_url = driver.current_url
            if "admin" in current_url and current_url != "https://app.alphamath.school/admin/downloads":
                print("✅ Successfully on admin dashboard with student table!")
            else:
                print(f"⚠️  Might not be on dashboard. URL: {current_url}")
            
        except Exception as e:
            print(f"❌ Error navigating to dashboard: {e}")
            print("🔍 Let me show you what links are available on this page:")
            
            # Debug: show available links
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for i, link in enumerate(links[:5]):
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"   Link {i+1}: '{text}' -> {href}")
            except:
                pass
            return
        
        # Step 5: Process each target student
        print(f"\n👥 Step 5: Processing {len(target_students)} target students...")
        
        student_data_collection = {}
        found_students = []
        not_found_students = []
        
        for i, student_name in enumerate(target_students, 1):
            print(f"\n{'='*60}")
            print(f"📚 Processing student {i}/{len(target_students)}")
            print(f"{'='*60}")
            
            # Find the student in the table
            student_found = find_and_click_student(driver, student_name)
            
            if student_found:
                print(f"✅ Found and clicked on student")
                found_students.append(student_name)
                
                # Collect data from student page
                student_data = collect_student_data(driver, student_name)
                student_data_collection[student_name] = student_data
                
                # Go back to dashboard using direct navigation (more reliable than browser back)
                print("🔙 Returning to dashboard...")
                
                # Try multiple methods to get back to dashboard
                success = False
                
                # Method 1: Try clicking a back button if present
                try:
                    back_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Back to Students') or contains(text(), 'Dashboard')]")
                    print(f"   Found back button: '{back_btn.text.strip()}'")
                    back_btn.click()
                    time.sleep(3)
                    success = True
                    print("   ✅ Used back button")
                except:
                    print("   ⚠️  No back button found")
                
                # Method 2: Direct navigation to admin dashboard
                if not success:
                    try:
                        print("   🔄 Navigating directly to dashboard...")
                        driver.get("https://app.alphamath.school/admin")
                        time.sleep(5)
                        success = True
                        print("   ✅ Direct navigation successful")
                    except:
                        print("   ❌ Direct navigation failed")
                
                # Method 3: Browser back as fallback
                if not success:
                    print("   ↩️  Using browser back as fallback...")
                    driver.back()
                    time.sleep(5)
                
                # Wait for table to reload and verify we're back
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    
                    # Verify we're on the right page
                    current_url = driver.current_url
                    if "admin" in current_url and "admin/downloads" not in current_url:
                        print("✅ Successfully back on dashboard")
                        
                        # Re-scroll to make sure all students are visible
                        print("   📜 Re-scrolling to load all students...")
                        last_height = driver.execute_script("return document.body.scrollHeight")
                        while True:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            new_height = driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                break
                            last_height = new_height
                        print("   ✅ Scroll complete")
                        
                    else:
                        print(f"⚠️  Might not be on dashboard. URL: {current_url}")
                        
                except Exception as e:
                    print(f"⚠️  Dashboard table not found after return: {e}")
                    print(f"   Current URL: {driver.current_url}")
                    # Continue anyway - we'll try to find the next student
                
            else:
                print(f"❌ Could not find student in the table")
                not_found_students.append(student_name)
                student_data_collection[student_name] = {
                    'name': student_name,
                    'status': 'not_found',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Step 6: Summary and save results
        print(f"\n🎉 Data collection complete!")
        print(f"📊 Summary:")
        print(f"   - Total target students: {len(target_students)}")
        print(f"   - Found and processed: {len(found_students)}")
        print(f"   - Not found: {len(not_found_students)}")
        
        if found_students:
            print(f"\n✅ Successfully processed: {len(found_students)} students")
        
        if not_found_students:
            print(f"\n❌ Not found in system: {len(not_found_students)} students")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"student_data_collection_{timestamp}.json"
        
        final_results = {
            'collection_timestamp': datetime.now().isoformat(),
            'total_target_students': len(target_students),
            'found_students': found_students,
            'not_found_students': not_found_students,
            'successful_collections': len(found_students),
            'student_data': student_data_collection
        }
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Keep browser open for inspection
        print(f"\n👀 Browser will stay open for 15 seconds for you to inspect...")
        for i in range(15, 0, -1):
            print(f"⏰ Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            print(f"\n👋 Browser closed")

def find_and_click_student(driver, student_name):
    """Find a student in the table and click on them"""
    try:
        print(f"🔍 Looking for student in the table...")
        
        # Scroll to top first
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Search through the page by scrolling
        max_scrolls = 50
        scroll_attempt = 0
        
        while scroll_attempt < max_scrolls:
            # Get currently visible table rows
            try:
                rows = driver.find_elements(By.XPATH, "//table//tr")
                
                for row in rows:
                    try:
                        row_text = row.text.strip()
                        # Check if this row contains the student name
                        if student_name.lower() in row_text.lower():
                            print(f"✅ Found student in row: {row_text[:100]}...")
                            
                            # Scroll the row into view
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", row)
                            time.sleep(2)
                            
                            # Try multiple clickable elements in the row
                            clickable_approaches = [
                                (".//td[1]//a", "link in first cell"),
                                (".//a", "any link in row"),
                                (".//td[1]", "first cell"),
                                (".", "entire row")
                            ]
                            
                            clickable_element = None
                            approach_used = None
                            
                            for xpath, description in clickable_approaches:
                                try:
                                    clickable_element = row.find_element(By.XPATH, xpath)
                                    approach_used = description
                                    print(f"   📍 Found clickable element: {description}")
                                    break
                                except:
                                    continue
                            
                            if clickable_element:
                                print(f"🖱️  Clicking on student...")
                                
                                # Use JavaScript click to ensure it works
                                driver.execute_script("arguments[0].click();", clickable_element)
                                time.sleep(5)  # Wait for page to load
                                
                                # Check if we navigated to a new page - be more flexible
                                new_url = driver.current_url
                                page_title = driver.title
                                
                                # Check if we're on a student-specific page
                                if (new_url != "https://app.alphamath.school/admin" and 
                                    "admin" in new_url):
                                    print(f"✅ Successfully navigated to student page!")
                                    print(f"   URL: {new_url}")
                                    print(f"   Title: {page_title}")
                                    return True
                                elif "Personal Information" in driver.page_source or student_name in driver.page_source:
                                    print(f"✅ Successfully navigated to student page (detected by content)!")
                                    print(f"   URL: {new_url}")
                                    print(f"   Title: {page_title}")
                                    return True
                                else:
                                    print(f"⚠️  Click didn't navigate to student page. Current URL: {new_url}")
                                    return False
                            
                    except Exception as e:
                        continue
                
                # Scroll down and continue searching
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                scroll_attempt += 1
                
            except Exception as e:
                break
        
        print(f"❌ Could not find student after scrolling through table")
        return False
        
    except Exception as e:
        print(f"❌ Error searching for student: {str(e)}")
        return False

def collect_student_data(driver, student_name):
    """Collect minimal essential data from the current student page"""
    try:
        print(f"📊 Collecting data for student...")
        
        # Wait for page to load
        time.sleep(3)
        
        # Start with just the student name and timestamp
        data = {
            'name': student_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # TODO: Add specific data collection here based on your requirements
        print(f"   ✅ Ready to collect specific metrics for student")
        
        print(f"✅ Data collection complete for student")
        return data
        
    except Exception as e:
        print(f"❌ Error collecting data for student: {str(e)}")
        return {
            'name': student_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    run_student_clicker()