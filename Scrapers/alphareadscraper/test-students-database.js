const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

async function testStudentsDatabase() {
  console.log('🔍 Testing student database connection and data...\n');
  
  // Check environment variables
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    console.log('❌ Missing Supabase credentials in .env file');
    console.log('Required environment variables:');
    console.log('  - SUPABASE_URL');
    console.log('  - SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)');
    console.log('\nPlease check your .env file configuration.');
    return;
  }
  
  console.log('✅ Found Supabase credentials');
  console.log(`📍 URL: ${supabaseUrl}`);
  console.log(`🔑 Key: ${supabaseKey.substring(0, 20)}...`);
  
  // Initialize Supabase client
  const supabase = createClient(supabaseUrl, supabaseKey);
  
  try {
    // Test connection by fetching students
    console.log('\n🔄 Fetching students from database...');
    
    const { data: students, error } = await supabase
      .from('students')
      .select('name, email, created_at')
      .not('email', 'is', null)
      .order('name', { ascending: true });

    if (error) {
      console.log('❌ Error fetching students:', error.message);
      console.log('💡 Common issues:');
      console.log('  - Table "students" does not exist');
      console.log('  - Insufficient permissions on the table');
      console.log('  - Network connectivity issues');
      return;
    }

    if (!students || students.length === 0) {
      console.log('⚠️  No students found in the database');
      console.log('💡 To add students, you can run SQL like:');
      console.log(`   INSERT INTO students (name, email) VALUES ('John Doe', 'john.doe@example.com');`);
      return;
    }

    console.log(`✅ Successfully found ${students.length} students in the database:\n`);
    
    // Display students in a nice format
    console.log('📋 Student List:');
    console.log('─'.repeat(70));
    console.log(`${'Name'.padEnd(25)} ${'Email'.padEnd(35)} Created`);
    console.log('─'.repeat(70));
    
    students.forEach((student, index) => {
      const name = (student.name || 'N/A').substring(0, 24).padEnd(25);
      const email = (student.email || 'N/A').substring(0, 34).padEnd(35);
      const created = student.created_at ? new Date(student.created_at).toLocaleDateString() : 'N/A';
      console.log(`${name} ${email} ${created}`);
    });
    
    console.log('─'.repeat(70));
    
    // Check for students with missing emails
    const { data: allStudents, error: allError } = await supabase
      .from('students')
      .select('name, email');
      
    if (!allError && allStudents) {
      const studentsWithoutEmail = allStudents.filter(s => !s.email);
      if (studentsWithoutEmail.length > 0) {
        console.log(`\n⚠️  Warning: ${studentsWithoutEmail.length} students have no email address and will be skipped:`);
        console.log(`   - ${studentsWithoutEmail.length} students missing email addresses`);
      }
    }
    
    console.log(`\n✅ Database test completed successfully!`);
    console.log(`🚀 The scraper will use these ${students.length} students when you run it.`);
    
  } catch (error) {
    console.log('💥 Unexpected error:', error.message);
    console.log('💡 Make sure your Supabase project is active and accessible.');
  }
}

// Run the test
if (require.main === module) {
  testStudentsDatabase().catch(console.error);
}

module.exports = testStudentsDatabase; 