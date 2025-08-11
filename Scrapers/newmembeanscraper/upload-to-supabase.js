const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Supabase configuration
// You'll need to add these to your .env file:
// SUPABASE_URL=your_supabase_project_url
// SUPABASE_ANON_KEY=your_supabase_anon_key

require('dotenv').config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Missing Supabase configuration in .env file');
    console.error('Please add:');
    console.error('SUPABASE_URL=your_supabase_project_url');
    console.error('SUPABASE_ANON_KEY=your_supabase_anon_key');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function uploadStudentData(fileName) {
    try {
        console.log(`📊 Reading data from ${fileName}...`);
        
        // Read the JSON file
        const filePath = path.join(__dirname, fileName);
        if (!fs.existsSync(filePath)) {
            throw new Error(`File not found: ${fileName}`);
        }
        
        const rawData = fs.readFileSync(filePath, 'utf8');
        const data = JSON.parse(rawData);
        
        if (!data.studentsData || !Array.isArray(data.studentsData)) {
            throw new Error('Invalid data format: studentsData array not found');
        }
        
        console.log(`📈 Found ${data.studentsData.length} students to upload...`);
        
        // Transform data for Supabase
        const supabaseData = data.studentsData
            .filter(student => student.studentName && !student.error) // Only upload successful students
            .map(student => ({
                url: student.url,
                timestamp: student.timestamp,
                student_name: student.studentName,
                recent_training: student.recentTraining || []
            }));
        
        console.log(`✅ Prepared ${supabaseData.length} valid student records`);
        
        if (supabaseData.length === 0) {
            console.log('⚠️  No valid student data to upload');
            return;
        }
        
        // Upload to Supabase
        console.log('🚀 Uploading to Supabase...');
        
        const { data: result, error } = await supabase
            .from('membean_students')
            .insert(supabaseData);
        
        if (error) {
            throw error;
        }
        
        console.log('✅ Successfully uploaded student data to Supabase!');
        console.log(`📊 Uploaded ${supabaseData.length} student records`);
        
        // Show summary
        const sessionCounts = supabaseData.map(s => s.recent_training.length);
        const totalSessions = sessionCounts.reduce((sum, count) => sum + count, 0);
        
        console.log(`\\n📈 Upload Summary:`);
        console.log(`- Students: ${supabaseData.length}`);
        console.log(`- Total training sessions: ${totalSessions}`);
        console.log(`- Average sessions per student: ${(totalSessions / supabaseData.length).toFixed(1)}`);
        
    } catch (error) {
        console.error('❌ Upload failed:', error.message);
        if (error.details) {
            console.error('Details:', error.details);
        }
        if (error.hint) {
            console.error('Hint:', error.hint);
        }
        process.exit(1);
    }
}

// Get the most recent data file if no filename provided
function getMostRecentDataFile() {
    const files = fs.readdirSync(__dirname)
        .filter(file => file.startsWith('students-data-') && file.endsWith('.json'))
        .sort()
        .reverse();
    
    return files[0];
}

// Main execution
if (require.main === module) {
    const fileName = process.argv[2] || getMostRecentDataFile();
    
    if (!fileName) {
        console.error('❌ No data files found');
        console.error('Usage: node upload-to-supabase.js [filename.json]');
        console.error('Or run the scraper first to generate data files');
        process.exit(1);
    }
    
    console.log(`🔄 Uploading data from: ${fileName}`);
    uploadStudentData(fileName);
}

module.exports = { uploadStudentData };