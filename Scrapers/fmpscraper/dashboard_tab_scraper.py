#!/usr/bin/env python3
"""
Dashboard Tab Scraper
Collects data from dashboard tabs instead of individual student pages
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

# Load environment variables
load_dotenv()

def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Keep visible
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def login(driver):
    """Login to the admin panel"""
    try:
        print("🔑 Logging in...")
        
        # Get credentials from environment
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        
        if not username or not password:
            print("❌ No credentials found in .env file")
            return False
        
        # Navigate to admin page (will redirect to login if needed)
        driver.get("https://app.alphamath.school/admin")
        time.sleep(3)
        
        # Find login fields
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
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def navigate_to_dashboard(driver):
    """Navigate to the admin dashboard"""
    try:
        print("🔙 Navigating to admin dashboard...")
        
        # Try to get to downloads page first
        driver.get("https://app.alphamath.school/admin/downloads")
        time.sleep(3)
        
        # Look for and click back button
        try:
            back_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Back to Admin Dashboard')]")
            print(f"✅ Found back button: '{back_button.text.strip()}'")
            back_button.click()
            time.sleep(5)
        except:
            # Direct navigation to admin dashboard
            print("🔄 Direct navigation to dashboard...")
            driver.get("https://app.alphamath.school/admin")
            time.sleep(5)
        
        # Wait for dashboard to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ Successfully on admin dashboard!")
        return True
        
    except Exception as e:
        print(f"❌ Error navigating to dashboard: {e}")
        return False

def find_dashboard_tabs(driver):
    """Find all available tabs/navigation items on the dashboard"""
    print("🔍 Looking for dashboard tabs and navigation...")
    
    tabs = []
    
    # Multiple selectors to find tabs/navigation
    tab_selectors = [
        "nav a",                    # Navigation links
        ".nav-item a",             # Bootstrap nav items
        ".nav-link",               # Nav links
        "[role='tab']",            # ARIA tabs
        ".tab a",                  # Tab links
        ".menu-item a",            # Menu items
        "li a",                    # List item links
        "button[data-tab]",        # Data tab buttons
        ".sidebar a",              # Sidebar links
        ".navigation a",           # Navigation links
        "a[href*='admin']",        # Admin related links
        ".btn-group .btn",         # Button groups
        ".tabs .tab"               # Tab elements
    ]
    
    for selector in tab_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                tab_text = element.text.strip()
                tab_href = element.get_attribute('href')
                
                # Filter for meaningful tabs
                if (tab_text and 
                    len(tab_text) > 0 and 
                    len(tab_text) < 50 and
                    tab_text not in [tab['text'] for tab in tabs]):  # Avoid duplicates
                    
                    tabs.append({
                        'text': tab_text,
                        'href': tab_href,
                        'element': element,
                        'selector': selector
                    })
        except Exception as e:
            continue
    
    print(f"📋 Found {len(tabs)} potential tabs/navigation items:")
    for i, tab in enumerate(tabs):
        print(f"   {i+1}. '{tab['text']}' -> {tab['href']}")
    
    return tabs

def collect_dashboard_data(driver, section_name):
    """Collect all visible data from the current dashboard view"""
    print(f"📊 Collecting data from: {section_name}")
    
    data = {
        'section_name': section_name,
        'url': driver.current_url,
        'timestamp': datetime.now().isoformat(),
        'tables': [],
        'text_content': [],
        'metrics': []
    }
    
    try:
        # Collect all tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"   📋 Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            table_data = {
                'table_index': i,
                'headers': [],
                'rows': []
            }
            
            # Get headers
            try:
                headers = table.find_elements(By.TAG_NAME, "th")
                table_data['headers'] = [h.text.strip() for h in headers]
            except:
                pass
            
            # Get all rows
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[:50]:  # Limit to first 50 rows
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells:  # Only add rows with data
                        row_data = [cell.text.strip() for cell in cells]
                        table_data['rows'].append(row_data)
            except:
                pass
            
            data['tables'].append(table_data)
        
        # Look for metric/statistic containers
        metric_selectors = [
            ".metric", ".stat", ".number", ".count", ".score",
            ".value", ".total", ".summary", ".card-body",
            "[class*='metric']", "[class*='stat']", "[class*='count']"
        ]
        
        for selector in metric_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) < 200:  # Reasonable length
                        data['metrics'].append({
                            'selector': selector,
                            'text': text,
                            'class': elem.get_attribute('class')
                        })
            except:
                continue
        
        # Get general page content (headings, important text)
        try:
            headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            for heading in headings:
                text = heading.text.strip()
                if text and len(text) < 100:
                    data['text_content'].append({
                        'type': 'heading',
                        'tag': heading.tag_name,
                        'text': text
                    })
        except:
            pass
        
        print(f"   ✅ Collected: {len(data['tables'])} tables, {len(data['metrics'])} metrics, {len(data['text_content'])} content items")
        
    except Exception as e:
        print(f"   ⚠️ Error collecting data: {e}")
    
    return data

def run_dashboard_scraper():
    """Main function to run the dashboard tab scraper"""
    driver = None
    
    try:
        print("🚀 Starting Dashboard Tab Scraper")
        
        # Setup browser
        print("🌐 Setting up browser...")
        driver = setup_driver()
        print("✅ Browser opened - you can see it!")
        
        # Login
        if not login(driver):
            return
        
        # Navigate to dashboard
        if not navigate_to_dashboard(driver):
            return
        
        # Collect data from main dashboard
        all_data = {}
        all_data['main_dashboard'] = collect_dashboard_data(driver, "Main Dashboard")
        
        # Find and explore tabs
        tabs = find_dashboard_tabs(driver)
        
        # Target specific tabs that might contain useful data
        target_keywords = ['CQPM', 'Analytics', 'Reports', 'Progress', 'Data', 'Metrics', 'Dashboard', 'Students', 'Summary']
        
        for tab in tabs:
            tab_text = tab['text']
            
            # Check if this tab might contain useful data
            if any(keyword.lower() in tab_text.lower() for keyword in target_keywords):
                print(f"\n🔄 Exploring tab: '{tab_text}'")
                
                try:
                    # Click the tab
                    driver.execute_script("arguments[0].click();", tab['element'])
                    time.sleep(4)  # Wait for content to load
                    
                    # Collect data from this tab
                    tab_key = f"tab_{tab_text.replace(' ', '_').replace('/', '_').lower()}"
                    all_data[tab_key] = collect_dashboard_data(driver, tab_text)
                    
                    print(f"   ✅ Collected data from '{tab_text}' tab")
                    
                except Exception as e:
                    print(f"   ⚠️ Could not access tab '{tab_text}': {e}")
                    continue
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_tab_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Dashboard data collection complete!")
        print(f"📊 Summary:")
        print(f"   - Total sections scraped: {len(all_data)}")
        print(f"   - Sections: {list(all_data.keys())}")
        print(f"💾 Results saved to: {filename}")
        
        # Keep browser open for inspection
        print("\n👀 Browser will stay open for 30 seconds for you to inspect...")
        for i in range(30, 0, -1):
            print(f"⏰ Closing in {i} seconds...", end="\r")
            time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("\n👋 Browser closed")

if __name__ == "__main__":
    run_dashboard_scraper()