#!/usr/bin/env python3
"""
Tab Specific Scraper
Scrapes data from Time Spent, Progress, and CQPM tabs on the dashboard
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
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def setup_supabase_client():
    """Setup Supabase client connection with service role for RLS bypass"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        
        # Try service role key first (for RLS policies), fallback to regular key
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("⚠️ Supabase credentials not found in .env file")
            print("   Please add SUPABASE_URL and either SUPABASE_SERVICE_KEY or SUPABASE_KEY to your .env file")
            return None
        
        # Determine which key type we're using
        key_type = "service_role" if os.getenv('SUPABASE_SERVICE_KEY') else "anon/public"
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"✅ Supabase client connected successfully ({key_type} key)")
        return supabase
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return None

def upload_student_data_to_supabase(supabase, student_organized_data):
    """Upload student data to Supabase table"""
    if not supabase:
        print("⚠️ No Supabase connection - skipping upload")
        return False
    
    try:
        print(f"📤 Uploading {len(student_organized_data)} students to Supabase...")
        
        uploaded_count = 0
        for student_name, student_data in student_organized_data.items():
            
            # Extract data from the nested structure
            tabs_data = student_data.get('tabs_data', {})
            time_spent_data = tabs_data.get('Time Spent', {})
            progress_data = tabs_data.get('Progress', {})
            cqpm_data = tabs_data.get('CQPM', {})
            
            # Prepare the record for insertion
            record = {
                'student_name': student_name,
                'scrape_timestamp': student_data.get('timestamp'),
                'campus': time_spent_data.get('CAMPUS') or progress_data.get('CAMPUS') or cqpm_data.get('CAMPUS'),
                'last_active': time_spent_data.get('LAST ACTIVE') or progress_data.get('LAST ACTIVE') or cqpm_data.get('LAST ACTIVE'),
                
                # Time Spent tab data
                'time_spent_active_track': time_spent_data.get('ACTIVE TRACK'),
                'time_spent_time_today': time_spent_data.get('TIME TODAY'),
                'time_spent_time_last_7_days': time_spent_data.get('TIME LAST 7 DAYS'),
                
                # Progress tab data
                'progress_last_active': progress_data.get('LAST ACTIVE'),
                
                # CQPM tab data
                'cqpm_last_active': cqpm_data.get('LAST ACTIVE'),
                'cqpm_latest_score': cqpm_data.get('LATEST CQPM'),
                'cqpm_previous_score': cqpm_data.get('PREVIOUS CQPM')
            }
            
            # Insert the record
            try:
                result = supabase.table('fastmath_students').insert(record).execute()
                print(f"   ✅ Uploaded: {student_name}")
                uploaded_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to upload {student_name}: {e}")
        
        print(f"📤 Upload complete: {uploaded_count}/{len(student_organized_data)} students uploaded successfully")
        return uploaded_count > 0
        
    except Exception as e:
        print(f"❌ Error during Supabase upload: {e}")
        return False

def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    
    # Check if running in CI environment or headless mode is enabled
    headless_mode = os.getenv('HEADLESS_MODE', 'false').lower() == 'true' or os.getenv('CI', 'false').lower() == 'true'
    
    if headless_mode:
        chrome_options.add_argument("--headless")
        print("🤖 Running in headless mode (CI environment detected)")
    else:
        print("👁️ Running in visible mode")
    
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def login_and_navigate_to_dashboard(driver):
    """Login and get to the dashboard with tabs"""
    try:
        print("🔑 Logging in and navigating to dashboard...")
        
        # Get credentials
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        
        if not username or not password:
            print("❌ No credentials found in .env file")
            return False
        
        # Navigate to admin downloads page first
        driver.get("https://app.alphamath.school/admin/downloads")
        time.sleep(3)
        
        # Check if we need to login
        try:
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            # Fill credentials
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            time.sleep(5)
            
            print("✅ Login successful!")
        except:
            print("✅ Already logged in!")
        
        # Click back to dashboard
        try:
            back_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Back to Admin Dashboard')]")
            print(f"🔙 Clicking: '{back_button.text.strip()}'")
            back_button.click()
            time.sleep(5)
        except:
            # Direct navigation if back button not found
            driver.get("https://app.alphamath.school/admin")
            time.sleep(5)
        
        print("✅ Successfully on admin dashboard!")
        return True
        
    except Exception as e:
        print(f"❌ Error during login/navigation: {e}")
        return False

