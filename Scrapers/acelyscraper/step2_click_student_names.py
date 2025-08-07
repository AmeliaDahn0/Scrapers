#!/usr/bin/env python3
"""
Step 2: Find students from our email list and click their name links
"""

import time
from acely_auth_base import AcelyAuthenticator, AuthConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger


class Step2ClickStudentNames(AcelyAuthenticator):
    """Step 2: Click on student name links for students in our target list"""
    
    def __init__(self, config: AuthConfig = None):
        super().__init__(config)
        self.target_emails = []
        self.clicked_students = []
        self.not_found_students = []
    
    def load_target_emails(self, email_file="student_emails.txt"):
        """Load target student emails from file"""
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                emails = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        emails.append(line.lower())  # Store in lowercase for comparison
                
                self.target_emails = emails
                logger.info(f"📧 Loaded {len(self.target_emails)} target student emails:")
                for email in self.target_emails:
                    logger.info(f"  - {email}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to load student emails from {email_file}: {e}")
            return False
    
    def navigate_back_to_student_list(self):
        """Navigate back to student list via Admin Console -> Manage Users"""
        try:
            logger.info("🔄 Navigating back to student list...")
            
            # Step 1: Click Admin Console button
            logger.info("🖱️ Looking for Admin Console button...")
            
            # Multiple selectors for the Admin Console link based on your element
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
                            logger.info(f"✅ Found Admin Console button with selector: {selector}")
                            break
                    if admin_console_link:
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
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
            
            # Verify we're back at admin console
            current_url = self.driver.current_url
            if 'admin-console' not in current_url:
                logger.warning(f"⚠️ Expected to be at admin console, but URL is: {current_url}")
                return False
            
            logger.info("✅ Successfully navigated to Admin Console")
            
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
                            logger.info(f"✅ Found Manage Users button with selector: {selector}")
                            break
                    if manage_users_button:
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
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
    
    def find_and_click_students(self):
        """Find students from our email list and click their name links"""
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
            else:
                logger.warning("⚠️ Could not find Manage Users button, assuming we're already there")
            
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
                
                # Find this specific student on the current page
                student_found = self.find_and_click_single_student(target_email)
                
                if student_found:
                    # Navigate back to student list for the next student
                    if email_index < len(self.target_emails) - 1:  # Don't navigate back after the last student
                        logger.info("🔄 Preparing for next student...")
                        if not self.navigate_back_to_student_list():
                            logger.error(f"❌ Failed to navigate back to student list after {target_email}")
                            break
                else:
                    logger.warning(f"⚠️ Student {target_email} not found on current page")
                    self.not_found_students.append(target_email)
            
            # Final summary
            logger.info(f"\n{'='*60}")
            logger.info("📊 Final Summary:")
            logger.info(f"  Successfully processed: {len(self.clicked_students)} students")
            logger.info(f"  Not found: {len(self.not_found_students)} students")
            
            if self.clicked_students:
                logger.info("✅ Successfully processed students:")
                for student in self.clicked_students:
                    logger.info(f"  - {student['name']} ({student['email']})")
            
            if self.not_found_students:
                logger.info("❌ Students not found on page:")
                for email in self.not_found_students:
                    logger.info(f"  - {email}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to find and click students: {e}")
            return False
    
    def find_and_click_single_student(self, target_email):
        """Find and click a single student by email"""
        try:
            logger.info(f"🔍 Looking for student: {target_email}")
            
            # Look for the student table rows
            student_rows = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'border-b')]")
            
            if not student_rows:
                # Try alternative selectors
                student_rows = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]")
            
            if not student_rows:
                # Try finding any row that contains an email
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
                                logger.info(f"✅ Successfully navigated to {student_name}'s dashboard: {current_url}")
                                
                                self.clicked_students.append({
                                    'name': student_name,
                                    'email': student_email,
                                    'dashboard_url': current_url
                                })
                                
                                return True
                            else:
                                logger.warning(f"⚠️ Unexpected URL after clicking {student_name}: {current_url}")
                                return False
                        else:
                            logger.warning(f"⚠️ Could not find name link for {student_email}")
                            return False
                    
                except Exception as e:
                    logger.debug(f"Error processing row {i+1}: {e}")
                    continue
            
            # Student not found on this page
            logger.warning(f"⚠️ Student {target_email} not found on current page")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to find student {target_email}: {e}")
            return False


def main():
    """Test the student name clicking with proper navigation"""
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
    scraper = Step2ClickStudentNames(config)
    
    try:
        # Setup the browser
        scraper.setup_driver()
        
        # Find and click student names
        success = scraper.find_and_click_students()
        
        if success:
            print("✅ Step 2 completed! Student processing finished")
            input("Press Enter to close browser...")
        else:
            print("❌ Step 2 failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always clean up
        scraper.close()


if __name__ == "__main__":
    main() 