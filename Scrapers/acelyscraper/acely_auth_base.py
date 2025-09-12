#!/usr/bin/env python3
"""
Acely Authentication Base Class
Provides robust Google OAuth authentication to access Acely admin console.
"""

import os
import time
import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from loguru import logger


@dataclass
class AuthConfig:
    """Configuration for authentication"""
    email: str
    password: str
    headless: bool = True
    wait_timeout: int = 10
    base_url: str = "https://app.acely.ai"
    admin_console_url: str = "https://app.acely.ai/team/admin-console"


class AcelyAuthenticator:
    """Base class for Acely authentication using Google OAuth"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config
        load_dotenv()
        self.email = os.getenv("ACELY_EMAIL") if not config else config.email
        self.password = os.getenv("ACELY_PASSWORD") if not config else config.password
        self.driver = None
        self.wait = None
        self.max_auth_attempts = 3
        self.is_authenticated = False
        
        # Validate credentials
        if not self.email or not self.password:
            raise ValueError("Email and password must be provided either via config or environment variables")
        
        # Setup logging
        logger.add(
            "scraper.log", 
            rotation="1 day", 
            retention="7 days",
            level="INFO"
        )
    
    def setup_driver(self, attempt_num=1):
        """Setup Chrome driver with enhanced anti-detection"""
        try:
            options = uc.ChromeOptions()
            
            # Enhanced anti-detection
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Aggressive Chrome dialog prevention
            options.add_argument("--disable-sync")
            options.add_argument("--disable-features=ChromeSigninProfileChooser")
            options.add_argument("--disable-account-consistency")
            options.add_argument("--disable-signin-scoped-device-id")
            options.add_argument("--disable-signin-frame-dialog")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-profile-picker-on-startup")
            options.add_argument("--disable-component-update")
            
            # Use fresh profile for each attempt
            user_data_dir = f"/tmp/acely_chrome_{attempt_num}_{int(time.time())}"
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            if self.config and self.config.headless:
                options.add_argument("--headless")
            elif not self.config and os.getenv("HEADLESS_MODE", "True").lower() == "true":
                options.add_argument("--headless")
            
            # Set custom user agent
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
            
            # Force Chrome version 140 to match installed Chrome
            self.driver = uc.Chrome(options=options, version_main=140)
            
            wait_timeout = self.config.wait_timeout if self.config else int(os.getenv("WAIT_TIMEOUT", "10"))
            self.wait = WebDriverWait(self.driver, wait_timeout)
            
            # Execute anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"✅ Chrome driver setup complete (attempt {attempt_num})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    def dismiss_chrome_dialog_aggressively(self):
        """Ultra-aggressive Chrome dialog dismissal"""
        try:
            logger.debug("🔍 Checking for Chrome dialogs...")
            
            # Multiple strategies to detect Chrome dialogs
            dialog_indicators = [
                "Sign in to Chrome?",
                "Set up a school profile",
                "Use Chrome Without an Account",
                "Continue as Learning",
                "chrome://settings"
            ]
            
            dialog_found = False
            for indicator in dialog_indicators:
                if indicator.lower() in self.driver.page_source.lower():
                    logger.info(f"🎯 Chrome dialog detected: {indicator}")
                    dialog_found = True
                    break
            
            if dialog_found:
                # Try every possible dismiss strategy
                dismiss_strategies = [
                    ("//button[contains(text(), 'Use Chrome Without an Account')]", "Use Chrome Without Account"),
                    ("//button[contains(text(), 'Use Chrome without an account')]", "Use Chrome without account"),
                    ("//button[contains(text(), 'No thanks')]", "No thanks"),
                    ("//button[contains(text(), 'Not now')]", "Not now"),
                    ("//button[contains(text(), 'Continue as Learning')]", "Continue as Learning"),
                    ("//div[contains(text(), 'Use Chrome Without an Account')]", "Div Use Chrome Without Account"),
                ]
                
                for selector, description in dismiss_strategies:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                logger.info(f"✅ Dismissing Chrome dialog: {description}")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                                time.sleep(0.5)
                                elem.click()
                                time.sleep(2)
                                return True
                    except Exception as e:
                        continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Chrome dialog dismissal check failed: {e}")
            return False
    
    def login(self):
        """Enhanced login with robust authentication"""
        for attempt in range(1, self.max_auth_attempts + 1):
            logger.info(f"🚀 Authentication attempt {attempt}/{self.max_auth_attempts}")
            
            try:
                if self.attempt_single_authentication(attempt):
                    logger.info(f"✅ Authentication successful on attempt {attempt}")
                    self.is_authenticated = True
                    return True
                else:
                    logger.warning(f"❌ Authentication failed on attempt {attempt}")
                    
                    if attempt < self.max_auth_attempts:
                        logger.info(f"⏳ Waiting before retry attempt {attempt + 1}...")
                        time.sleep(10)
                        
                        # Close current driver and start fresh
                        if self.driver:
                            self.driver.quit()
                        self.setup_driver(attempt + 1)
                    
            except Exception as e:
                logger.error(f"❌ Authentication attempt {attempt} failed with exception: {e}")
                
                if attempt < self.max_auth_attempts:
                    time.sleep(10)
                    if self.driver:
                        self.driver.quit()
                    self.setup_driver(attempt + 1)
        
        logger.error("❌ All authentication attempts failed")
        return False
    
    def attempt_single_authentication(self, attempt_num):
        """Single authentication attempt"""
        try:
            logger.info(f"🌐 Navigating to Acely sign-in (attempt {attempt_num})")
            self.driver.get("https://app.acely.ai/sign-in")
            time.sleep(5)
            
            # Dismiss Chrome dialogs immediately
            self.dismiss_chrome_dialog_aggressively()
            
            # Find and click Google OAuth button
            logger.info("🔍 Looking for Google OAuth button...")
            google_selectors = [
                "//button[contains(text(), 'Continue with Google')]",
                "//button[contains(text(), 'Sign in with Google')]",
                "//div[contains(text(), 'Continue with Google')]//parent::button",
                "*[contains(text(), 'Continue with Google')]"
            ]
            
            google_button = None
            for selector in google_selectors:
                try:
                    google_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"✅ Found Google button: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not google_button:
                logger.error("❌ Google OAuth button not found")
                return False
            
            # Click Google button
            logger.info("🖱️ Clicking Google OAuth button...")
            google_button.click()
            time.sleep(5)
            
            # Dismiss Chrome dialogs after OAuth click
            self.dismiss_chrome_dialog_aggressively()
            
            # Handle Google authentication
            if not self.handle_google_auth():
                return False
            
            # Wait for authentication completion with enhanced logic
            if not self.wait_for_auth_completion_enhanced(attempt_num):
                return False
            
            # Verify we can access admin console
            return self.verify_admin_access()
            
        except Exception as e:
            logger.error(f"❌ Single authentication attempt failed: {e}")
            return False
    
    def handle_google_auth(self):
        """Handle Google authentication steps"""
        try:
            logger.info("📧 Entering Google credentials...")
            
            # Wait for Google page
            time.sleep(3)
            current_url = self.driver.current_url
            if "google" not in current_url.lower():
                logger.error(f"❌ Not on Google page: {current_url}")
                return False
            
            # Dismiss Chrome dialogs before entering credentials
            self.dismiss_chrome_dialog_aggressively()
            
            # Enter email
            try:
                email_input = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email']"))
                )
                email_input.clear()
                email_input.send_keys(self.email)
                
                next_btn = self.driver.find_element(By.ID, "identifierNext")
                next_btn.click()
                time.sleep(3)
                logger.info("✅ Email entered successfully")
            except Exception as e:
                logger.error(f"❌ Email entry failed: {e}")
                return False
            
            # Enter password
            try:
                password_input = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
                )
                password_input.clear()
                password_input.send_keys(self.password)
                
                signin_btn = self.driver.find_element(By.ID, "passwordNext")
                signin_btn.click()
                time.sleep(3)
                logger.info("✅ Password entered successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Password entry failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google authentication failed: {e}")
            return False
    
    def wait_for_auth_completion_enhanced(self, attempt_num, max_wait=180):
        """Enhanced authentication completion waiting"""
        logger.info(f"⏳ Waiting for authentication completion (attempt {attempt_num})...")
        
        start_time = time.time()
        callback_detected = False
        
        while time.time() - start_time < max_wait:
            current_url = self.driver.current_url
            logger.debug(f"📍 Current URL: {current_url}")
            
            # Continuously dismiss Chrome dialogs
            self.dismiss_chrome_dialog_aggressively()
            
            # Handle callback page
            if "callback" in current_url:
                if not callback_detected:
                    logger.info("🔄 Callback page detected - handling Acely's broken OAuth")
                    callback_detected = True
                
                # Wait longer on first callback detection
                if time.time() - start_time < 30:
                    time.sleep(5)
                    continue
                
                # Try direct navigation to admin console
                logger.info("🔗 Attempting direct navigation to admin console...")
                try:
                    self.driver.get("https://app.acely.ai/team/admin-console")
                    time.sleep(10)
                    
                    new_url = self.driver.current_url
                    if "admin-console" in new_url and "sign-in" not in new_url:
                        logger.info("✅ Successfully reached admin console via direct navigation")
                        return True
                except Exception as e:
                    logger.warning(f"❌ Direct navigation failed: {e}")
            
            # Check for successful authentication
            if self.is_authenticated_check(current_url):
                logger.info("✅ Authentication completed successfully!")
                return True
            
            # Handle sign-in redirects
            if "sign-in" in current_url and time.time() - start_time > 30:
                logger.warning("🔄 Redirected back to sign-in - authentication may have failed")
                return False
            
            time.sleep(5)
        
        logger.error(f"❌ Authentication timeout after {max_wait} seconds")
        return False
    
    def is_authenticated_check(self, current_url):
        """Check if successfully authenticated"""
        if ("sign-in" not in current_url and 
            "login" not in current_url and 
            "callback" not in current_url and 
            "acely.ai" in current_url):
            return True
        return False
    
    def verify_admin_access(self):
        """Verify we can access the admin console"""
        try:
            logger.info("🔍 Verifying admin console access...")
            
            # Try to navigate to admin console
            self.driver.get("https://app.acely.ai/team/admin-console")
            time.sleep(10)
            
            current_url = self.driver.current_url
            if "admin-console" in current_url and "sign-in" not in current_url:
                logger.info("✅ Admin console access verified")
                return True
            else:
                logger.warning(f"❌ Admin console access failed: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Admin console verification failed: {e}")
            return False
    
    def close(self):
        """Clean up driver resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Error closing driver: {e}")


def main():
    """Test authentication functionality"""
    load_dotenv()
    
    email = os.getenv("ACELY_EMAIL")
    password = os.getenv("ACELY_PASSWORD")
    
    if not email or not password:
        print("❌ Please set ACELY_EMAIL and ACELY_PASSWORD in .env file")
        return
    
    # Create configuration
    config = AuthConfig(
        email=email,
        password=password,
        headless=os.getenv("HEADLESS_MODE", "True").lower() == "true",
        wait_timeout=int(os.getenv("WAIT_TIMEOUT", "10"))
    )
    
    # Test authentication
    authenticator = AcelyAuthenticator(config)
    
    try:
        authenticator.setup_driver()
        success = authenticator.login()
        
        if success:
            print("✅ Authentication test successful!")
            print(f"📍 Current URL: {authenticator.driver.current_url}")
        else:
            print("❌ Authentication test failed!")
        
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
    finally:
        authenticator.close()


if __name__ == "__main__":
    main() 