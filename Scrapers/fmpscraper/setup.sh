#!/bin/bash

# FastMath Pro Scraper Setup Script

echo "🚀 Setting up FastMath Pro Downloads Scraper..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment (optional but recommended)
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "🎯 To run the scraper:"
echo "   source venv/bin/activate  # Activate virtual environment"
echo "   python scraper.py         # Run the scraper"
echo ""
echo "📚 Check README.md for more information"