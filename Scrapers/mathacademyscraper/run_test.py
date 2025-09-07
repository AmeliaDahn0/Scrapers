#!/usr/bin/env python3
"""
Quick test runner for the Math Academy scraper.
This helps you test the improvements without running the full scraper.
"""

import asyncio
import os
from scraper import load_target_students, validate_supabase_connection

async def test_configuration():
    """Test configuration and student loading"""
    print("🧪 Testing Math Academy Scraper Configuration")
    print("=" * 50)
    
    # Test Supabase connection
    print("1. Testing Supabase connection...")
    if validate_supabase_connection():
        print("   ✅ Supabase connection successful")
    else:
        print("   ❌ Supabase connection failed")
        return False
    
    # Test student loading
    print("\n2. Loading target students from database...")
    target_students, math_academy_mapping = load_target_students()
    
    if target_students:
        print(f"   ✅ Loaded {len(target_students)} students from database")
        print(f"   📋 Students: {sorted(list(target_students))}")
        
        if math_academy_mapping:
            print(f"   🗺️  Name mapping: {dict(list(math_academy_mapping.items())[:3])}...")
    else:
        print("   ❌ No students loaded from database")
        return False
    
    # Check environment variables
    print("\n3. Checking environment variables...")
    required_vars = ['MATH_ACADEMY_USERNAME', 'MATH_ACADEMY_PASSWORD', 'SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("   ✅ All environment variables present")
    
    print("\n🎉 Configuration test completed successfully!")
    print("\nYou can now run: python3 scraper.py")
    return True

if __name__ == "__main__":
    asyncio.run(test_configuration())