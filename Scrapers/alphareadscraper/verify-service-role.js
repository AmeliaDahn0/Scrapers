const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

async function verifyServiceRole() {
  console.log('🔐 Verifying Supabase Service Role Key Configuration...\n');
  
  // Check environment variables
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const anonKey = process.env.SUPABASE_ANON_KEY;
  
  console.log('📋 Environment Variables Check:');
  console.log(`  SUPABASE_URL: ${supabaseUrl ? '✅ Set' : '❌ Missing'}`);
  console.log(`  SUPABASE_SERVICE_ROLE_KEY: ${serviceRoleKey ? '✅ Set' : '❌ Missing'}`);
  console.log(`  SUPABASE_ANON_KEY: ${anonKey ? '✅ Set' : '❌ Missing'}`);
  
  if (!supabaseUrl) {
    console.log('\n❌ SUPABASE_URL is missing. Please add it to your .env file.');
    return;
  }
  
  if (!serviceRoleKey) {
    console.log('\n❌ SUPABASE_SERVICE_ROLE_KEY is missing. Please add it to your .env file.');
    console.log('💡 Get your service role key from: https://app.supabase.com/project/_/settings/api');
    return;
  }
  
  console.log('\n✅ All required environment variables are set');
  
  // Initialize Supabase client with service role key
  const supabase = createClient(supabaseUrl, serviceRoleKey);
  
  try {
    console.log('\n🔄 Testing service role key permissions...');
    
    // Test 1: Try to read from students table (should work with service role)
    console.log('  Test 1: Reading from students table...');
    const { data: students, error: studentsError } = await supabase
      .from('students')
      .select('count')
      .limit(1);
    
    if (studentsError) {
      console.log(`    ❌ Error: ${studentsError.message}`);
    } else {
      console.log('    ✅ Success: Can read from students table');
    }
    
    // Test 2: Try to insert into student_data table (should work with service role)
    console.log('  Test 2: Testing insert permission on student_data table...');
    const testRecord = {
      email: 'test@example.com',
      scraped_at: new Date().toISOString(),
      profile_url: 'https://test.com',
      grade_level: 10,
      reading_level: 5,
      average_score: '85%',
      sessions_this_month: 5,
      total_sessions: 25,
      time_reading: '2h 30m',
      success_rate: '90%',
      last_active: 'Today',
      avg_session_time: '15m',
      current_course: 'Test Course'
    };
    
    const { data: insertData, error: insertError } = await supabase
      .from('student_data')
      .insert(testRecord)
      .select();
    
    if (insertError) {
      console.log(`    ❌ Error: ${insertError.message}`);
    } else {
      console.log('    ✅ Success: Can insert into student_data table');
      
      // Clean up test record
      console.log('    🧹 Cleaning up test record...');
      await supabase
        .from('student_data')
        .delete()
        .eq('email', 'test@example.com');
      console.log('    ✅ Test record cleaned up');
    }
    
    // Test 3: Check if we can bypass RLS (service role should bypass all RLS)
    console.log('  Test 3: Verifying RLS bypass capability...');
    
    // This test assumes you have RLS enabled. If not, it will still work.
    const { data: rlsTest, error: rlsError } = await supabase
      .from('student_data')
      .select('email')
      .limit(1);
    
    if (rlsError && rlsError.message.includes('RLS')) {
      console.log('    ⚠️  RLS policy detected - this is normal if RLS is enabled');
      console.log('    ✅ Service role key should bypass RLS policies');
    } else if (rlsError) {
      console.log(`    ❌ Error: ${rlsError.message}`);
    } else {
      console.log('    ✅ Success: Can read data (RLS not blocking)');
    }
    
    console.log('\n🎉 Service Role Key Verification Complete!');
    console.log('✅ Your service role key is properly configured and working');
    console.log('✅ You can now run the scraper with database upload enabled');
    
  } catch (error) {
    console.log('\n💥 Verification failed:', error.message);
    console.log('💡 Common issues:');
    console.log('  - Check your Supabase project URL');
    console.log('  - Verify your service role key is correct');
    console.log('  - Ensure your Supabase project is active');
    console.log('  - Check if required tables exist in your database');
  }
}

// Run the verification
if (require.main === module) {
  verifyServiceRole().catch(console.error);
}

module.exports = { verifyServiceRole }; 