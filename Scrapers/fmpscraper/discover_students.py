#!/usr/bin/env python3
"""
Student Discovery - Just show all students available on dashboard
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
from dotenv import load_dotenv

load_dotenv()

def discover_students():
    driver = None
    try:
        print("🚀 Starting Student Discovery")
        
        # Setup browser
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,1000")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Browser opened")
        print("🔑 Logging in...")
        
        # Navigate and login
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
        print("📋 Discovering all students...")
        
        # Wait for dashboard
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Get initial count
        initial_rows = driver.find_elements(By.XPATH, "//table//tr")
        print(f"   Initial rows visible: {len(initial_rows)}")
        
        # Collect all students by scrolling
        all_students = set()
        scroll_attempts = 0
        last_count = 0
        
        while scroll_attempts < 30:  # Limit scrolling attempts
            # Get current students
            rows = driver.find_elements(By.XPATH, "//table//tr")
            
            for row in rows:
                try:
                    # Get first cell text (student name)
                    first_cell = row.find_element(By.XPATH, ".//td[1]")
                    name = first_cell.text.strip()
                    
                    # Filter valid names
                    if name and len(name) > 2 and name not in ['NAME', 'Name']:
                        all_students.add(name)
                except:
                    continue
            
            current_count = len(all_students)
            
            # If we found new students, continue
            if current_count > last_count:
                print(f"   📚 Found {current_count} total students so far...")
                last_count = current_count
            
            # Scroll down
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            
            # Check if we've hit bottom
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll = driver.execute_script("return window.pageYOffset + window.innerHeight")
            
            if current_scroll >= scroll_height - 100:  # Near bottom
                print("📜 Reached bottom of page")
                break
                
            scroll_attempts += 1
        
        print(f"\n🎉 Discovery Complete!")
        print(f"📊 Total students found: {len(all_students)}")
        print(f"\n📋 All Students on Dashboard:")
        
        sorted_students = sorted(list(all_students))
        for i, student in enumerate(sorted_students, 1):
            print(f"   {i:2d}. Student {i}")
        
        # Read target students
        print(f"\n🎯 Your Target Students:")
        target_students = []
        try:
            with open('students.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name = line.split(',')[0].split('\t')[0].strip()
                        if name:
                            target_students.append(name)
            
            for i, student in enumerate(target_students, 1):
                print(f"   {i:2d}. Target student {i}")
        except:
            print("   ❌ Could not read students.txt")
        
        # Check matches
        print(f"\n🔍 Matching Analysis:")
        matches = []
        for target in target_students:
            found = False
            for available in sorted_students:
                if target.lower() in available.lower() or available.lower() in target.lower():
                    matches.append((target, available))
                    print(f"   ✅ '{target}' → FOUND as '{available}'")
                    found = True
                    break
            if not found:
                print(f"   ❌ '{target}' → NOT FOUND")
        
        print(f"\n📊 Match Summary:")
        print(f"   - Target students: {len(target_students)}")
        print(f"   - Available students: {len(sorted_students)}")
        print(f"   - Successful matches: {len(matches)}")
        
        # Keep browser open for inspection
        print(f"\n👀 Browser will stay open for 30 seconds for you to inspect...")
        print(f"   You can see all the students in the dashboard!")
        
        for i in range(30, 0, -1):
            print(f"   ⏰ Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            print(f"\n👋 Browser closed")

if __name__ == "__main__":
    discover_students()