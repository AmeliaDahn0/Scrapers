#!/usr/bin/env python3
"""
Step 3: Extract student data from each dashboard page
"""

import time
import json
import os
from datetime import datetime
from acely_auth_base import AcelyAuthenticator, AuthConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger
from dotenv import load_dotenv


class Step3ExtractData(AcelyAuthenticator):
    """Step 3: Extract data from student dashboard pages"""
    
    def __init__(self, config: AuthConfig = None):
        super().__init__(config)
        self.target_emails = []
        self.student_data = {}
        self.not_found_students = []
    
    def load_target_emails(self):
        """Load target student emails from Supabase students table"""
        try:
            # Connect to Supabase
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment")
            
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            
            # Fetch all emails from the students table
            logger.info("🔗 Connecting to Supabase to fetch student emails...")
            response = supabase.table("students").select("email").execute()
            
            if not response.data:
                logger.warning("⚠️ No students found in the students table")
                self.target_emails = []
                return True
            
            # Extract emails and store in lowercase for comparison
            emails = []
            for row in response.data:
                email = row.get("email")
                if email and email.strip():
                    emails.append(email.strip().lower())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_emails = []
            for email in emails:
                if email not in seen:
                    seen.add(email)
                    unique_emails.append(email)
            
            self.target_emails = unique_emails
            logger.info(f"📧 Loaded {len(self.target_emails)} target student emails from Supabase:")
            for email in self.target_emails:
                logger.info(f"  - {email}")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ Failed to load student emails from Supabase: {e}")
            return False
    
    def extract_student_data(self, student_email, student_name):
        """Extract data from the current student dashboard page"""
        try:
            logger.info(f"📊 Extracting data for {student_name} ({student_email})")
            
            # Initialize student data structure
            student_data = {
                "email": student_email,
                "name": student_name,
                "dashboard_url": self.driver.current_url,
                "scrape_timestamp": datetime.now().isoformat(),
                "data_extracted": {}
            }
            
            # Extract join date
            join_date = self.extract_join_date()
            if join_date:
                student_data["data_extracted"]["join_date"] = join_date
                logger.info(f"  ✅ Join date: {join_date}")
            else:
                logger.warning(f"  ⚠️ Join date not found")
            
            # Extract most recent score
            most_recent_score = self.extract_most_recent_score()
            if most_recent_score is not None:
                student_data["data_extracted"]["most_recent_score"] = most_recent_score
                logger.info(f"  ✅ Most recent score: {most_recent_score}")
            else:
                logger.warning(f"  ⚠️ Most recent score not found")
            
            # Extract this week accuracy
            this_week_accuracy = self.extract_this_week_accuracy()
            if this_week_accuracy is not None:
                student_data["data_extracted"]["this_week_accuracy"] = this_week_accuracy
                logger.info(f"  ✅ This week accuracy: {this_week_accuracy}")
            else:
                logger.warning(f"  ⚠️ This week accuracy not found")
            
            # Extract last week accuracy
            last_week_accuracy = self.extract_last_week_accuracy()
            if last_week_accuracy is not None:
                student_data["data_extracted"]["last_week_accuracy"] = last_week_accuracy
                logger.info(f"  ✅ Last week accuracy: {last_week_accuracy}")
            else:
                logger.warning(f"  ⚠️ Last week accuracy not found")
            
            # Extract questions answered this week
            questions_this_week = self.extract_questions_answered_this_week()
            if questions_this_week is not None:
                student_data["data_extracted"]["questions_answered_this_week"] = questions_this_week
                logger.info(f"  ✅ Questions answered this week: {questions_this_week}")
            else:
                logger.warning(f"  ⚠️ Questions answered this week not found")
            
            # Extract questions answered last week
            questions_last_week = self.extract_questions_answered_last_week()
            if questions_last_week is not None:
                student_data["data_extracted"]["questions_answered_last_week"] = questions_last_week
                logger.info(f"  ✅ Questions answered last week: {questions_last_week}")
            else:
                logger.warning(f"  ⚠️ Questions answered last week not found")
            
            # Extract daily activity calendar
            daily_activity_calendar = self.extract_daily_activity_calendar()
            if daily_activity_calendar is not None:
                student_data["data_extracted"]["daily_activity_calendar"] = daily_activity_calendar
                logger.info(f"  ✅ Daily activity calendar extracted: {len(daily_activity_calendar)} weeks")
            else:
                logger.warning(f"  ⚠️ Daily activity calendar not found")
            
            # Extract strongest area
            strongest_area = self.extract_strongest_area()
            if strongest_area is not None:
                student_data["data_extracted"]["strongest_area"] = strongest_area
                logger.info(f"  ✅ Strongest area: {strongest_area['area']} ({strongest_area['accuracy']})")
            else:
                logger.warning(f"  ⚠️ Strongest area not found")
            
            # Extract weakest area
            weakest_area = self.extract_weakest_area()
            if weakest_area is not None:
                student_data["data_extracted"]["weakest_area"] = weakest_area
                logger.info(f"  ✅ Weakest area: {weakest_area['area']} ({weakest_area['accuracy']})")
            else:
                logger.warning(f"  ⚠️ Weakest area not found")
            
            # Extract mock exam results
            mock_exam_results = self.extract_mock_exam_results()
            if mock_exam_results is not None:
                student_data["data_extracted"]["mock_exam_results"] = mock_exam_results
                logger.info(f"  ✅ Mock exam results extracted: {len(mock_exam_results)} exams")
            else:
                logger.warning(f"  ⚠️ Mock exam results not found")
            
            # TODO: Add more data extraction methods here
            # etc.
            
            return student_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract data for {student_name}: {e}")
            return {
                "email": student_email,
                "name": student_name,
                "dashboard_url": self.driver.current_url,
                "scrape_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def extract_join_date(self):
        """Extract the join date from the student dashboard"""
        try:
            # Look for the join date using the exact element you provided
            join_date_selectors = [
                # Using the exact class and text pattern
                "//div[contains(@class, 'text-neutral-600') and contains(@class, 'text-sm') and contains(@class, 'pt-2') and contains(text(), 'Joined:')]",
                # Broader search for join date
                "//div[contains(text(), 'Joined:')]",
                "//*[contains(text(), 'Joined:')]",
                # Alternative patterns
                "//div[contains(@class, 'text-neutral-600') and contains(text(), 'Joined')]",
                "//span[contains(text(), 'Joined:')]"
            ]
            
            for selector in join_date_selectors:
                try:
                    logger.debug(f"Trying join date selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            logger.debug(f"Found join date element text: '{text}'")
                            
                            # Extract the date from "Joined: September 22, 2024" format
                            if "Joined:" in text:
                                date_part = text.replace("Joined:", "").strip()
                                logger.info(f"✅ Extracted join date: {date_part}")
                                return date_part
                    
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ Join date not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract join date: {e}")
            return None
    
    def extract_most_recent_score(self):
        """Extract the most recent score from the student dashboard"""
        try:
            # Look for the most recent score using the specific element structure
            score_selectors = [
                # Using the exact class structure provided
                "//span[contains(@class, 'text-lg') and contains(@class, 'font-semibold') and contains(@class, 'underline') and contains(@class, 'decoration-yellow-800')]",
                # Alternative patterns for the score
                "//span[contains(@class, 'text-lg') and contains(@class, 'font-semibold') and contains(@class, 'underline')]",
                # Look for "Most Recent Score:" section and find the score span
                "//*[contains(text(), 'Most Recent Score:')]/following-sibling::*//span[contains(@class, 'text-lg')]",
                "//*[contains(text(), 'Most Recent Score:')]/parent::*//*[contains(@class, 'text-lg') and contains(@class, 'font-semibold')]",
                # Broader search for the score pattern
                "//span[contains(@class, 'decoration-yellow-800')]"
            ]
            
            for selector in score_selectors:
                try:
                    logger.debug(f"Trying score selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            logger.debug(f"Found score element text: '{text}'")
                            
                            # Check if the text is a valid score (numeric)
                            if text.isdigit():
                                score = int(text)
                                logger.info(f"✅ Extracted most recent score: {score}")
                                return score
                            elif text.replace('.', '', 1).isdigit():  # Handle decimal scores
                                score = float(text)
                                logger.info(f"✅ Extracted most recent score: {score}")
                                return score
                    
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ Most recent score not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract most recent score: {e}")
            return None
    
    def _parse_accuracy_text(self, text):
        """Parse accuracy text to extract this week and last week values"""
        import re
        
        # Patterns we might see:
        # "N/A vs. 67% last week" -> this_week: "N/A", last_week: "67"
        # "85% vs. 67% last week" -> this_week: "85", last_week: "67"
        # "N/A" -> this_week: "N/A", last_week: None
        # "85%" -> this_week: "85", last_week: None
        
        this_week = None
        last_week = None
        
        # Look for "vs." pattern which indicates comparison
        if "vs." in text or "vs " in text:
            # Split on "vs." to get this week vs last week
            parts = re.split(r'\s*vs\.?\s*', text, 1)
            if len(parts) == 2:
                this_week_part = parts[0].strip()
                last_week_part = parts[1].strip()
                
                # Parse this week part
                if this_week_part.upper() in ['N/A', 'NA']:
                    this_week = "N/A"
                else:
                    # Extract percentage from this week
                    match = re.search(r'(\d+(?:\.\d+)?)%?', this_week_part)
                    if match:
                        this_week = match.group(1)
                
                # Parse last week part - look for percentage
                last_week_match = re.search(r'(\d+(?:\.\d+)?)%', last_week_part)
                if last_week_match:
                    last_week = last_week_match.group(1)
        else:
            # No "vs." - just a single value
            if text.upper().strip() in ['N/A', 'NA']:
                this_week = "N/A"
            else:
                # Extract percentage
                match = re.search(r'(\d+(?:\.\d+)?)%?', text)
                if match:
                    this_week = match.group(1)
        
        return this_week, last_week
    
    def extract_this_week_accuracy(self):
        """Extract the This Week accuracy from the student dashboard"""
        try:
            # Look for the This Week accuracy section using the specific element structure
            accuracy_selectors = [
                # Using the exact class structure provided for the accuracy value
                "//div[contains(@class, 'text-3xl') and contains(@class, 'font-medium') and contains(@class, 'text-navy-800')]",
                # Look specifically in the Accuracy section under "This Week"
                "//*[contains(text(), 'Accuracy')]/following-sibling::*//div[contains(@class, 'text-3xl')]",
                "//*[contains(text(), 'Accuracy')]/parent::*//*[contains(@class, 'text-3xl') and contains(@class, 'font-medium')]",
                # Look for the accuracy section more broadly
                "//*[contains(text(), 'This Week')]/following-sibling::*//*[contains(text(), 'Accuracy')]/following-sibling::*//div[contains(@class, 'text-3xl')]",
                # Alternative pattern for accuracy values
                "//div[contains(@class, 'text-3xl') and contains(@class, 'text-navy-800')]"
            ]
            
            for selector in accuracy_selectors:
                try:
                    logger.debug(f"Trying accuracy selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            logger.debug(f"Found accuracy element text: '{text}'")
                            
                            # Check if this element is in the accuracy context
                            # Look for nearby "Accuracy" text to confirm this is the right element
                            try:
                                parent = element.find_element(By.XPATH, "./ancestor::*[contains(., 'Accuracy')]")
                                if parent:
                                    this_week, last_week = self._parse_accuracy_text(text)
                                    if this_week is not None:
                                        # Store last week for later retrieval
                                        self._last_week_accuracy = last_week
                                        logger.info(f"✅ Extracted this week accuracy: {this_week}")
                                        return this_week
                            except:
                                # If we can't find "Accuracy" in parent, check if the text looks like accuracy data
                                if text in ['N/A', 'n/a'] or '%' in text or text.replace('.', '', 1).replace('%', '').isdigit():
                                    # Additional check: make sure we're in the "This Week" section
                                    try:
                                        this_week_section = element.find_element(By.XPATH, "./ancestor::*[contains(., 'This Week')]")
                                        if this_week_section:
                                            this_week, last_week = self._parse_accuracy_text(text)
                                            if this_week is not None:
                                                # Store last week for later retrieval
                                                self._last_week_accuracy = last_week
                                                logger.info(f"✅ Extracted this week accuracy: {this_week}")
                                                return this_week
                                    except:
                                        continue
                    
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ This week accuracy not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract this week accuracy: {e}")
            return None
    
    def extract_last_week_accuracy(self):
        """Extract the Last Week accuracy (parsed from the same element as this week)"""
        try:
            # Check if we already parsed this from the this_week_accuracy extraction
            if hasattr(self, '_last_week_accuracy') and self._last_week_accuracy is not None:
                logger.info(f"✅ Extracted last week accuracy: {self._last_week_accuracy}")
                return self._last_week_accuracy
            
            logger.warning("⚠️ Last week accuracy not found - no comparison data available")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract last week accuracy: {e}")
            return None
    
    def _parse_questions_text(self, text):
        """Parse questions answered text to extract this week and last week values"""
        import re
        
        # Patterns we might see:
        # "0 vs. 6 last week" -> this_week: 0, last_week: 6
        # "15 vs. 12 last week" -> this_week: 15, last_week: 12
        # "5" -> this_week: 5, last_week: None
        
        this_week = None
        last_week = None
        
        # Look for "vs." pattern which indicates comparison
        if "vs." in text or "vs " in text:
            # Split on "vs." to get this week vs last week
            parts = re.split(r'\s*vs\.?\s*', text)
            if len(parts) >= 2:
                this_week_part = parts[0].strip()
                last_week_part = parts[1].strip()
                
                # Parse this week part - extract number
                this_week_match = re.search(r'(\d+)', this_week_part)
                if this_week_match:
                    this_week = int(this_week_match.group(1))
                
                # Parse last week part - extract number
                last_week_match = re.search(r'(\d+)', last_week_part)
                if last_week_match:
                    last_week = int(last_week_match.group(1))
        else:
            # No "vs." - just a single value
            match = re.search(r'(\d+)', text)
            if match:
                this_week = int(match.group(1))
        
        return this_week, last_week
    
    def extract_questions_answered_this_week(self):
        """Extract Questions Answered This Week from the student dashboard"""
        try:
            # Look for the Questions Answered section
            questions_selectors = [
                # Look for the Questions Answered section in the This Week area
                "//*[contains(text(), 'Questions Answered')]/following-sibling::*//div[contains(@class, 'text-3xl')]",
                "//*[contains(text(), 'Questions Answered')]/parent::*//*[contains(@class, 'text-3xl') and contains(@class, 'font-medium')]",
                # Look within the rounded border container that contains Questions Answered
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and .//text()[contains(., 'Questions Answered')]]//div[contains(@class, 'text-3xl')]",
                # Alternative pattern
                "//div[contains(@class, 'text-3xl') and contains(@class, 'font-medium') and contains(@class, 'text-navy-800') and contains(text(), 'vs.')]"
            ]
            
            for selector in questions_selectors:
                try:
                    logger.debug(f"Trying questions selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            logger.debug(f"Found questions element text: '{text}'")
                            
                            # Check if this element contains questions data (should have "vs." pattern or be a number)
                            if "vs." in text or text.isdigit():
                                # Check if this is in the Questions Answered context
                                try:
                                    parent = element.find_element(By.XPATH, "./ancestor::*[contains(., 'Questions Answered')]")
                                    if parent:
                                        this_week, last_week = self._parse_questions_text(text)
                                        if this_week is not None:
                                            # Store last week for later retrieval
                                            self._last_week_questions = last_week
                                            logger.info(f"✅ Extracted questions answered this week: {this_week}")
                                            return this_week
                                except:
                                    continue
                    
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ Questions answered this week not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract questions answered this week: {e}")
            return None
    
    def extract_questions_answered_last_week(self):
        """Extract Questions Answered Last Week (parsed from the same element as this week)"""
        try:
            # Check if we already parsed this from the questions_this_week extraction
            if hasattr(self, '_last_week_questions') and self._last_week_questions is not None:
                logger.info(f"✅ Extracted questions answered last week: {self._last_week_questions}")
                return self._last_week_questions
            
            logger.warning("⚠️ Questions answered last week not found - no comparison data available")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract questions answered last week: {e}")
            return None
    
    def extract_daily_activity_calendar(self):
        """Extract the daily activity calendar showing weekly activity patterns"""
        try:
            logger.info("🔍 Looking for Daily Activity calendar...")
            
            # Look for the main calendar container using the exact structure you provided
            calendar_selectors = [
                "//div[contains(@class, 'flex') and contains(@class, 'flex-col') and contains(@class, 'gap-8') and contains(@class, 'w-full')]",
                "//div[@class='flex flex-col gap-8 w-full']"
            ]
            
            calendar_container = None
            for selector in calendar_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Found {len(containers)} containers with selector: {selector}")
                    
                    for container in containers:
                        if container.is_displayed():
                            # Check if this container has week rows with date patterns
                            week_rows = container.find_elements(By.XPATH, ".//div[contains(@class, 'flex-row') and contains(@class, 'items-center') and contains(@class, 'w-full') and contains(@class, 'justify-between')]")
                            if len(week_rows) > 0:
                                # Check if any week row contains date patterns
                                for row in week_rows:
                                    date_elements = row.find_elements(By.XPATH, ".//div[contains(@class, 'text-sm') and contains(@class, 'font-medium') and contains(@class, 'text-neutral-600')]")
                                    for date_elem in date_elements:
                                        if "/" in date_elem.text and "-" in date_elem.text:
                                            calendar_container = container
                                            logger.info(f"✅ Found Daily Activity calendar container with {len(week_rows)} week rows")
                                            break
                                    if calendar_container:
                                        break
                            if calendar_container:
                                break
                    if calendar_container:
                        break
                        
                except Exception as e:
                    logger.debug(f"Calendar selector {selector} failed: {e}")
                    continue
            
            if not calendar_container:
                logger.warning("⚠️ Daily Activity calendar container not found")
                return None
            
            # Extract data from each week row
            activity_calendar = {}
            week_rows = calendar_container.find_elements(By.XPATH, ".//div[contains(@class, 'flex-row') and contains(@class, 'items-center') and contains(@class, 'w-full') and contains(@class, 'justify-between')]")
            
            for week_row in week_rows:
                try:
                    # Find the date range element
                    date_elements = week_row.find_elements(By.XPATH, ".//div[contains(@class, 'text-sm') and contains(@class, 'font-medium') and contains(@class, 'text-neutral-600')]")
                    
                    for date_elem in date_elements:
                        week_text = date_elem.text.strip()
                        if "/" in week_text and "-" in week_text:  # Date pattern like "07/13 - 07/19"
                            logger.info(f"Processing week: {week_text}")
                            
                            # Extract activity data for this week
                            week_data = self._extract_week_activity_new(week_row, week_text)
                            if week_data:
                                activity_calendar[week_text] = week_data
                                logger.info(f"✅ Extracted data for week {week_text}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to process week row: {e}")
                    continue
            
            if activity_calendar:
                logger.info(f"✅ Successfully extracted calendar data for {len(activity_calendar)} weeks")
                return activity_calendar
            else:
                logger.warning("⚠️ No calendar data extracted")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract daily activity calendar: {e}")
            return None
    
    def _extract_week_activity_new(self, week_row, week_range):
        """Extract activity data for a single week row using the exact HTML structure"""
        try:
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            week_data = {}
            
            logger.debug(f"Extracting activity for week: {week_range}")
            
            # Find all day columns - they have class "flex flex-col items-center"
            day_columns = week_row.find_elements(By.XPATH, ".//div[contains(@class, 'flex') and contains(@class, 'flex-col') and contains(@class, 'items-center')]")
            logger.debug(f"Found {len(day_columns)} day columns in week row")
            
            for i, day_column in enumerate(day_columns):
                if i >= len(days):  # Skip if we have more columns than days
                    break
                    
                day_name = days[i]
                activity_status = False
                questions_attempted = 0
                
                try:
                    # Look for the tooltip with data-tip attribute
                    tooltip_elements = day_column.find_elements(By.XPATH, ".//div[contains(@class, 'tooltip') and @data-tip]")
                    
                    if tooltip_elements:
                        tooltip = tooltip_elements[0]
                        data_tip = tooltip.get_attribute("data-tip")
                        
                        if data_tip:
                            logger.debug(f"Day {day_name} tooltip: {data_tip}")
                            
                            # Extract question count from tooltip like "55 questions attempted on Jul 13th."
                            import re
                            match = re.search(r'(\d+)\s+questions?\s+attempted', data_tip)
                            if match:
                                questions_attempted = int(match.group(1))
                                if questions_attempted > 0:
                                    activity_status = True
                            
                            # Also check for "0 question attempted" (singular)
                            elif "0 question attempted" in data_tip or "0 questions attempted" in data_tip:
                                activity_status = False
                                questions_attempted = 0
                    
                    # Double-check by looking at SVG class for active/inactive status
                    svg_elements = day_column.find_elements(By.XPATH, ".//svg")
                    for svg in svg_elements:
                        class_attr = svg.get_attribute("class") or ""
                        if "text-green-200" in class_attr:
                            activity_status = True
                            logger.debug(f"Day {day_name} confirmed ACTIVE (green SVG)")
                        elif "text-neutral-200" in class_attr:
                            # Only set to inactive if we don't already have questions from tooltip
                            if questions_attempted == 0:
                                activity_status = False
                            logger.debug(f"Day {day_name} confirmed INACTIVE (neutral SVG)")
                        break
                    
                except Exception as e:
                    logger.debug(f"Error processing day {day_name}: {e}")
                
                week_data[day_name] = {
                    "active": activity_status,
                    "questions_attempted": questions_attempted
                }
                
                logger.debug(f"Day {day_name}: active={activity_status}, questions={questions_attempted}")
                
            logger.debug(f"Week {week_range} final data: {week_data}")
            return week_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract week activity for {week_range}: {e}")
            return None

    def _extract_week_activity_simple(self, week_row, week_range):
        """Extract activity data for a single week row using a simplified approach"""
        try:
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            week_data = {}
            
            logger.debug(f"Extracting activity for week: {week_range}")
            
            # Look for all SVG elements in the week row - these represent the activity dots
            svg_elements = week_row.find_elements(By.XPATH, ".//svg")
            logger.debug(f"Found {len(svg_elements)} SVG elements in week row")
            
            # The SVGs should be in order: Sun, Mon, Tue, Wed, Thu, Fri, Sat
            for i, day_name in enumerate(days):
                activity_status = False
                questions_attempted = 0
                
                if i < len(svg_elements):
                    svg = svg_elements[i]
                    
                    # Check if the SVG has active styling (looking for color attributes)
                    # Active days typically have green/yellow colors, inactive are gray
                    svg_html = svg.get_attribute("outerHTML")
                    class_attr = svg.get_attribute("class") or ""
                    
                    # Look for active indicators in the SVG
                    if ("fill-green" in svg_html or 
                        "fill-yellow" in svg_html or 
                        "fill-lime" in svg_html or
                        "text-green" in class_attr or
                        "text-yellow" in class_attr or
                        "text-lime" in class_attr):
                        activity_status = True
                        logger.debug(f"Day {day_name} appears ACTIVE based on SVG styling")
                    else:
                        logger.debug(f"Day {day_name} appears INACTIVE")
                        
                    # Try to get question count from parent element or tooltip
                    try:
                        parent_element = svg.find_element(By.XPATH, "./parent::*")
                        title_attr = parent_element.get_attribute("title")
                        if title_attr and "question" in title_attr.lower():
                            import re
                            match = re.search(r'(\d+)', title_attr)
                            if match:
                                questions_attempted = int(match.group(1))
                    except:
                        pass
                
                week_data[day_name] = {
                    "active": activity_status,
                    "questions_attempted": questions_attempted
                }
                
            logger.debug(f"Week {week_range} data: {week_data}")
            return week_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract week activity for {week_range}: {e}")
            return None

    def _extract_week_activity(self, week_row, week_range):
        """Extract activity data for a single week row (legacy method)"""
        try:
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            week_data = {}
            
            # Find all day columns in this week row
            day_columns = week_row.find_elements(By.XPATH, ".//div[contains(@class, 'flex-col') and contains(@class, 'items-center')]")
            
            for i, day_column in enumerate(day_columns):
                if i < len(days):  # Only process the 7 days of the week
                    day_name = days[i]
                    
                    # Look for SVG elements that represent activity bubbles
                    svg_elements = day_column.find_elements(By.XPATH, ".//svg")
                    
                    activity_status = "inactive"  # Default to inactive
                    questions_attempted = 0
                    
                    for svg in svg_elements:
                        # Check the color class to determine activity
                        class_attr = svg.get_attribute("class")
                        
                        if class_attr:
                            if ("text-green-200" in class_attr or 
                                "text-yellow-200" in class_attr or 
                                "text-lime-200" in class_attr):
                                activity_status = "active"
                                
                                # Try to extract question count from tooltip
                                tooltip_element = day_column.find_element(By.XPATH, ".//div[contains(@class, 'tooltip')]")
                                if tooltip_element:
                                    tooltip_text = tooltip_element.get_attribute("data-tip")
                                    if tooltip_text:
                                        # Extract number from tooltip like "44 questions attempted on Jul 21st."
                                        import re
                                        match = re.search(r'(\d+)\s+questions?\s+attempted', tooltip_text)
                                        if match:
                                            questions_attempted = int(match.group(1))
                                break
                            elif "text-neutral-200" in class_attr:
                                activity_status = "inactive"
                                break
                    
                    week_data[day_name] = {
                        "active": activity_status == "active",
                        "questions_attempted": questions_attempted
                    }
            
            return week_data
            
        except Exception as e:
            logger.debug(f"Failed to extract week activity for {week_range}: {e}")
            return None
    
    def extract_strongest_area(self):
        """Extract the strongest academic area and its accuracy"""
        try:
            # Look for the "Strongest" section with more flexible selectors
            strongest_selectors = [
                # Original selectors
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and contains(@class, 'border-gray-300') and .//text()[contains(., 'Strongest')]]",
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and .//div[contains(@class, 'text-sm') and contains(@class, 'font-medium') and contains(text(), 'Strongest')]]",
                "//*[contains(text(), 'Strongest')]/ancestor::div[contains(@class, 'rounded-lg')]",
                # More flexible selectors
                "//div[contains(@class, 'rounded-lg') and .//text()[contains(., 'Strongest')]]",
                "//*[contains(text(), 'Strongest')]/parent::*/parent::*",
                "//*[contains(text(), 'Strongest')]/ancestor::div[contains(@class, 'border')]",
                # Broad search for any container with "Strongest"
                "//*[contains(text(), 'Strongest')]/ancestor::div[1]",
                "//*[contains(text(), 'Strongest')]/ancestor::div[2]",
                "//*[contains(text(), 'Strongest')]/ancestor::div[3]"
            ]
            
            logger.debug("🔍 Searching for Strongest area section...")
            
            for i, selector in enumerate(strongest_selectors):
                try:
                    logger.debug(f"Trying strongest selector {i+1}: {selector}")
                    containers = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Found {len(containers)} containers with selector {i+1}")
                    
                    for j, container in enumerate(containers):
                        if container.is_displayed():
                            logger.debug(f"Container {j+1} is displayed, extracting text...")
                            container_text = container.text.strip()
                            logger.debug(f"Container {j+1} text: '{container_text[:100]}...'")
                            
                            # Look for area name - try multiple patterns
                            area_elements = []
                            area_selectors = [
                                ".//div[contains(@class, 'text-lg') and contains(@class, 'font-medium') and contains(@class, 'text-navy-800')]",
                                ".//div[contains(@class, 'text-lg') and contains(@class, 'font-medium')]",
                                ".//div[contains(@class, 'text-navy-800')]",
                                "./*[2]",  # Often the second child element
                                ".//*[contains(@class, 'truncate')]"
                            ]
                            
                            for area_sel in area_selectors:
                                try:
                                    area_elements = container.find_elements(By.XPATH, area_sel)
                                    if area_elements:
                                        logger.debug(f"Found {len(area_elements)} area elements with selector: {area_sel}")
                                        break
                                except:
                                    continue
                            
                            # Look for accuracy text - try multiple patterns  
                            accuracy_elements = []
                            accuracy_selectors = [
                                ".//div[contains(@class, 'text-base') and contains(@class, 'text-neutral-400') and contains(@class, 'font-medium') and contains(text(), 'accuracy')]",
                                ".//div[contains(text(), 'accuracy')]",
                                ".//div[contains(text(), '%')]",
                                "./*[3]",  # Often the third child element
                                ".//*[contains(text(), 'with')]"
                            ]
                            
                            for acc_sel in accuracy_selectors:
                                try:
                                    accuracy_elements = container.find_elements(By.XPATH, acc_sel)
                                    if accuracy_elements:
                                        logger.debug(f"Found {len(accuracy_elements)} accuracy elements with selector: {acc_sel}")
                                        break
                                except:
                                    continue
                            
                            if area_elements and accuracy_elements:
                                area_name = area_elements[0].text.strip()
                                accuracy_text = accuracy_elements[0].text.strip()
                                
                                logger.debug(f"Raw area name: '{area_name}'")
                                logger.debug(f"Raw accuracy text: '{accuracy_text}'")
                                
                                # Extract percentage from text like "with 100% accuracy"
                                import re
                                accuracy_match = re.search(r'(\d+)%', accuracy_text)
                                accuracy = accuracy_match.group(1) + "%" if accuracy_match else accuracy_text
                                
                                if area_name and accuracy:
                                    result = {
                                        "area": area_name,
                                        "accuracy": accuracy
                                    }
                                    
                                    logger.info(f"✅ Extracted strongest area: {area_name} with {accuracy}")
                                    return result
                    
                except Exception as e:
                    logger.debug(f"Strongest area selector {i+1} failed: {e}")
                    continue
            
            logger.warning("⚠️ Strongest area not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract strongest area: {e}")
            return None
    
    def extract_weakest_area(self):
        """Extract the weakest academic area and its accuracy"""
        try:
            # Look for the "Weakest" section with more flexible selectors
            weakest_selectors = [
                # Original selectors
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and contains(@class, 'border-gray-300') and .//text()[contains(., 'Weakest')]]",
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and .//div[contains(@class, 'text-sm') and contains(@class, 'font-medium') and contains(text(), 'Weakest')]]",
                "//*[contains(text(), 'Weakest')]/ancestor::div[contains(@class, 'rounded-lg')]",
                # More flexible selectors
                "//div[contains(@class, 'rounded-lg') and .//text()[contains(., 'Weakest')]]",
                "//*[contains(text(), 'Weakest')]/parent::*/parent::*",
                "//*[contains(text(), 'Weakest')]/ancestor::div[contains(@class, 'border')]",
                # Broad search for any container with "Weakest"
                "//*[contains(text(), 'Weakest')]/ancestor::div[1]",
                "//*[contains(text(), 'Weakest')]/ancestor::div[2]",
                "//*[contains(text(), 'Weakest')]/ancestor::div[3]"
            ]
            
            logger.debug("🔍 Searching for Weakest area section...")
            
            for i, selector in enumerate(weakest_selectors):
                try:
                    logger.debug(f"Trying weakest selector {i+1}: {selector}")
                    containers = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Found {len(containers)} containers with selector {i+1}")
                    
                    for j, container in enumerate(containers):
                        if container.is_displayed():
                            logger.debug(f"Container {j+1} is displayed, extracting text...")
                            container_text = container.text.strip()
                            logger.debug(f"Container {j+1} text: '{container_text[:100]}...'")
                            
                            # Look for area name - try multiple patterns
                            area_elements = []
                            area_selectors = [
                                ".//div[contains(@class, 'text-lg') and contains(@class, 'font-medium') and contains(@class, 'text-navy-800')]",
                                ".//div[contains(@class, 'text-lg') and contains(@class, 'font-medium')]",
                                ".//div[contains(@class, 'text-navy-800')]",
                                "./*[2]",  # Often the second child element
                                ".//*[contains(@class, 'truncate')]"
                            ]
                            
                            for area_sel in area_selectors:
                                try:
                                    area_elements = container.find_elements(By.XPATH, area_sel)
                                    if area_elements:
                                        logger.debug(f"Found {len(area_elements)} area elements with selector: {area_sel}")
                                        break
                                except:
                                    continue
                            
                            # Look for accuracy text - try multiple patterns  
                            accuracy_elements = []
                            accuracy_selectors = [
                                ".//div[contains(@class, 'text-base') and contains(@class, 'text-neutral-400') and contains(@class, 'font-medium') and contains(text(), 'accuracy')]",
                                ".//div[contains(text(), 'accuracy')]",
                                ".//div[contains(text(), '%')]",
                                "./*[3]",  # Often the third child element
                                ".//*[contains(text(), 'with')]"
                            ]
                            
                            for acc_sel in accuracy_selectors:
                                try:
                                    accuracy_elements = container.find_elements(By.XPATH, acc_sel)
                                    if accuracy_elements:
                                        logger.debug(f"Found {len(accuracy_elements)} accuracy elements with selector: {acc_sel}")
                                        break
                                except:
                                    continue
                            
                            if area_elements and accuracy_elements:
                                area_name = area_elements[0].text.strip()
                                accuracy_text = accuracy_elements[0].text.strip()
                                
                                logger.debug(f"Raw area name: '{area_name}'")
                                logger.debug(f"Raw accuracy text: '{accuracy_text}'")
                                
                                # Extract percentage from text like "with 50% accuracy"
                                import re
                                accuracy_match = re.search(r'(\d+)%', accuracy_text)
                                accuracy = accuracy_match.group(1) + "%" if accuracy_match else accuracy_text
                                
                                if area_name and accuracy:
                                    result = {
                                        "area": area_name,
                                        "accuracy": accuracy
                                    }
                                    
                                    logger.info(f"✅ Extracted weakest area: {area_name} with {accuracy}")
                                    return result
                    
                except Exception as e:
                    logger.debug(f"Weakest area selector {i+1} failed: {e}")
                    continue
            
            logger.warning("⚠️ Weakest area not found with any selector")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract weakest area: {e}")
            return None
    
    def extract_mock_exam_results(self):
        """Extract all mock exam results from the student dashboard"""
        try:
            # Look for the Mock Exam Results section and extract all exam entries
            mock_exam_selectors = [
                # Look for the list items containing exam results
                "//h2[contains(text(), 'Mock Exam Results')]/following-sibling::*//li[contains(@class, '') or not(@class)]",
                "//h2[contains(text(), 'Mock Exam Results')]/parent::*/following-sibling::*//li",
                "//*[contains(text(), 'Mock Exam Results')]/following-sibling::*//li",
                # Alternative patterns for exam containers
                "//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and .//h3[contains(@class, 'text-heading-3')]]",
                "//li//div[contains(@class, 'rounded-lg') and contains(@class, 'border') and .//span[contains(@class, 'text-4xl') or contains(@class, 'text-3xl')]]"
            ]
            
            logger.debug("🔍 Searching for Mock Exam Results section...")
            
            mock_exams = []
            
            for i, selector in enumerate(mock_exam_selectors):
                try:
                    logger.debug(f"Trying mock exam selector {i+1}: {selector}")
                    exam_containers = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Found {len(exam_containers)} exam containers with selector {i+1}")
                    
                    if len(exam_containers) > 0:
                        for j, container in enumerate(exam_containers):
                            if container.is_displayed():
                                logger.debug(f"Processing exam container {j+1}")
                                
                                # Extract exam data from this container
                                exam_data = self._extract_single_exam_data(container, j+1)
                                if exam_data:
                                    mock_exams.append(exam_data)
                                    logger.debug(f"Successfully extracted exam {j+1}: {exam_data}")
                        
                        # If we found exams with this selector, break and use them
                        if mock_exams:
                            break
                    
                except Exception as e:
                    logger.debug(f"Mock exam selector {i+1} failed: {e}")
                    continue
            
            if mock_exams:
                logger.info(f"✅ Successfully extracted {len(mock_exams)} mock exam results")
                return mock_exams
            else:
                logger.warning("⚠️ Mock exam results not found with any selector")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to extract mock exam results: {e}")
            return None
    
    def _extract_single_exam_data(self, container, exam_number):
        """Extract data from a single mock exam container"""
        try:
            exam_data = {
                "exam_number": exam_number,
                "exam_title": None,
                "completion_date": None,
                "score": None
            }
            
            # Extract exam title
            title_selectors = [
                ".//h3[contains(@class, 'text-heading-3')]",
                ".//h3",
                ".//*[contains(@class, 'text-heading')]",
                ".//*[contains(text(), 'Exam') or contains(text(), 'Quiz')]"
            ]
            
            for title_sel in title_selectors:
                try:
                    title_elements = container.find_elements(By.XPATH, title_sel)
                    if title_elements:
                        exam_data["exam_title"] = title_elements[0].text.strip()
                        logger.debug(f"Found exam title: '{exam_data['exam_title']}'")
                        break
                except:
                    continue
            
            # Extract completion date
            date_selectors = [
                ".//span[contains(text(), 'Completed')]",
                ".//*[contains(text(), 'Completed')]",
                ".//div[contains(@class, 'text-gray-600') and contains(text(), '202')]",
                ".//*[contains(text(), '2025') or contains(text(), '2024')]"
            ]
            
            for date_sel in date_selectors:
                try:
                    date_elements = container.find_elements(By.XPATH, date_sel)
                    if date_elements:
                        date_text = date_elements[0].text.strip()
                        # Extract just the date part from "Completed July 21, 2025"
                        import re
                        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', date_text)
                        if date_match:
                            exam_data["completion_date"] = date_match.group(0)
                        else:
                            exam_data["completion_date"] = date_text
                        logger.debug(f"Found completion date: '{exam_data['completion_date']}'")
                        break
                except:
                    continue
            
            # Extract score
            score_selectors = [
                ".//span[contains(@class, 'text-4xl') or contains(@class, 'text-3xl')]",
                ".//*[contains(@class, 'font-medium') and (contains(@class, 'text-4xl') or contains(@class, 'text-3xl'))]",
                ".//span[contains(@class, 'font-readex')]",
                ".//*[text() and string-length(text()) <= 10 and (contains(text(), '0') or contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4') or contains(text(), '5') or contains(text(), '6') or contains(text(), '7') or contains(text(), '8') or contains(text(), '9'))]"
            ]
            
            for score_sel in score_selectors:
                try:
                    score_elements = container.find_elements(By.XPATH, score_sel)
                    for score_elem in score_elements:
                        score_text = score_elem.text.strip()
                        # Check if this looks like a score (number or number range)
                        import re
                        if re.match(r'^\d{2,4}(-\d{2,4})?$', score_text):
                            exam_data["score"] = score_text
                            logger.debug(f"Found score: '{exam_data['score']}'")
                            break
                    if exam_data["score"]:
                        break
                except:
                    continue
            
            # Only return the exam data if we have at least title and score
            if exam_data["exam_title"] and exam_data["score"]:
                return exam_data
            else:
                logger.debug(f"Incomplete exam data: {exam_data}")
                return None
            
        except Exception as e:
            logger.debug(f"Failed to extract single exam data: {e}")
            return None
    
    def navigate_back_to_student_list(self):
        """Navigate back to student list via Admin Console -> Manage Users"""
        try:
            logger.info("🔄 Navigating back to student list...")
            
            # Step 1: Click Admin Console button
            logger.info("🖱️ Looking for Admin Console button...")
            
            admin_console_selectors = [
                "//a[@href='/team/admin-console' and contains(text(), 'Admin Console')]",
                "//a[contains(@href, '/team/admin-console')]",
                "//li//a[contains(text(), 'Admin Console')]",
                "//a[contains(@class, 'flex') and contains(@href, '/team/admin-console')]"
            ]
            
            admin_console_link = None
            for selector in admin_console_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            admin_console_link = element
                            logger.info(f"✅ Found Admin Console button")
                            break
                    if admin_console_link:
                        break
                except Exception as e:
                    continue
            
            if not admin_console_link:
                logger.error("❌ Could not find Admin Console button")
                return False
            
            # Click Admin Console
            logger.info("🖱️ Clicking Admin Console button...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", admin_console_link)
            time.sleep(1)
            admin_console_link.click()
            time.sleep(3)
            
            # Step 2: Click Manage Users button
            logger.info("🖱️ Looking for Manage Users button...")
            
            manage_users_selectors = [
                "//button[text()='Manage Users']",
                "//button[contains(text(), 'Manage Users')]"
            ]
            
            manage_users_button = None
            for selector in manage_users_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            manage_users_button = element
                            logger.info(f"✅ Found Manage Users button")
                            break
                    if manage_users_button:
                        break
                except Exception as e:
                    continue
            
            if not manage_users_button:
                logger.error("❌ Could not find Manage Users button")
                return False
            
            # Click Manage Users
            logger.info("🖱️ Clicking Manage Users button...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", manage_users_button)
            time.sleep(1)
            manage_users_button.click()
            time.sleep(3)
            
            logger.info("✅ Successfully navigated back to student list")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate back to student list: {e}")
            return False
    
    def find_and_extract_student_data(self, target_email):
        """Find a student and extract their data"""
        try:
            logger.info(f"🔍 Looking for student: {target_email}")
            
            # Look for the student table rows
            student_rows = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'border-b')]")
            
            if not student_rows:
                student_rows = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]")
            
            if not student_rows:
                student_rows = self.driver.find_elements(By.XPATH, "//tr[contains(., '@')]")
            
            logger.debug(f"Found {len(student_rows)} potential student rows")
            
            # Process each student row to find our target
            for i, row in enumerate(student_rows):
                try:
                    # Look for email in this row
                    email_elements = row.find_elements(By.XPATH, ".//td[contains(text(), '@')] | .//span[contains(text(), '@')] | .//*[contains(text(), '@')]")
                    
                    student_email = None
                    for email_elem in email_elements:
                        text = email_elem.text.strip()
                        if '@' in text and '.' in text:  # Basic email validation
                            student_email = text.lower()
                            break
                    
                    if not student_email:
                        continue
                    
                    # Check if this is our target student
                    if student_email == target_email:
                        logger.info(f"✅ Found target student: {student_email}")
                        
                        # Look for the name link in this row
                        name_links = row.find_elements(By.XPATH, ".//a[contains(@class, 'link') and contains(@href, '/student-dashboard/')]")
                        
                        if not name_links:
                            name_links = row.find_elements(By.XPATH, ".//a[contains(@href, '/student-dashboard/')]")
                        
                        if not name_links:
                            name_links = row.find_elements(By.XPATH, ".//a[contains(@class, 'text-blue')]")
                        
                        if name_links:
                            name_link = name_links[0]
                            student_name = name_link.text.strip()
                            
                            logger.info(f"🎯 Found name link for {student_name} ({student_email})")
                            
                            # Click the student name link
                            logger.info(f"🖱️ Clicking on {student_name}...")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", name_link)
                            time.sleep(1)
                            name_link.click()
                            time.sleep(3)
                            
                            # Verify navigation to student dashboard
                            current_url = self.driver.current_url
                            if '/student-dashboard/' in current_url:
                                logger.info(f"✅ Successfully navigated to {student_name}'s dashboard")
                                
                                # Extract data from the dashboard
                                student_data = self.extract_student_data(student_email, student_name)
                                return student_data
                            else:
                                logger.warning(f"⚠️ Unexpected URL after clicking {student_name}: {current_url}")
                                return None
                        else:
                            logger.warning(f"⚠️ Could not find name link for {student_email}")
                            return None
                    
                except Exception as e:
                    logger.debug(f"Error processing row {i+1}: {e}")
                    continue
            
            # Student not found on this page
            logger.warning(f"⚠️ Student {target_email} not found on current page")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to find student {target_email}: {e}")
            return None

    def upload_individual_to_supabase(self, email, student_data):
        """Upload individual student data to Supabase immediately after scraping"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Check if Supabase credentials are available
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("⚠️ Supabase credentials not found. Skipping individual upload.")
                return False
            
            # Import Supabase (only when needed)
            try:
                from supabase import create_client, Client
            except ImportError:
                logger.warning("⚠️ Supabase library not installed. Skipping individual upload.")
                return False
            
            # Connect to Supabase
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Transform and upload the student's data
            transformed = self.transform_student_data(student_data)
            
            # Insert new row to Supabase
            result = supabase.table("acely_students").insert(transformed).execute()
            
            if result.data:
                logger.info(f"☁️ Uploaded to Supabase: {transformed['name']} ({transformed['email']})")
                return True
            else:
                logger.warning(f"⚠️ No data returned from Supabase for {transformed['name']}")
                return False
                        
        except Exception as e:
            logger.error(f"❌ Failed to upload individual data for {email}: {e}")
            return False

    def save_final_combined_data(self):
        """Save final combined data to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"all_students_data_{timestamp}.json"
            
            # Create the final combined structure
            final_data = {
                "scrape_timestamp": timestamp,
                "total_students": len(self.student_data),
                "students_not_found": len(self.not_found_students),
                "students": self.student_data,
                "not_found_emails": self.not_found_students
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved final combined data to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to save final combined data: {e}")
            return None
    
    def scrape_all_students(self):
        """Main method to scrape data from all target students"""
        try:
            # First, authenticate and navigate to manage users
            if not self.is_authenticated:
                logger.info("🔐 Authenticating to Acely...")
                if not self.login():
                    logger.error("❌ Authentication failed")
                    return False
            
            # Navigate to admin console and click Manage Users
            logger.info("📍 Navigating to Manage Users section...")
            self.driver.get("https://app.acely.ai/team/admin-console")
            time.sleep(5)
            
            # Click Manage Users button
            manage_users_button = None
            selectors = [
                "//button[text()='Manage Users']",
                "//button[contains(text(), 'Manage Users')]"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            manage_users_button = element
                            break
                    if manage_users_button:
                        break
                except:
                    continue
            
            if manage_users_button:
                logger.info("🖱️ Clicking Manage Users button...")
                manage_users_button.click()
                time.sleep(3)
            
            # Load target emails
            if not self.load_target_emails():
                return False
            
            if not self.target_emails:
                logger.warning("⚠️ No target emails to search for")
                return True
            
            # Process each target email one by one
            logger.info(f"🚀 Starting to process {len(self.target_emails)} target students...")
            
            for email_index, target_email in enumerate(self.target_emails):
                logger.info(f"\n{'='*60}")
                logger.info(f"📧 Processing student {email_index + 1}/{len(self.target_emails)}: {target_email}")
                logger.info(f"{'='*60}")
                
                # Find and extract data for this student
                student_data = self.find_and_extract_student_data(target_email)
                
                if student_data:
                    # Store the extracted data
                    self.student_data[target_email] = student_data
                    logger.info(f"✅ Data extracted for {target_email}")
                    
                    # Upload to Supabase immediately
                    self.upload_individual_to_supabase(target_email, student_data)
                    
                    # Navigate back to student list for the next student
                    if email_index < len(self.target_emails) - 1:  # Don't navigate back after the last student
                        logger.info("🔄 Preparing for next student...")
                        if not self.navigate_back_to_student_list():
                            logger.error(f"❌ Failed to navigate back to student list after {target_email}")
                            break
                else:
                    logger.warning(f"⚠️ Student {target_email} not found or data extraction failed")
                    self.not_found_students.append(target_email)
            
            # Save final combined data to JSON file
            if self.student_data:
                logger.info("💾 Saving final combined data to JSON...")
                self.save_final_combined_data()
            else:
                logger.warning("⚠️ No student data collected to save")
            
            # Final summary
            logger.info(f"\n{'='*60}")
            logger.info("📊 Final Summary:")
            logger.info(f"  Successfully processed: {len(self.student_data)} students")
            logger.info(f"  Not found/failed: {len(self.not_found_students)} students")
            
            if self.student_data:
                logger.info("✅ Successfully processed students:")
                for email, data in self.student_data.items():
                    logger.info(f"  - {data.get('name', 'Unknown')} ({email})")
            
            if self.not_found_students:
                logger.info("❌ Students not found on page:")
                for email in self.not_found_students:
                    logger.info(f"  - {email}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape students: {e}")
            return False
    

    
    def upload_to_supabase_direct(self):
        """Upload the scraped data directly to Supabase (no JSON file created)"""
        try:
            logger.info("🚀 Starting direct Supabase upload...")
            
            # Load environment variables
            load_dotenv()
            
            # Check if Supabase credentials are available
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("⚠️ Supabase credentials not found in .env file. Skipping upload.")
                logger.info("💡 To enable automatic upload, add SUPABASE_URL and SUPABASE_ANON_KEY to your .env file")
                return False
            
            # Import Supabase (only when needed)
            try:
                from supabase import create_client, Client
            except ImportError:
                logger.warning("⚠️ Supabase library not installed. Skipping upload.")
                logger.info("💡 Install with: pip install supabase")
                return False
            
            # Connect to Supabase
            supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Connected to Supabase successfully")
            
            # Use in-memory student data (no JSON file)
            if not self.student_data:
                logger.warning("⚠️ No student data found to upload")
                return False
            
            logger.info(f"👥 Found {len(self.student_data)} students to upload")
            
            # Transform and upload each student's data
            uploaded_count = 0
            for email, student_data in self.student_data.items():
                try:
                    transformed = self.transform_student_data(student_data)
                    
                    # Insert new row to Supabase (always creates new records)
                    result = supabase.table("acely_students").insert(transformed).execute()
                    
                    if result.data:
                        logger.info(f"✅ Inserted new record for {transformed['name']} ({transformed['email']})")
                        uploaded_count += 1
                    else:
                        logger.warning(f"⚠️ No data returned for {transformed['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to upload data for {email}: {e}")
                    continue
            
            logger.info(f"✅ Successfully uploaded {uploaded_count}/{len(self.student_data)} student records to Supabase")
            return uploaded_count > 0
            
        except Exception as e:
            logger.error(f"❌ Supabase upload failed: {e}")
            return False
    
    def transform_student_data(self, student_data):
        """Transform scraped student data to match the acely_students table structure"""
        try:
            # Extract data from the scraped structure
            extracted = student_data.get("data_extracted", {})
            
            # Transform strongest/weakest areas
            strongest_area = extracted.get("strongest_area", {})
            weakest_area = extracted.get("weakest_area", {})
            
            # Create the transformed record with scrape timestamp
            transformed = {
                "name": student_data.get("name"),
                "email": student_data.get("email"),
                "url": student_data.get("dashboard_url"),
                "join_date": extracted.get("join_date"),
                "most_recent_score": extracted.get("most_recent_score"),
                "this_week_accuracy": extracted.get("this_week_accuracy"),
                "last_week_accuracy": extracted.get("last_week_accuracy"),
                "questions_answered_this_week": extracted.get("questions_answered_this_week"),
                "questions_answered_last_week": extracted.get("questions_answered_last_week"),
                "daily_activity": extracted.get("daily_activity_calendar"),
                "strongest_area": strongest_area.get("area") if strongest_area else None,
                "weakest_area": weakest_area.get("area") if weakest_area else None,
                "strongest_area_accuracy": strongest_area.get("accuracy") if strongest_area else None,
                "weakest_area_accuracy": weakest_area.get("accuracy") if weakest_area else None,
                "mock_exam_results": extracted.get("mock_exam_results"),
                "scrape_timestamp": datetime.now().isoformat(),
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"❌ Failed to transform student data: {e}")
            raise


def main():
    """Test the data extraction"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Create configuration
    config = AuthConfig(
        email=os.getenv("ACELY_EMAIL"),
        password=os.getenv("ACELY_PASSWORD"),
        headless=os.getenv("HEADLESS_MODE", "False").lower() == "true",  # Use visible mode for debugging
        wait_timeout=int(os.getenv("WAIT_TIMEOUT", "10"))
    )
    
    # Create and run scraper
    scraper = Step3ExtractData(config)
    
    try:
        # Setup the browser
        scraper.setup_driver()
        
        # Scrape all students
        success = scraper.scrape_all_students()
        
        if success:
            print("✅ Step 3 completed! Student data extraction finished")
            print(f"📊 Extracted data for {len(scraper.student_data)} students")
            logger.info("🔄 Automatically closing browser...")
        else:
            print("❌ Step 3 failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always clean up
        scraper.close()


if __name__ == "__main__":
    main() 