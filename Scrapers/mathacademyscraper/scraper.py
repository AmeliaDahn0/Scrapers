"""
Math Academy Teacher Dashboard Scraper

SECURITY IMPORTANT: This script uses SUPABASE_SERVICE_KEY for backend operations.
This key bypasses Row Level Security (RLS) policies and should NEVER be exposed
to frontend applications or client-side code. Keep your .env file secure.
"""

import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from supabase import create_client
import re
from dateutil import parser as date_parser

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Security check: Ensure we're using the service key, not the anon key
service_key = os.getenv('SUPABASE_SERVICE_KEY')
if not service_key:
    logger.error("SUPABASE_SERVICE_KEY not found in environment variables")
    logger.error("Please set SUPABASE_SERVICE_KEY in your .env file")
    logger.error("This should be the service_role key from your Supabase project settings")
    exit(1)

# Validate that it's actually a service key (starts with 'eyJ' and is longer than anon key)
if len(service_key) < 100:
    logger.error("SUPABASE_SERVICE_KEY appears to be too short")
    logger.error("Make sure you're using the service_role key, not the anon key")
    exit(1)

# Initialize Supabase client with service key for backend operations
# IMPORTANT: Use SUPABASE_SERVICE_KEY (not anon key) for backend operations
# This bypasses RLS policies and should NEVER be exposed to the frontend
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    service_key
)

