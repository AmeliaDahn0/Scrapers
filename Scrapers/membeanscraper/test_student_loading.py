#!/usr/bin/env python3
"""
Test script to verify database connection and student loading functionality.
Run this to test the updated scraper functionality before running the main scrapers.
"""

from supabase import create_client, Client
from decouple import config
from typing import List

def load_student_list() -> List[str]:
    """Load the list of students to process from Supabase database (same as scrapers)"""
    
    # Initialize Supabase client
    supabase: Client = create_client(
        config("SUPABASE_URL"),
        config("SUPABASE_KEY")
    )
    
    students = []
    try:
        # Query the students table to get all student names
        response = supabase.table('students').select('name').execute()
        print("DEBUG: Raw response from Supabase:", response)
        
        if response.data:
            students = [student['name'] for student in response.data]
            print(f"✓ Loaded {len(students)} students from database")
        else:
            print("⚠ No students found in database")
            
    except Exception as e:
        print(f"✗ Error loading students from database: {e}")
        print("Please ensure the database connection is working and the students table exists")
        return []
    
    return students

def test_database_connection():
    """Test the basic database connection"""
    print("Testing database connection...")
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(
            config("SUPABASE_URL"),
            config("SUPABASE_KEY")
        )
        
        # Try a simple query to test connection
        response = supabase.table('students').select('count', count='exact').execute()
        print("✓ Database connection successful")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Please check your .env file and database credentials")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Testing Membean Scraper Database Integration")
    print("=" * 60)
    
    # Test 1: Database connection
    print("\n1. Testing database connection...")
    if not test_database_connection():
        print("\n❌ Database connection test failed!")
        print("Please check your .env file and ensure:")
        print("   - SUPABASE_URL is set correctly")
        print("   - SUPABASE_KEY is set correctly")
        print("   - Database is accessible")
        return
    
    # Test 2: Student loading
    print("\n2. Testing student loading...")
    students = load_student_list()
    
    if students:
        print(f"✓ Successfully loaded {len(students)} students:")
        for i, student in enumerate(students, 1):
            print(f"   {i:2d}. {student}")
        
        print("\n✅ All tests passed!")
        print("Your scrapers are ready to use the database for student lists.")
        print("\nYou can now run:")
        print("   - python membean_scraper.py (daily scraping)")
        print("   - python membean_scraper_weekly.py (weekly scraping)")
        print("   - python membean_historical_scraper.py (historical scraping)")
        
    else:
        print("\n⚠ No students found in database!")
        print("Please run the migration script first:")
        print("   python migrate_students_to_db.py")
        print("\nOr manually add students to the database 'students' table.")

if __name__ == "__main__":
    main() 