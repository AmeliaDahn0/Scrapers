#!/usr/bin/env python3
"""
Debug script to test Keyen Gupta's database update step by step
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

class DebugKeyenDatabaseUpdate:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def debug_keyen_update_process(self):
        """Debug Keyen's database update process step by step"""
        print("=== DEBUGGING KEYEN'S DATABASE UPDATE PROCESS ===")
        
        student_id = "12615"
        
        # Step 1: Check current state
        print(f"\n1. CURRENT STATE:")
        result = self.supabase.table('math_academy_students').select('*').eq('student_id', student_id).execute()
        if result.data:
            current_record = result.data[0]
            print(f"   Current estimated_completion: '{current_record.get('estimated_completion')}'")
            print(f"   Current updated_at: {current_record.get('updated_at')}")
        else:
            print("   No record found!")
            return
        
        # Step 2: Test if we can find the record for update
        print(f"\n2. TESTING RECORD LOOKUP:")
        existing = self.supabase.table('math_academy_students').select('id').eq('student_id', student_id).execute()
        if existing.data:
            print(f"   ✓ Found existing record with ID: {existing.data[0]['id']}")
        else:
            print("   ✗ Could not find existing record")
            return
        
        # Step 3: Test a simple update
        print(f"\n3. TESTING SIMPLE UPDATE:")
        test_value = f"TEST_UPDATE_{datetime.now().strftime('%H%M%S')}"
        update_data = {
            'estimated_completion': test_value,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"   Attempting to update with: {update_data}")
        
        try:
            result = self.supabase.table('math_academy_students').update(update_data).eq('student_id', student_id).execute()
            print(f"   ✓ Update successful: {result}")
            
            # Verify the update worked
            verify = self.supabase.table('math_academy_students').select('estimated_completion, updated_at').eq('student_id', student_id).execute()
            if verify.data:
                print(f"   ✓ Verification - estimated_completion is now: '{verify.data[0].get('estimated_completion')}'")
                print(f"   ✓ Verification - updated_at is now: {verify.data[0].get('updated_at')}")
            else:
                print("   ✗ Could not verify update")
                
        except Exception as e:
            print(f"   ✗ Update failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Test with the actual "July, 2032" value
        print(f"\n4. TESTING WITH ACTUAL VALUE:")
        actual_data = {
            'estimated_completion': 'July, 2032',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            result = self.supabase.table('math_academy_students').update(actual_data).eq('student_id', student_id).execute()
            print(f"   ✓ Update with 'July, 2032' successful: {result}")
            
            # Final verification
            final_verify = self.supabase.table('math_academy_students').select('estimated_completion, updated_at').eq('student_id', student_id).execute()
            if final_verify.data:
                print(f"   ✓ FINAL - estimated_completion is: '{final_verify.data[0].get('estimated_completion')}'")
                print(f"   ✓ FINAL - updated_at is: {final_verify.data[0].get('updated_at')}")
            
        except Exception as e:
            print(f"   ✗ Final update failed: {e}")
        
        # Step 5: Check for any RLS policies or constraints
        print(f"\n5. CHECKING FOR POTENTIAL ISSUES:")
        try:
            # Try to get all columns to see if there are any constraints
            all_data = self.supabase.table('math_academy_students').select('*').eq('student_id', student_id).execute()
            if all_data.data:
                record = all_data.data[0]
                print(f"   Record has {len(record)} fields")
                print(f"   ID field: {record.get('id')}")
                print(f"   Student ID field: {record.get('student_id')}")
                print(f"   Name field: {record.get('name')}")
                
                # Check if estimated_completion field exists and what type it is
                estimated_value = record.get('estimated_completion')
                print(f"   Current estimated_completion: '{estimated_value}' (type: {type(estimated_value)})")
                
        except Exception as e:
            print(f"   Error checking record details: {e}")

def main():
    debugger = DebugKeyenDatabaseUpdate()
    debugger.debug_keyen_update_process()

if __name__ == "__main__":
    main()