def validate_supabase_connection():
    """Validate that the Supabase connection is working with the service key."""
    try:
        # Try a simple query to test the connection
        response = supabase.table('students').select('count', count='exact').execute()
        logger.info("✅ Supabase connection validated successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        logger.error("Please check your SUPABASE_URL and SUPABASE_SERVICE_KEY")
        return False

def load_target_students():
    """Load the list of target students from Supabase students table."""
    try:
        # Query just the names from the students table
        response = supabase.table('students').select('name').execute()
        
        if response.data:
            # Create a set of student names
            students = set()
            math_academy_mapping = {}
            
            for student in response.data:
                name = student['name']
                students.add(name)
                math_academy_mapping[name] = name  # Identity mapping
            
            logger.info(f"Loaded {len(students)} target students from database")
            return students, math_academy_mapping
        else:
            logger.warning("No target students found in database students table")
            return set(), {}
            
    except Exception as e:
        logger.error(f"Error loading target students from database: {str(e)}")
        logger.info("Falling back to target_students.txt file if available")
        
        # Fallback to file-based loading if database fails
        try:
            with open('target_students.txt', 'r') as f:
                students = [
                    line.strip() 
                    for line in f.readlines() 
                    if line.strip() and not line.strip().startswith('#')
                ]
            if students:
                logger.info(f"Loaded {len(students)} target students from fallback file")
                students_set = set(students)
                mapping = {name: name for name in students}  # Identity mapping for fallback
                return students_set, mapping
            else:
                logger.warning("No target students found in fallback file")
                return set(), {}
        except FileNotFoundError:
            logger.error("Database query failed and no fallback target_students.txt file found")
            return set(), {}

async def login_to_math_academy(page):
    """Login to Math Academy using credentials from .env file."""
    try:
        await page.goto('https://www.mathacademy.com/login')
        logger.info("Navigated to login page")

        # Fill in login credentials
        await page.fill('#usernameOrEmail', os.getenv('MATH_ACADEMY_USERNAME'))
        await page.fill('#password', os.getenv('MATH_ACADEMY_PASSWORD'))
        
        # Click login button
        await page.click('#loginButton')
        
        # Wait for navigation after login
        await page.wait_for_load_state('networkidle')
        
        # Check if login was successful
        if 'login' not in page.url:
            logger.info("Login successful")
            return True
        else:
            logger.error("Login failed - still on login page")
            return False
            
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return False

async def get_task_details(page, task_element):
    task_info = {
        'id': None,
        'type': None,
        'name': None,
        'completion_time': None,
        'points': {
            'earned': None,
            'possible': None,
            'raw_text': None
        },
        'progress': None,
        'initial_placement': None
    }
    
    try:
        # Get task ID and attributes
        task_id = await task_element.get_attribute('id')
        if task_id:
            task_info['id'] = task_id.replace('task-', '')
        
        # Get task type
        task_type_elem = await task_element.query_selector('td.taskTypeColumn')
        if task_type_elem:
            task_info['type'] = (await task_type_elem.text_content()).strip()
            
        # Get task name
        task_name_elem = await task_element.query_selector('div.taskName')
        if task_name_elem:
            task_info['name'] = (await task_name_elem.text_content()).strip()
            
        # Get completion time
        completion_time_elem = await task_element.query_selector('td.taskCompletedColumn')
        if completion_time_elem:
            task_info['completion_time'] = (await completion_time_elem.text_content()).strip()
            
        # Get points information
        points_elem = await task_element.query_selector('span.taskPoints')
        if points_elem:
            points_text = await points_elem.text_content()
            task_info['points']['raw_text'] = points_text.strip()
            
            # Parse points (format: "6/4 XP")
            try:
                earned = points_text.split('/')[0].strip()
                possible = points_text.split('/')[1].split('XP')[0].strip()
                task_info['points']['earned'] = int(earned)
                task_info['points']['possible'] = int(possible)
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse points from text: {points_text}")
                
        # Get progress and initial placement from attributes
        progress = await task_element.get_attribute('progress')
        if progress:
            task_info['progress'] = progress
            
        initial_placement = await task_element.get_attribute('initialplacement')
        if initial_placement:
            task_info['initial_placement'] = initial_placement
            
    except Exception as e:
        logger.error(f"Error extracting task details: {str(e)}")
        
    return task_info

async def get_progress_details(page, student_id):
    """Get detailed progress information from a student's progress page."""
    try:
        # Navigate to student's progress page
        progress_url = f'https://www.mathacademy.com/students/{student_id}/progress'
        await page.goto(progress_url)
        
        # Wait for the page to be fully loaded
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_load_state('load')
        
        # Add a small delay to ensure dynamic content is loaded
        await asyncio.sleep(2)
        
        logger.info(f"Navigated to progress page: {progress_url}")
        
        # Initialize data structure for progress
        progress_data = {
            'units': []
        }
        
        # Get all unit divs
        units = await page.query_selector_all('div.unit')
        
        for unit in units:
            try:
                # Get unit header info
                header = await unit.query_selector('div.unitHeader')
                unit_number = await header.query_selector('div.unitNumber')
                unit_name = await header.query_selector('span.unitName')
                unit_topics = await header.query_selector('div.unitNumTopics')
                
                # Get progress bar data
                progress_bar = await unit.query_selector('table.unitProgressBar tr')
                progress_cells = await progress_bar.query_selector_all('td')
                progress_segments = []
                
                for cell in progress_cells:
                    style = await cell.get_attribute('style')
                    width = None
                    color = None
                    
                    # Extract width and color from style
                    if style:
                        for attr in style.split(';'):
                            if 'width:' in attr:
                                width = attr.split('width:')[1].strip().replace('%', '')
                            elif 'background-color:' in attr:
                                color = attr.split('background-color:')[1].strip()
                    
                    progress_segments.append({
                        'width': float(width) if width else 0,
                        'color': color
                    })
                
                # Get modules data
                modules = await unit.query_selector_all('div.module')
                modules_data = []
                
                for module in modules:
                    module_name = await module.query_selector('div')
                    topics = await module.query_selector_all('tr')
                    topics_data = []
                    
                    for topic in topics:
                        topic_circle = await topic.query_selector('div.topicCircle')
                        topic_number = await topic.query_selector('td.topicNumber')
                        topic_name = await topic.query_selector('td.topicName a')
                        
                        circle_style = await topic_circle.get_attribute('style')
                        status_color = None
                        if circle_style:
                            for attr in circle_style.split(';'):
                                if 'background:' in attr:
                                    status_color = attr.split('background:')[1].strip()
                        
                        topics_data.append({
                            'number': await topic_number.text_content() if topic_number else None,
                            'name': await topic_name.text_content() if topic_name else None,
                            'status_color': status_color,
                            'url': await topic_name.get_attribute('href') if topic_name else None
                        })
                    
                    modules_data.append({
                        'name': await module_name.text_content() if module_name else None,
                        'topics': topics_data
                    })
                
                # Add unit data to progress_data
                progress_data['units'].append({
                    'number': await unit_number.text_content() if unit_number else None,
                    'name': await unit_name.text_content() if unit_name else None,
                    'total_topics': await unit_topics.text_content() if unit_topics else None,
                    'progress_segments': progress_segments,
                    'modules': modules_data
                })
                
            except Exception as e:
                logger.error(f"Error processing unit: {str(e)}")
                continue
        
        return progress_data
        
    except Exception as e:
        logger.error(f"Error getting progress details: {str(e)}")
        return None

async def get_activity_details(page, student_id):
    """Get detailed activity information from a student's activity page."""
    try:
        # Navigate to student's activity page
        student_url = f'https://www.mathacademy.com/students/{student_id}/activity'
        await page.goto(student_url)
        
        # Wait for the page to be fully loaded
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_load_state('load')
        
        # Add a small delay to ensure dynamic content is loaded
        await asyncio.sleep(2)
        
        logger.info(f"Navigated to student page: {student_url}")
        
        # Get estimated completion date
        estimated_completion = None
        try:
            # Try multiple approaches to find the completion date
            # First try: Look for the specific text in any element
            completion_elem = await page.query_selector('div >> text="Estimated completion is"')
            if not completion_elem:
                # Second try: Look for any element containing the text
                completion_elem = await page.query_selector('div:has-text("Estimated completion")')
            if not completion_elem:
                # Third try: Look for text nodes containing the phrase
                completion_elem = await page.evaluate('''() => {
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    let node;
                    while (node = walker.nextNode()) {
                        if (node.textContent.includes("Estimated completion is")) {
                            return node.textContent;
                        }
                    }
                    return null;
                }''')
            
            if completion_elem:
                if isinstance(completion_elem, str):
                    completion_text = completion_elem
                else:
                    completion_text = await completion_elem.text_content()
                
                if "Estimated completion is" in completion_text:
                    estimated_completion = completion_text.split("Estimated completion is")[1].strip()
                    logger.info(f"Found estimated completion date: {estimated_completion}")
                
        except Exception as e:
            logger.warning(f"Could not get estimated completion date: {str(e)}")
        
        # Initialize data structures
        daily_tasks = {}
        current_date = None
        
        # Get all task rows including date headers
        rows = await page.query_selector_all('tr')
        
        for row in rows:
            try:
                # Check if this is a date header
                date_header = await row.query_selector('td.dateHeader')
                if date_header:
                    # Extract date and XP
                    header_text = await date_header.text_content()
                    date_parts = header_text.split('XP')[0].strip()
                    xp_text = await date_header.query_selector('span.dateTotalXP')
                    daily_xp = await xp_text.text_content() if xp_text else "0 XP"
                    
                    current_date = {
                        'date': date_parts,
                        'daily_xp': daily_xp.strip(),
                        'tasks': []
                    }
                    daily_tasks[date_parts] = current_date
                    continue
                
                # Check if this is a task row
                task_id = await row.get_attribute('id')
                if task_id and task_id.startswith('task-'):
                    if current_date:
                        task_info = await get_task_details(page, row)
                        # Only include if the task is completed (has a completion time and earned XP)
                        if task_info.get('completion_time') and task_info['points'].get('earned') is not None:
                            current_date['tasks'].append(task_info)
                
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue
        
        # Ensure today is present in daily_tasks, even if empty
        today_str = datetime.now().strftime('%a, %b %d')
        if today_str not in daily_tasks:
            daily_tasks[today_str] = {
                'date': today_str,
                'daily_xp': '0 XP',
                'tasks': []
            }
        
        return {
            'daily_activity': daily_tasks,
            'estimated_completion': estimated_completion
        }
        
    except Exception as e:
        logger.error(f"Error getting activity details: {str(e)}")
        return None

async def get_student_details(page, student_id):
    """Get detailed information from a student's individual page."""
    try:
        # Get activity data
        activity_data = await get_activity_details(page, student_id)
        
        # Get progress data
        progress_data = await get_progress_details(page, student_id)
        
        # Combine the data
        return {
            'student_url': f'https://www.mathacademy.com/students/{student_id}',
            'daily_activity': activity_data['daily_activity'] if activity_data else {},
            'progress': progress_data if progress_data else {},
            'estimated_completion': activity_data['estimated_completion'] if activity_data else None
        }
        
    except Exception as e:
        logger.error(f"Error getting student details: {str(e)}")
        return None

def parse_last_activity(text):
    """Parse 'Last activity on Mon, Feb 24th', 'Last activity on Today', or 'Last activity on Yesterday' to ISO timestamp or None."""
    if not text or not text.strip():
        return None
    # Handle 'today'
    if 'today' in text.lower():
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    # Handle 'yesterday'
    if 'yesterday' in text.lower():
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    match = re.search(r"Last activity on (\w+), (\w+) (\d+)(?:st|nd|rd|th)?", text)
    if match:
        try:
            month = match.group(2)
            day = match.group(3)
            year = datetime.now().year
            date_str = f"{month} {day} {year}"
            dt = date_parser.parse(date_str)
            return dt.isoformat()
        except Exception:
            return None
    return None

async def scrape_teacher_dashboard(browser):
    """Scrape information from the teacher dashboard."""
    try:
        # Validate Supabase connection first
        if not validate_supabase_connection():
            logger.error("Cannot proceed without valid Supabase connection")
            return
            
        # Load target students
        target_students, math_academy_mapping = load_target_students()
        if not target_students:
            logger.error("No target students found. Please add students to your Supabase students table")
            return
            
        # Create initial context and page
        context = await browser.new_context()
        page = await context.new_page()
        
        # Login first
        login_successful = await login_to_math_academy(page)
        if not login_successful:
            logger.error("Failed to login")
            await context.close()
            return
            
        # Navigate to students page
        await page.goto('https://www.mathacademy.com/students')
        await page.wait_for_load_state('networkidle')
        
        logger.info("Starting to scrape teacher dashboard")
        
        # Initialize student data list
        student_data = []
        
        # Wait for student elements to be visible and get all students
        await page.wait_for_selector('td[id^="studentName-"]', timeout=60000)
        student_name_elements = await page.query_selector_all('td[id^="studentName-"]')
        logger.info(f"Found {len(student_name_elements)} student name elements")
        
        # Get list of all students for logging
        all_names = []
        target_student_elements = []
        for student_name_elem in student_name_elements:
            try:
                # Get the student name link from within the TD
                name_link = await student_name_elem.query_selector('a.studentNameLink')
                if name_link:
                    # Get the name (format: "Last, First")
                    full_name = await name_link.text_content()
                    full_name = full_name.strip()
                    all_names.append(full_name)
                    
                    # Extract student ID from the TD's id attribute
                    td_id = await student_name_elem.get_attribute('id')
                    if td_id:
                        student_id = td_id.replace('studentName-', '')
                        # Find the parent row element for this student
                        parent_row = await student_name_elem.evaluate('(element) => element.closest("tr")')
                        if parent_row:
                            target_student_elements.append((full_name, parent_row, student_id))
            except Exception as e:
                logger.error(f"Error getting student name: {str(e)}")
                continue
                
        logger.info(f"Found {len(all_names)} total students")
        logger.info(f"Found {len(target_student_elements)} target students")
        
        # Improved matching: Create a more sophisticated name matching system
        target_student_elements_corrected = []
        processed_students = set()  # Track processed student IDs to prevent duplicates
        
        # Create a mapping for better name matching
        def normalize_name(name):
            """Normalize name for better matching"""
            return name.lower().strip().replace('.', '').replace(',', '')
        
        def extract_math_academy_name(full_name):
            """Extract the actual name from Math Academy format"""
            if ', ' in full_name:
                # Math Academy format is "Last, First"
                parts = full_name.split(', ')
                if len(parts) == 2:
                    # Format: "Last, First" -> "First Last"
                    return f"{parts[1].strip()} {parts[0].strip()}"
            return full_name.strip()
        
        # Create reverse mapping from database names for better matching
        db_name_variants = {}
        for db_name in target_students:
            normalized = normalize_name(db_name)
            db_name_variants[normalized] = db_name
            
            # Add first name only variant
            first_name = db_name.split()[0]
            first_normalized = normalize_name(first_name)
            if first_normalized not in db_name_variants:
                db_name_variants[first_normalized] = db_name
        
        for full_name, student_row, student_id in target_student_elements:
            try:
                # Skip if we've already processed this student ID
                if student_id in processed_students:
                    continue
                
                # Extract the actual name from Math Academy format
                actual_name = extract_math_academy_name(full_name)
                normalized_actual = normalize_name(actual_name)
                
                # Try to find a match in our database
                matched_db_name = None
                
                # 1. Try exact match first
                if normalized_actual in db_name_variants:
                    matched_db_name = db_name_variants[normalized_actual]
                else:
                    # 2. Try matching individual words (for partial matches)
                    actual_words = actual_name.lower().split()
                    for db_name in target_students:
                        db_words = db_name.lower().split()
                        
                        # Check if all words in actual_name appear in db_name
                        if len(actual_words) == len(db_words):
                            if all(normalize_name(aw) == normalize_name(dw) for aw, dw in zip(actual_words, db_words)):
                                matched_db_name = db_name
                                break
                
                if matched_db_name:
                    # Extract dashboard data immediately while elements are still valid
                    dashboard_data = {}
                    try:
                        course_name_elem = await student_row.query_selector('td.courseName')
                        course_progress_elem = await student_row.query_selector('td.studentProgress a.tableLink')
                        last_activity_elem = await student_row.query_selector('td.fieldData:nth-child(4)')
                        todays_xp_elem = await student_row.query_selector('td.studentDayXP')
                        this_weeks_xp_elem = await student_row.query_selector('td.studentWeekXP')
                        
                        dashboard_data = {
                            'course_name': await course_name_elem.text_content() if course_name_elem else '',
                            'course_progress': await course_progress_elem.text_content() if course_progress_elem else '',
                            'last_activity': await last_activity_elem.text_content() if last_activity_elem else '',
                            'todays_xp': await todays_xp_elem.text_content() if todays_xp_elem else '',
                            'this_weeks_xp': await this_weeks_xp_elem.text_content() if this_weeks_xp_elem else ''
                        }
                    except Exception as e:
                        logger.warning(f"Could not extract dashboard data for {matched_db_name}: {str(e)}")
                        dashboard_data = {
                            'course_name': '', 'course_progress': '', 'last_activity': '',
                            'todays_xp': '', 'this_weeks_xp': ''
                        }
                    
                    target_student_elements_corrected.append((matched_db_name, dashboard_data, student_id))
                    processed_students.add(student_id)
                    logger.info(f"✅ Found target student: '{matched_db_name}' (Math Academy: '{full_name}' -> '{actual_name}', ID: {student_id})")
                    
            except Exception as e:
                logger.error(f"Error processing student element: {str(e)}")
                continue
        
        logger.info(f"Database target names: {list(target_students)[:10]}...")
        logger.info(f"Found {len(target_student_elements_corrected)} exact matches")
        
        # Report on matching status
        matched_db_names = {name for name, _, _ in target_student_elements_corrected}
        unmatched_db_names = target_students - matched_db_names
        
        if matched_db_names:
            logger.info(f"✅ Successfully matched students: {sorted(matched_db_names)}")
        
        if unmatched_db_names:
            logger.warning(f"❌ Unmatched database students: {sorted(unmatched_db_names)}")
            logger.info("🔍 Searching for similar names in Math Academy for unmatched students...")
            
            # Try to find similar names for debugging
            for unmatched in unmatched_db_names:
                logger.info(f"Looking for matches for: '{unmatched}'")
                unmatched_words = unmatched.lower().split()
                
                # Look through first 50 Math Academy names for potential matches
                potential_matches = []
                for i, name in enumerate(all_names[:50]):
                    ma_name = extract_math_academy_name(name)
                    ma_words = ma_name.lower().split()
                    
                    # Check for partial matches
                    if any(word in ' '.join(ma_words) for word in unmatched_words):
                        potential_matches.append(f"'{name}' -> '{ma_name}'")
                
                if potential_matches:
                    logger.info(f"   Potential matches: {potential_matches[:3]}")
                else:
                    logger.info(f"   No similar names found in first 50 Math Academy students")
        
        if len(target_student_elements_corrected) == 0:
            logger.error("❌ No students matched!")
            logger.error("")
            logger.error("The student names in your Supabase 'students' table do not exactly match any names in Math Academy.")
            logger.error("")
            logger.error("SOLUTION: Update the 'name' column in your Supabase students table to exactly match")
            logger.error("the corresponding names as they appear in Math Academy.")
            logger.error("")
            logger.error("For example, if 'Keyen Gupta' in your database is actually 'Duke' in Math Academy,")
            logger.error("you need to update that row: UPDATE students SET name = 'Duke' WHERE name = 'Keyen Gupta';")
            logger.error("")
            logger.error("This scraper will ONLY process students whose names exactly match between both systems.")
        
        # Use the corrected list
        target_student_elements = target_student_elements_corrected
        
        # Keep the page and context open for processing students
        # Don't close them yet - we'll use them for student processing
        
        # Remove duplicates by database name (keep first occurrence)
        seen_db_names = set()
        unique_target_students = []
        for db_name, dashboard_data, student_id in target_student_elements_corrected:
            if db_name not in seen_db_names:
                unique_target_students.append((db_name, dashboard_data, student_id))
                seen_db_names.add(db_name)
            else:
                logger.info(f"⚠️ Skipping duplicate database student: {db_name}")
        
        logger.info(f"Processing {len(unique_target_students)} unique students (removed {len(target_student_elements_corrected) - len(unique_target_students)} duplicates)")
        
        # Process each target student using the same session
        for student_name, dashboard_data, student_id in unique_target_students:
            try:
                logger.info(f"Processing student: {student_name}")
                
                # Get detailed information from student's page using the existing student_id
                logger.info(f"Getting detailed information for student: {student_name}")
                detailed_info = await get_student_details(page, student_id)
                
                # Use pre-extracted dashboard data
                course_name = dashboard_data.get('course_name', '')
                course_progress = dashboard_data.get('course_progress', '')
                last_activity = dashboard_data.get('last_activity', '')
                todays_xp = dashboard_data.get('todays_xp', '')
                this_weeks_xp = dashboard_data.get('this_weeks_xp', '')
                
                # Prepare data for Supabase
                parsed_last_activity = parse_last_activity(last_activity.strip())

                # Fallback: if parsed_last_activity is None, use the most recent date from daily_activity
                if not parsed_last_activity and detailed_info and detailed_info.get('daily_activity'):
                    daily_activity = detailed_info['daily_activity']
                    if daily_activity:
                        # Try to get the most recent date key
                        try:
                            # Remove extra whitespace and sort by parsed date
                            def parse_key_to_date(key):
                                # Remove newlines and extra spaces
                                date_str = key.split('\n')[0].strip()
                                # Add current year for parsing
                                return date_parser.parse(date_str + ' ' + str(datetime.now().year))
                            most_recent = max(daily_activity.keys(), key=parse_key_to_date)
                            dt = parse_key_to_date(most_recent)
                            parsed_last_activity = dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                        except Exception:
                            parsed_last_activity = None

                supabase_data = {
                    'student_id': student_id,
                    'name': student_name,
                    'course_name': course_name.strip(),
                    'percent_complete': course_progress.strip(),
                    'last_activity': parsed_last_activity,
                    'daily_xp': todays_xp.strip(),
                    'weekly_xp': this_weeks_xp.strip(),
                    'expected_weekly_xp': detailed_info.get('expected_weekly_xp') if detailed_info else None,
                    'estimated_completion': detailed_info.get('estimated_completion') if detailed_info else None,
                    'student_url': f'https://www.mathacademy.com/students/{student_id}/activity',
                    'daily_activity': detailed_info.get('daily_activity', {}) if detailed_info else {},
                    'tasks': detailed_info.get('tasks', []) if detailed_info else []
                }

                # Only save if student_id and name are present, and student_id is numeric
                if supabase_data['student_id'] and supabase_data['name'] and supabase_data['student_id'].isdigit():
                    success = await save_to_supabase(supabase_data)
                    if success:
                        logger.info(f"Successfully saved data for student {student_name} to Supabase")
                    else:
                        logger.error(f"Failed to save data for student {student_name} to Supabase")
                    student_data.append(supabase_data)
                else:
                    logger.warning(f"Skipping student with missing or non-numeric student_id or name: {supabase_data}")
                
                # Small delay between students to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing student {student_name}: {str(e)}")
                continue
        
        # Close the page and context after processing all students
        await page.close()
        await context.close()
        
        if not student_data:
            logger.warning("No data collected. Check if the student names in target_students.txt match exactly with Math Academy.")
            return
            
        logger.info(f"Successfully processed {len(student_data)} students and saved to Supabase database")
        
    except Exception as e:
        logger.error(f"Error while scraping dashboard: {str(e)}")

async def save_to_supabase(student_data):
    """Save student data to Supabase as a new row every time."""
    try:
        # Prepare the data according to the schema
        supabase_data = {
            'student_id': str(student_data.get('student_id')),
            'name': str(student_data.get('name')),
            'course_name': str(student_data.get('course_name')) if student_data.get('course_name') else None,
            'percent_complete': str(student_data.get('percent_complete')) if student_data.get('percent_complete') else None,
            'last_activity': str(student_data.get('last_activity')) if student_data.get('last_activity') else None,
            'daily_xp': str(student_data.get('daily_xp')) if student_data.get('daily_xp') else None,
            'weekly_xp': str(student_data.get('weekly_xp')) if student_data.get('weekly_xp') else None,
            'expected_weekly_xp': str(student_data.get('expected_weekly_xp')) if student_data.get('expected_weekly_xp') else None,
            'estimated_completion': str(student_data.get('estimated_completion')) if student_data.get('estimated_completion') else None,
            'student_url': str(student_data.get('student_url')) if student_data.get('student_url') else None,
            'daily_activity': student_data.get('daily_activity', {}),
            'tasks': student_data.get('tasks', []),
            'created_at': datetime.now().isoformat()
        }

        # Remove None values to avoid null constraints
        supabase_data = {k: v for k, v in supabase_data.items() if v is not None}

        # Only insert if student_id and name are present
        if supabase_data.get('student_id') and supabase_data.get('name'):
            result = supabase.table('math_academy_students').insert(supabase_data).execute()
            if hasattr(result, 'data'):
                logger.info(f"Successfully inserted data for student {supabase_data.get('student_id')} to Supabase")
                return True
            else:
                logger.error(f"Failed to insert data for student {supabase_data.get('student_id')} to Supabase. Response: {result}")
                return False
        else:
            logger.warning(f"Skipping student with missing student_id or name: {supabase_data}")
            return False

    except Exception as e:
        logger.error(f"Error inserting to Supabase: {str(e)}")
        return False

async def main():
    """Main function to run the scraper."""
    async with async_playwright() as p:
        # Use headless mode in CI environments
        is_ci = os.getenv('CI', 'false').lower() == 'true'
        browser = await p.chromium.launch(headless=is_ci)
        try:
            await scrape_teacher_dashboard(browser)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 