def get_target_students_from_supabase(supabase):
    """Get the list of target students from Supabase students table"""
    try:
        if not supabase:
            print("❌ No Supabase connection - cannot get student list")
            return []
        
        print("📚 Fetching student list from Supabase...")
        
        # Query the students table to get all student names
        response = supabase.table('students').select('name, email, id').execute()
        
        if response.data:
            students = [student['name'] for student in response.data if student['name']]
            print(f"🎯 Found {len(students)} students in Supabase:")
            for i, student in enumerate(students[:10], 1):  # Show first 10
                print(f"   {i}. {student}")
            if len(students) > 10:
                print(f"   ... and {len(students) - 10} more students")
            
            return students
        else:
            print("⚠️ No students found in Supabase students table")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching students from Supabase: {e}")
        return []

def scroll_and_collect_target_student_rows(driver, target_students):
    """Scroll through the table and collect ONLY rows for target students"""
    print(f"📜 Looking for {len(target_students)} target students...")
    
    # Scroll to load all content
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    
    while scroll_count < 10:  # Limit scrolls
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1
    
    print(f"   ✅ Completed {scroll_count} scrolls")
    
    # Now collect ONLY target student data
    target_rows_data = []
    found_students = []
    
    try:
        table = driver.find_element(By.TAG_NAME, "table")
        
        # Get headers first
        headers = []
        try:
            header_row = table.find_element(By.TAG_NAME, "thead")
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            headers = [cell.text.strip() for cell in header_cells]
        except:
            # If no thead, try first row
            first_row = table.find_element(By.TAG_NAME, "tr")
            header_cells = first_row.find_elements(By.TAG_NAME, "th")
            if header_cells:
                headers = [cell.text.strip() for cell in header_cells]
        
        # Get all data rows and filter for target students
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:  # Only process rows with data cells (not headers)
                row_data = [cell.text.strip() for cell in cells]
                
                if row_data and len(row_data) > 0:
                    student_name = row_data[0]  # First column should be student name
                    
                    # Check if this student is in our target list
                    if student_name in target_students:
                        target_rows_data.append(row_data)
                        found_students.append(student_name)
                        print(f"   ✅ Found target student: {student_name}")
        
        print(f"   📊 Found {len(target_rows_data)} target students out of {len(target_students)} requested")
        print(f"   📋 Headers: {headers}")
        
        # Show which students were not found
        not_found = [s for s in target_students if s not in found_students]
        if not_found:
            print(f"   ⚠️ Students not found: {not_found}")
        
        # Convert rows to key-value format
        student_objects = []
        for row_data in target_rows_data:
            student_obj = {}
            for i, header in enumerate(headers):
                if i < len(row_data):
                    student_obj[header] = row_data[i]
                else:
                    student_obj[header] = ""  # Empty if no data
            student_objects.append(student_obj)
        
        return {
            'students': student_objects,
            'total_students': len(student_objects),
            'found_students': found_students,
            'not_found_students': not_found
        }
        
    except Exception as e:
        print(f"   ⚠️ Error collecting table data: {e}")
        return {'students': [], 'total_students': 0, 'found_students': [], 'not_found_students': target_students}

def click_tab_and_collect(driver, tab_name, target_students):
    """Click on a specific tab and collect data for target students only"""
    print(f"\n🔄 Switching to '{tab_name}' tab...")
    
    try:
        # Find the tab by text content
        tab_xpath_options = [
            f"//button[contains(text(), '{tab_name}')]",
            f"//a[contains(text(), '{tab_name}')]",
            f"//*[contains(@class, 'tab') and contains(text(), '{tab_name}')]",
            f"//*[contains(@role, 'tab') and contains(text(), '{tab_name}')]",
            f"//div[contains(text(), '{tab_name}')]//parent::*[contains(@class, 'tab')]",
            f"//*[text()='{tab_name}']"
        ]
        
        tab_clicked = False
        
        for xpath in tab_xpath_options:
            try:
                tab_element = driver.find_element(By.XPATH, xpath)
                print(f"   🎯 Found tab using: {xpath}")
                print(f"   📍 Tab text: '{tab_element.text.strip()}'")
                
                # Click the tab
                driver.execute_script("arguments[0].click();", tab_element)
                time.sleep(4)  # Wait for content to load
                
                tab_clicked = True
                print(f"   ✅ Successfully clicked '{tab_name}' tab")
                break
                
            except Exception as e:
                continue
        
        if not tab_clicked:
            print(f"   ❌ Could not find or click '{tab_name}' tab")
            return None
        
        # Wait for new content to load
        time.sleep(3)
        
        # Collect data from this tab (ONLY for target students)
        tab_data = {
            'tab_name': tab_name,
            'timestamp': datetime.now().isoformat(),
            'url': driver.current_url
        }
        
        # Collect table data for target students only
        table_data = scroll_and_collect_target_student_rows(driver, target_students)
        tab_data.update(table_data)
        
        print(f"   ✅ Collected data from '{tab_name}' tab: {table_data['total_students']} target students")
        
        return tab_data
        
    except Exception as e:
        print(f"   ❌ Error collecting data from '{tab_name}' tab: {e}")
        return None

