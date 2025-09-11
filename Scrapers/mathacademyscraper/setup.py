#!/usr/bin/env python3
"""
Setup script for Math Academy Scraper
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("Setting up Math Academy Scraper...")
    
    # Install Python dependencies
    print("\n1. Installing Python dependencies...")
    run_command("pip install -r requirements.txt")
    
    # Install Playwright browsers
    print("\n2. Installing Playwright browsers...")
    run_command("playwright install chromium")
    
    # Check if .env file exists
    print("\n3. Checking environment setup...")
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("Please create a .env file with your Math Academy credentials:")
        print("  cp .env.example .env")
        print("  # Then edit .env with your actual username and password")
    else:
        print("✓ .env file found")
    
    print("\nSetup complete! 🎉")
    print("\nTo run the scraper:")
    print("  python scraper_simple.py")

if __name__ == "__main__":
    main()