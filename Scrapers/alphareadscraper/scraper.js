const { chromium } = require('playwright');
require('dotenv').config();

// Utility function to get Central Time
function getCentralTime() {
  return new Date().toLocaleString('en-US', {
    timeZone: 'America/Chicago',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

async function scrapeAlphaRead() {
  // Check if login credentials are provided
  const email = process.env.ALPHAREAD_EMAIL;
  const password = process.env.ALPHAREAD_PASSWORD;
  const enableLogin = process.env.ENABLE_LOGIN === 'true';
  const showBrowser = process.env.SHOW_BROWSER === 'true';
  
  if (enableLogin && (!email || !password || email === 'your.email@example.com')) {
    console.log('⚠️  Login enabled but credentials not properly configured in .env file');
    console.log('Please update ALPHAREAD_EMAIL and ALPHAREAD_PASSWORD in .env file');
    return;
  }
  
  // Launch browser
  const browser = await chromium.launch({ 
    headless: !showBrowser, // Show browser if SHOW_BROWSER=true in .env
    slowMo: 1000 // Slow down operations by 1 second for better observation
  });
  
  try {
    const context = await browser.newContext({
      // Set user agent to avoid bot detection
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });
    
    const page = await context.newPage();
    
    console.log('🚀 Starting to scrape Alpha Read...');
    
    // Navigate to the Alpha Read sign-in page
    await page.goto('https://alpharead.alpha.school/signin', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    console.log('📄 Page loaded successfully');
    
    // Perform login if enabled and credentials are provided
    if (enableLogin && email && password) {
      console.log('🔐 Attempting to login...');
      
      try {
        // Wait for the form to be fully loaded
        await page.waitForSelector('form', { timeout: 10000 });
        console.log('📋 Login form detected');
        
        // Look for email input field with specific Alpha Read selectors
        await page.waitForSelector('input[type="email"][placeholder="you@example.com"]', { timeout: 10000 });
        
        // Fill in email using the specific selector
        const emailField = await page.$('input[type="email"][placeholder="you@example.com"]');
        if (emailField) {
          await emailField.click(); // Click to focus first
          await emailField.fill(''); // Clear any existing content
          await emailField.fill(email);
          console.log('📧 Email entered successfully');
        } else {
          throw new Error('Email field not found with expected selector');
        }
        
        // Fill in password using the specific selector
        const passwordField = await page.$('input[type="password"][placeholder="Password"]');
        if (passwordField) {
          await passwordField.click(); // Click to focus first
          await passwordField.fill(''); // Clear any existing content
          await passwordField.fill(password);
          console.log('🔑 Password entered successfully');
        } else {
          throw new Error('Password field not found with expected selector');
        }
        
        // Small delay to ensure fields are filled
        await page.waitForTimeout(1000);
        
        // Click the specific sign in button (not the Google one)
        const signInButton = await page.$('button[type="submit"]:has-text("Sign in")');
        if (signInButton) {
          await signInButton.click();
          console.log('👆 Sign in button clicked');
          
          // Wait for navigation or login completion
          try {
            await page.waitForURL(url => !url.includes('/signin'), { timeout: 15000 });
            console.log('✅ Login successful - redirected from sign-in page');
          } catch (redirectError) {
            // Check if we're still on signin page (might indicate login failure)
            const currentUrl = page.url();
            if (currentUrl.includes('/signin')) {
              console.log('⚠️  Still on sign-in page - login might have failed');
              
              // Check for error messages
              const errorMessages = await page.$$eval('[class*="error"], [class*="alert"], .text-red-500, .text-danger', 
                elements => elements.map(el => el.textContent.trim()).filter(text => text)
              );
              
              if (errorMessages.length > 0) {
                console.log('❌ Login errors found:', errorMessages);
              }
            } else {
              console.log('✅ Login appears successful');
            }
          }
          
          // Wait a moment for any dynamic content to load after login
          await page.waitForTimeout(3000);
          
          // Navigate to Guide Dashboard
          console.log('🎯 Navigating to Guide Dashboard...');
          try {
            // Look for Guide Dashboard link using exact selector
            const guideDashboardLink = await page.$('a[href="/guide"]:has-text("Guide Dashboard")');
            if (guideDashboardLink) {
              await guideDashboardLink.click();
              console.log('📊 Clicked Guide Dashboard');
              
              // Wait for page to load
              await page.waitForTimeout(3000);
              const currentUrl = page.url();
              if (currentUrl.includes('/guide')) {
                console.log('✅ Successfully navigated to Guide Dashboard');
              } else {
                console.log(`⚠️ URL after click: ${currentUrl}`);
              }
              
              // Wait for dashboard content to load
              await page.waitForTimeout(2000);
              
              // Look for student management section
              console.log('👥 Looking for Student Management...');
              
              // Try multiple possible selectors for student management
              const studentManagementSelectors = [
                'a:has-text("view students")',
                'a:has-text("student management")',
                'a:has-text("View Students")',
                'a:has-text("Student Management")',
                'button:has-text("view students")',
                'button:has-text("student management")',
                '[href*="student"]',
                '[href*="manage"]'
              ];
              
              let studentManagementElement = null;
              for (const selector of studentManagementSelectors) {
                studentManagementElement = await page.$(selector);
                if (studentManagementElement) {
                  console.log(`📋 Found student management with selector: ${selector}`);
                  break;
                }
              }
              
              if (studentManagementElement) {
                await studentManagementElement.click();
                console.log('👥 Clicked on student management section');
                
                // Wait for student management page to load
                await page.waitForTimeout(3000);
                console.log('✅ Successfully navigated to Student Management');
              } else {
                console.log('⚠️  Student management section not found with known selectors');
                
                // Let's examine what's available on the Guide Dashboard
                const availableLinks = await page.$$eval('a, button', elements => 
                  elements.map(el => ({
                    text: el.textContent.trim(),
                    href: el.href || null,
                    tag: el.tagName.toLowerCase()
                  })).filter(item => item.text)
                );
                
                console.log('🔍 Available navigation options on Guide Dashboard:');
                availableLinks.forEach(link => 
                  console.log(`  ${link.tag.toUpperCase()}: "${link.text}" ${link.href ? '-> ' + link.href : ''}`)
                );
              }
              
            } else {
              console.log('❌ Guide Dashboard link not found');
              
              // Let's see what navigation options are available
              const navLinks = await page.$$eval('a', links => 
                links.map(link => ({
                  text: link.textContent.trim(),
                  href: link.href
                })).filter(link => link.text)
              );
              
              console.log('🔍 Available navigation links:');
              navLinks.forEach(link => console.log(`  "${link.text}" -> ${link.href}`));
            }
            
          } catch (navError) {
            console.log('❌ Navigation error:', navError.message);
            console.log('📄 Continuing with current page scraping...');
          }
          
        }
      } catch (loginError) {
        console.log('❌ Login failed:', loginError.message);
        console.log('📄 Continuing with page scraping...');
      }
    }
    
    // Extract page data
    const pageData = await page.evaluate(() => {
      const data = {};
      
      // Get page title
      data.title = document.title;
      
      // Get page URL
      data.url = window.location.href;
      
      // Look for the main heading
      const mainHeading = document.querySelector('h1');
      data.mainHeading = mainHeading ? mainHeading.textContent.trim() : null;
      
      // Get all headings
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
        .map(h => ({
          tag: h.tagName.toLowerCase(),
          text: h.textContent.trim()
        }));
      data.headings = headings;
      
      // Look for form elements
      const forms = Array.from(document.querySelectorAll('form')).map(form => {
        const inputs = Array.from(form.querySelectorAll('input')).map(input => ({
          type: input.type,
          name: input.name,
          placeholder: input.placeholder,
          id: input.id,
          required: input.required
        }));
        
        const buttons = Array.from(form.querySelectorAll('button')).map(btn => ({
          text: btn.textContent.trim(),
          type: btn.type,
          id: btn.id,
          className: btn.className
        }));
        
        return { inputs, buttons };
      });
      data.forms = forms;
      
      // Look for sign-in options
      const signInButtons = Array.from(document.querySelectorAll('button, a'))
        .filter(el => el.textContent.toLowerCase().includes('sign') || 
                     el.textContent.toLowerCase().includes('google') ||
                     el.textContent.toLowerCase().includes('login'))
        .map(el => ({
          text: el.textContent.trim(),
          tag: el.tagName.toLowerCase(),
          href: el.href || null,
          className: el.className
        }));
      data.signInOptions = signInButtons;
      
      // Get all links
      const links = Array.from(document.querySelectorAll('a'))
        .map(link => ({
          text: link.textContent.trim(),
          href: link.href,
          target: link.target
        }))
        .filter(link => link.text && link.href);
      data.links = links;
      
      // Get meta information
      const metaTags = Array.from(document.querySelectorAll('meta'))
        .map(meta => ({
          name: meta.name,
          property: meta.getAttribute('property'),
          content: meta.content
        }))
        .filter(meta => meta.name || meta.property);
      data.metaTags = metaTags;
      
      return data;
    });
    
    // Take a screenshot
    await page.screenshot({ 
      path: 'alpharead-screenshot.png',
      fullPage: true 
    });
    
    console.log('📸 Screenshot saved as alpharead-screenshot.png');
    
    // Check if there are any input fields (for potential form interaction)
    const inputFields = await page.$$eval('input', inputs => 
      inputs.map(input => ({
        type: input.type,
        name: input.name,
        placeholder: input.placeholder,
        required: input.required
      }))
    );
    
    // Log the scraped data
    console.log('\n📊 SCRAPED DATA:');
    console.log('='.repeat(50));
    console.log(`Title: ${pageData.title}`);
    console.log(`URL: ${pageData.url}`);
    console.log(`Main Heading: ${pageData.mainHeading}`);
    
    if (pageData.headings.length > 0) {
      console.log('\n📝 Headings found:');
      pageData.headings.forEach(h => console.log(`  ${h.tag.toUpperCase()}: ${h.text}`));
    }
    
    if (pageData.signInOptions.length > 0) {
      console.log('\n🔐 Sign-in options found:');
      pageData.signInOptions.forEach(option => console.log(`  ${option.tag.toUpperCase()}: ${option.text}`));
    }
    
    if (inputFields.length > 0) {
      console.log('\n📝 Input fields found:');
      inputFields.forEach(field => console.log(`  ${field.type}: ${field.placeholder || field.name || 'No placeholder'}`));
    }
    
    if (pageData.links.length > 0) {
      console.log('\n🔗 Links found:');
      pageData.links.forEach(link => console.log(`  "${link.text}" -> ${link.href}`));
    }
    
    // Save data to JSON file
    const fs = require('fs');
    
    // Add current URL and timestamp to the data
    pageData.currentUrl = page.url();
    pageData.scrapedAt = getCentralTime();
    pageData.navigationPath = enableLogin ? 'Login -> Guide Dashboard -> Student Management' : 'Direct page access';
    
    fs.writeFileSync('alpharead-data.json', JSON.stringify(pageData, null, 2));
    console.log('\n💾 Data saved to alpharead-data.json');
    console.log(`📍 Final URL: ${pageData.currentUrl}`);
    
    return pageData;
    
  } catch (error) {
    console.error('❌ Error occurred:', error.message);
    throw error;
  } finally {
    await browser.close();
    console.log('🏁 Browser closed');
  }
}

// Run the scraper
if (require.main === module) {
  scrapeAlphaRead()
    .then(data => {
      console.log('\n✅ Scraping completed successfully!');
      console.log(`📊 Total data points collected: ${Object.keys(data).length}`);
    })
    .catch(error => {
      console.error('💥 Scraping failed:', error);
      process.exit(1);
    });
}

module.exports = { scrapeAlphaRead }; 