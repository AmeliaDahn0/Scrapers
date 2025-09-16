const { scrapeMultipleStudents } = require('./multi-email-scraper');
require('dotenv').config();

async function testParsingFix() {
  console.log('🧪 Testing parsing fix for Last Active field...');
  console.log('This will scrape one student to verify the parsing is working correctly.');
  
  // Create a temporary test email file with just Sloka's email
  const fs = require('fs');
  const originalEmails = fs.readFileSync('emails.txt', 'utf-8');
  
  // Backup original emails
  fs.writeFileSync('emails.txt.backup', originalEmails);
  
  // Write test email
  fs.writeFileSync('emails.txt', 'sloka.vudumu@2hourlearning.com\n');
  
  console.log('📧 Testing with Sloka Vudumu\'s email only...');
  console.log('Expected Last Active: Jun 2 (from Alpha Read profile)');
  
  try {
    const results = await scrapeMultipleStudents();
    
    if (results && results.length > 0) {
      const sloka = results[0];
      console.log('\n📊 PARSING TEST RESULTS:');
      console.log('========================');
      console.log(`Test student configured`);
      console.log(`Last Active (parsed): ${sloka.profile?.lastActive}`);
      console.log(`Grade Level: ${sloka.profile?.gradeLevel}`);
      console.log(`Reading Level: ${sloka.profile?.readingLevel}`);
      console.log(`Time Reading: ${sloka.profile?.timeReading}`);
      console.log(`Success Rate: ${sloka.profile?.successRate}`);
      
      // Check if parsing is correct
      if (sloka.profile?.lastActive === 'Jun 2') {
        console.log('\n✅ SUCCESS: Last Active parsed correctly as "Jun 2"');
      } else {
        console.log(`\n❌ ISSUE: Last Active parsed as "${sloka.profile?.lastActive}" but should be "Jun 2"`);
        console.log('💡 The DOM structure might be different than expected.');
      }
      
    } else {
      console.log('❌ No results returned from scraping');
    }
    
  } catch (error) {
    console.error('💥 Test failed:', error.message);
  } finally {
    // Restore original emails
    fs.writeFileSync('emails.txt', originalEmails);
    fs.unlinkSync('emails.txt.backup');
    console.log('\n🔄 Restored original emails.txt file');
  }
}

async function testExistingData() {
  console.log('\n🔍 Analyzing existing data for comparison...');
  
  try {
    const fs = require('fs');
    const files = fs.readdirSync('.')
      .filter(file => file.startsWith('student-data-') && file.endsWith('.json'))
      .sort()
      .reverse();
    
    if (files.length === 0) {
      console.log('No existing data files found');
      return;
    }
    
    const latestFile = files[0];
    console.log(`📁 Reading from: ${latestFile}`);
    
    const content = fs.readFileSync(latestFile, 'utf-8');
    const data = JSON.parse(content);
    
    const sloka = data.students.find(s => s.email === 'sloka.vudumu@2hourlearning.com');
    
    if (sloka) {
      console.log('\n📊 EXISTING DATA ANALYSIS:');
      console.log('==========================');
      console.log(`Test student configured`);
      console.log(`Last Active (existing): ${sloka.profile?.lastActive}`);
      console.log(`Scraped At: ${sloka.scrapedAt}`);
      
      if (sloka.profile?.lastActive === 'Jun 3') {
        console.log('⚠️  This confirms the old parsing issue (shows Jun 3 instead of Jun 2)');
      } else if (sloka.profile?.lastActive === 'Jun 2') {
        console.log('✅ Data already shows correct value (Jun 2)');
      } else {
        console.log(`❓ Unexpected value: ${sloka.profile?.lastActive}`);
      }
    } else {
      console.log('❌ Sloka not found in existing data');
    }
    
  } catch (error) {
    console.log('❌ Error reading existing data:', error.message);
  }
}

if (require.main === module) {
  // Show usage instructions
  console.log(`
🧪 PARSING FIX TEST SCRIPT

This script helps verify that the Last Active parsing fix is working correctly.

Choose an option:
1. Run: node test-parsing-fix.js test    # Test with fresh scraping
2. Run: node test-parsing-fix.js analyze # Analyze existing data only

The test will:
- Temporarily modify emails.txt to test only Sloka's email
- Run the scraper with debug output
- Compare results with expected value (Jun 2)
- Restore your original emails.txt file
`);

  const mode = process.argv[2];
  
  if (mode === 'test') {
    testParsingFix()
      .then(() => console.log('🏁 Parsing test completed'))
      .catch(error => console.error('💥 Test failed:', error));
  } else if (mode === 'analyze') {
    testExistingData()
      .then(() => console.log('🏁 Analysis completed'))
      .catch(error => console.error('💥 Analysis failed:', error));
  } else {
    console.log('Usage: node test-parsing-fix.js [test|analyze]');
  }
}

module.exports = { testParsingFix, testExistingData }; 