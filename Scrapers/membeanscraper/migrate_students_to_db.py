#!/usr/bin/env python3
"""
Migration script to transfer student names from students.csv to Supabase database.
Run this once to populate the students table in your database.
"""

import csv
from supabase import create_client, Client
from decouple import config

def migrate_students():
    """Migrate students from CSV to Supabase database"""
    
    # Initialize Supabase client
    supabase: Client = create_client(
        config("SUPABASE_URL"),
        config("SUPABASE_KEY")
    )
    
    students_to_insert = []
    
    # Read students from CSV
    try:
        with open('students.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):  # Skip empty lines and comments
                    student_name = row[0].strip()
                    if student_name:
                        students_to_insert.append({'name': student_name})
        
        print(f"Found {len(students_to_insert)} students in CSV file")
        
    except FileNotFoundError:
        print("Error: students.csv not found")
        return False
    
    if not students_to_insert:
        print("No students found in CSV file")
        return False
    
    # Insert students into database
    try:
        # Check if students already exist to avoid duplicates
        existing_response = supabase.table('students').select('name').execute()
        existing_names = {student['name'] for student in existing_response.data} if existing_response.data else set()
        
        # Filter out students that already exist
        new_students = [student for student in students_to_insert if student['name'] not in existing_names]
        
        if not new_students:
            print("All students already exist in the database")
            return True
        
        # Insert new students
        response = supabase.table('students').insert(new_students).execute()
        
        if response.data:
            print(f"Successfully inserted {len(new_students)} students into database:")
            for student in new_students:
                print(f"  - {student['name']}")
        else:
            print("No students were inserted")
            return False
            
    except Exception as e:
        print(f"Error inserting students into database: {e}")
        return False
    
    return True

def verify_migration():
    """Verify that all students were successfully migrated"""
    
    # Initialize Supabase client
    supabase: Client = create_client(
        config("SUPABASE_URL"),
        config("SUPABASE_KEY")
    )
    
    try:
        response = supabase.table('students').select('name').execute()
        
        if response.data:
            print(f"\nVerification: Found {len(response.data)} students in database:")
            for student in response.data:
                print(f"  - {student['name']}")
        else:
            print("No students found in database")
            return False
            
    except Exception as e:
        print(f"Error verifying migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting student migration from CSV to Supabase database...")
    print("=" * 60)
    
    if migrate_students():
        print("\n✓ Migration completed successfully!")
        verify_migration()
        print("\n" + "=" * 60)
        print("You can now run your scrapers - they will use the database for student lists.")
        print("The students.csv file is no longer needed for the scrapers.")
    else:
        print("\n✗ Migration failed!")
        print("Please check your database connection and try again.") 