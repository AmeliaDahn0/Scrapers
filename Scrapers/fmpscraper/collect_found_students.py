#!/usr/bin/env python3
"""
Collect data for the 3 students we found on the dashboard
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

def collect_student_data():
    driver = None
    try:
        # The 3 students we found
        found_students = ["Ananya Peesu", "Geetesh Parelly", "Sloka Vudumu"]
        
        print("🚀 Starting data collection for found students")
        print(f"📚 Students to process: {found_students}")
        
        # Setup browser
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,1000")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Login and navigate
        print("🔑 Logging in...")
        driver.get("https://app.alphamath.school/admin")
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
        
        print("✅ Logged in successfully")
        
        # Wait for dashboard
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        student_data = {}
        
        # Process each student
        for i, student_name in enumerate(found_students, 1):
            print(f"\n{'='*50}")
            print(f"📚 Processing {i}/{len(found_students)}: {student_name}")
            print(f"{'='*50}")
            
            # Find and click the student
            if find_and_click_student(driver, student_name):
                # Collect data from student page
                data = scrape_student_page(driver, student_name)
                student_data[student_name] = data
                
                # Go back to dashboard
                print("🔙 Returning to dashboard...")
                driver.back()
                time.sleep(3)
                
                # Wait for table to reload
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            else:
                student_data[student_name] = {
                    'name': student_name,
                    'status': 'not_clickable',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"found_students_data_{timestamp}.json"
        
        final_results = {
            'collection_timestamp': datetime.now().isoformat(),
            'students_processed': len(found_students),
            'successful_collections': len([d for d in student_data.values() if d.get('status') == 'success']),
            'student_data': student_data
        }
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n🎉 Data collection complete!")
        print(f"📊 Summary:")
        print(f"   - Students processed: {final_results['students_processed']}")
        print(f"   - Successful collections: {final_results['successful_collections']}")
        print(f"💾 Results saved to: {filename}")
        
        # Keep browser open briefly
        print(f"\n👀 Browser will close in 10 seconds...")
        for i in range(10, 0, -1):
            print(f"   ⏰ {i}...", end='\r')
            time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()

def find_and_click_student(driver, student_name):
    """Find and click on a specific student"""
    try:
        print(f"🔍 Looking for {student_name}...")
        
        # Scroll to top first
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Search through the page
        max_scrolls = 30
        for scroll in range(max_scrolls):
            # Check current visible rows
            rows = driver.find_elements(By.XPATH, "//table//tr")
            
            for row in rows:
                try:
                    row_text = row.text.strip()
                    if student_name.lower() in row_text.lower():
                        print(f"✅ Found {student_name} in table!")
                        
                        # Scroll row into view
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", row)
                        time.sleep(2)
                        
                        # Try to find clickable element
                        try:
                            # Look for clickable name in first cell
                            clickable = row.find_element(By.XPATH, ".//td[1]//a")
                        except:
                            try:
                                # Try the first cell itself
                                clickable = row.find_element(By.XPATH, ".//td[1]")
                            except:
                                clickable = row
                        
                        print(f"🖱️  Clicking on {student_name}...")
                        driver.execute_script("arguments[0].click();", clickable)
                        time.sleep(5)  # Wait for page to load
                        
                        print(f"✅ Successfully clicked {student_name}")
                        return True
                        
                except:
                    continue
            
            # Scroll down and continue searching
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
        
        print(f"❌ Could not find clickable element for {student_name}")
        return False
        
    except Exception as e:
        print(f"❌ Error finding {student_name}: {str(e)}")
        return False

def scrape_student_page(driver, student_name):
    """Scrape data from the current student page"""
    try:
        print(f"📊 Collecting data for {student_name}...")
        
        # Wait for page to load
        time.sleep(3)
        
        data = {
            'name': student_name,
            'url': driver.current_url,
            'title': driver.title,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        print(f"   📄 Page: {data['title']}")
        print(f"   🔗 URL: {data['url']}")
        
        # Get page text
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            data['page_text'] = body_text[:2000]  # First 2000 characters
            print(f"   📝 Collected page text ({len(body_text)} characters)")
        except:
            pass
        
        # Look for specific data elements
        try:
            # Check for tables
            tables = driver.find_elements(By.TAG_NAME, "table")
            if tables:
                data['tables_found'] = len(tables)
                print(f"   📋 Found {len(tables)} tables")
        except:
            pass
        
        try:
            # Check for progress indicators
            progress_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'progress') or contains(text(), 'Progress') or contains(text(), 'score') or contains(text(), 'Score')]")
            if progress_elements:
                data['progress_indicators'] = [elem.text.strip() for elem in progress_elements[:5]]
                print(f"   📈 Found {len(progress_elements)} progress indicators")
        except:
            pass
        
        # Take screenshot
        try:
            screenshot_name = f"{student_name.replace(' ', '_')}_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_name)
            data['screenshot'] = screenshot_name
            print(f"   📸 Screenshot saved: {screenshot_name}")
        except:
            pass
        
        print(f"✅ Data collection complete for {student_name}")
        return data
        
    except Exception as e:
        print(f"❌ Error collecting data for {student_name}: {str(e)}")
        return {
            'name': student_name,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    collect_student_data()