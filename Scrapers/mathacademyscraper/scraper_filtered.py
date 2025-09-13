#!/usr/bin/env python3
"""
Filtered Math Academy Students Scraper
Extracts data only for students whose names are listed in student_names_to_scrape.txt
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

class FilteredMathAcademyStudentScraper:
    def __init__(self, names_file="student_names_to_scrape.txt"):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        
        self.students_url = "https://www.mathacademy.com/students"
        self.names_file = names_file
        self.target_names = self.load_target_names()
        
    def load_target_names(self):
        """Load the list of student names to scrape from file"""
        target_names = []
        
        if not os.path.exists(self.names_file):
            print(f"Warning: {self.names_file} not found. Creating example file...")
            # Create example file if it doesn't exist
            with open(self.names_file, 'w') as f:
                f.write("# Add student names here, one per line\n")
                f.write("# Lines starting with # are comments\n")
                f.write("\n")
            return target_names
        
        try:
            with open(self.names_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        target_names.append(line.lower())  # Convert to lowercase for case-insensitive matching
            
            print(f"Loaded {len(target_names)} target student names from {self.names_file}")
            for name in target_names:
                print(f"  - {name}")
            
        except Exception as e:
            print(f"Error loading names file: {e}")
            
        return target_names
    
    def should_scrape_student(self, student_name):
        """Check if this student should be scraped based on the target names list"""
        if not self.target_names:
            return False
        
        student_name_lower = student_name.lower()
        
        # Check if any target name is contained in the student name
        for target_name in self.target_names:
            if target_name in student_name_lower:
                return True
        
        return False

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

    async def extract_filtered_student_data(self, page):
        """Extract student data only for target students"""
        print("Extracting filtered student data...")
        
        if not self.target_names:
            print("No target names specified. Please add names to student_names_to_scrape.txt")
            return []
        
        # Wait for the page to fully load
        await page.wait_for_load_state('networkidle')
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        students = []
        found_students = []
        skipped_count = 0
        
        # Find all student name links
        student_links = soup.find_all('a', class_='studentNameLink')
        print(f"Found {len(student_links)} total student links")
        
        for link in student_links:
            try:
                student_name = link.get_text(strip=True)
                
                # Check if this student should be scraped
                if not self.should_scrape_student(student_name):
                    skipped_count += 1
                    continue
                
                print(f"✓ Extracting data for: {student_name}")
                found_students.append(student_name)
                
                student_data = {}
                
                # Extract student ID from href (/students/22710/activity)
                href = link.get('href', '')
                student_id_match = re.search(r'/students/(\d+)/', href)
                if student_id_match:
                    student_data['student_id'] = int(student_id_match.group(1))
                
                # Extract student name
                student_data['name'] = student_name
                
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
                                
                                # Parse structured data from cells
                                if len(cell_texts) >= 7:
                                    student_data['course'] = cell_texts[3] if len(cell_texts) > 3 else ''
                                    student_data['progress_percentage'] = cell_texts[4] if len(cell_texts) > 4 else ''
                                    student_data['last_activity'] = cell_texts[5] if len(cell_texts) > 5 else ''
                                    
                                    # Try to extract activity counts
                                    if len(cell_texts) > 6 and cell_texts[6].isdigit():
                                        student_data['activity_count'] = int(cell_texts[6])
                                    if len(cell_texts) > 7 and cell_texts[7].isdigit():
                                        student_data['problems_completed'] = int(cell_texts[7])
                                
                                # Store all cell data for analysis
                                student_data['row_data'] = cell_texts
                
                # Add extraction timestamp
                student_data['extracted_at'] = datetime.now().isoformat()
                
                students.append(student_data)
                
            except Exception as e:
                print(f"Error extracting data for student link {link}: {e}")
                continue
        
        print(f"\n=== FILTERING RESULTS ===")
        print(f"Total students on page: {len(student_links)}")
        print(f"Students matching target names: {len(students)}")
        print(f"Students skipped: {skipped_count}")
        
        if found_students:
            print(f"\nFound students:")
            for name in found_students:
                print(f"  ✓ {name}")
        
        # Check for any target names that weren't found
        found_names_lower = [name.lower() for name in found_students]
        missing_names = []
        for target in self.target_names:
            found_match = False
            for found in found_names_lower:
                if target in found:
                    found_match = True
                    break
            if not found_match:
                missing_names.append(target)
        
        if missing_names:
            print(f"\nTarget names NOT found:")
            for name in missing_names:
                print(f"  ✗ {name}")
        
        return students

    async def scrape_filtered_students(self):
        """Main scraping function for filtered students"""
        if not self.target_names:
            print("No target names loaded. Please add student names to student_names_to_scrape.txt")
            return []
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Login
                await self.login(page)
                
                # Check if we're on the students page
                if '/students' not in page.url:
                    raise Exception(f"Expected to be on students page, but current URL is: {page.url}")
                
                print(f"Successfully logged in. Current URL: {page.url}")
                
                # Extract filtered student data
                students = await self.extract_filtered_student_data(page)
                
                if not students:
                    print("No matching students found!")
                    return students
                
                # Save data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save as JSON
                json_filename = f"filtered_students_data_{timestamp}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(students, f, indent=2, ensure_ascii=False)
                
                # Save as CSV
                csv_filename = f"filtered_students_data_{timestamp}.csv"
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
                
                print(f"\n=== FILES SAVED ===")
                print(f"JSON: {json_filename}")
                print(f"CSV: {csv_filename}")
                
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
        scraper = FilteredMathAcademyStudentScraper()
        students = await scraper.scrape_filtered_students()
        
        print(f"\n=== SCRAPING COMPLETE ===")
        print(f"Total filtered students scraped: {len(students)}")
        
        if students:
            print(f"\nFiltered student data:")
            for i, student in enumerate(students):
                print(f"{i+1}. {student.get('name', 'Unknown')} (ID: {student.get('student_id', 'N/A')})")
                if 'course' in student:
                    print(f"    Course: {student['course']}")
                if 'progress_percentage' in student:
                    print(f"    Progress: {student['progress_percentage']}")
        
        return students
        
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())