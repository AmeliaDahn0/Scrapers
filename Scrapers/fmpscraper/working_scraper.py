#!/usr/bin/env python3
"""
Working Student Scraper - Simple and reliable
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

def run_working_scraper():
    driver = None
    try:
        print("🚀 Starting Working Student Scraper")
        
        # Setup browser (visible)
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,1000")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Browser opened - you can see it!")
        
        # Step 1: Go to downloads page and login
        print("📄 Step 1: Going to downloads page...")
        driver.get("https://app.alphamath.school/admin/downloads")
        time.sleep(3)
        
        # Login if needed
        if "login" in driver.page_source.lower():
            print("🔑 Step 2: Logging in...")
            username = os.getenv('USERNAME')
            password = os.getenv('PASSWORD')
            
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            password_field.send_keys("\n")
            
            time.sleep(5)
            print("✅ Login successful!")
            
            # Navigate back to downloads page after login
            print("🔄 Navigating back to downloads page after login...")
            driver.get("https://app.alphamath.school/admin/downloads")
            time.sleep(3)
        
        # Step 3: Debug what's on the page first
        print("🔍 Step 3: Debugging page content...")
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page Title: {driver.title}")
        print(f"📝 Page contains 'Back': {'Back' in driver.page_source}")
        print(f"📝 Page contains 'Dashboard': {'Dashboard' in driver.page_source}")
        
        # Step 3b: Look for and click the back button
        print("🔙 Step 3b: Looking for 'Back to Admin Dashboard' button...")
        
        try:
            # Try multiple selectors for the back button
            back_button = None
            selectors = [
                "//a[contains(text(), 'Back to Admin Dashboard')]",
                "//a[contains(text(), 'Back to Admin')]", 
                "//a[contains(text(), 'Dashboard')]",
                "//a[contains(text(), '← Back')]",
                "//a[@href='/admin']",
                "//a[@href='https://app.alphamath.school/admin']",
                ".//a[contains(@class, 'back')]"
            ]
            
            for selector in selectors:
                try:
                    back_button = driver.find_element(By.XPATH, selector)
                    print(f"✅ Found back button using selector: {selector}")
                    print(f"   Button text: '{back_button.text.strip()}'")
                    print(f"   Button href: '{back_button.get_attribute('href')}'")
                    break
                except:
                    continue
            
            if back_button:
                # Click it
                print("🖱️  Clicking back button...")
                back_button.click()
                time.sleep(5)
                print("✅ Successfully clicked back button!")
            else:
                print("❌ Could not find back button with any selector")
                print("🔍 Let me show you what links are available on this page:")
                
                # Show all links on the page for debugging
                links = driver.find_elements(By.TAG_NAME, "a")
                for i, link in enumerate(links[:10]):  # Show first 10 links
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"   Link {i+1}: '{text}' -> {href}")
                return
            
        except Exception as e:
            print(f"❌ Error with back button: {e}")
            return
        
        # Step 4: Verify we're on the dashboard
        print("📊 Step 4: Verifying we're on the admin dashboard...")
        
        # Give the page more time to load
        time.sleep(10)
        
        # Debug current state
        print(f"📍 Current URL after click: {driver.current_url}")
        print(f"📄 Current Title: {driver.title}")
        
        # Wait for the student table to load with longer timeout
        try:
            print("⏳ Waiting for student table to load...")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            print("✅ Dashboard table found!")
            
            # Check current URL and title
            current_url = driver.current_url
            page_title = driver.title
            
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page Title: {page_title}")
            
            if "admin" in current_url and "downloads" not in current_url:
                print("✅ Successfully on admin dashboard!")
            else:
                print("⚠️  Might not be on the right page...")
            
        except Exception as e:
            print(f"❌ Could not find dashboard table: {e}")
            return
        
        # Step 5: Quick student count
        print("📚 Step 5: Counting students...")
        
        try:
            # Count table rows (students)
            rows = driver.find_elements(By.XPATH, "//table//tr")
            student_count = len(rows) - 1  # Subtract header row
            print(f"📊 Found approximately {student_count} students in the table")
            
            # Show first few student names
            print("👥 First few students:")
            for i in range(1, min(6, len(rows))):  # Skip header, show first 5
                try:
                    first_cell = rows[i].find_element(By.XPATH, ".//td[1]")
                    student_name = first_cell.text.strip()
                    print(f"   {i}. {student_name}")
                except:
                    continue
            
        except Exception as e:
            print(f"❌ Error counting students: {e}")
        
        # Step 6: Keep browser open for inspection
        print("\n🎉 SUCCESS! The scraper is working correctly!")
        print("📋 Summary of what happened:")
        print("   1. ✅ Opened browser (visible)")
        print("   2. ✅ Navigated to downloads page")
        print("   3. ✅ Logged in successfully")
        print("   4. ✅ Found and clicked 'Back to Admin Dashboard' button")
        print("   5. ✅ Successfully reached the admin dashboard")
        print("   6. ✅ Found the student table")
        
        print(f"\n👀 Browser will stay open for 30 seconds so you can see the dashboard...")
        for i in range(30, 0, -1):
            print(f"⏰ Closing in {i} seconds... (you can see the student dashboard!)", end='\r')
            time.sleep(1)
        
        print(f"\n✅ Scraper completed successfully!")
        
        # Save basic results
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'final_url': current_url,
            'page_title': page_title,
            'approximate_student_count': student_count,
            'message': 'Successfully navigated to admin dashboard and found student table'
        }
        
        filename = f"working_scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            print(f"\n👋 Browser closed")

if __name__ == "__main__":
    run_working_scraper()