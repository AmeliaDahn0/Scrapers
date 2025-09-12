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
# Run the scraper
python3 scraper_supabase.py

echo "✅ Math Academy scraper completed!"