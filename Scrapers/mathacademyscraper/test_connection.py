#!/usr/bin/env python3
"""
Test script to verify Supabase connection and service key setup.
Run this before running the main scraper to ensure everything is configured correctly.
"""

import os
from dotenv import load_dotenv
import logging
from supabase import create_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_supabase_connection():
    """Test the Supabase connection with the service key."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return False
    
    # Validate service key length
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    if len(service_key) < 100:
        logger.error("❌ SUPABASE_SERVICE_KEY appears to be too short")
        logger.error("Make sure you're using the service_role key, not the anon key")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            service_key
        )
        
        # Test connection by querying the students table
        logger.info("🔍 Testing Supabase connection...")
        response = supabase.table('students').select('count', count='exact').execute()
        
        logger.info("✅ Supabase connection successful!")
        logger.info(f"📊 Found {response.count} students in the database")
        
        # Test inserting into math_academy_students table
        logger.info("🔍 Testing write access to math_academy_students table...")
        test_data = {
            'student_id': 'test_connection',
            'name': 'Test Connection',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        # Try to insert test data
        insert_response = supabase.table('math_academy_students').insert(test_data).execute()
        
        if hasattr(insert_response, 'data'):
            logger.info("✅ Write access to math_academy_students table successful!")
            
            # Clean up test data
            supabase.table('math_academy_students').delete().eq('student_id', 'test_connection').execute()
            logger.info("🧹 Test data cleaned up")
        else:
            logger.error("❌ Failed to write to math_academy_students table")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {str(e)}")
        logger.error("Please check your SUPABASE_URL and SUPABASE_SERVICE_KEY")
        return False

def test_math_academy_credentials():
    """Test if Math Academy credentials are configured."""
    
    username = os.getenv('MATH_ACADEMY_USERNAME')
    password = os.getenv('MATH_ACADEMY_PASSWORD')
    
    if not username or not password:
        logger.error("❌ Missing Math Academy credentials")
        logger.error("Please set MATH_ACADEMY_USERNAME and MATH_ACADEMY_PASSWORD in your .env file")
        return False
    
    logger.info("✅ Math Academy credentials found")
    return True

if __name__ == "__main__":
    logger.info("🧪 Testing Math Academy Scraper Configuration")
    logger.info("=" * 50)
    
    # Test Math Academy credentials
    math_academy_ok = test_math_academy_credentials()
    
    # Test Supabase connection
    supabase_ok = test_supabase_connection()
    
    logger.info("=" * 50)
    
    if math_academy_ok and supabase_ok:
        logger.info("🎉 All tests passed! Your configuration is ready.")
        logger.info("You can now run: python scraper.py")
    else:
        logger.error("❌ Some tests failed. Please fix the issues above before running the scraper.")
        exit(1) 