const fs = require('fs');
const path = require('path');
const { uploadBatchToSupabase } = require('./multi-email-scraper');
require('dotenv').config();

async function uploadExistingData() {
  console.log('🔍 Looking for existing student data files...');
  
  // Get command line argument for specific file, or find the most recent one
  const targetFile = process.argv[2];
  
  let jsonFile;
  if (targetFile) {
    if (fs.existsSync(targetFile)) {
      jsonFile = targetFile;
      console.log(`📁 Using specified file: ${jsonFile}`);
    } else {
      console.log(`❌ File not found: ${targetFile}`);
      return;
    }
  } else {
    // Find the most recent student-data-*.json file
    const files = fs.readdirSync('.')
      .filter(file => file.startsWith('student-data-') && file.endsWith('.json'))
      .sort()
      .reverse(); // Most recent first
    
    if (files.length === 0) {
      console.log('❌ No student data files found');
      console.log('💡 Student data files should match pattern: student-data-*.json');
      return;
    }
    
    jsonFile = files[0];
    console.log(`📁 Using most recent file: ${jsonFile}`);
    
    if (files.length > 1) {
      console.log(`🗂️  Other available files:`);
      files.slice(1, 5).forEach(file => console.log(`   - ${file}`));
      if (files.length > 5) {
        console.log(`   ... and ${files.length - 5} more`);
      }
      console.log(`💡 To upload a specific file: npm run upload-existing filename.json`);
    }
  }
  
  try {
    console.log(`📖 Reading data from: ${jsonFile}`);
    const content = fs.readFileSync(jsonFile, 'utf-8');
    const data = JSON.parse(content);
    
    if (!data.students || !Array.isArray(data.students)) {
      console.log('❌ Invalid data format. Expected {students: [...]}');
      return;
    }
    
    console.log(`📊 Found ${data.students.length} students in file`);
    console.log(`📅 Original scrape date: ${data.scrapedAt}`);
    
    // Filter out students with errors
    const validStudents = data.students.filter(student => !student.error);
    const errorStudents = data.students.filter(student => student.error);
    
    console.log(`✅ Valid students: ${validStudents.length}`);
    if (errorStudents.length > 0) {
      console.log(`⚠️  Students with errors (will be skipped): ${errorStudents.length}`);
      errorStudents.forEach(student => {
        console.log(`   - ${student.email}: ${student.error}`);
      });
    }
    
    if (validStudents.length === 0) {
      console.log('❌ No valid students to upload');
      return;
    }
    
    // Upload to Supabase
    console.log(`\n🚀 Starting upload to Supabase...`);
    const uploadResults = await uploadBatchToSupabase(validStudents);
    
    console.log(`\n🎉 Upload completed!`);
    console.log(`📊 Summary:`);
    console.log(`   - Total students in file: ${data.students.length}`);
    console.log(`   - Valid students: ${validStudents.length}`);
    console.log(`   - Successfully uploaded: ${uploadResults.successful}`);
    console.log(`   - Failed uploads: ${uploadResults.failed}`);
    
    if (uploadResults.errors && uploadResults.errors.length > 0) {
      console.log(`\n❌ Upload errors:`);
      uploadResults.errors.forEach(err => {
        console.log(`   - ${err.email}: ${err.error}`);
      });
    }
    
  } catch (error) {
    console.error('💥 Upload failed:', error.message);
    
    if (error.message.includes('JSON')) {
      console.log('💡 Make sure the file contains valid JSON data');
    } else if (error.message.includes('ENOENT')) {
      console.log('💡 Make sure the file exists and the path is correct');
    } else if (error.message.includes('Supabase')) {
      console.log('💡 Check your Supabase credentials in .env file');
    }
  }
}

// Show usage if requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
📚 Upload Existing Data to Supabase

Usage:
  npm run upload-existing                    # Upload most recent file
  npm run upload-existing filename.json     # Upload specific file
  npm run upload-existing -- --help         # Show this help

Description:
  This script uploads student data from existing JSON files to your Supabase database.
  It will automatically find the most recent student-data-*.json file, or you can 
  specify a particular file to upload.

Requirements:
  - Supabase credentials configured in .env file
  - ENABLE_DATABASE_UPLOAD=true in .env file
  - Valid student data JSON file

Examples:
  npm run upload-existing
  npm run upload-existing student-data-07-06-2025-09-28-43.769CT.json
`);
  process.exit(0);
}

if (require.main === module) {
  uploadExistingData()
    .then(() => console.log('✅ Upload script completed'))
    .catch(error => console.error('💥 Upload script failed:', error));
}

module.exports = { uploadExistingData }; 