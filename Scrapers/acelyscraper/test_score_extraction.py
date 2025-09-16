#!/usr/bin/env python3
"""
Test script for the new most recent score extraction functionality
"""

import os
import sys
from dotenv import load_dotenv
from step3_extract_data import Step3ExtractData, AuthConfig

def test_score_extraction():
    """Test the score extraction on a single student"""
    load_dotenv()
    
    # Create configuration for testing
    config = AuthConfig(
        email=os.getenv("ACELY_EMAIL"),
        password=os.getenv("ACELY_PASSWORD"),
        headless=False,  # Use visible mode for testing so we can see what's happening
        wait_timeout=int(os.getenv("WAIT_TIMEOUT", "10"))
    )
    
    if not config.email or not config.password:
        print("❌ Missing credentials. Please set ACELY_EMAIL and ACELY_PASSWORD in .env file")
        return False
    
    # Create the scraper
    scraper = Step3ExtractData(config)
    
    try:
        print("🚀 Starting score extraction test...")
        
        # Setup the browser
        scraper.setup_driver()
        
        # Load target emails
        if not scraper.load_target_emails():
            print("❌ Failed to load target emails")
            return False
        
        if not scraper.target_emails:
            print("❌ No target emails found")
            return False
        
        # Test with just the first student
        test_email = scraper.target_emails[0]
        print(f"🎯 Testing score extraction with: {test_email}")
        
        # Authenticate and navigate
        if not scraper.is_authenticated:
            print("🔐 Authenticating...")
            if not scraper.login():
                print("❌ Authentication failed")
                return False
        
        # Navigate to admin console
        print("📍 Navigating to admin console...")
        scraper.driver.get("https://app.acely.ai/team/admin-console")
        import time
        time.sleep(5)
        
        # Click Manage Users
        from selenium.webdriver.common.by import By
        manage_users_button = None
        selectors = [
            "//button[text()='Manage Users']",
            "//button[contains(text(), 'Manage Users')]"
        ]
        
        for selector in selectors:
            try:
                elements = scraper.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        manage_users_button = element
                        break
                if manage_users_button:
                    break
            except:
                continue
        
        if manage_users_button:
            print("🖱️ Clicking Manage Users...")
            manage_users_button.click()
            time.sleep(3)
        
        # Find and extract data for the test student
        print(f"🔍 Looking for test student")
        student_data = scraper.find_and_extract_student_data(test_email)
        
        if student_data:
            print("✅ Student data extracted successfully!")
            print("📊 Extracted data:")
        print(f"  - Student data extracted successfully")
            
            extracted_data = student_data.get('data_extracted', {})
            if 'join_date' in extracted_data:
                print(f"  - Join Date: {extracted_data['join_date']}")
            if 'most_recent_score' in extracted_data:
                print(f"  - Most Recent Score: {extracted_data['most_recent_score']}")
            else:
                print("  ⚠️ Most recent score not found")
            
            # Keep browser open for manual inspection
            input("\n🔍 Press Enter to close browser and finish test...")
            return True
        else:
            print("❌ Failed to extract student data")
            input("\n🔍 Press Enter to close browser...")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        input("\n🔍 Press Enter to close browser...")
        return False
    finally:
        scraper.close()

if __name__ == "__main__":
    print("🧪 Testing Most Recent Score Extraction")
    print("=" * 50)
    success = test_score_extraction()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")