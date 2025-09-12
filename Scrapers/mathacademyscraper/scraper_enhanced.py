#!/usr/bin/env python3
"""
Enhanced Math Academy Students Scraper
Extracts detailed student data from the students page
"""

import asyncio
import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()

class MathAcademyStudentScraper:
    def __init__(self):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        
        self.students_url = "https://www.mathacademy.com/students"
        
    async def login(self, page):
        """Login to Math Academy"""
        print("Navigating to students page...")
        await page.goto(self.students_url)
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        
        # Try multiple selectors for login form
        login_selectors = [
            'input[type="email"]',
            'input[name="username"]', 
            'input[name="email"]',
            'input[id="email"]',
            'input[id="username"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            'form input[type="text"]'
        ]
        
        login_field = None
        for selector in login_selectors:
            try:
                login_field = await page.query_selector(selector)
                if login_field:
                    print(f"Found login field with selector: {selector}")
                    break
            except:
                continue
        
        if not login_field:
            # Look for login links
            login_links = await page.query_selector_all('a[href*="login"], a[href*="signin"], a[href*="sign-in"]')
            if login_links:
                print(f"Found {len(login_links)} potential login links")
                await login_links[0].click()
                await page.wait_for_load_state('networkidle')
                
                # Try to find login form again
                for selector in login_selectors:
                    try:
                        login_field = await page.query_selector(selector)
                        if login_field:
                            print(f"Found login field after clicking login link: {selector}")
                            break
                    except:
                        continue
        
        if login_field:
            print("Logging in...")
            await login_field.fill(self.username)
            
            # Find password field
            password_field = await page.query_selector('input[type="password"]')
            if password_field:
                await password_field.fill(self.password)
                
                # Find and click submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'button:has-text("Log in")',
                    'form button'
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_btn = await page.query_selector(selector)
                        if submit_btn:
                            print(f"Clicking submit button: {selector}")
                            await submit_btn.click()
                            break
                    except:
                        continue
                
                # Wait for navigation
                await page.wait_for_load_state('networkidle', timeout=15000)
                print("Login completed!")
            else:
                raise Exception("Could not find password field")
        else:
            raise Exception("Could not find login form")

    async def extract_student_data(self, page):
        """Extract student data from the page"""
        print("Extracting student data...")
        
        # Wait for the page to fully load
        await page.wait_for_load_state('networkidle')
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        students = []
        
        # Find all student name links
        student_links = soup.find_all('a', class_='studentNameLink')
        print(f"Found {len(student_links)} student links")
        
        for link in student_links:
            try:
                student_data = {}
                
                # Extract student ID from href (/students/22710/activity)
                href = link.get('href', '')
                student_id_match = re.search(r'/students/(\d+)/', href)
                if student_id_match:
                    student_data['student_id'] = int(student_id_match.group(1))
                
                # Extract student name
                student_data['name'] = link.get_text(strip=True)
                
                # Extract link ID to get the row
                link_id = link.get('id', '')
                if link_id:
                    # Get the student ID from the link ID (studentNameLink-22710)
                    id_match = re.search(r'studentNameLink-(\d+)', link_id)
                    if id_match:
                        row_student_id = id_match.group(1)
                        
                        # Find the corresponding table row to get more data
                        # Look for elements with studentid attribute
                        menu_icon = soup.find('div', {'studentid': row_student_id})
                        if menu_icon:
                            # Navigate up to find the table row
                            row = menu_icon.find_parent('tr')
                            if row:
                                # Extract all cell data
                                cells = row.find_all('td')
                                cell_texts = [cell.get_text(strip=True) for cell in cells]
                                
                                # Try to find progress/activity data
                                for cell in cells:
                                    # Look for links with numbers (activity counts)
                                    activity_links = cell.find_all('a', class_='tableLink')
                                    for activity_link in activity_links:
                                        activity_text = activity_link.get_text(strip=True)
                                        if activity_text.isdigit():
                                            student_data['activity_count'] = int(activity_text)
                                            break
                                
                                # Store all cell data for analysis
                                student_data['row_data'] = cell_texts
                
                # Add extraction timestamp
                student_data['extracted_at'] = datetime.now().isoformat()
                
                students.append(student_data)
                
            except Exception as e:
                print(f"Error extracting data for student link {link}: {e}")
                continue
        
        return students

    async def scrape_all_students(self):
        """Main scraping function"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Login
                await self.login(page)
                
                # Check if we're on the students page
                if '/students' not in page.url:
                    raise Exception(f"Expected to be on students page, but current URL is: {page.url}")
                
                print(f"Successfully logged in. Current URL: {page.url}")
                
                # Extract student data from current page
                students = await self.extract_student_data(page)
                
                # Check if there are pagination controls or load more buttons
                print("Checking for pagination or load more options...")
                
                # Look for pagination buttons, load more buttons, etc.
                load_more_selectors = [
                    'button:has-text("Load More")',
                    'button:has-text("Show More")',
                    'a:has-text("Next")',
                    '.pagination a',
                    '[class*="load"]',
                    '[class*="more"]'
                ]
                
                for selector in load_more_selectors:
                    try:
                        load_more_btn = await page.query_selector(selector)
                        if load_more_btn:
                            print(f"Found load more button: {selector}")
                            # You might want to implement pagination here
                            break
                    except:
                        continue
                
                # Save data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save as JSON
                json_filename = f"students_data_{timestamp}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(students, f, indent=2, ensure_ascii=False)
                
                # Save as CSV
                csv_filename = f"students_data_{timestamp}.csv"
                if students:
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                        # Get all possible fieldnames
                        fieldnames = set()
                        for student in students:
                            fieldnames.update(student.keys())
                        fieldnames = sorted(list(fieldnames))
                        
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(students)
                
                print(f"Scraped {len(students)} students")
                print(f"Data saved to {json_filename} and {csv_filename}")
                
                return students
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"error_screenshot_{timestamp}.png")
                raise
                
            finally:
                await browser.close()

async def main():
    """Main function"""
    try:
        scraper = MathAcademyStudentScraper()
        students = await scraper.scrape_all_students()
        
        print(f"\n=== SCRAPING COMPLETE ===")
        print(f"Total students scraped: {len(students)}")
        
        if students:
            print(f"\nSample student data:")
            for i, student in enumerate(students[:3]):  # Show first 3 students
                print(f"{i+1}. {student}")
        
        return students
        
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())