def run_tab_scraper():
    """Main function to scrape specific tabs for target students only"""
    driver = None
    
    try:
        print("🚀 Starting Tab-Specific Scraper")
        print("🎯 Target tabs: Time Spent → Progress → CQPM")
        
        # Setup Supabase connection
        supabase = setup_supabase_client()
        if not supabase:
            print("❌ Supabase connection required to fetch student list")
            return
        
        # Get target students from Supabase students table
        target_students = get_target_students_from_supabase(supabase)
        if not target_students:
            print("❌ No target students found in Supabase students table")
            return
        
        # Setup browser
        print("\n🌐 Setting up browser...")
        driver = setup_driver()
        print("✅ Browser opened - you can see it!")
        
        # Login and navigate to dashboard
        if not login_and_navigate_to_dashboard(driver):
            return
        
        # Wait for dashboard to fully load
        time.sleep(5)
        
        all_data = {}
        
        # Target tabs in order
        target_tabs = ['Time Spent', 'Progress', 'CQPM']
        
        for tab_name in target_tabs:
            tab_data = click_tab_and_collect(driver, tab_name, target_students)
            if tab_data:
                key = f"{tab_name.lower().replace(' ', '_')}_tab"
                all_data[key] = tab_data
            else:
                print(f"⚠️ Failed to collect data from '{tab_name}' tab")
        
        # Reorganize data by student instead of by tab
        print(f"\n🔄 Reorganizing data by student...")
        student_organized_data = {}
        
        # Get all unique students across all tabs
        all_students = set()
        for tab_data in all_data.values():
            for student in tab_data.get('found_students', []):
                all_students.add(student)
        
        # For each student, collect their data from all tabs
        for student_name in all_students:
            student_organized_data[student_name] = {
                'student_name': student_name,
                'timestamp': datetime.now().isoformat(),
                'tabs_data': {}
            }
            
            # Go through each tab and find this student's data
            for tab_key, tab_data in all_data.items():
                tab_name = tab_data.get('tab_name', tab_key)
                student_found = False
                
                # Find this student in the tab's data
                for student_data in tab_data.get('students', []):
                    if student_data.get('NAME') == student_name:
                        # Remove the NAME field since it's redundant (already in the key)
                        student_tab_data = {k: v for k, v in student_data.items() if k != 'NAME'}
                        student_organized_data[student_name]['tabs_data'][tab_name] = student_tab_data
                        student_found = True
                        break
                
                if not student_found:
                    student_organized_data[student_name]['tabs_data'][tab_name] = "Not found in this tab"
        
        print(f"\n🎉 Data reorganization complete!")
        print(f"📊 Summary:")
        print(f"   - Total students: {len(student_organized_data)}")
        for student_name, student_data in student_organized_data.items():
            tabs_with_data = len([tab for tab, data in student_data['tabs_data'].items() if data != "Not found in this tab"])
            print(f"   - {student_name}: Found in {tabs_with_data} tabs")
        
        # Upload to Supabase
        print(f"\n📤 Uploading data to Supabase...")
        upload_success = upload_student_data_to_supabase(supabase, student_organized_data)
        
        if upload_success:
            print("✅ Data successfully uploaded to Supabase!")
        else:
            print("⚠️ Supabase upload failed - data is still saved locally")
        
        # Keep browser open for inspection (only in non-CI environments)
        if not os.getenv('CI', 'false').lower() == 'true':
            print("\n👀 Browser will stay open for 20 seconds for you to inspect...")
            for i in range(20, 0, -1):
                print(f"⏰ Closing in {i} seconds...", end="\r")
                time.sleep(1)
        else:
            print("\n🤖 CI environment detected - closing browser immediately")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("\n👋 Browser closed")

if __name__ == "__main__":
    run_tab_scraper()