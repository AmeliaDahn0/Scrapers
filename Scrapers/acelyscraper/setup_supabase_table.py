#!/usr/bin/env python3
"""
Setup script to create the acely_students table in Supabase.
Run this script once to set up your database table.
"""

import os
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

def create_table(supabase: Client):
    """Create the acely_students table using the SQL script."""
    try:
        # Read the SQL script
        with open("create_acely_students_table.sql", "r") as f:
            sql_script = f.read()
        
        # Execute the SQL script
        result = supabase.rpc("exec_sql", {"sql": sql_script}).execute()
        
        logger.info("✅ Successfully created acely_students table")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create table: {e}")
        logger.info("💡 Note: You may need to run the SQL script manually in your Supabase dashboard")
        logger.info("📄 SQL script location: create_acely_students_table.sql")
        return False

def test_table_access(supabase: Client):
    """Test if we can access the acely_students table."""
    try:
        # Try to query the table (should return empty result if table exists)
        result = supabase.table("acely_students").select("*").limit(1).execute()
        logger.info("✅ Table access test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table access test failed: {e}")
        return False

def main():
    """Main setup function."""
    try:
        logger.info("🚀 Setting up Supabase table for acely_students...")
        
        # Check if .env file exists
        if not os.path.exists(".env"):
            logger.error("❌ .env file not found!")
            logger.info("📝 Please create a .env file with:")
            logger.info("   SUPABASE_URL=your_supabase_url")
            logger.info("   SUPABASE_ANON_KEY=your_supabase_anon_key")
            return
        
        # Connect to Supabase
        supabase = connect_to_supabase()
        
        # Test table access (in case table already exists)
        if test_table_access(supabase):
            logger.info("✅ Table already exists and is accessible!")
        else:
            logger.info("📋 Table doesn't exist yet, attempting to create...")
            
            # Try to create the table
            if create_table(supabase):
                # Test access again after creation
                if test_table_access(supabase):
                    logger.info("✅ Table created and verified successfully!")
                else:
                    logger.warning("⚠️ Table may have been created but access test failed")
            else:
                logger.warning("⚠️ Automatic table creation failed")
                logger.info("📄 Please run the SQL script manually:")
                logger.info("   1. Open your Supabase dashboard")
                logger.info("   2. Go to SQL Editor")
                logger.info("   3. Copy and paste the contents of 'create_acely_students_table.sql'")
                logger.info("   4. Run the script")
        
        logger.info("🎯 Setup complete! You can now run upload_to_supabase.py")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()