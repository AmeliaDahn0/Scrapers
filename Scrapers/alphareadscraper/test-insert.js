const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

async function testInsert() {
  console.log('🧪 Testing service role key insert capability...\n');
  
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const tableName = process.env.TABLE_NAME || 'student_data';
  
  console.log(`📋 Configuration:`);
  console.log(`  Table: ${tableName}`);
  console.log(`  URL: ${supabaseUrl}`);
  console.log(`  Service Role Key: ${serviceRoleKey ? '✅ Set' : '❌ Missing'}`);
  
  if (!serviceRoleKey) {
    console.log('\n❌ Service role key not found in environment variables');
    return;
  }
  
  const supabase = createClient(supabaseUrl, serviceRoleKey);
  
  try {
    // First, let's see what tables exist
    console.log('\n🔍 Checking available tables...');
    const { data: tables, error: tablesError } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'public');
    
    if (tablesError) {
      console.log('❌ Error checking tables:', tablesError.message);
    } else {
      console.log('📋 Available tables:');
      tables.forEach(table => console.log(`  - ${table.table_name}`));
    }
    
    // Test insert with a simple record
    console.log(`\n🔄 Testing insert into ${tableName}...`);
    
    const testRecord = {
      email: 'test-service-role@example.com',
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
    
    const { data, error } = await supabase
      .from(tableName)
      .insert(testRecord)
      .select();
    
    if (error) {
      console.log(`❌ Insert failed: ${error.message}`);
      console.log(`   Code: ${error.code}`);
      console.log(`   Details: ${error.details}`);
      console.log(`   Hint: ${error.hint}`);
    } else {
      console.log('✅ Insert successful!');
      console.log('📊 Inserted record:', data[0]);
      
      // Clean up
      console.log('\n🧹 Cleaning up test record...');
      const { error: deleteError } = await supabase
        .from(tableName)
        .delete()
        .eq('email', 'test-service-role@example.com');
      
      if (deleteError) {
        console.log(`⚠️  Cleanup failed: ${deleteError.message}`);
      } else {
        console.log('✅ Test record cleaned up');
      }
    }
    
  } catch (error) {
    console.log('💥 Unexpected error:', error.message);
  }
}

if (require.main === module) {
  testInsert().catch(console.error);
}

module.exports = { testInsert }; 