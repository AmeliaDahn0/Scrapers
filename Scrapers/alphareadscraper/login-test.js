const { chromium } = require('playwright');
require('dotenv').config();

async function testLogin() {
  const email = process.env.ALPHAREAD_EMAIL;
  const password = process.env.ALPHAREAD_PASSWORD;
  
  if (!email || !password || email === 'your.email@example.com') {
    console.log('❌ Please configure your credentials in .env file first');
    console.log('Set ALPHAREAD_EMAIL and ALPHAREAD_PASSWORD with your actual Alpha Read credentials');
    return;
  }
  
  console.log('🧪 Testing Alpha Read login functionality...');
  
  const browser = await chromium.launch({ 
    headless: false, // Always show browser for login testing
    slowMo: 2000 // Slower for observation
  });
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });
    
    const page = await context.newPage();
    
    console.log('🌐 Navigating to Alpha Read sign-in page...');
    await page.goto('https://alpharead.alpha.school/signin', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    console.log('📄 Page loaded, analyzing form structure...');
    
    // Check if the form elements are present
    const formExists = await page.$('form');
    console.log(`📋 Form found: ${formExists ? '✅' : '❌'}`);
    
    const emailField = await page.$('input[type="email"][placeholder="you@example.com"]');
    console.log(`📧 Email field found: ${emailField ? '✅' : '❌'}`);
    
    const passwordField = await page.$('input[type="password"][placeholder="Password"]');
    console.log(`🔑 Password field found: ${passwordField ? '✅' : '❌'}`);
    
    const submitButton = await page.$('button[type="submit"]');
    console.log(`🚀 Submit button found: ${submitButton ? '✅' : '❌'}`);
    
    if (!emailField || !passwordField || !submitButton) {
      console.log('❌ Required form elements not found. Page structure may have changed.');
      return;
    }
    
    console.log('🔐 Attempting login...');
    
    // Fill email
    await emailField.click();
    await emailField.fill('');
    await emailField.fill(email);
    console.log('📧 Email filled');
    
    // Fill password
    await passwordField.click();
    await passwordField.fill('');
    await passwordField.fill(password);
    console.log('🔑 Password filled');
    
    // Take screenshot before submit
    await page.screenshot({ path: 'before-login.png' });
    console.log('📸 Screenshot taken before login');
    
    // Click submit
    await submitButton.click();
    console.log('👆 Submit button clicked');
    
    // Wait for response
    try {
      await page.waitForURL(url => !url.includes('/signin'), { timeout: 15000 });
      console.log('✅ Login successful! Redirected from sign-in page');
      
      // Take screenshot after successful login
      await page.screenshot({ path: 'after-login.png' });
      console.log('📸 Screenshot taken after login');
      
      console.log(`🎉 Current URL: ${page.url()}`);
      
    } catch (timeoutError) {
      console.log('⏰ No redirect detected within 15 seconds');
      
      // Check for error messages
      const errorMessages = await page.$$eval(
        '[class*="error"], [class*="alert"], .text-red-500, .text-danger, [role="alert"]', 
        elements => elements.map(el => el.textContent.trim()).filter(text => text)
      );
      
      if (errorMessages.length > 0) {
        console.log('❌ Error messages found:', errorMessages);
      } else {
        console.log('🤔 No error messages found. Login status unclear.');
      }
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'login-debug.png' });
      console.log('📸 Debug screenshot saved');
    }
    
    // Wait a bit more to see final state
    await page.waitForTimeout(3000);
    
  } catch (error) {
    console.error('💥 Test failed:', error.message);
  } finally {
    console.log('🏁 Closing browser...');
    await browser.close();
  }
}

if (require.main === module) {
  testLogin()
    .then(() => console.log('🧪 Login test completed'))
    .catch(error => console.error('💥 Login test failed:', error));
}

module.exports = { testLogin }; 