const { chromium } = require('playwright');
require('dotenv').config();

async function debugAvailableStudents() {
  const loginEmail = process.env.ALPHAREAD_EMAIL;
  const loginPassword = process.env.ALPHAREAD_PASSWORD;
  
  if (!loginEmail || !loginPassword || loginEmail === 'your.email@example.com') {
    console.log('❌ Please configure your login credentials in .env file');
    return;
  }
  
  console.log('🕵️ Debugging available students in your guide account...');
  
  const browser = await chromium.launch({ 
    headless: false, // Show browser to see what's happening
    slowMo: 1000
  });
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });
    
    const page = await context.newPage();
    
    // Login
    console.log('🔐 Logging in...');
    await page.goto('https://alpharead.alpha.school/signin');
    await page.waitForSelector('input[type="email"][placeholder="you@example.com"]');
    await page.fill('input[type="email"][placeholder="you@example.com"]', loginEmail);
    await page.fill('input[type="password"][placeholder="Password"]', loginPassword);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Navigate to student management
    console.log('🎯 Navigating to Student Management...');
    const guideDashboardLink = await page.$('a[href="/guide"]:has-text("Guide Dashboard")');
    if (guideDashboardLink) {
      await guideDashboardLink.click();
      await page.waitForTimeout(3000);
      
      const studentManagementLink = await page.$('a[href="/guide/students"]');
      if (studentManagementLink) {
        await studentManagementLink.click();
        await page.waitForTimeout(3000);
        console.log('✅ Reached Student Management page');
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'debug-students-page.png', fullPage: true });
    console.log('📸 Screenshot saved: debug-students-page.png');
    
    // Extract all available students
    console.log('\n🔍 Extracting all available students...');
    
    const studentsData = await page.evaluate(() => {
      const results = {
        totalRows: 0,
        students: [],
        tableHeaders: [],
        pageInfo: {
          url: window.location.href,
          title: document.title
        }
      };
      
      // Get table headers
      const headers = Array.from(document.querySelectorAll('th')).map(th => th.textContent.trim());
      results.tableHeaders = headers;
      
      // Get all table rows
      const rows = Array.from(document.querySelectorAll('tbody tr'));
      results.totalRows = rows.length;
      
      // Extract student data from each row
      rows.forEach((row, index) => {
        const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
        const detailsLink = row.querySelector('a[href*="/guide/students/"]');
        
        if (cells.length > 0) {
          results.students.push({
            rowIndex: index + 1,
            email: cells[0] || 'No email found',
            grade: cells[1] || 'No grade',
            readingGrade: cells[2] || 'No reading grade',
            hasManualEnrollment: cells[3] || 'No enrollment info',
            currentCourse: cells[4] || 'No course',
            remainingItems: cells[5] || 'No remaining items',
            detailsHref: detailsLink ? detailsLink.href : null,
            allCells: cells
          });
        }
      });
      
      return results;
    });
    
    console.log('\n📊 AVAILABLE STUDENTS ANALYSIS:');
    console.log('================================');
    console.log(`📋 Total students found: ${studentsData.students.length}`);
    console.log(`📊 Table headers: ${studentsData.tableHeaders.join(' | ')}`);
    console.log(`🌐 Current URL: ${studentsData.pageInfo.url}`);
    
    if (studentsData.students.length > 0) {
      console.log('\n👥 First 10 students in your account:');
      studentsData.students.slice(0, 10).forEach((student, index) => {
        console.log(`${index + 1}. Student ${index + 1} (Grade: ${student.grade}, Course: ${student.currentCourse})`);
      });
      
      if (studentsData.students.length > 10) {
        console.log(`\n... and ${studentsData.students.length - 10} more students`);
      }
      
      // Check if the target email exists
      const targetEmail = 'keyen.gupta@2hourlearning.com';
      const foundStudent = studentsData.students.find(student => 
        student.email.toLowerCase().includes(targetEmail.toLowerCase()) ||
        targetEmail.toLowerCase().includes(student.email.toLowerCase())
      );
      
      if (foundStudent) {
      console.log(`\n✅ Found your target student`);
      console.log(`   Details: Grade ${foundStudent.grade}, Course: ${foundStudent.currentCourse}`);
      } else {
        console.log(`\n❌ Target student not found in this page`);
        console.log('\n🔍 Similar emails found:');
        const similarEmails = studentsData.students.filter(student => 
          student.email.includes('keyen') || 
          student.email.includes('gupta') ||
          student.email.includes('2hourlearning')
        );
        
        if (similarEmails.length > 0) {
          console.log(`   - Found ${similarEmails.length} students with similar details`);
        } else {
          console.log('   - No similar emails found');
        }
      }
      
      // Save all students to file for reference
      const fs = require('fs');
      fs.writeFileSync('available-students.json', JSON.stringify(studentsData, null, 2));
      console.log('\n💾 Full student list saved to: available-students.json');
      
    } else {
      console.log('\n⚠️  No students found on this page');
    }
    
    // Check for pagination
    const paginationInfo = await page.evaluate(() => {
      const pagination = {
        hasPagination: false,
        currentPage: null,
        totalPages: null,
        nextButton: null,
        prevButton: null
      };
      
      // Look for pagination elements
      const paginationElements = document.querySelectorAll('[class*="pagination"], [class*="page"], [aria-label*="page"]');
      if (paginationElements.length > 0) {
        pagination.hasPagination = true;
      }
      
      // Look for page numbers
      const pageNumbers = Array.from(document.querySelectorAll('button, a')).filter(el => 
        /^\d+$/.test(el.textContent.trim())
      );
      
      if (pageNumbers.length > 0) {
        pagination.hasPagination = true;
        pagination.totalPages = pageNumbers.length;
      }
      
      // Look for next/prev buttons
      const nextBtn = document.querySelector('button:has-text("Next"), a:has-text("Next"), [aria-label*="next"]');
      const prevBtn = document.querySelector('button:has-text("Previous"), a:has-text("Previous"), [aria-label*="previous"]');
      
      pagination.nextButton = nextBtn ? nextBtn.textContent.trim() : null;
      pagination.prevButton = prevBtn ? prevBtn.textContent.trim() : null;
      
      return pagination;
    });
    
    if (paginationInfo.hasPagination) {
      console.log('\n📄 PAGINATION DETECTED:');
      console.log(`   - Current page: ${paginationInfo.currentPage || 'Unknown'}`);
      console.log(`   - Total pages: ${paginationInfo.totalPages || 'Unknown'}`);
      console.log(`   - Next button: ${paginationInfo.nextButton || 'None'}`);
      console.log(`   - Previous button: ${paginationInfo.prevButton || 'None'}`);
      console.log('\n💡 Your target student might be on a different page!');
    }
    
  } catch (error) {
    console.error('💥 Debug failed:', error.message);
  } finally {
    console.log('\n🏁 Debug complete. Check the browser window and available-students.json file.');
    console.log('Press Ctrl+C to close browser when done reviewing.');
    
    // Keep browser open for manual inspection
    await new Promise(resolve => {
      process.on('SIGINT', () => {
        console.log('\n👋 Closing browser...');
        browser.close().then(resolve);
      });
    });
  }
}

if (require.main === module) {
  debugAvailableStudents()
    .then(() => console.log('🧪 Debug completed'))
    .catch(error => console.error('💥 Debug failed:', error));
}

module.exports = { debugAvailableStudents }; 