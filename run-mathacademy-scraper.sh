#!/bin/bash

# Math Academy Scraper Runner
# This script runs the Math Academy scraper with proper environment setup

set -e  # Exit on any error

echo "🚀 Starting Math Academy Scraper"
echo "================================"

# Navigate to the Math Academy scraper directory
cd Scrapers/mathacademyscraper

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one first with: python3 -m venv venv"
    echo "Then install requirements: pip install -r requirements.txt"
    exit 1
fi

echo "📦 Activating virtual environment..."
# Activate virtual environment
source venv/bin/activate

echo "🔍 Checking Python environment..."
which python3
python3 --version

echo "📊 Running Math Academy scraper..."

# Check if we're in a headless environment (no display)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "🖥️  No display detected - running in headless mode"
    export HEADLESS=true
    
    # Check if xvfb-run is available as a fallback
    if command -v xvfb-run >/dev/null 2>&1; then
        echo "🖥️  Using xvfb-run for virtual display"
        xvfb-run -a python3 scraper_supabase.py
    else
        echo "🖥️  Running in pure headless mode"
        python3 scraper_supabase.py
    fi
else
    echo "🖥️  Display available - running normally"
    python3 scraper_supabase.py
fi

echo "✅ Math Academy scraper completed!"