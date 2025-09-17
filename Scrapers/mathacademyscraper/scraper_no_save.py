#!/usr/bin/env python3
"""
Math Academy Scraper - Data Extraction with Supabase Update
This version extracts all student data and updates existing rows in Supabase
"""

import asyncio
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

class MathAcademySupabaseUpdater:
    def __init__(self):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.username or not self.password:
            raise ValueError("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file")
        
        # Initialize Supabase client for database operations
        from supabase import create_client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        self.target_names = self.load_target_names_from_supabase()
        print(f"Loaded {len(self.target_names)} target student names from Supabase students table")
        
        if self.target_names:
            print("Names converted to 'Last, First' format:")
            for i, name in enumerate(list(self.target_names)[:10], 1):  # Show first 10
                print(f"  - Target student {i}")
            if len(self.target_names) > 10:
                print(f"  ... and {len(self.target_names) - 10} more")

    def convert_name_format(self, name: str) -> str:
        """Convert 'First Last' to 'Last, First' format (lowercase)"""
        name = name.strip()
        if ',' in name:
            # Already in "Last, First" format, just lowercase
            parts = [part.strip().lower() for part in name.split(',')]
            return f"{parts[0]}, {parts[1]}"
        else:
            # Convert "First Last" to "last, first"
            parts = name.split()
            if len(parts) >= 2:
                first_parts = parts[:-1]  # Everything except last part
                last_part = parts[-1]    # Last part
                first_name = ' '.join(first_parts).lower()
                last_name = last_part.lower()
                return f"{last_name}, {first_name}"
            else:
                # Single name, return as is (lowercase)
                return name.lower()

    def load_target_names_from_supabase(self) -> set:
        """Load target student names directly from Supabase students table"""
        names = set()
        try:
            from supabase import create_client
            
            # Initialize Supabase client
            supabase = create_client(self.supabase_url, self.supabase_key)
            print("✓ Connected to Supabase for student names")
            
            # Fetch student names from Supabase
            result = supabase.table('students').select('name').execute()
            
            if result.data:
                for student in result.data:
                    name = student.get('name', '').strip()
                    if name:
                        converted_name = self.convert_name_format(name)
                        names.add(converted_name)
                
                print(f"✓ Fetched {len(names)} student names from Supabase")
            else:
                print("Warning: No students found in Supabase students table")
            
            return names
            
        except Exception as e:
            print(f"Error fetching student names from Supabase: {e}")
            print("Falling back to empty set - will process no students")
            return set()

    async def login(self, page: Page) -> bool:
        """Login to Math Academy"""
        try:
            print("Logging in...")
            await page.goto("https://www.mathacademy.com/login")
            await page.wait_for_load_state('networkidle')
            
            
            # Try different possible selectors for login form
            login_selectors = [
                'input[name="usernameOrEmail"]',  # This is the correct selector
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id="username"]',
                'input[id="email"]',
                '#username',
                '#email'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]',
                '#password'
            ]
            
            username_field = None
            password_field = None
            
            # Find username field
            for selector in login_selectors:
                try:
                    field = await page.query_selector(selector)
                    if field:
                        username_field = selector
                        print(f"Found username field with selector: {selector}")
                        break
                except:
                    continue
            
            # Find password field
            for selector in password_selectors:
                try:
                    field = await page.query_selector(selector)
                    if field:
                        password_field = selector
                        print(f"Found password field with selector: {selector}")
                        break
                except:
                    continue
            
            if not username_field or not password_field:
                # Get page content to debug
                content = await page.content()
                with open("login_page_content.html", "w") as f:
                    f.write(content)
                print("Login form fields not found. Page content saved to login_page_content.html")
                return False
            
            # Fill login form
            await page.fill(username_field, self.username)
            await page.fill(password_field, self.password)
            
            # Try different submit button selectors
            submit_selectors = [
                'input[type="submit"]',  # This is the correct selector
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.btn-primary',
                '.login-button',
                'form button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        submit_button = selector
                        print(f"Found submit button with selector: {selector}")
                        break
                except:
                    continue
            
            if submit_button:
                await page.click(submit_button)
            else:
                # Try pressing Enter on password field
                await page.press(password_field, 'Enter')
            
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check if login was successful
            current_url = page.url
            if '/students' in current_url or '/dashboard' in current_url:
                print("Login completed!")
                return True
            else:
                print(f"Login may have failed. Current URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    async def get_detailed_student_data(self, page, student_id: int, student_name: str) -> Dict[str, Any]:
        """Get comprehensive detailed data by clicking on the student's link from the dashboard"""
        
        try:
            print(f"  → Getting detailed data for {student_name} (ID: {student_id})")
            
            # First go back to the students page if we're not there
            current_url = page.url
            if '/students' not in current_url or len(current_url.split('/')) > 4:
                print(f"    → Navigating back to students dashboard")
                await page.goto("https://www.mathacademy.com/students")
                await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Try clicking the student link to get to the activity page
            student_link_selector = f'a[id="studentNameLink-{student_id}"]'
            student_link = await page.query_selector(student_link_selector)
            
            if student_link:
                print(f"    → Clicking on student link")
                await student_link.click()
                await page.wait_for_load_state('networkidle', timeout=15000)
                
                # Wait a bit more for any dynamic content to load
                await page.wait_for_timeout(3000)
            else:
                # Try direct navigation to the activity page
                print(f"    → Student link not found, trying direct navigation")
                activity_url = f"https://www.mathacademy.com/students/{student_id}/activity"
                await page.goto(activity_url)
                await page.wait_for_load_state('networkidle', timeout=15000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            student_url = f"https://www.mathacademy.com/students/{student_id}/activity"
            detailed_data = {
                'student_url': student_url,
                'daily_activity': {},
                'tasks': {},
                'weekly_xp': None,
                'daily_xp': None,
                'estimated_completion': None
            }
            
            # Extract specific data using the exact HTML elements
            
            # 1. Weekly XP from <div id="thisWeekTotalXP">0 XP</div>
            weekly_xp_element = soup.find('div', id='thisWeekTotalXP')
            if weekly_xp_element:
                weekly_xp_text = weekly_xp_element.get_text(strip=True)
                detailed_data['weekly_xp'] = weekly_xp_text
                pass  # Found weekly XP data
            
            # 2. Daily XP from <td id="dailyGoalPoints">0/70 XP</td>
            daily_xp_element = soup.find('td', id='dailyGoalPoints')
            if daily_xp_element:
                daily_xp_text = daily_xp_element.get_text(strip=True)
                detailed_data['daily_xp'] = daily_xp_text
                pass  # Found daily XP data
            
            # 3. Course completion percentage from <div id="coursePercentComplete">29%</div>
            course_percent_element = soup.find('div', id='coursePercentComplete')
            if course_percent_element:
                course_percent_text = course_percent_element.get_text(strip=True)
                detailed_data['estimated_completion'] = course_percent_text
                print(f"    → Found course completion: {course_percent_text}")
            
            # 4. Extract detailed daily activity from task table
            task_rows = soup.find_all('tr', id=re.compile(r'task-\d+'))
            
            if task_rows:
                pass  # Found task rows
                
                daily_activities = []
                for task_row in task_rows:
                    try:
                        task_data = {}
                        
                        # Extract task ID
                        task_id = task_row.get('id', '')
                        if task_id:
                            task_data['task_id'] = task_id
                        
                        # Extract task type (Review, Lesson, etc.)
                        task_type = task_row.get('type', '')
                        if task_type:
                            task_data['task_type'] = task_type
                        
                        # Extract progress
                        progress = task_row.get('progress', '')
                        if progress:
                            task_data['progress'] = progress
                        
                        # Extract task name from <div id="taskName-XXXXX" class="taskName">
                        task_name_div = task_row.find('div', class_='taskName')
                        if task_name_div:
                            task_data['task_name'] = task_name_div.get_text(strip=True)
                        
                        # Extract completion percentage from taskCompletedColumn
                        completion_cell = task_row.find('td', class_='taskCompletedColumn')
                        if completion_cell:
                            completion_text = completion_cell.get_text(strip=True)
                            if completion_text and '%' in completion_text:
                                task_data['completion_percentage'] = completion_text
                            elif completion_text and ':' in completion_text:
                                task_data['completion_time'] = completion_text
                        
                        # Extract XP from taskPointsColumn
                        points_cell = task_row.find('td', class_='taskPointsColumn')
                        if points_cell:
                            xp_spans = points_cell.find_all('span')
                            for span in xp_spans:
                                span_text = span.get_text(strip=True)
                                if 'XP' in span_text:
                                    task_data['xp_earned'] = span_text
                                    break
                        
                        if task_data:
                            daily_activities.append(task_data)
                            
                    except Exception as e:
                        continue
                
                detailed_data['daily_activity'] = daily_activities
                pass  # Extracted task activities
            
            # 5. Extract date-specific XP totals from dateHeader rows
            date_headers = soup.find_all('td', class_='dateHeader')
            date_totals = []
            
            for date_header in date_headers:
                try:
                    date_info = {}
                    date_text = date_header.get_text(strip=True)
                    
                    # Extract date
                    date_parts = date_text.split()
                    if len(date_parts) >= 3:
                        date_info['date'] = ' '.join(date_parts[:3])
                    
                    # Extract XP total from span with class dateTotalXP
                    xp_span = date_header.find('span', class_='dateTotalXP')
                    if xp_span:
                        date_info['total_xp'] = xp_span.get_text(strip=True)
                    
                    if date_info:
                        date_totals.append(date_info)
                        
                except Exception as e:
                    continue
            
            if date_totals:
                # Add date totals directly to the daily_activity list
                if isinstance(detailed_data['daily_activity'], list):
                    # Extend the existing list with date totals (flattened structure)
                    for date_total in date_totals:
                        date_total['type'] = 'date_total'  # Mark as date total
                        detailed_data['daily_activity'].append(date_total)
                else:
                    # If no tasks, just set as date totals list
                    for date_total in date_totals:
                        date_total['type'] = 'date_total'
                    detailed_data['daily_activity'] = date_totals
                print(f"    → Extracted {len(date_totals)} daily XP totals")
            
            return detailed_data
            
        except Exception as e:
            print(f"  ✗ Error getting detailed data for {student_name}: {e}")
            return {
                'student_url': f"https://www.mathacademy.com/students/{student_id}/activity",
                'error': str(e),
                'weekly_xp': None,
                'daily_xp': None,
                'estimated_completion': None,
                'daily_activity': [],
                'tasks': {}
            }

    async def save_to_supabase(self, student_data: Dict[str, Any]) -> bool:
        """Update existing student data in Supabase or insert if not exists"""
        try:
            print(f"  → Updating Supabase record...")
            
            # Remove fields that aren't in the Supabase schema
            supabase_data = {k: v for k, v in student_data.items() 
                           if k not in ['error', 'tasks']}  # Skip fields not in schema
            
            # Handle last_activity field - ensure it's a string or None
            if 'last_activity' in supabase_data:
                last_activity = supabase_data['last_activity']
                if last_activity and isinstance(last_activity, str):
                    # Keep the casual date format as-is (e.g., "Fri, Aug 8")
                    # The column is now TEXT type so it can handle this format
                    print(f"  → Saving last_activity: {last_activity}")
                else:
                    supabase_data['last_activity'] = None
                    print(f"  → Setting last_activity to None (no valid date)")
            
            # Check if student already exists
            existing = self.supabase.table('math_academy_students').select('id').eq('student_id', student_data['student_id']).execute()
            
            if existing.data:
                # Update existing record
                result = self.supabase.table('math_academy_students').update(supabase_data).eq('student_id', student_data['student_id']).execute()
                print(f"  ✓ Updated existing record in Supabase")
            else:
                # Insert new record (only if student doesn't exist)
                result = self.supabase.table('math_academy_students').insert(supabase_data).execute()
                print(f"  ✓ Inserted new record to Supabase")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error saving to Supabase: {e}")
            return False

    async def extract_and_save_student_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract student data from the main dashboard and get detailed data for target students only"""
        try:
            print("Extracting student data...")
            
            # Get the page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all student links
            student_links = soup.find_all('a', id=re.compile(r'studentNameLink-\d+'))
            print(f"Found {len(student_links)} total student links")
            
            # First pass: identify target students
            target_students = []
            
            for link in student_links:
                try:
                    # Extract student ID from the link id
                    link_id = link.get('id', '')
                    student_id_match = re.search(r'studentNameLink-(\d+)', link_id)
                    if not student_id_match:
                        continue
                    
                    student_id = int(student_id_match.group(1))
                    
                    # Extract student name
                    student_name = link.get_text(strip=True)
                    
                    # Convert to lowercase for comparison
                    student_name_lower = student_name.lower()
                    
                    # Check if this student is in our target list
                    if not self.target_names or student_name_lower in self.target_names:
                        print(f"✓ Found target student")
                        target_students.append({
                            'id': student_id,
                            'name': student_name,
                            'name_lower': student_name_lower
                        })
                    
                except Exception as e:
                    continue
            
            if not target_students:
                print("❌ No target students found on the dashboard")
                return []
            
            print(f"=== PROCESSING {len(target_students)} TARGET STUDENTS ===")
            
            # Second pass: get detailed data for each target student
            scraped_students = []
            
            for target in target_students:
                try:
                    student_id = target['id']
                    student_name = target['name']
                    
                    print(f"✓ Processing: {student_name}")
                    
                    # Get basic info from dashboard first
                    student_row = soup.find('tr', id=f'studentRow-{student_id}')
                    basic_data = {
                        'student_id': str(student_id),
                        'name': student_name,
                        'course_name': None,
                        'percent_complete': None,
                        'last_activity': None
                    }
                    
                    if student_row:
                        cells = student_row.find_all('td')
                        print(f"    → Found {len(cells)} cells in dashboard row for {student_name}")
                        
                        if len(cells) >= 4:
                            # Extract actual course name from cell 3 (not the code from cell 1)
                            course_cell = cells[3] if len(cells) > 3 else None
                            if course_cell:
                                course_text = course_cell.get_text(strip=True)
                                basic_data['course_name'] = course_text if course_text else None
                                print(f"    → Course: {basic_data['course_name']}")
                            
                            # Extract progress from cell 2
                            progress_cell = cells[2] if len(cells) > 2 else None
                            if progress_cell:
                                progress_text = progress_cell.get_text(strip=True)
                                basic_data['percent_complete'] = progress_text if progress_text else None
                                print(f"    → Progress: {basic_data['percent_complete']}")
                            
                            # Extract last activity from cell 3
                            activity_cell = cells[3] if len(cells) > 3 else None
                            if activity_cell:
                                activity_text = activity_cell.get_text(strip=True)
                                basic_data['last_activity'] = activity_text if activity_text else None
                                print(f"    → Last Activity: {basic_data['last_activity']}")
                        else:
                            print(f"    → Not enough cells found for basic data extraction")
                    else:
                        print(f"    → Student row not found on dashboard for ID {student_id}")
                        
                        # Try alternative approach - look for student data in the link's parent row
                        for link in student_links:
                            if f'studentNameLink-{student_id}' in link.get('id', ''):
                                parent_row = link.find_parent('tr')
                                if parent_row:
                                    cells = parent_row.find_all('td')
                                    print(f"    → Found {len(cells)} cells in parent row")
                                    
                                    
                                    if len(cells) >= 4:
                                        # Try different cell positions for the data
                                        # Cell 0: Usually student name
                                        # Cell 1: Usually course name
                                        # Look for percentage in cells that contain '%'
                                        # Look for last activity in cells that might contain dates/times
                                        
                                        # Extract actual course name from cell 3 (not the code from cell 1)
                                        basic_data['course_name'] = cells[3].get_text(strip=True) if len(cells) > 3 else None
                                        
                                        # Search for progress percentage (contains %)
                                        for i, cell in enumerate(cells):
                                            cell_text = cell.get_text(strip=True)
                                            if '%' in cell_text and cell_text != '':
                                                basic_data['percent_complete'] = cell_text
                                                print(f"    → Found progress in cell {i}: {cell_text}")
                                                break
                                        
                                        # Search for last activity (look for time-related text or dates)
                                        for i, cell in enumerate(cells):
                                            cell_text = cell.get_text(strip=True)
                                            # Look for patterns like "3 days ago", "Today", "Yesterday", dates, etc.
                                            if any(keyword in cell_text.lower() for keyword in ['ago', 'today', 'yesterday', 'day', 'week', 'month', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) and cell_text != '':
                                                basic_data['last_activity'] = cell_text
                                                print(f"    → Found last activity in cell {i}: {cell_text}")
                                                break
                                        
                                        print(f"    → Final extraction - Course: {basic_data['course_name']}, Progress: {basic_data['percent_complete']}, Last Activity: {basic_data['last_activity']}")
                                break
                    
                    print(f"  → Clicking into {student_name}'s detailed page...")
                    
                    # Get detailed data by clicking into the student's page
                    detailed_data = await self.get_detailed_student_data(page, student_id, student_name)
                    
                    # Combine basic and detailed data
                    combined_data = {**basic_data, **detailed_data}
                    
                    # Display extracted data instead of saving
                    print(f"  ✓ EXTRACTED DATA FOR {student_name}:")
                    print(f"    - Course: {combined_data.get('course_name', 'N/A')}")
                    print(f"    - Progress: {combined_data.get('percent_complete', 'N/A')}")
                    print(f"    - Weekly XP: {combined_data.get('weekly_xp', 'N/A')}")
                    print(f"    - Daily XP: {combined_data.get('daily_xp', 'N/A')}")
                    print(f"    - Course Completion: {combined_data.get('estimated_completion', 'N/A')}")
                    
                    daily_activity = combined_data.get('daily_activity', [])
                    if daily_activity:
                        # Count different types of activities in the flattened list
                        task_count = sum(1 for item in daily_activity if isinstance(item, dict) and item.get('task_id'))
                        date_total_count = sum(1 for item in daily_activity if isinstance(item, dict) and item.get('type') == 'date_total')
                        print(f"    - Task Activities: {task_count}")
                        print(f"    - Daily XP Totals: {date_total_count}")
                    
                    # Save to Supabase (update existing or insert new)
                    success = await self.save_to_supabase(combined_data)
                    if success:
                        scraped_students.append(combined_data)
                    
                except Exception as e:
                    print(f"✗ Error processing {target.get('name', 'Unknown')}: {e}")
                    continue
            
            return scraped_students
            
        except Exception as e:
            print(f"Error in extract_and_save_student_data: {e}")
            return []

    async def scrape_and_update_supabase(self) -> List[Dict[str, Any]]:
        """Main scraping method - extract data and update Supabase"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Navigate and login
                print("Navigating to students page...")
                await page.goto("https://www.mathacademy.com/students")
                await page.wait_for_load_state('networkidle')
                
                # Login
                login_success = await self.login(page)
                if not login_success:
                    print("❌ Login failed")
                    return []
                
                print(f"Successfully logged in. Current URL: {page.url}")
                
                # Extract student data
                scraped_students = await self.extract_and_save_student_data(page)
                
                if scraped_students:
                    print(f"\n🎉 Successfully processed {len(scraped_students)} students!")
                    print(f"📊 All data updated in Supabase math_academy_students table")
                    
# JSON backup removed per user request
                    
                else:
                    print("❌ No student data was processed")
                
                return scraped_students
                
            except Exception as e:
                print(f"❌ Scraping failed: {e}")
                return []
                
            finally:
                await browser.close()

async def main():
    """Main function"""
    try:
        updater = MathAcademySupabaseUpdater()
        scraped_data = await updater.scrape_and_update_supabase()
        
        if scraped_data:
            print(f"\n✅ Scraping and update completed successfully!")
            print(f"📊 Total students updated in Supabase: {len(scraped_data)}")
            
            # Show summary
            print("\n📋 UPDATE SUMMARY:")
            for i, student in enumerate(scraped_data[:5], 1):
                name = student.get('name', 'Unknown')
                course = student.get('course_name', 'N/A')
                progress = student.get('percent_complete', 'N/A')
                weekly_xp = student.get('weekly_xp', 'N/A')
                print(f"  {i}. {name}")
                print(f"     Course: {course}, Progress: {progress}, Weekly XP: {weekly_xp}")
            
            if len(scraped_data) > 5:
                print(f"     ... and {len(scraped_data) - 5} more students")
        else:
            print("❌ No data processed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())