#!/usr/bin/env python3
"""
Auto Math Academy Scraping Workflow - Non-Interactive Version
Automatically runs the scraping workflow without user input prompts
"""

import asyncio
import sys
import os
from fetch_student_names import StudentNamesFetcher
from scraper_supabase import MathAcademySupabaseScraper

class AutoScrapingWorkflow:
    def __init__(self):
        self.names_fetcher = StudentNamesFetcher()
        
    async def run_auto_workflow(self, 
                               limit=20, 
                               community_number=None, 
                               min_total_xp=None,
                               fetch_names=True):
        """
        Run the complete scraping workflow automatically
        
        Args:
            limit: Maximum number of students to scrape (default: 20)
            community_number: Filter by specific community (default: None)
            min_total_xp: Filter by minimum XP (default: None)
            fetch_names: Whether to fetch fresh names from Supabase (default: True)
        """
        print("🚀 Starting Auto Math Academy Scraping Workflow")
        print("=" * 60)
        print(f"Configuration:")
        print(f"  - Limit: {limit} students")
        print(f"  - Community filter: {community_number or 'None'}")
        print(f"  - Min XP filter: {min_total_xp or 'None'}")
        print(f"  - Fetch fresh names: {fetch_names}")
        print("=" * 60)
        
        try:
            # Step 1: Fetch student names from Supabase (if requested)
            if fetch_names:
                print("\n📋 STEP 1: Fetching student names from Supabase...")
                students, success = self.names_fetcher.fetch_and_update(
                    limit=limit,
                    community_number=community_number, 
                    min_total_xp=min_total_xp
                )
                
                if not success or not students:
                    print("❌ Failed to fetch student names. Stopping workflow.")
                    return False
                
                print(f"✅ Successfully fetched {len(students)} students")
            else:
                print("\n📋 STEP 1: Using existing student names file...")
            
            # Step 2: Run the Math Academy scraper
            print("\n🔍 STEP 2: Running Math Academy scraper...")
            
            # Set headless mode if no display is available
            if not os.getenv('DISPLAY') and not os.getenv('WAYLAND_DISPLAY'):
                os.environ['HEADLESS'] = 'true'
                print("🖥️  No display detected - enabling headless mode")
            
            scraper = MathAcademySupabaseScraper()
            scraped_students = await scraper.scrape_to_supabase()
            
            if scraped_students:
                print(f"✅ Successfully scraped {len(scraped_students)} students")
                
                # Step 3: Summary report
                print("\n📊 STEP 3: Workflow Summary")
                print("-" * 40)
                
                if fetch_names:
                    print(f"Students fetched from Supabase: {len(students)}")
                print(f"Students successfully scraped: {len(scraped_students)}")
                
                # Show some sample data
                print("\nSample scraped data:")
                for i, student in enumerate(scraped_students[:3], 1):
                    name = student.get('name', 'Unknown')
                    course = student.get('course_name', 'N/A')
                    progress = student.get('percent_complete', 'N/A')
                    weekly_xp = student.get('weekly_xp', 'N/A')
                    print(f"  {i}. Student {i}")
                    print(f"     Course: [HIDDEN], Progress: [HIDDEN], Weekly XP: [HIDDEN]")
                
                if len(scraped_students) > 3:
                    print(f"     ... and {len(scraped_students) - 3} more students")
                
                print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
                print(f"All data has been saved to Supabase math_academy_students table.")
                return True
                
            else:
                print("❌ No students were successfully scraped")
                return False
                
        except Exception as e:
            print(f"❌ Workflow failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main function - runs top 20 students automatically"""
    workflow = AutoScrapingWorkflow()
    
    # You can modify these parameters as needed:
    success = await workflow.run_auto_workflow(
        limit=20,                    # Top 20 students
        community_number=None,       # All communities
        min_total_xp=None,          # No XP filter
        fetch_names=True            # Fetch fresh names from Supabase
    )
    
    if success:
        print("\n✅ Auto workflow completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Auto workflow failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())