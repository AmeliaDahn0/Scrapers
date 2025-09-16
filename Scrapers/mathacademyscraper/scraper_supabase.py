#!/usr/bin/env python3
"""
Math Academy Students Scraper with Supabase Integration
Extracts detailed student data and saves to Supabase database
"""

import asyncio
import os
import json
import csv
from datetime import datetime, timezone
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from supabase import create_client, Client
from typing import Optional, Dict, Any, List

# Load environment variables
load_dotenv()

class MathAcademySupabaseScraper:
    def __init__(self, names_file="student_names_to_scrape.txt"):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.username or not self.password:
            raise ValueError("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file")
        
        self.students_url = "https://www.mathacademy.com/students"
        self.names_file = names_file
        self.target_names = self.load_target_names()
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print("✓ Supabase client initialized")
        
    def convert_name_format(self, name):
        """Convert 'First Last' to 'Last, First' format"""
        name = name.strip()
        
        # If already in "Last, First" format, return as is
        if ',' in name:
            return name.lower()
        
        # Split by space and assume last word is last name
        parts = name.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            first_names = ' '.join(parts[:-1])
            converted = f"{last_name}, {first_names}"
            return converted.lower()
        else:
            # Single name, return as is
            return name.lower()
    
    def load_target_names(self):
        """Load the list of student names to scrape from file"""
        target_names = []
        
        if not os.path.exists(self.names_file):
            print(f"Warning: {self.names_file} not found.")
            return target_names
        
        try:
            with open(self.names_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Convert to "Last, First" format
                        converted_name = self.convert_name_format(line)
                        target_names.append(converted_name)
            
            print(f"Loaded {len(target_names)} target student names from {self.names_file}")
            print("Names converted to 'Last, First' format:")
            for i, name in enumerate(target_names, 1):
                print(f"  - Target student {i}")
            
        except Exception as e:
            print(f"Error loading names file: {e}")
            
        return target_names
    
    def should_scrape_student(self, student_name):
        """Check if this student should be scraped based on the target names list"""
        if not self.target_names:
            return False
        
        student_name_lower = student_name.lower()
        
        for target_name in self.target_names:
            if target_name in student_name_lower:
                return True
        
        return False

    async def login(self, page):
        """Login to Math Academy"""
        print("Navigating to students page...")
        await page.goto(self.students_url)
        
        await page.wait_for_load_state('networkidle')
        
        login_selectors = [
            'input[type="email"]',
            'input[name="username"]', 
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            'form input[type="text"]'
        ]
        
        login_field = None
        for selector in login_selectors:
            try:
                login_field = await page.query_selector(selector)
                if login_field:
                    break
            except:
                continue
        
        if not login_field:
            login_links = await page.query_selector_all('a[href*="login"], a[href*="signin"], a[href*="sign-in"]')
            if login_links:
                await login_links[0].click()
                await page.wait_for_load_state('networkidle')
                
                for selector in login_selectors:
                    try:
                        login_field = await page.query_selector(selector)
                        if login_field:
                            break
                    except:
                        continue
        
        if login_field:
            print("Logging in...")
            await login_field.fill(self.username)
            
            password_field = await page.query_selector('input[type="password"]')
            if password_field:
                await password_field.fill(self.password)
                
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'form button'
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_btn = await page.query_selector(selector)
                        if submit_btn:
                            await submit_btn.click()
                            break
                    except:
                        continue
                
                await page.wait_for_load_state('networkidle', timeout=15000)
                print("Login completed!")
            else:
                raise Exception("Could not find password field")
        else:
            raise Exception("Could not find login form")

    async def get_detailed_student_data(self, page, student_id: int, student_name: str) -> Dict[str, Any]:
        """Get comprehensive detailed data by clicking on the student's link from the dashboard"""
        
        try:
            print(f"  → Getting detailed data for student")
            
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
            
            # Take a screenshot for debugging if needed
            # await page.screenshot(path=f"student_{student_id}_page.png")
            
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
            
            # Extract specific data using the exact HTML elements you provided
            
            # 1. Weekly XP from <div id="thisWeekTotalXP">0 XP</div>
            weekly_xp_element = soup.find('div', id='thisWeekTotalXP')
            if weekly_xp_element:
                weekly_xp_text = weekly_xp_element.get_text(strip=True)
                detailed_data['weekly_xp'] = weekly_xp_text
                print(f"    → Found weekly XP data")
            
            # 2. Daily XP from <td id="dailyGoalPoints">0/70 XP</td>
            daily_xp_element = soup.find('td', id='dailyGoalPoints')
            if daily_xp_element:
                daily_xp_text = daily_xp_element.get_text(strip=True)
                detailed_data['daily_xp'] = daily_xp_text
                print(f"    → Found daily XP data")
            
            # 3. Estimated completion date from <div id="estimatedCompletion">
            estimated_completion_element = soup.find('div', id='estimatedCompletion')
            if estimated_completion_element:
                # Extract the date from the span inside the div
                span_element = estimated_completion_element.find('span')
                if span_element:
                    estimated_date = span_element.get_text(strip=True)
                    detailed_data['estimated_completion'] = estimated_date
                    print(f"    → Found estimated completion date")
                else:
                    # Fallback: get all text and extract date
                    full_text = estimated_completion_element.get_text(strip=True)
                    detailed_data['estimated_completion'] = full_text
                    print(f"    → Found estimated completion data")
            
            # 4. Extract detailed daily activity with dates from task table
            # First, get all date headers to create a date context map
            date_headers = soup.find_all('td', class_='dateHeader')
            date_context_map = {}
            
            for date_header in date_headers:
                try:
                    # Get the raw text from the date header
                    date_text = date_header.get_text(strip=True)
                    
                    # Extract clean date by looking for the date pattern before any XP information
                    # Format is typically "Day, Month DDth" or "Day, Month DD"
                    clean_date = None
                    date_total_xp = "0 XP"
                    
                    # Look for pattern like "Fri, Jul 11th" at the beginning
                    date_match = re.match(r'^([A-Za-z]{3}, [A-Za-z]{3} \d{1,2}(?:st|nd|rd|th)?)', date_text)
                    if date_match:
                        clean_date = date_match.group(1)
                        
                        # Extract XP total separately from span or remaining text
                        xp_span = date_header.find('span', class_='dateTotalXP')
                        if xp_span:
                            date_total_xp = xp_span.get_text(strip=True)
                        else:
                            # Look for XP in the remaining text
                            remaining_text = date_text[len(clean_date):].strip()
                            xp_match = re.search(r'(\d+\s*XP)', remaining_text)
                            if xp_match:
                                date_total_xp = xp_match.group(1)
                    else:
                        # Fallback: try to extract first 3 words as date
                        date_parts = date_text.split()
                        if len(date_parts) >= 3:
                            clean_date = ' '.join(date_parts[:3])
                            # Remove any trailing numbers that might be XP values
                            clean_date = re.sub(r'\d+$', '', clean_date).strip()
                    
                    if clean_date:
                        # Get the parent row to find position in DOM
                        parent_row = date_header.find_parent('tr')
                        if parent_row:
                            date_context_map[parent_row] = {
                                'date': clean_date,
                                'total_xp': date_total_xp
                            }
                except Exception as e:
                    continue
            
            # Now extract tasks and associate them with dates
            task_rows = soup.find_all('tr', id=re.compile(r'task-\d+'))
            daily_activities_by_date = {}
            
            if task_rows:
                print(f"    → Found {len(task_rows)} task rows")
                
                for task_row in task_rows:
                    try:
                        task_data = {}
                        
                        # Extract task ID
                        task_id = task_row.get('id', '')
                        if task_id:
                            task_data['task_id'] = task_id
                        
                        # Find the closest preceding date header by walking up the DOM
                        current_date = None
                        current_element = task_row
                        
                        # Look for the nearest date header by checking previous siblings
                        while current_element:
                            prev_sibling = current_element.find_previous_sibling('tr')
                            if prev_sibling and prev_sibling in date_context_map:
                                current_date = date_context_map[prev_sibling]['date']
                                date_total_xp = date_context_map[prev_sibling]['total_xp']
                                break
                            current_element = prev_sibling
                        
                        # If no date found, look for any date header before this task in the document
                        if not current_date and date_context_map:
                            # Use the last date header found as fallback
                            for date_row, date_info in date_context_map.items():
                                if task_row.sourceline and date_row.sourceline and date_row.sourceline < task_row.sourceline:
                                    current_date = date_info['date']
                                    date_total_xp = date_info['total_xp']
                        
                        # If still no date, use "Unknown Date"
                        if not current_date:
                            current_date = "Unknown Date"
                            date_total_xp = "0 XP"
                        
                        # Initialize date entry if needed
                        if current_date not in daily_activities_by_date:
                            daily_activities_by_date[current_date] = {
                                'date': current_date,
                                'total_xp': date_total_xp,
                                'activities': []
                            }
                        
                        # Associate task with date
                        task_data['date'] = current_date
                        
                        # Extract task type (Review, Lesson, etc.)
                        task_type = task_row.get('type', '')
                        if task_type:
                            task_data['task_type'] = task_type
                        
                        # Extract progress
                        progress = task_row.get('progress', '')
                        if progress:
                            task_data['progress'] = progress
                        
                        # Extract task name from <div class="taskName">
                        task_name_div = task_row.find('div', class_='taskName')
                        if task_name_div:
                            task_data['task_name'] = task_name_div.get_text(strip=True)
                        
                        # Extract completion percentage from taskCompletedColumn
                        completion_cell = task_row.find('td', class_='taskCompletedColumn')
                        if completion_cell:
                            completion_text = completion_cell.get_text(strip=True)
                            if completion_text and '%' in completion_text:
                                task_data['completion_percentage'] = completion_text
                            elif completion_text and ':' in completion_text:  # Time format like "12:10 PM"
                                task_data['completion_time'] = completion_text
                        
                        # Extract XP from taskPointsColumn
                        points_cell = task_row.find('td', class_='taskPointsColumn')
                        if points_cell:
                            # Look for XP values in various spans
                            xp_spans = points_cell.find_all('span')
                            for span in xp_spans:
                                span_text = span.get_text(strip=True)
                                if 'XP' in span_text:
                                    task_data['xp_earned'] = span_text
                                    break
                        
                        # Add to the date's activities
                        if task_data:
                            daily_activities_by_date[current_date]['activities'].append(task_data)
                            
                    except Exception as e:
                        continue
                
                detailed_data['daily_activity'] = daily_activities_by_date
                total_tasks = sum(len(date_data['activities']) for date_data in daily_activities_by_date.values())
                print(f"    → Extracted {total_tasks} task activities across {len(daily_activities_by_date)} dates")
            
            # 5. Extract activity data from various page elements
            # Look for progress bars, charts, and activity summaries
            progress_elements = soup.find_all(['div', 'span', 'td'], class_=re.compile(r'progress|activity|score|xp', re.I))
            for element in progress_elements:
                text = element.get_text(strip=True)
                if text and any(keyword in text.lower() for keyword in ['daily', 'week', 'activity', 'progress', 'xp', 'points']):
                    key = element.get('class', ['unknown'])[0] if element.get('class') else 'activity_data'
                    detailed_data['daily_activity'][key] = text
            
            # Look for task/assignment data
            task_elements = soup.find_all(['div', 'span', 'td', 'li'], class_=re.compile(r'task|assignment|problem|exercise', re.I))
            for element in task_elements:
                text = element.get_text(strip=True)
                if text:
                    key = element.get('class', ['unknown'])[0] if element.get('class') else 'task_data'
                    detailed_data['tasks'][key] = text
            
            # Extract data from tables more comprehensively
            tables = soup.find_all('table')
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                table_data = {}
                
                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if key and value:
                            table_data[f"row_{row_idx}_{key}"] = value
                
                if table_data:
                    if any(keyword in str(table_data).lower() for keyword in ['activity', 'daily', 'weekly']):
                        detailed_data['daily_activity'][f'table_{table_idx}'] = table_data
                    elif any(keyword in str(table_data).lower() for keyword in ['task', 'assignment', 'problem']):
                        detailed_data['tasks'][f'table_{table_idx}'] = table_data
                    else:
                        detailed_data['daily_activity'][f'general_table_{table_idx}'] = table_data
            
            # IMPORTANT: Re-extract estimated completion AFTER table processing to ensure correct value
            # This prevents table extraction from overwriting the correct estimated completion
            estimated_completion_element = soup.find('div', id='estimatedCompletion')
            if estimated_completion_element:
                # Extract the date from the span inside the div
                span_element = estimated_completion_element.find('span')
                if span_element:
                    estimated_date = span_element.get_text(strip=True)
                    detailed_data['estimated_completion'] = estimated_date
                    print(f"    → Final estimated completion date collected")
                else:
                    # Fallback: get all text and extract date
                    full_text = estimated_completion_element.get_text(strip=True)
                    detailed_data['estimated_completion'] = full_text
                    print(f"    → Final estimated completion data collected")
            
            # Re-extract daily XP to prevent table overwriting
            daily_xp_element = soup.find('td', id='dailyGoalPoints')
            if daily_xp_element:
                daily_xp_text = daily_xp_element.get_text(strip=True)
                detailed_data['daily_xp'] = daily_xp_text
                print(f"    → Final daily XP data collected")
            
            # Re-extract weekly XP to prevent table overwriting  
            weekly_xp_element = soup.find('div', id='thisWeekTotalXP')
            if weekly_xp_element:
                weekly_xp_text = weekly_xp_element.get_text(strip=True)
                detailed_data['weekly_xp'] = weekly_xp_text
                print(f"    → Final weekly XP data collected")
            
            # Look for JavaScript data more comprehensively
            scripts = soup.find_all('script')
            for script_idx, script in enumerate(scripts):
                if script.string:
                    script_content = script.string
                    
                    # Look for various data patterns
                    data_patterns = [
                        r'var\s+(\w*(?:activity|progress|xp|task)\w*)\s*=\s*([^;]+)',
                        r'let\s+(\w*(?:activity|progress|xp|task)\w*)\s*=\s*([^;]+)',
                        r'const\s+(\w*(?:activity|progress|xp|task)\w*)\s*=\s*([^;]+)',
                        r'(\w*(?:activity|progress|xp|task)\w*)\s*:\s*([^,}]+)',
                    ]
                    
                    for pattern in data_patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE)
                        for var_name, var_value in matches:
                            try:
                                # Try to parse as JSON
                                if var_value.strip().startswith(('{', '[')):
                                    data = json.loads(var_value.strip().rstrip(','))
                                    if 'activity' in var_name.lower() or 'progress' in var_name.lower():
                                        detailed_data['daily_activity'][var_name] = data
                                    elif 'task' in var_name.lower():
                                        detailed_data['tasks'][var_name] = data
                                else:
                                    # Store as string
                                    if 'activity' in var_name.lower() or 'progress' in var_name.lower():
                                        detailed_data['daily_activity'][var_name] = var_value.strip().rstrip(',').strip('"\'')
                                    elif 'task' in var_name.lower():
                                        detailed_data['tasks'][var_name] = var_value.strip().rstrip(',').strip('"\'')
                            except:
                                continue
            
            # Look for specific Math Academy elements
            # Activity charts, progress indicators, etc.
            charts = soup.find_all(['canvas', 'svg', 'div'], class_=re.compile(r'chart|graph|progress', re.I))
            for chart in charts:
                chart_data = {}
                # Get any data attributes
                for attr, value in chart.attrs.items():
                    if 'data' in attr.lower():
                        chart_data[attr] = value
                
                if chart_data:
                    detailed_data['daily_activity']['chart_data'] = chart_data
            
            # Save raw page content for debugging (first 1000 chars) - only in local backup, not Supabase
            # detailed_data['page_sample'] = page_text[:1000] if page_text else ""
            
            print(f"    ✓ Extracted {len(detailed_data['daily_activity'])} activity items and {len(detailed_data['tasks'])} task items")
            
            return detailed_data
            
        except Exception as e:
            print(f"    ⚠️  Error getting detailed data for {student_name}: {e}")
            return {
                'student_url': f"https://www.mathacademy.com/students/{student_id}",
                'daily_activity': {},
                'tasks': {},
                'weekly_xp': None,
                'daily_xp': None,
                'estimated_completion': None,
                'error': str(e)
            }

    def parse_last_activity(self, activity_str: str) -> Optional[datetime]:
        """Parse last activity string to datetime"""
        if not activity_str or activity_str.strip() == "":
            return None
        
        try:
            # Handle various date formats
            activity_str = activity_str.strip()
            
            if activity_str.lower() in ['today', 'now']:
                return datetime.now(timezone.utc)
            
            # Try common formats
            formats = [
                "%a, %b %d",  # "Tue, Sep 9"
                "%b %d",      # "Sep 9"
                "%Y-%m-%d",   # "2025-09-09"
                "%m/%d/%Y",   # "09/09/2025"
                "%d/%m/%Y",   # "09/09/2025"
            ]
            
            for fmt in formats:
                try:
                    # For formats without year, assume current year
                    if "%Y" not in fmt:
                        current_year = datetime.now().year
                        parsed = datetime.strptime(f"{activity_str} {current_year}", f"{fmt} %Y")
                    else:
                        parsed = datetime.strptime(activity_str, fmt)
                    
                    return parsed.replace(tzinfo=timezone.utc)
                except:
                    continue
                    
            return None
        except:
            return None

    async def extract_and_save_student_data(self, page):
        """Extract student data and save to Supabase - ONLY for target students"""
        print("Extracting student data for Supabase...")
        
        if not self.target_names:
            print("No target names specified. Please add names to student_names_to_scrape.txt")
            return []
        
        await page.wait_for_load_state('networkidle')
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        students = []
        found_students = []
        
        # First, identify ONLY the target students from the main page
        student_links = soup.find_all('a', class_='studentNameLink')
        print(f"Found {len(student_links)} total student links")
        
        target_students = []  # Only students we want to scrape
        
        for link in student_links:
            try:
                student_name = link.get_text(strip=True)
                
                if self.should_scrape_student(student_name):
                    # Extract student ID
                    href = link.get('href', '')
                    student_id_match = re.search(r'/students/(\d+)/', href)
                    if student_id_match:
                        student_id = student_id_match.group(1)
                        target_students.append({
                            'name': student_name,
                            'student_id': student_id,
                            'link': link
                        })
                        print(f"✓ Found target student")
            except Exception as e:
                continue
        
        print(f"\n=== PROCESSING {len(target_students)} TARGET STUDENTS ===")
        
        # Now process ONLY the target students
        for student_info in target_students:
            student_name = student_info['name']
            student_id = student_info['student_id']
            
            try:
                print(f"\n✓ Processing target student")
                found_students.append(student_name)
                
                # Get basic data from main table first
                student_data = {
                    'student_id': student_id,
                    'name': student_name,
                    'course_name': None,
                    'percent_complete': None,
                    'last_activity': None,
                    'weekly_xp': None,
                    'estimated_completion': None,
                    'student_url': f"https://www.mathacademy.com/students/{student_id}",
                    'daily_activity': {},
                    'tasks': {},
                    'daily_xp': None,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Extract data from main table row
                link_id = student_info['link'].get('id', '')
                if link_id:
                    id_match = re.search(r'studentNameLink-(\d+)', link_id)
                    if id_match:
                        row_student_id = id_match.group(1)
                        menu_icon = soup.find('div', {'studentid': row_student_id})
                        if menu_icon:
                            row = menu_icon.find_parent('tr')
                            if row:
                                cells = row.find_all('td')
                                cell_texts = [cell.get_text(strip=True) for cell in cells]
                                
                                # Parse structured data from the main table
                                if len(cell_texts) >= 4:
                                    student_data['course_name'] = cell_texts[3] if len(cell_texts) > 3 else None
                                    student_data['percent_complete'] = cell_texts[4] if len(cell_texts) > 4 else None
                                    
                                    # Parse last activity
                                    if len(cell_texts) > 5:
                                        last_activity_str = cell_texts[5]
                                        parsed_date = self.parse_last_activity(last_activity_str)
                                        if parsed_date:
                                            student_data['last_activity'] = parsed_date.isoformat()
                
                # NOW click into this specific student's page for detailed data
                print(f"  → Clicking into student's detailed page...")
                detailed_data = await self.get_detailed_student_data(page, int(student_id), student_name)
                student_data.update(detailed_data)
                
                # Save to Supabase
                try:
                    print(f"  → Saving to Supabase...")
                    
                    # Prepare data for Supabase (remove None values and ensure JSON fields are properly formatted)
                    supabase_data = {}
                    for key, value in student_data.items():
                        if value is not None:
                            # Skip error field as it's not in the Supabase schema
                            if key == 'error':
                                continue
                            if key in ['daily_activity', 'tasks']:
                                # Ensure these are valid JSON
                                if isinstance(value, dict):
                                    supabase_data[key] = value
                                else:
                                    supabase_data[key] = {}
                            else:
                                supabase_data[key] = value
                    
                    # Insert or update in Supabase
                    # First try to find existing record
                    existing = self.supabase.table('math_academy_students').select('id').eq('student_id', student_id).execute()
                    
                    if existing.data:
                        # Update existing record
                        result = self.supabase.table('math_academy_students').update(supabase_data).eq('student_id', student_id).execute()
                    else:
                        # Insert new record
                        result = self.supabase.table('math_academy_students').insert(supabase_data).execute()
                    
                    print(f"  ✓ Saved to Supabase successfully")
                    
                except Exception as e:
                    print(f"  ✗ Error saving to Supabase: {e}")
                
                students.append(student_data)
                
            except Exception as e:
                print(f"  ✗ Error processing student: {e}")
                continue
        
        print(f"\n=== RESULTS ===")
        print(f"Total students on page: {len(student_links)}")
        print(f"Target students found: {len(target_students)}")
        print(f"Students successfully processed: {len(students)}")
        print(f"Students skipped (not in target list): {len(student_links) - len(target_students)}")
        
        if found_students:
            print(f"\nProcessed students: {len(found_students)} students")
        
        return students

    async def scrape_to_supabase(self):
        """Main scraping function that saves to Supabase"""
        if not self.target_names:
            print("No target names loaded. Please add student names to student_names_to_scrape.txt")
            return []
            
        async with async_playwright() as p:
            # Check for headless mode from environment variable or display availability
            import os
            headless_mode = (
                os.getenv('HEADLESS', '').lower() == 'true' or 
                not os.getenv('DISPLAY') and not os.getenv('WAYLAND_DISPLAY')
            )
            
            if headless_mode:
                print("🖥️  Running browser in headless mode (no display detected)")
            else:
                print("🖥️  Running browser with display")
                
            browser = await p.chromium.launch(headless=headless_mode)
            page = await browser.new_page()
            
            try:
                await self.login(page)
                
                if '/students' not in page.url:
                    raise Exception(f"Expected to be on students page, but current URL is: {page.url}")
                
                print(f"Successfully logged in. Current URL: {page.url}")
                
                students = await self.extract_and_save_student_data(page)
                
                # Also save a local backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_filename = f"supabase_backup_{timestamp}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(students, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"\n=== COMPLETION ===")
                print(f"✓ {len(students)} students saved to Supabase")
                print(f"✓ Backup saved to {json_filename}")
                
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
        scraper = MathAcademySupabaseScraper()
        students = await scraper.scrape_to_supabase()
        
        print(f"\n🎉 SCRAPING COMPLETE!")
        print(f"Students processed: {len(students)}")
        
        return students
        
    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())