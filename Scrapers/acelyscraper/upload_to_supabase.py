#!/usr/bin/env python3
"""
Upload scraped student data to Supabase acely_students table.
This script transforms the JSON output into the specific table structure.
"""

import json
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

def connect_to_supabase() -> Client:
    """Connect to Supabase using environment variables."""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables")
        
        supabase: Client = create_client(url, key)
        logger.info("✅ Connected to Supabase successfully")
        return supabase
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        raise

def transform_student_data(student_data: dict) -> dict:
    """Transform scraped student data to match the acely_students table structure."""
    try:
        # Extract data from the scraped structure
        extracted = student_data.get("data_extracted", {})
        
        # Transform strongest/weakest areas
        strongest_area = extracted.get("strongest_area", {})
        weakest_area = extracted.get("weakest_area", {})
        
        # Create the transformed record
        transformed = {
            "name": student_data.get("name"),
            "email": student_data.get("email"),
            "url": student_data.get("dashboard_url"),
            "join_date": extracted.get("join_date"),
            "most_recent_score": extracted.get("most_recent_score"),
            "this_week_accuracy": extracted.get("this_week_accuracy"),
            "last_week_accuracy": extracted.get("last_week_accuracy"),
            "questions_answered_this_week": extracted.get("questions_answered_this_week"),
            "questions_answered_last_week": extracted.get("questions_answered_last_week"),
            "daily_activity": extracted.get("daily_activity_calendar"),
            "strongest_area": strongest_area.get("area") if strongest_area else None,
            "weakest_area": weakest_area.get("area") if weakest_area else None,
            "strongest_area_accuracy": strongest_area.get("accuracy") if strongest_area else None,
            "weakest_area_accuracy": weakest_area.get("accuracy") if weakest_area else None,
            "mock_exam_results": extracted.get("mock_exam_results"),
        }
        
        logger.debug(f"Transformed data for {transformed['name']}: {len(str(transformed))} characters")
        return transformed
        
    except Exception as e:
        logger.error(f"❌ Failed to transform student data: {e}")
        raise

def upload_student_data(supabase: Client, student_records: list) -> int:
    """Upload student records to Supabase, handling upserts by email."""
    try:
        uploaded_count = 0
        
        for record in student_records:
            try:
                # Try to upsert (insert or update if email exists)
                result = supabase.table("acely_students").upsert(
                    record,
                    on_conflict="email"  # Use email as the conflict resolution column
                ).execute()
                
                if result.data:
                    logger.info(f"✅ Uploaded/updated data for student")
                    uploaded_count += 1
                else:
                    logger.warning(f"⚠️ No data returned for {record['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to upload data for {record.get('name', 'Unknown')}: {e}")
                continue
        
        return uploaded_count
        
    except Exception as e:
        logger.error(f"❌ Failed to upload student data: {e}")
        raise

def load_latest_json_file() -> str:
    """Find and return the path to the most recent student_data_*.json file."""
    try:
        import glob
        
        # Look for student_data_*.json files
        pattern = "student_data_*.json"
        files = glob.glob(pattern)
        
        if not files:
            raise FileNotFoundError("No student_data_*.json files found")
        
        # Sort by modification time and get the latest
        latest_file = max(files, key=os.path.getmtime)
        logger.info(f"📄 Found latest data file: {latest_file}")
        return latest_file
        
    except Exception as e:
        logger.error(f"❌ Failed to find latest JSON file: {e}")
        raise

def main():
    """Main function to upload student data to Supabase."""
    try:
        logger.info("🚀 Starting Supabase upload process...")
        
        # Connect to Supabase
        supabase = connect_to_supabase()
        
        # Find and load the latest JSON file
        json_file_path = load_latest_json_file()
        
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"📊 Loaded data from {json_file_path}")
        
        # Extract student data
        students_data = data.get("students", {})
        
        if not students_data:
            logger.warning("⚠️ No student data found in JSON file")
            return
        
        logger.info(f"👥 Found {len(students_data)} students to upload")
        
        # Transform each student's data
        transformed_records = []
        for email, student_data in students_data.items():
            try:
                transformed = transform_student_data(student_data)
                transformed_records.append(transformed)
            except Exception as e:
                logger.error(f"❌ Failed to transform data for student: {e}")
                continue
        
        if not transformed_records:
            logger.error("❌ No valid student records to upload")
            return
        
        # Upload to Supabase
        uploaded_count = upload_student_data(supabase, transformed_records)
        
        logger.info(f"✅ Successfully uploaded {uploaded_count}/{len(transformed_records)} student records")
        
        # Summary
        logger.info(f"📋 Upload Summary: {len(transformed_records)} students processed")
        
    except Exception as e:
        logger.error(f"❌ Upload process failed: {e}")
        raise

if __name__ == "__main__":
    main()