#!/usr/bin/env python3
"""
Complete Math Academy Scraping Workflow
1. Fetches target student names from Supabase students table
2. Runs the scraper to get detailed Math Academy data
3. Saves all data back to Supabase math_academy_students table
"""

import asyncio
import sys
from fetch_student_names import StudentNamesFetcher
from scraper_supabase import MathAcademySupabaseScraper

class FullScrapingWorkflow:
    def __init__(self):
        self.names_fetcher = StudentNamesFetcher()
        
    async def run_complete_workflow(self, 
                                   limit=50, 
                                   community_number=None, 
                                   min_total_xp=None,
                                   fetch_names=True):
        """
        Run the complete scraping workflow
        
        Args:
            limit: Maximum number of students to scrape
            community_number: Filter by specific community
            min_total_xp: Filter by minimum XP
            fetch_names: Whether to fetch fresh names from Supabase (True) or use existing file (False)
        """
        print("🚀 Starting Complete Math Academy Scraping Workflow")
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
                    print(f"  {i}. {name}")
                    print(f"     Course: {course}, Progress: {progress}, Weekly XP: {weekly_xp}")
                
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
            return False

async def main():
    """Main function with different workflow options"""
    workflow = FullScrapingWorkflow()
    
    print("Math Academy Scraping Workflow Options:")
    print("1. Scrape top 20 students by XP")
    print("2. Scrape specific community")
    print("3. Scrape students with minimum XP")
    print("4. Use existing names file (skip Supabase fetch)")
    print("5. Custom configuration")
    
    try:
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            # Top students by XP
            success = await workflow.run_complete_workflow(limit=20)
            
        elif choice == "2":
            # Specific community
            community = input("Enter community number: ").strip()
            try:
                community_num = int(community)
                success = await workflow.run_complete_workflow(
                    limit=30, 
                    community_number=community_num
                )
            except ValueError:
                print("Invalid community number")
                return
                
        elif choice == "3":
            # Minimum XP filter
            min_xp = input("Enter minimum XP: ").strip()
            try:
                min_xp_num = int(min_xp)
                success = await workflow.run_complete_workflow(
                    limit=25, 
                    min_total_xp=min_xp_num
                )
            except ValueError:
                print("Invalid XP number")
                return
                
        elif choice == "4":
            # Use existing file
            success = await workflow.run_complete_workflow(fetch_names=False)
            
        elif choice == "5":
            # Custom configuration
            limit = input("Enter limit (default 25): ").strip()
            limit = int(limit) if limit.isdigit() else 25
            
            community = input("Enter community number (or press Enter to skip): ").strip()
            community_num = int(community) if community.isdigit() else None
            
            min_xp = input("Enter minimum XP (or press Enter to skip): ").strip()
            min_xp_num = int(min_xp) if min_xp.isdigit() else None
            
            success = await workflow.run_complete_workflow(
                limit=limit,
                community_number=community_num,
                min_total_xp=min_xp_num
            )
            
        else:
            print("Invalid option selected")
            return
        
        if success:
            print("\n✅ Workflow completed successfully!")
        else:
            print("\n❌ Workflow failed")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Workflow cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())