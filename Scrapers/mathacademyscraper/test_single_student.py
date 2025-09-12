#!/usr/bin/env python3
"""
Test scraper for a single student to validate data extraction
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()

class TestSingleStudent:
    def __init__(self):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        self.students_url = "https://www.mathacademy.com/students"
        
    async def login(self, page):
        """Login to Math Academy"""
        print("Logging in...")
        await page.goto(self.students_url)
        await page.wait_for_load_state('networkidle')
        
        # Handle login
        login_links = await page.query_selector_all('a[href*="login"], a[href*="signin"], a[href*="sign-in"]')
        if login_links:
            await login_links[0].click()
            await page.wait_for_load_state('networkidle')
        
        # Fill login form
        await page.fill('input[placeholder*="email" i]', self.username)
        await page.fill('input[type="password"]', self.password)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state('networkidle', timeout=15000)
        print("✓ Logged in successfully")

    async def test_student_data_extraction(self):
        """Test data extraction for Olivia Attia"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Login
                await self.login(page)
                
                # Test student: Olivia Attia (ID: 12616)
                student_id = "12616"
                student_name = "Attia, Olivia"
                
                print(f"\n=== Testing data extraction for {student_name} ===")
                
                # Navigate to the activity page
                activity_url = f"https://www.mathacademy.com/students/{student_id}/activity"
                print(f"Navigating to: {activity_url}")
                
                await page.goto(activity_url)
                await page.wait_for_load_state('networkidle', timeout=15000)
                await page.wait_for_timeout(3000)  # Extra wait for dynamic content
                
                # Take screenshot for debugging
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"test_student_{student_id}_{timestamp}.png")
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Save full HTML for inspection
                with open(f"test_student_{student_id}_{timestamp}.html", 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Saved debug files: test_student_{student_id}_{timestamp}.png/html")
                
                # Test specific element extraction
                print("\n=== Testing element extraction ===")
                
                # 1. Weekly XP
                weekly_xp_element = soup.find('div', id='thisWeekTotalXP')
                if weekly_xp_element:
                    weekly_xp = weekly_xp_element.get_text(strip=True)
                    print(f"✓ Weekly XP: {weekly_xp}")
                else:
                    print("✗ Weekly XP element not found")
                
                # 2. Daily XP
                daily_xp_element = soup.find('td', id='dailyGoalPoints')
                if daily_xp_element:
                    daily_xp = daily_xp_element.get_text(strip=True)
                    print(f"✓ Daily XP: {daily_xp}")
                else:
                    print("✗ Daily XP element not found")
                
                # 3. Course completion
                course_percent_element = soup.find('div', id='coursePercentComplete')
                if course_percent_element:
                    course_percent = course_percent_element.get_text(strip=True)
                    print(f"✓ Course completion: {course_percent}")
                else:
                    print("✗ Course completion element not found")
                
                # 4. Estimated completion date
                estimated_completion_element = soup.find('div', id='estimatedCompletion')
                if estimated_completion_element:
                    span_element = estimated_completion_element.find('span')
                    if span_element:
                        estimated_date = span_element.get_text(strip=True)
                        print(f"✓ Estimated completion: {estimated_date}")
                    else:
                        full_text = estimated_completion_element.get_text(strip=True)
                        print(f"✓ Estimated completion (full): {full_text}")
                else:
                    print("✗ Estimated completion element not found")
                
                # 5. Task rows
                task_rows = soup.find_all('tr', id=re.compile(r'task-\d+'))
                if task_rows:
                    print(f"✓ Found {len(task_rows)} task rows")
                    
                    # Show first few tasks
                    for i, task_row in enumerate(task_rows[:3]):
                        task_name_div = task_row.find('div', class_='taskName')
                        task_type = task_row.get('type', 'Unknown')
                        if task_name_div:
                            task_name = task_name_div.get_text(strip=True)
                            print(f"  Task {i+1}: {task_type} - {task_name}")
                else:
                    print("✗ No task rows found")
                
                # 6. Date headers
                date_headers = soup.find_all('td', class_='dateHeader')
                if date_headers:
                    print(f"✓ Found {len(date_headers)} date headers")
                    for i, date_header in enumerate(date_headers[:3]):
                        date_text = date_header.get_text(strip=True)
                        print(f"  Date {i+1}: {date_text}")
                else:
                    print("✗ No date headers found")
                
                # Check current URL
                current_url = page.url
                print(f"\nCurrent URL: {current_url}")
                
                # Look for any elements with the IDs we're targeting
                print("\n=== Checking for target IDs in page ===")
                all_ids = [elem.get('id') for elem in soup.find_all(id=True)]
                target_ids = ['thisWeekTotalXP', 'dailyGoalPoints', 'coursePercentComplete', 'estimatedCompletion']
                
                for target_id in target_ids:
                    if target_id in all_ids:
                        print(f"✓ Found {target_id}")
                    else:
                        print(f"✗ Missing {target_id}")
                
                print(f"\nTotal elements with IDs: {len(all_ids)}")
                if len(all_ids) > 0:
                    print("Sample IDs found:", all_ids[:10])
                
            except Exception as e:
                print(f"Error: {e}")
                await page.screenshot(path=f"error_test_{timestamp}.png")
                
            finally:
                await browser.close()

async def main():
    test = TestSingleStudent()
    await test.test_student_data_extraction()

if __name__ == "__main__":
    asyncio.run(main())