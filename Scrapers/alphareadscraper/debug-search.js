const { chromium } = require('playwright');
require('dotenv').config();

async function debugSearch() {
  const loginEmail = process.env.ALPHAREAD_EMAIL;
  const loginPassword = process.env.ALPHAREAD_PASSWORD;
  
  if (!loginEmail || !loginPassword || loginEmail === 'your.email@example.com') {
    console.log('❌ Please configure your login credentials in .env file');
    return;
  }
  
  console.log('🕵️ Debugging search functionality...');
  
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
    
    // Take screenshot of the page
    await page.screenshot({ path: 'debug-search-initial.png', fullPage: true });
    console.log('📸 Screenshot saved: debug-search-initial.png');
    
    // Debug search field detection
    console.log('\n🔍 Analyzing search elements...');
    
    const searchAnalysis = await page.evaluate(() => {
      const results = {
        allInputs: [],
        searchInputs: [],
        searchButtons: [],
        possibleSearchElements: []
      };
      
      // Find all input elements
      const inputs = document.querySelectorAll('input');
      inputs.forEach((input, index) => {
        results.allInputs.push({
          index: index + 1,
          type: input.type,
          placeholder: input.placeholder,
          name: input.name,
          id: input.id,
          className: input.className,
          value: input.value
        });
      });
      
      // Find potential search inputs
      const searchSelectors = [
        'input[type="search"]',
        'input[placeholder*="Search"]',
        'input[placeholder*="search"]',
        'input[name*="search"]',
        'input[name*="Search"]',
        'input[id*="search"]',
        'input[id*="Search"]',
        'input[class*="search"]',
        'input[class*="Search"]'
      ];
      
      searchSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          results.searchInputs.push({
            selector: selector,
            placeholder: element.placeholder,
            name: element.name,
            id: element.id,
            className: element.className,
            visible: element.offsetParent !== null
          });
        });
      });
      
      // Find search buttons
      const buttons = document.querySelectorAll('button');
      buttons.forEach(button => {
        const text = button.textContent.trim().toLowerCase();
        if (text.includes('search') || text.includes('find')) {
          results.searchButtons.push({
            text: button.textContent.trim(),
            className: button.className,
            visible: button.offsetParent !== null
          });
        }
      });
      
      // Look for any element that might be search-related
      const allElements = document.querySelectorAll('*');
      allElements.forEach(element => {
        const text = element.textContent.trim().toLowerCase();
        const tagName = element.tagName.toLowerCase();
        
        if ((tagName === 'input' || tagName === 'button') && 
            (text.includes('search') || 
             element.placeholder?.toLowerCase().includes('search') ||
             element.className?.toLowerCase().includes('search'))) {
          results.possibleSearchElements.push({
            tagName: tagName,
            text: text.substring(0, 50),
            placeholder: element.placeholder,
            className: element.className,
            id: element.id,
            name: element.name
          });
        }
      });
      
      return results;
    });
    
    console.log('\n📊 SEARCH ANALYSIS:');
    console.log('==================');
    
    console.log(`\n📝 Found ${searchAnalysis.allInputs.length} total input elements:`);
    searchAnalysis.allInputs.forEach(input => {
      console.log(`  Input ${input.index}: type="${input.type}", placeholder="${input.placeholder}", name="${input.name}", class="${input.className}"`);
    });
    
    console.log(`\n🔍 Found ${searchAnalysis.searchInputs.length} potential search inputs:`);
    searchAnalysis.searchInputs.forEach(input => {
      console.log(`  - Selector: ${input.selector}`);
      console.log(`    Placeholder: "${input.placeholder}"`);
      console.log(`    Name: "${input.name}"`);
      console.log(`    Class: "${input.className}"`);
      console.log(`    Visible: ${input.visible}`);
      console.log('');
    });
    
    console.log(`\n🔘 Found ${searchAnalysis.searchButtons.length} search buttons:`);
    searchAnalysis.searchButtons.forEach(button => {
      console.log(`  - Text: "${button.text}"`);
      console.log(`    Class: "${button.className}"`);
      console.log(`    Visible: ${button.visible}`);
      console.log('');
    });
    
    console.log(`\n🎯 All possible search elements:`);
    searchAnalysis.possibleSearchElements.forEach(element => {
      console.log(`  - ${element.tagName}: "${element.text}"`);
      console.log(`    Placeholder: "${element.placeholder}"`);
      console.log(`    Class: "${element.className}"`);
      console.log('');
    });
    
    // Try to test search functionality
    console.log('\n🧪 Testing search functionality...');
    
    // Try different search selectors
    const testSelectors = [
      'input[type="search"]',
      'input[placeholder*="Search"]',
      'input[placeholder*="search"]',
      'input[name*="search"]',
      'input[class*="search"]',
      'input' // Try the first input if others fail
    ];
    
    let searchWorked = false;
    
    for (const selector of testSelectors) {
      try {
        console.log(`\n🔍 Testing selector: ${selector}`);
        const searchInput = await page.$(selector);
        
        if (searchInput) {
          console.log(`✅ Found search input with selector: ${selector}`);
          
          // Test with actual emails from emails.txt
          const testEmails = [
            'keyen.gupta@2hourlearning.com',
            'olivia.attia@2hourlearning.com', 
            'layla.kelch@alpha.school'
          ];
          
          for (const testEmail of testEmails) {
            console.log(`🧪 Testing search with: ${testEmail}`);
            
            await searchInput.click();
            await searchInput.fill('');
            await page.waitForTimeout(500);
            await searchInput.type(testEmail);
            await page.waitForTimeout(3000); // Wait for results
            
            // Take screenshot after search
            await page.screenshot({ path: `debug-search-${testEmail.replace(/[^a-zA-Z0-9]/g, '_')}.png`, fullPage: true });
            console.log(`📸 Screenshot saved: debug-search-${testEmail.replace(/[^a-zA-Z0-9]/g, '_')}.png`);
            
            // Check if results changed
            const resultsFound = await page.evaluate((email) => {
              const pageText = document.body.textContent;
              const hasEmail = pageText.includes(email);
              
              // Count visible Details buttons (fix the selector)
              const allLinks = Array.from(document.querySelectorAll('a[href*="/guide/students/"]'));
              const detailsButtons = allLinks.filter(link => 
                link.textContent.trim().toLowerCase().includes('details')
              );
              
              return {
                hasEmail: hasEmail,
                detailsButtonCount: detailsButtons.length,
                firstTableRow: document.querySelector('tbody tr')?.textContent?.trim() || 'No table rows found',
                totalTableRows: document.querySelectorAll('tbody tr').length
              };
            }, testEmail);
            
            console.log(`📊 Search results for ${testEmail}:`);
            console.log(`  - Email found in page: ${resultsFound.hasEmail}`);
            console.log(`  - Details buttons visible: ${resultsFound.detailsButtonCount}`);
            console.log(`  - Total table rows: ${resultsFound.totalTableRows}`);
            console.log(`  - First table row: ${resultsFound.firstTableRow}`);
            
            if (resultsFound.hasEmail && resultsFound.detailsButtonCount > 0) {
              console.log(`✅ Search found student: ${testEmail}`);
              searchWorked = true;
            } else {
              console.log(`❌ Student not found: ${testEmail}`);
            }
            
            // Clear search to reset
            await searchInput.fill('');
            await page.waitForTimeout(2000);
          }
          
          break;
        } else {
          console.log(`❌ No element found with selector: ${selector}`);
        }
      } catch (error) {
        console.log(`❌ Error testing selector ${selector}:`, error.message);
      }
    }
    
    if (!searchWorked) {
      console.log('\n❌ Search functionality not working with any tested method');
      console.log('💡 The search might:');
      console.log('   - Require a specific trigger (Enter key, button click)');
      console.log('   - Be implemented with JavaScript that we need to wait for');
      console.log('   - Use a different mechanism (dropdown, autocomplete, etc.)');
    }
    
    // Wait for manual inspection
    console.log('\n⏸️ Pausing for 15 seconds for manual inspection...');
    await page.waitForTimeout(15000);
    
  } catch (error) {
    console.error('💥 Debug failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  debugSearch()
    .then(() => console.log('🕵️ Debug completed'))
    .catch(error => console.error('💥 Debug failed:', error));
}

module.exports = { debugSearch }; 