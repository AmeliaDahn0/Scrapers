#!/usr/bin/env python3
"""
Apply Row Level Security (RLS) to the acely_students table.
This will remove the "Unrestricted" warning in Supabase.
"""

import os
from dotenv import load_dotenv
from loguru import logger
import psycopg2

def apply_rls_security():
    """Apply Row Level Security to the acely_students table"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase connection details
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_DB_PASSWORD")  # This is your database password
        
        if not supabase_url or not supabase_password:
            logger.error("❌ Missing SUPABASE_URL or SUPABASE_DB_PASSWORD in .env file")
            logger.info("💡 You need to add your Supabase database password to .env as SUPABASE_DB_PASSWORD")
            logger.info("🔗 Find it in: Supabase Dashboard > Settings > Database > Connection string")
            return False
        
        # Extract database connection details from Supabase URL
        # Format: https://xxxxx.supabase.co
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
        
        # Database connection parameters
        db_config = {
            'host': f'db.{project_id}.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': supabase_password
        }
        
        logger.info("🔐 Connecting to Supabase database...")
        
        # Connect to the database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        logger.info("✅ Connected to database successfully")
        
        # Read and execute the RLS security SQL
        with open('setup_rls_security.sql', 'r') as f:
            rls_sql = f.read()
        
        logger.info("🛡️ Applying Row Level Security policies...")
        
        # Execute the security setup
        cursor.execute(rls_sql)
        conn.commit()
        
        logger.info("✅ Row Level Security applied successfully!")
        logger.info("🔒 The acely_students table is now secured and should no longer show 'Unrestricted'")
        
        # Verify RLS is enabled
        cursor.execute("""
            SELECT tablename, rowsecurity 
            FROM pg_tables 
            WHERE tablename = 'acely_students' AND schemaname = 'public'
        """)
        
        result = cursor.fetchone()
        if result and result[1]:  # rowsecurity = True
            logger.info("✅ Verification: Row Level Security is ENABLED")
        else:
            logger.warning("⚠️ Verification: Row Level Security status unclear")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        logger.info("💡 Make sure your SUPABASE_DB_PASSWORD is correct")
        return False
    except FileNotFoundError:
        logger.error("❌ Could not find setup_rls_security.sql file")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to apply security: {e}")
        return False

def main():
    """Main function"""
    logger.info("🛡️ Setting up Row Level Security for acely_students table...")
    
    if not os.path.exists(".env"):
        logger.error("❌ .env file not found!")
        logger.info("📝 Please ensure your .env file contains:")
        logger.info("   SUPABASE_URL=your_supabase_url")
        logger.info("   SUPABASE_DB_PASSWORD=your_database_password")
        return
    
    if apply_rls_security():
        logger.info("🎉 Security setup completed successfully!")
        logger.info("🔄 Refresh your Supabase dashboard to see the changes")
    else:
        logger.error("❌ Security setup failed")
        logger.info("🔧 Alternative: Run the SQL manually in Supabase SQL Editor:")
        logger.info("📄 Copy contents of setup_rls_security.sql and run in Supabase Dashboard > SQL Editor")

if __name__ == "__main__":
    main()