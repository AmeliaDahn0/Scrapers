const { chromium } = require('playwright');
require('dotenv').config();

async function testNavigation() {
  const email = process.env.ALPHAREAD_EMAIL;
  const password = process.env.ALPHAREAD_PASSWORD;
  
  if (!email || !password || email === 'your.email@example.com') {
    console.log('❌ Please configure your credentials in .env file first');
    return;
  }
  
  console.log('🧭 Testing Alpha Read navigation to Student Management...');
  
  const browser = await chromium.launch({ 
    headless: false, // Show browser for navigation testing
    slowMo: 2000 // Slow for observation
  });
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });
    
    const page = await context.newPage();
    
    // Step 1: Navigate and login
    console.log('🌐 Step 1: Navigating to Alpha Read sign-in page...');
    await page.goto('https://alpharead.alpha.school/signin', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    // Quick login
    console.log('🔐 Step 2: Logging in...');
    await page.waitForSelector('input[type="email"][placeholder="you@example.com"]');
    await page.fill('input[type="email"][placeholder="you@example.com"]', email);
    await page.fill('input[type="password"][placeholder="Password"]', password);
    await page.click('button[type="submit"]');
    
    // Wait for successful login
    await page.waitForURL('**', { timeout: 15000 });
    const currentUrl = page.url();
    if (!currentUrl.includes('/signin')) {
      console.log('✅ Step 2 Complete: Login successful');
    } else {
      console.log('⚠️ Still on signin page, but continuing...');
    }
    
    // Step 3: Navigate to Guide Dashboard
    console.log('🎯 Step 3: Looking for Guide Dashboard...');
    await page.waitForTimeout(2000);
    
    // Take screenshot of dashboard
    await page.screenshot({ path: 'step3-after-login.png' });
    
    // Examine available navigation options
    const allNavElements = await page.$$eval('a, button', elements => 
      elements.map(el => ({
        text: el.textContent.trim(),
        href: el.href || null,
        tag: el.tagName.toLowerCase(),
        classes: el.className
      })).filter(item => item.text && item.text.length > 0)
    );
    
    console.log('🔍 All available navigation elements:');
    allNavElements.forEach((el, index) => {
      console.log(`  ${index + 1}. ${el.tag.toUpperCase()}: "${el.text}" ${el.href ? '-> ' + el.href : ''}`);
    });
    
    // Look specifically for Guide Dashboard using exact selector
    const guideDashboardLink = await page.$('a[href="/guide"]:has-text("Guide Dashboard")');
    
    if (guideDashboardLink) {
      console.log('✅ Found Guide Dashboard link');
      
      // Click on Guide Dashboard
      await guideDashboardLink.click();
      
      console.log('👆 Clicked Guide Dashboard');
      await page.waitForTimeout(3000);
      
      // Take screenshot of guide dashboard
      await page.screenshot({ path: 'step4-guide-dashboard.png' });
      
      // Step 4: Look for Student Management
      console.log('👥 Step 4: Looking for Student Management...');
      
      const dashboardElements = await page.$$eval('a, button, div[role="button"]', elements => 
        elements.map(el => ({
          text: el.textContent.trim(),
          href: el.href || null,
          tag: el.tagName.toLowerCase(),
          classes: el.className
        })).filter(item => item.text && item.text.length > 0)
      );
      
      console.log('🔍 Elements on Guide Dashboard:');
      dashboardElements.forEach((el, index) => {
        console.log(`  ${index + 1}. ${el.tag.toUpperCase()}: "${el.text}" ${el.href ? '-> ' + el.href : ''}`);
      });
      
      // Look for student management related elements
      const studentElements = dashboardElements.filter(el => 
        el.text.toLowerCase().includes('student') || 
        el.text.toLowerCase().includes('manage') ||
        el.text.toLowerCase().includes('view')
      );
      
      if (studentElements.length > 0) {
        console.log('👥 Found potential student management elements:');
        studentElements.forEach((el, index) => {
          console.log(`  ${index + 1}. ${el.tag.toUpperCase()}: "${el.text}" ${el.href ? '-> ' + el.href : ''}`);
        });
        
        // Try to click the most likely candidate
        const bestMatch = studentElements.find(el => 
          el.text.toLowerCase().includes('view') && el.text.toLowerCase().includes('student')
        ) || studentElements[0];
        
        console.log(`🎯 Attempting to click: "${bestMatch.text}"`);
        
        if (bestMatch.href) {
          await page.goto(bestMatch.href);
        } else {
          await page.click(`${bestMatch.tag}:has-text("${bestMatch.text}")`);
        }
        
        await page.waitForTimeout(3000);
        console.log('✅ Step 4 Complete: Navigated to student section');
        
        // Take final screenshot
        await page.screenshot({ path: 'step5-student-management.png' });
        
      } else {
        console.log('❌ No student management elements found');
      }
      
    } else {
      console.log('❌ Guide Dashboard not found in available navigation');
    }
    
    console.log(`🎉 Final URL: ${page.url()}`);
    
  } catch (error) {
    console.error('💥 Navigation test failed:', error.message);
  } finally {
    console.log('🏁 Closing browser in 5 seconds...');
    try {
      await page.waitForTimeout(5000);
      await browser.close();
    } catch (closeError) {
      console.log('Browser already closed');
    }
  }
}

if (require.main === module) {
  testNavigation()
    .then(() => console.log('🧭 Navigation test completed'))
    .catch(error => console.error('💥 Navigation test failed:', error));
}

module.exports = { testNavigation }; 