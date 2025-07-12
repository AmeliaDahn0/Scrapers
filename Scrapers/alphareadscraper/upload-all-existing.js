const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
require('dotenv').config();

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;
const tableName = process.env.TABLE_NAME || 'student_data';

console.log('🔧 Configuration:');
console.log(`📊 Table name: ${tableName}`);
console.log(`🔗 Supabase URL: ${supabaseUrl ? 'Set' : 'Missing'}`);
console.log(`🔑 Supabase Key: ${supabaseKey ? 'Set' : 'Missing'}`);

if (!supabaseUrl || !supabaseKey) {
  console.log('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Fixed upload function
async function uploadToSupabase(studentData) {
  try {
    // Parse the date correctly - format is "MM/DD/YYYY, HH:mm:ss"
    let scrapedAtISO;
    try {
      // Parse US format date string
      const dateStr = studentData.scrapedAt;
      const [datePart, timePart] = dateStr.split(', ');
      const [month, day, year] = datePart.split('/');
      const [hour, minute, second] = timePart.split(':');
      
      // Create date in ISO format
      const parsedDate = new Date(`${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T${hour.padStart(2, '0')}:${minute.padStart(2, '0')}:${second.padStart(2, '0')}.000Z`);
      scrapedAtISO = parsedDate.toISOString();
    } catch (dateError) {
      console.log(`⚠️  Date parsing error for ${studentData.email}, using current time:`, dateError.message || 'Unknown date error');
      scrapedAtISO = new Date().toISOString();
    }
    
    // Transform the data to match the database schema
    const dbRecord = {
      email: studentData.email,
      scraped_at: scrapedAtISO,
      profile_url: studentData.url,
      grade_level: studentData.profile?.gradeLevel ? parseInt(studentData.profile.gradeLevel) : null,
      reading_level: studentData.profile?.readingLevel ? parseInt(studentData.profile.readingLevel) : null,
      average_score: studentData.profile?.averageScore,
      sessions_this_month: studentData.profile?.sessionsThisMonth ? parseInt(studentData.profile.sessionsThisMonth) : null,
      total_sessions: studentData.profile?.totalSessions ? parseInt(studentData.profile.totalSessions) : null,
      time_reading: studentData.profile?.timeReading,
      success_rate: studentData.profile?.successRate,
      last_active: studentData.profile?.lastActive,
      avg_session_time: studentData.profile?.avgSessionTime,
      current_course: studentData.profile?.currentCourse
    };

    const { data, error } = await supabase
      .from(tableName)
      .upsert(dbRecord, { 
        onConflict: 'email,scraped_at'
      })
      .select();

    if (error) {
      const errorMsg = error.message || error.details || JSON.stringify(error) || 'Unknown database error';
      return { success: false, error: errorMsg };
    }

    return { success: true, data };

  } catch (error) {
    const errorMsg = error.message || error.toString() || 'Unknown upload error';
    return { success: false, error: errorMsg };
  }
}

async function uploadAllData() {
  try {
    // Find all student data files
    const files = fs.readdirSync('.').filter(f => f.startsWith('student-data-') && f.endsWith('.json'));
    
    if (files.length === 0) {
      console.log('❌ No student data files found');
      return;
    }
    
    console.log(`📁 Found ${files.length} student data files`);
    
    // Use the most recent file
    const latestFile = files.sort().pop();
    console.log(`📁 Using latest file: ${latestFile}`);
    
    const data = JSON.parse(fs.readFileSync(latestFile, 'utf-8'));
    const students = data.students;
    
    if (!students || students.length === 0) {
      console.log('❌ No students found in file');
      return;
    }
    
    console.log(`🚀 Uploading ${students.length} students to database...`);
    
    const results = {
      successful: 0,
      failed: 0,
      errors: []
    };
    
    for (const student of students) {
      if (student.error) {
        console.log(`⏭️  Skipping ${student.email} - contains error data`);
        continue;
      }

      console.log(`🔄 Uploading ${student.email}...`);
      const result = await uploadToSupabase(student);
      
      if (result.success) {
        console.log(`✅ Successfully uploaded ${student.email}`);
        results.successful++;
      } else {
        console.log(`❌ Failed to upload ${student.email}:`, result.error);
        results.failed++;
        results.errors.push({
          email: student.email,
          error: result.error
        });
      }
      
      // Small delay to prevent rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log(`\n📊 UPLOAD RESULTS:`);
    console.log(`✅ Successfully uploaded: ${results.successful} students`);
    console.log(`❌ Failed to upload: ${results.failed} students`);
    
    if (results.errors.length > 0) {
      console.log(`\n❌ Upload errors:`);
      results.errors.forEach(err => {
        console.log(`   - ${err.email}: ${err.error}`);
      });
    }
    
  } catch (error) {
    console.log('💥 Upload process failed:', error.message);
  }
}

uploadAllData(); 