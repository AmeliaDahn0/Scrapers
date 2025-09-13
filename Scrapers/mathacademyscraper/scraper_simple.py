#!/usr/bin/env python3
"""
Math Academy Students Page Scraper using Playwright
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

class MathAcademyScraper:
    def __init__(self):
        self.username = os.getenv('MATH_ACADEMY_USERNAME')
        self.password = os.getenv('MATH_ACADEMY_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        
        self.students_url = "https://www.mathacademy.com/students"
        
    async def login_and_scrape(self):
        """Login and scrape the students page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                print("Navigating to students page...")
                await page.goto(self.students_url)
                
                # Take a screenshot to see what we're dealing with
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"initial_page_{timestamp}.png")
                
                # Wait for page to load
                await page.wait_for_load_state('networkidle')
                
                # Get page content to inspect
                content = await page.content()
                with open(f'initial_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Initial page saved as initial_page_{timestamp}.html and initial_page_{timestamp}.png")
                
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
                    print("No login field found. Let's check if we're already logged in or need to navigate differently...")
                    
                    # Check if we're already on a logged-in page
                    current_url = page.url
                    print(f"Current URL: {current_url}")
                    
                    # Look for any links that might lead to login
                    login_links = await page.query_selector_all('a[href*="login"], a[href*="signin"], a[href*="sign-in"]')
                    if login_links:
                        print(f"Found {len(login_links)} potential login links")
                        await login_links[0].click()
                        await page.wait_for_load_state('networkidle')
                        await page.screenshot(path=f"after_login_click_{timestamp}.png")
                        
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
                        await page.screenshot(path=f"after_login_{timestamp}.png")
                        
                        print("Login attempt completed!")
                    else:
                        print("Could not find password field")
                else:
                    print("Could not find login form. Saving current page for inspection.")
                
                # Wait for page to load
                await page.wait_for_load_state('networkidle')
                
                # Save final page HTML for inspection
                final_content = await page.content()
                with open(f'final_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                print(f"Final page saved as final_page_{timestamp}.html")
                print(f"Current URL: {page.url}")
                
                return final_content
                
            except Exception as e:
                print(f"Error: {e}")
                await page.screenshot(path=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                raise
            finally:
                await browser.close()

async def main():
    scraper = MathAcademyScraper()
    await scraper.login_and_scrape()

if __name__ == "__main__":
    asyncio.run(main())