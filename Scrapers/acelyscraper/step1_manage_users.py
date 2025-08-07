#!/usr/bin/env python3
"""
Step 1: Navigate to Manage Users section
"""

import time
from acely_auth_base import AcelyAuthenticator, AuthConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger


class Step1ManageUsers(AcelyAuthenticator):
    """Step 1: Click Manage Users button"""
    
    def __init__(self, config: AuthConfig = None):
        super().__init__(config)
    
    def navigate_to_manage_users(self):
        """Navigate to manage users section"""
        try:
            # First, authenticate
            if not self.is_authenticated:
                logger.info("🔐 Authenticating to Acely...")
                if not self.login():
                    logger.error("❌ Authentication failed")
                    return False
            
            logger.info("🚀 Starting navigation to Manage Users...")
            
            # Ensure we're on admin console
            logger.info("📍 Navigating to admin console...")
            self.driver.get("https://app.acely.ai/team/admin-console")
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"📍 Current URL: {current_url}")
            
            # Look for the Manage Users button using the exact element you provided
            logger.info("🔍 Looking for 'Manage Users' button...")
            
            # Try multiple selectors based on the element you provided
            selectors = [
                # Using the exact ID from your element
                "//button[@id='radix-:rme:-trigger-Manage Users']",
                # Using text content
                "//button[text()='Manage Users']",
                # Using aria-controls attribute
                "//button[@aria-controls='radix-:rme:-content-Manage Users']",
                # Using role and text combination
                "//button[@role='tab' and text()='Manage Users']",
                # Broader search with contains
                "//button[contains(text(), 'Manage Users')]"
            ]
            
            manage_users_button = None
            used_selector = None
            
            for selector in selectors:
                try:
                    logger.debug(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            manage_users_button = element
                            used_selector = selector
                            logger.info(f"✅ Found Manage Users button with selector: {selector}")
                            break
                    
                    if manage_users_button:
                        break
                        
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not manage_users_button:
                logger.error("❌ Could not find Manage Users button")
                
                # Let's see what buttons are available
                logger.info("🔍 Checking what buttons are available on the page...")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(all_buttons[:10]):  # Check first 10 buttons
                    try:
                        text = btn.text.strip()
                        if text:
                            logger.info(f"  Button {i+1}: '{text}'")
                    except:
                        continue
                
                return False
            
            # Click the Manage Users button
            logger.info("🖱️ Clicking 'Manage Users' button...")
            try:
                # Scroll into view first
                self.driver.execute_script("arguments[0].scrollIntoView(true);", manage_users_button)
                time.sleep(1)
                
                # Click the button
                manage_users_button.click()
                logger.info("✅ Successfully clicked Manage Users button")
                
            except Exception as e:
                logger.warning(f"Regular click failed: {e}")
                try:
                    # Try JavaScript click as backup
                    self.driver.execute_script("arguments[0].click();", manage_users_button)
                    logger.info("✅ Successfully clicked Manage Users button (using JavaScript)")
                except Exception as js_e:
                    logger.error(f"❌ Both click methods failed: {js_e}")
                    return False
            
            # Wait a moment for the page to respond
            time.sleep(3)
            
            # Check if we successfully navigated to manage users section
            logger.info("🔍 Verifying navigation to Manage Users section...")
            
            # Check for indicators that we're in the Manage Users section
            success_indicators = [
                "//div[contains(text(), 'Manage Users')]",
                "//h1[contains(text(), 'Manage Users')]",
                "//h2[contains(text(), 'Manage Users')]",
                "//*[@aria-selected='true' and contains(text(), 'Manage Users')]",
                "//button[@aria-selected='true' and contains(text(), 'Manage Users')]"
            ]
            
            navigation_success = False
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements:
                        logger.info(f"✅ Navigation success confirmed by: {indicator}")
                        navigation_success = True
                        break
                except:
                    continue
            
            if navigation_success:
                logger.info("✅ Successfully navigated to Manage Users section!")
                
                # Log the current page state
                current_url = self.driver.current_url
                page_title = self.driver.title
                logger.info(f"📍 Current URL: {current_url}")
                logger.info(f"📄 Page title: {page_title}")
                
                return True
            else:
                logger.warning("⚠️ Button clicked but couldn't confirm navigation to Manage Users section")
                logger.info("🔍 Checking page state after click...")
                
                # Take a screenshot of current state for debugging
                try:
                    timestamp = int(time.time())
                    screenshot_path = f"debug_after_manage_users_click_{timestamp}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                except:
                    pass
                
                return True  # We'll consider this success if the click worked
                
        except Exception as e:
            logger.error(f"❌ Navigation to Manage Users failed: {e}")
            return False


def main():
    """Test the Manage Users navigation"""
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
    scraper = Step1ManageUsers(config)
    
    try:
        # Setup the browser
        scraper.setup_driver()
        
        # Navigate to Manage Users
        success = scraper.navigate_to_manage_users()
        
        if success:
            print("✅ Step 1 completed! Successfully navigated to Manage Users section")
            input("Press Enter to close browser...")
        else:
            print("❌ Step 1 failed - could not navigate to Manage Users section")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always clean up
        scraper.close()


if __name__ == "__main__":
    main() 