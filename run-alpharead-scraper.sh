#!/bin/bash

# AlphaRead Scraper Runner Script
# Simple shell script to run the AlphaRead scraper

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "Scrapers/alphareadscraper" ]; then
    print_error "AlphaRead scraper directory not found!"
    print_error "Please run this script from the root of the repository."
    exit 1
fi

# Change to the scraper directory
cd Scrapers/alphareadscraper

print_status "Starting AlphaRead scraper setup..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    print_warning "Please create .env file with your credentials."
    print_warning "You can copy from env.template and fill in your details."
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm ci
    print_success "Dependencies installed"
else
    print_success "Dependencies already installed"
fi

# Install Playwright browsers if needed
if [ ! -d "node_modules/@playwright" ]; then
    print_status "Installing Playwright browsers..."
    npx playwright install chromium
    print_success "Playwright browsers installed"
else
    print_success "Playwright browsers already installed"
fi

# Parse command line arguments
SCRAPER_TYPE="multi"
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --single)
            SCRAPER_TYPE="single"
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    echo "AlphaRead Scraper Runner"
    echo "Usage: ./run-alpharead-scraper.sh [options]"
    echo ""
    echo "Options:"
    echo "  --single     Run single student scraper (default: multi-student)"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run-alpharead-scraper.sh           # Run multi-student scraper"
    echo "  ./run-alpharead-scraper.sh --single  # Run single student scraper"
    exit 0
fi

# Set table name environment variable
export TABLE_NAME="alpharead_students"

# Run the appropriate scraper
if [ "$SCRAPER_TYPE" = "single" ]; then
    print_status "Running single student scraper..."
    npm run scrape
else
    print_status "Running multi-student scraper..."
    npm run scrape-students
fi

print_success "AlphaRead scraper completed successfully!"
print_status "Check the output files in the current directory." 