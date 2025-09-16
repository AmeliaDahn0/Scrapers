#!/usr/bin/env python3
"""
Fetch Student Names from Supabase
This script fetches student names from the Supabase students table and 
updates the student_names_to_scrape.txt file automatically.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class StudentNamesFetcher:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print("✓ Connected to Supabase")
    
    def fetch_student_names(self, limit=None, community_number=None, min_total_xp=None):
        """
        Fetch student names from Supabase students table
        
        Args:
            limit: Maximum number of students to fetch (None for all)
            community_number: Filter by specific community number (None for all)
            min_total_xp: Filter by minimum total XP (None for no filter)
        """
        try:
            print("Fetching student names from Supabase...")
            
            # Build the query
            query = self.supabase.table('students').select('name, email, total_xp, community_number, created_at')
            
            # Apply filters
            if community_number is not None:
                query = query.eq('community_number', community_number)
                print(f"  → Filtering by community number: {community_number}")
            
            if min_total_xp is not None:
                query = query.gte('total_xp', min_total_xp)
                print(f"  → Filtering by minimum XP: {min_total_xp}")
            
            # Apply limit
            if limit is not None:
                query = query.limit(limit)
                print(f"  → Limiting to {limit} students")
            
            # Order by total XP descending (most active students first)
            query = query.order('total_xp', desc=True)
            
            # Execute query
            result = query.execute()
            
            if result.data:
                students = result.data
                print(f"✓ Fetched {len(students)} students from Supabase")
                return students
            else:
                print("✗ No students found in Supabase")
                return []
                
        except Exception as e:
            print(f"✗ Error fetching students from Supabase: {e}")
            return []
    
    def update_names_file(self, students, filename="student_names_to_scrape.txt"):
        """Update the student names file with fetched data"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create backup of existing file
            if os.path.exists(filename):
                backup_filename = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(filename, backup_filename)
                print(f"✓ Created backup: {backup_filename}")
            
            # Write new file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Student Names for Math Academy Scraping\n")
                f.write(f"# Auto-generated from Supabase on {timestamp}\n")
                f.write(f"# Total students: {len(students)}\n")
                f.write(f"#\n")
                f.write(f"# Format: First Last (will be auto-converted to 'Last, First')\n")
                f.write(f"# Lines starting with # are comments and will be ignored\n")
                f.write(f"\n")
                
                if not students:
                    f.write("# No students found in Supabase\n")
                    f.write("# Please check your database connection and filters\n")
                else:
                    for i, student in enumerate(students, 1):
                        name = student.get('name', '').strip()
                        total_xp = student.get('total_xp', 0)
                        community_number = student.get('community_number', 'N/A')
                        email = student.get('email', 'N/A')
                        
                        # Add student name (one per line)
                        if name:
                            f.write(f"{name}\n")
                            
                            # Optionally add metadata as comments
                            if i <= 5:  # Show details for first 5 students
                                f.write(f"# ↳ XP: {total_xp}, Community: {community_number}, Email: {email}\n")
                        else:
                            f.write(f"# Student {i}: (no name)\n")
            
            print(f"✓ Updated {filename} with {len(students)} student names")
            
            # Show summary
            if students:
                print(f"\nSample students added:")
                for i, student in enumerate(students[:5], 1):
                    name = student.get('name', 'No name')
                    total_xp = student.get('total_xp', 0)
                    print(f"  {i}. Student {i} (XP: {total_xp})")
                
                if len(students) > 5:
                    print(f"  ... and {len(students) - 5} more students")
            
            return True
            
        except Exception as e:
            print(f"✗ Error updating names file: {e}")
            return False
    
    def fetch_and_update(self, **kwargs):
        """Convenience method to fetch and update in one call"""
        students = self.fetch_student_names(**kwargs)
        success = self.update_names_file(students)
        return students, success

def main():
    """Main function with example usage"""
    try:
        fetcher = StudentNamesFetcher()
        
        print("\n=== Fetching Student Names from Supabase ===")
        
        # Example configurations - modify as needed:
        
        # Option 1: Fetch all students (might be a lot!)
        # students, success = fetcher.fetch_and_update()
        
        # Option 2: Fetch top 50 students by XP
        students, success = fetcher.fetch_and_update(limit=50)
        
        # Option 3: Fetch students from specific community
        # students, success = fetcher.fetch_and_update(community_number=1, limit=25)
        
        # Option 4: Fetch students with minimum XP
        # students, success = fetcher.fetch_and_update(min_total_xp=100, limit=30)
        
        if success:
            print(f"\n🎉 Success! Updated student_names_to_scrape.txt with {len(students)} students")
            print("You can now run the scraper with: python scraper_supabase.py")
        else:
            print("\n❌ Failed to update student names file")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()