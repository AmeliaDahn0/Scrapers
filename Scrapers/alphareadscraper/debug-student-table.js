const { chromium } = require('playwright');
require('dotenv').config();

async function debugStudentTable() {
  const loginEmail = process.env.ALPHAREAD_EMAIL;
  const loginPassword = process.env.ALPHAREAD_PASSWORD;
  
  if (!loginEmail || !loginPassword || loginEmail === 'your.email@example.com') {
    console.log('❌ Please configure your login credentials in .env file');
    return;
  }
  
  console.log('🕵️ Debugging student table structure...');
  
  const browser = await chromium.launch({ 
    headless: false, // Show browser to see what's happening
    slowMo: 2000
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
    
    // Debug the table structure
    const tableData = await page.evaluate(() => {
      const results = {
        allText: document.body.textContent.substring(0, 2000),
        tableInfo: [],
        detailsButtons: [],
        allEmails: []
      };
      
      // Find all emails on the page
      const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
      const pageText = document.body.textContent;
      results.allEmails = pageText.match(emailRegex) || [];
      
      // Analyze table structure
      const tables = document.querySelectorAll('table');
      tables.forEach((table, tableIndex) => {
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
        const rows = Array.from(table.querySelectorAll('tbody tr, tr')).slice(0, 3); // First 3 rows only
        
        const tableInfo = {
          tableIndex: tableIndex + 1,
          headers: headers,
          sampleRows: rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim());
            return cells;
          })
        };
        
        results.tableInfo.push(tableInfo);
      });
      
      // Find Details buttons and their context
      const allLinks = Array.from(document.querySelectorAll('a[href*="/guide/students/"]'));
      const detailsButtons = allLinks.filter(link => 
        link.textContent.trim().toLowerCase().includes('details')
      );
      
      detailsButtons.slice(0, 5).forEach((button, index) => { // First 5 only
        const row = button.closest('tr');
        const rowData = row ? Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim()) : [];
        
        results.detailsButtons.push({
          index: index + 1,
          href: button.href,
          rowData: rowData,
          previousSibling: button.previousElementSibling?.textContent?.trim() || null,
          nextSibling: button.nextElementSibling?.textContent?.trim() || null
        });
      });
      
      return results;
    });
    
    console.log('\n📊 TABLE ANALYSIS:');
    console.log('==================');
    
    console.log(`\n📧 Found ${tableData.allEmails.length} emails on page:`);
    tableData.allEmails.slice(0, 10).forEach(email => console.log(`  - ${email}`));
    if (tableData.allEmails.length > 10) {
      console.log(`  ... and ${tableData.allEmails.length - 10} more`);
    }
    
    console.log(`\n📋 Found ${tableData.tableInfo.length} tables:`);
    tableData.tableInfo.forEach(table => {
      console.log(`\nTable ${table.tableIndex}:`);
      console.log(`  Headers: [${table.headers.join(', ')}]`);
      console.log(`  Sample rows:`);
      table.sampleRows.forEach((row, index) => {
        console.log(`    Row ${index + 1}: [${row.join(' | ')}]`);
      });
    });
    
    console.log(`\n🔗 Found ${tableData.detailsButtons.length} Details buttons:`);
    tableData.detailsButtons.forEach(button => {
      console.log(`\nButton ${button.index}:`);
      console.log(`  Href: ${button.href}`);
      console.log(`  Row data: [${button.rowData.join(' | ')}]`);
    });
    
    // Wait to observe
    console.log('\n⏸️ Pausing for 10 seconds to observe...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('💥 Debug failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  debugStudentTable()
    .then(() => console.log('🕵️ Debug completed'))
    .catch(error => console.error('💥 Debug failed:', error));
}

module.exports = { debugStudentTable }; 