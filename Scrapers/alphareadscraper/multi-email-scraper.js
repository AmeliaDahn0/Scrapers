const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
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

// Utility function to get Central Time formatted for filenames
function getCentralTimeForFilename() {
  const centralTime = new Date().toLocaleString('en-US', {
    timeZone: 'America/Chicago',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
    hour12: false
  });
  
  // Convert to filename-safe format: 2024-01-15T10-30-45-123CT
  return centralTime.replace(/[/\s:]/g, '-').replace(/,/g, '') + 'CT';
}

// Initialize Supabase client
let supabase = null;
const enableDatabaseUpload = process.env.ENABLE_DATABASE_UPLOAD === 'true';

if (enableDatabaseUpload) {
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;
  
  if (supabaseUrl && supabaseKey) {
    supabase = createClient(supabaseUrl, supabaseKey);
    console.log('✅ Supabase client initialized');
  } else {
    console.log('⚠️  Supabase credentials not found. Database upload disabled.');
    console.log('Please check your .env file for SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY');
  }
}

// Function to upload student data to Supabase
async function uploadToSupabase(studentData) {
  if (!supabase || !enableDatabaseUpload) {
    console.log('📄 Database upload is disabled');
    return { success: false, message: 'Database upload is disabled' };
  }

  try {
    const tableName = process.env.TABLE_NAME || 'student_data';
    
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
      console.log(`⚠️  Date parsing error for student, using current time:`, dateError.message || 'Unknown date error');
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

    console.log(`🔄 Uploading student to table ${tableName}...`);

    const { data, error } = await supabase
      .from(tableName)
      .upsert(dbRecord, { 
        onConflict: 'email,scraped_at'
      })
      .select();

    if (error) {
      const errorMsg = error.message || error.details || JSON.stringify(error) || 'Unknown database error';
      console.log(`❌ Database upload error for student:`, errorMsg);
      return { success: false, error: errorMsg };
    }

      console.log(`✅ Successfully uploaded student to database`);
    return { success: true, data };

  } catch (error) {
    const errorMsg = error.message || error.toString() || 'Unknown upload error';
    console.log(`💥 Database upload failed for student:`, errorMsg);
    return { success: false, error: errorMsg };
  }
}

// Function to upload multiple students to Supabase
async function uploadBatchToSupabase(studentsArray) {
  if (!supabase || !enableDatabaseUpload) {
    console.log('📄 Batch database upload is disabled');
    return { success: false, message: 'Database upload is disabled' };
  }

  console.log(`🚀 Uploading ${studentsArray.length} students to Supabase...`);
  
  const uploadResults = {
    successful: 0,
    failed: 0,
    errors: []
  };

  for (const student of studentsArray) {
    if (student.error) {
      console.log(`⏭️  Skipping student - contains error data`);
      continue;
    }

    const result = await uploadToSupabase(student);
    if (result.success) {
      uploadResults.successful++;
    } else {
      uploadResults.failed++;
      uploadResults.errors.push({
        email: student.email,
        error: result.error || result.message
      });
    }
    
    // Small delay to prevent rate limiting
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log(`\n📊 DATABASE UPLOAD RESULTS:`);
  console.log(`✅ Successfully uploaded: ${uploadResults.successful} students`);
  console.log(`❌ Failed to upload: ${uploadResults.failed} students`);
  
  if (uploadResults.errors.length > 0) {
    console.log(`\n❌ Upload errors:`);
    uploadResults.errors.forEach(err => {
      console.log(`   - Student: ${err.error}`);
    });
  }

  return uploadResults;
}

// Function to read emails from text file (kept as fallback)
function readEmailsFromTxt() {
  try {
    const content = fs.readFileSync('emails.txt', 'utf-8');
    const emails = content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#')) // Remove empty lines and comments
      .map(email => ({ email, name: email.split('@')[0] })); // Extract name from email
    
    return emails;
  } catch (error) {
    console.log('📄 emails.txt not found or empty');
    return [];
  }
}

// Function to read emails from JSON file (kept as fallback)
function readEmailsFromJson() {
  try {
    const content = fs.readFileSync('emails.json', 'utf-8');
    const data = JSON.parse(content);
    return data.emails || [];
  } catch (error) {
    console.log('📄 emails.json not found or invalid');
    return [];
  }
}

// Function to fetch students from database
async function fetchStudentsFromDatabase() {
  if (!supabase) {
    console.log('❌ Supabase client not initialized. Cannot fetch students from database.');
    return [];
  }

  try {
    console.log('🔄 Fetching students from database...');
    
    const { data: students, error } = await supabase
      .from('students')
      .select('name, email')
      .not('email', 'is', null) // Only get students with non-null emails
      .order('name', { ascending: true });

    if (error) {
      console.log('❌ Error fetching students from database:', error.message);
      return [];
    }

    if (!students || students.length === 0) {
      console.log('⚠️  No students found in database');
      return [];
    }

    // Transform to match expected format
    const formattedStudents = students.map(student => ({
      email: student.email,
      name: student.name
    }));

    console.log(`✅ Found ${formattedStudents.length} students in database`);
    return formattedStudents;

  } catch (error) {
    console.log('💥 Failed to fetch students from database:', error.message);
    return [];
  }
}

// Function to get list of target emails
async function getTargetEmails() {
  // First try to get students from database
  const dbStudents = await fetchStudentsFromDatabase();
  
  if (dbStudents.length > 0) {
    console.log(`📋 Using ${dbStudents.length} students from database`);
    return dbStudents;
  }
  
  // Fallback to file-based methods if database fails
  console.log('⚠️  Database fetch failed, falling back to file-based email sources...');
  
  const txtEmails = readEmailsFromTxt();
  const jsonEmails = readEmailsFromJson();
  
  // Check if TXT has real emails (not example emails)
  const txtHasRealEmails = txtEmails.some(email => 
    !email.email.includes('example.com') && email.email.includes('@')
  );
  
  // Check if JSON has real emails (not example emails)  
  const jsonHasRealEmails = jsonEmails.some(email => 
    !email.email.includes('example.com') && email.email.includes('@')
  );
  
  // Prefer TXT if it has real emails, otherwise JSON, otherwise any emails found
  if (txtHasRealEmails) {
    console.log(`📋 Found ${txtEmails.length} real emails in emails.txt`);
    return txtEmails;
  } else if (jsonHasRealEmails) {
    console.log(`📋 Found ${jsonEmails.length} real emails in emails.json`);
    return jsonEmails;
  } else if (txtEmails.length > 0) {
    console.log(`📋 Found ${txtEmails.length} emails in emails.txt (may be examples)`);
    return txtEmails;
  } else if (jsonEmails.length > 0) {
    console.log(`📋 Found ${jsonEmails.length} emails in emails.json (may be examples)`);
    return jsonEmails;
  } else {
    console.log('❌ No emails found in database, emails.txt, or emails.json');
    console.log('Please add student records to the database or add emails to either file before running the scraper');
    return [];
  }
}

// Function to extract comprehensive data from student detail page
async function extractStudentDetailData(page, studentEmail, rowData) {
  console.log(`📋 Extracting data for student`);
  
  try {
    // Wait for detail page to fully load
    await page.waitForTimeout(2000);
        
    // Extract comprehensive student data from detail page
    const studentData = await page.evaluate((params) => {
      const { email, tableRowData } = params;
      const data = {
        email: email,
        tableRowData: tableRowData, // Data from the student management table
        scrapedAt: new Date().toLocaleString('en-US', {
          timeZone: 'America/Chicago',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        }),
        url: window.location.href
      };
          
          // Extract all text content for comprehensive data
          const fullPageText = document.body.textContent.trim();
          data.fullPageText = fullPageText;
          
          // Parse structured student profile data
          const studentProfile = {};
          
          // Function to extract value after a label in the text
          function extractValueAfterLabel(text, label) {
            const patterns = [
              new RegExp(label + '\\s*([\\d\\.]+%?)', 'i'),
              new RegExp(label + '\\s*([\\d\\.]+\\s*[a-zA-Z]+)', 'i'),
              new RegExp(label + '\\s*([A-Za-z]+\\s*\\d+)', 'i'),
              new RegExp(label + '\\s*([\\d]+\\s*-\\s*[^\\d]*)', 'i'),
              new RegExp(label + '\\s*([^\\d]*\\d+[^\\d]*)', 'i')
            ];
            
            for (const pattern of patterns) {
              const match = text.match(pattern);
              if (match && match[1]) {
                return match[1].trim();
              }
            }
            return null;
          }
          
          // Extract specific fields from the page text
          try {
            // Debug: Log a sample of the full page text for troubleshooting
            console.log(`Debug for ${email}: Page text sample around Last Active:`, 
              fullPageText.substring(
                Math.max(0, fullPageText.indexOf('Last Active') - 50), 
                fullPageText.indexOf('Last Active') + 100
              )
            );
            // Grade Level - look for pattern like "11Grade Level"
            const gradeMatch = fullPageText.match(/(\d+)Grade Level/);
            studentProfile.gradeLevel = gradeMatch ? gradeMatch[1] : null;
            
            // Reading Level - look for pattern like "8Reading Level"  
            const readingMatch = fullPageText.match(/Grade Level(\d+)Reading Level/);
            studentProfile.readingLevel = readingMatch ? readingMatch[1] : null;
            
            // Average Score - look for pattern like "62.2%Average Score"
            const avgScoreMatch = fullPageText.match(/([\d.]+%)Average Score/);
            studentProfile.averageScore = avgScoreMatch ? avgScoreMatch[1] : null;
            
            // Sessions This Month - look for pattern like "0Sessions This Month"
            const sessionsMonthMatch = fullPageText.match(/Average Score(\d+)Sessions This Month/);
            studentProfile.sessionsThisMonth = sessionsMonthMatch ? sessionsMonthMatch[1] : null;
            
            // Total Sessions - look for pattern like "15Total Sessions"
            const totalSessionsMatch = fullPageText.match(/Sessions This Month(\d+)Total Sessions/);
            studentProfile.totalSessions = totalSessionsMatch ? totalSessionsMatch[1] : null;
            
            // Time Reading - look for pattern like "2h 36mTime Reading"
            const timeReadingMatch = fullPageText.match(/Total Sessions([\dhmsw ]+)Time Reading/);
            studentProfile.timeReading = timeReadingMatch ? timeReadingMatch[1].trim() : null;
            
            // Success Rate - look for pattern like "62.2%Success Rate"
            const successRateMatch = fullPageText.match(/Time Reading([\d.]+%)Success Rate/);
            studentProfile.successRate = successRateMatch ? successRateMatch[1] : null;
            
            // Last Active - look for pattern like "Last Active" followed by date
            // Try multiple patterns to be more precise
            let lastActiveMatch = fullPageText.match(/Last Active([A-Za-z\s\d]+?)(?:Avg\.|$)/);
            if (!lastActiveMatch) {
              // Alternative pattern: look for date pattern after "Last Active"
              lastActiveMatch = fullPageText.match(/Last Active\s*([A-Za-z]{3}\s+\d{1,2})/);
            }
            if (!lastActiveMatch) {
              // Another alternative: look in reverse from "Avg. Session Time"
              const reverseMatch = fullPageText.match(/([A-Za-z]{3}\s+\d{1,2})\s*Last Active/);
              lastActiveMatch = reverseMatch ? [null, reverseMatch[1]] : null;
            }
            studentProfile.lastActive = lastActiveMatch ? lastActiveMatch[1].trim() : null;
            
            // Avg Session Time - look for pattern like "10mAvg. Session Time" or after "Last Active"
            let avgSessionMatch = fullPageText.match(/Last Active[A-Za-z\s\d]*?(\d+m)\s*Avg\. Session Time/);
            if (!avgSessionMatch) {
              // Alternative pattern
              avgSessionMatch = fullPageText.match(/(\d+m)\s*Avg\. Session Time/);
            }
            studentProfile.avgSessionTime = avgSessionMatch ? avgSessionMatch[1] : null;
            
            // Current Course - look for course information
            const courseMatch = fullPageText.match(/Current Course([\d\s\-A-Za-z()]+)(?:User PowerPath|$)/);
            studentProfile.currentCourse = courseMatch ? courseMatch[1].trim() : null;
            
          } catch (parseError) {
            console.log('Error parsing student profile:', parseError.message);
          }
          
          // Alternative extraction method using DOM structure
          try {
            // Look for structured data using common patterns in the Alpha Read interface
            const structuredData = {};
            
            // Find all text nodes that contain common metrics
            const allTextElements = Array.from(document.querySelectorAll('*')).filter(el => 
              el.children.length === 0 && el.textContent.trim().length > 0
            );
            
            // Look for Last Active specifically in the structured layout
            allTextElements.forEach(el => {
              const text = el.textContent.trim();
              // Look for date patterns (Jun 2, Mar 6, etc.)
              const datePattern = /^([A-Za-z]{3}\s+\d{1,2})$/;
              if (datePattern.test(text)) {
                // Check if this element or nearby elements indicate it's the "Last Active" date
                const parent = el.parentElement;
                const previousElements = Array.from(parent.children).slice(0, Array.from(parent.children).indexOf(el));
                const hasLastActiveLabel = previousElements.some(sibling => 
                  sibling.textContent.toLowerCase().includes('last active')
                );
                
                if (hasLastActiveLabel || 
                    (el.previousElementSibling && el.previousElementSibling.textContent.toLowerCase().includes('last active'))) {
                  structuredData.lastActive = text;
                }
              }
            });
            
                         // Additional method: Look for metric cards or stat containers
             const metricContainers = document.querySelectorAll('div, section, article');
             metricContainers.forEach(container => {
               const containerText = container.textContent.toLowerCase();
               if (containerText.includes('last active')) {
                 // Look for date patterns within this container
                 const dateMatches = container.textContent.match(/([A-Za-z]{3}\s+\d{1,2})/g);
                 if (dateMatches && dateMatches.length > 0) {
                   // Take the last date match (most likely to be the actual value)
                   structuredData.lastActive = dateMatches[dateMatches.length - 1];
                 }
               }
             });
             
             // Override text-parsed data with structured data if found
             if (structuredData.lastActive) {
               if (!studentProfile.lastActive || studentProfile.lastActive !== structuredData.lastActive) {
                 console.log(`Correcting Last Active from "${studentProfile.lastActive}" to "${structuredData.lastActive}"`);
                 studentProfile.lastActive = structuredData.lastActive;
               }
             }
            
          } catch (structuredError) {
            console.log('Error in structured extraction:', structuredError.message);
          }
          
          data.studentProfile = studentProfile;
          
          // Extract profile information from various selectors
          const profileData = {};
          
          // Look for labeled fields (various formats)
          const labelSelectors = [
            'label', '.field-label', '.profile-field', 'dt', '.label',
            '[class*="label"]', '[data-label]', 'span[class*="label"]'
          ];
          
          labelSelectors.forEach(selector => {
            const fields = document.querySelectorAll(selector);
            fields.forEach(field => {
              const label = field.textContent.trim();
              let value = null;
              
              // Try different methods to find the associated value
              value = field.nextElementSibling?.textContent?.trim() ||
                     field.parentElement?.querySelector('span:not([class*="label"]), div:not([class*="label"]), dd, input')?.textContent?.trim() ||
                     field.parentElement?.nextElementSibling?.textContent?.trim();
              
              if (label && value && value !== label && label.length > 0 && value.length > 0) {
                profileData[label] = value;
              }
            });
          });
          
          // Extract data from input fields
          const inputs = document.querySelectorAll('input[value], textarea');
          inputs.forEach(input => {
            const label = input.getAttribute('placeholder') || 
                         input.getAttribute('name') ||
                         input.previousElementSibling?.textContent?.trim() ||
                         input.parentElement?.querySelector('label')?.textContent?.trim();
            const value = input.value;
            
            if (label && value && label.length > 0 && value.length > 0) {
              profileData[label] = value;
            }
          });
          
          // Extract all table data more comprehensively
          const tables = Array.from(document.querySelectorAll('table')).map((table, tableIndex) => {
            const headers = Array.from(table.querySelectorAll('th, thead td')).map(th => th.textContent.trim());
            const rows = Array.from(table.querySelectorAll('tbody tr, tr')).map(row => {
              const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
              const rowData = {};
              
              if (headers.length > 0) {
                headers.forEach((header, index) => {
                  if (cells[index]) rowData[header] = cells[index];
                });
              } else {
                // If no headers, create generic column names
                cells.forEach((cell, index) => {
                  rowData[`Column_${index + 1}`] = cell;
                });
              }
              return rowData;
            });
            
            return { 
              tableIndex: tableIndex + 1,
              headers, 
              rows,
              rawHTML: table.innerHTML
            };
          });
          
          // Extract all div-based data sections
          const dataSections = {};
          const divs = document.querySelectorAll('div[class*="section"], div[class*="profile"], div[class*="info"], div[class*="detail"]');
          divs.forEach((div, index) => {
            const sectionTitle = div.querySelector('h1, h2, h3, h4, h5, h6')?.textContent?.trim() || `Section_${index + 1}`;
            const sectionContent = div.textContent.trim();
            if (sectionContent && sectionContent.length > 0) {
              dataSections[sectionTitle] = sectionContent;
            }
          });
          
          // Extract all list data
          const lists = Array.from(document.querySelectorAll('ul, ol')).map((list, index) => {
            const items = Array.from(list.querySelectorAll('li')).map(li => li.textContent.trim());
            return {
              listIndex: index + 1,
              type: list.tagName.toLowerCase(),
              items: items
            };
          });
          
          // Extract any progress/score data
          const progressData = {};
          const progressElements = document.querySelectorAll('[class*="progress"], [class*="score"], [class*="grade"], [class*="percent"]');
          progressElements.forEach((element, index) => {
            const label = element.getAttribute('aria-label') || 
                         element.previousElementSibling?.textContent?.trim() ||
                         element.parentElement?.querySelector('label')?.textContent?.trim() ||
                         `Progress_${index + 1}`;
            const value = element.textContent.trim() || element.getAttribute('value');
            
            if (label && value) {
              progressData[label] = value;
            }
          });
          
          // Keep legacy data sections for reference but prioritize studentProfile
          data.profileData = profileData;
          data.tables = tables;
          data.dataSections = dataSections;
          data.lists = lists;
          data.progressData = progressData;
          
          // Extract any visible metrics or statistics
          const metrics = {};
          const metricElements = document.querySelectorAll('[class*="metric"], [class*="stat"], [class*="count"], [class*="total"]');
          metricElements.forEach((element, index) => {
            const label = element.getAttribute('data-label') ||
                         element.previousElementSibling?.textContent?.trim() ||
                         `Metric_${index + 1}`;
            const value = element.textContent.trim();
            
            if (label && value) {
              metrics[label] = value;
            }
          });
          data.metrics = metrics;
          
      return data;
    }, { email: studentEmail, tableRowData: rowData });
    
    // Screenshot disabled for faster scraping
    // await page.screenshot({ 
    //   path: `student-${studentEmail.replace('@', '_at_').replace(/\./g, '_')}-profile.png`,
    //   fullPage: true 
    // });
    
    console.log(`⚡ Data extracted for student (no screenshot)`);
    
    return studentData;
    
  } catch (error) {
    console.log(`❌ Error extracting data for student:`, error.message);
    return {
      email: studentEmail,
      error: error.message,
      scrapedAt: new Date().toISOString()
    };
  }
}

// Main function to scrape multiple students
async function scrapeMultipleStudents() {
  const loginEmail = process.env.ALPHAREAD_EMAIL;
  const loginPassword = process.env.ALPHAREAD_PASSWORD;
  const isCI = process.env.CI === 'true';
  
  console.log(`🔧 Environment: ${isCI ? 'GitHub Actions CI' : 'Local'}`);
  console.log(`📧 Login email: [HIDDEN]`);
  console.log(`🔑 Password: [HIDDEN]`);
  
  if (!loginEmail || !loginPassword || loginEmail === 'your.email@example.com') {
    console.log('❌ Please configure your login credentials in environment variables');
    console.log('Required: ALPHAREAD_EMAIL and ALPHAREAD_PASSWORD');
    return;
  }
  
  const targetEmails = await getTargetEmails();
  if (targetEmails.length === 0) {
    return;
  }
  
  console.log(`🚀 Starting multi-student scraper for ${targetEmails.length} students...`);
  
  // Configure browser for CI vs local environment
  const browserOptions = {
    headless: process.env.SHOW_BROWSER !== 'true',
    slowMo: isCI ? 2000 : 1000, // Slower in CI environment
  };
  
  // Add CI-specific browser arguments
  if (isCI) {
    browserOptions.args = [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-default-apps'
    ];
  }
  
  console.log(`🌐 Browser config: ${JSON.stringify(browserOptions)}`);
  const browser = await chromium.launch(browserOptions);
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    // Login process
    console.log('🔐 Logging in to Alpha Read...');
    await page.goto('https://alpharead.alpha.school/signin', { 
      waitUntil: 'networkidle',
      timeout: isCI ? 60000 : 30000 // Longer timeout in CI
    });
    
    await page.waitForSelector('input[type="email"][placeholder="you@example.com"]', {
      timeout: isCI ? 30000 : 10000
    });
    
    // Slower, more deliberate form filling for CI
    const emailInput = await page.$('input[type="email"][placeholder="you@example.com"]');
    await emailInput.click();
    await page.waitForTimeout(isCI ? 1000 : 500);
    await emailInput.fill(loginEmail);
    await page.waitForTimeout(isCI ? 1000 : 500);
    
    const passwordInput = await page.$('input[type="password"][placeholder="Password"]');
    await passwordInput.click();
    await page.waitForTimeout(isCI ? 1000 : 500);
    await passwordInput.fill(loginPassword);
    await page.waitForTimeout(isCI ? 2000 : 1000);
    
    console.log('🚀 Submitting login form...');
    await page.click('button[type="submit"]');
    
    // Wait for login to complete and verify success
    console.log('⏳ Waiting for login to complete...');
    try {
      // Wait for navigation away from signin page (longer timeout for CI)
      await page.waitForFunction(() => {
        return !window.location.href.includes('/signin');
      }, { timeout: isCI ? 30000 : 15000 });
      
      console.log(`✅ Login successful - redirected to: ${page.url()}`);
    } catch (error) {
      console.log(`❌ Login failed - still on: ${page.url()}`);
      console.log('🔍 Checking for error messages...');
      
      // Check for error messages on the page
      const errorMessages = await page.$$eval('*', elements => {
        return elements
          .map(el => el.textContent?.trim())
          .filter(text => text && (
            text.toLowerCase().includes('error') ||
            text.toLowerCase().includes('invalid') ||
            text.toLowerCase().includes('incorrect') ||
            text.toLowerCase().includes('failed')
          ))
          .slice(0, 3);
      });
      
      if (errorMessages.length > 0) {
        console.log('🚨 Error messages found:', errorMessages);
      }
      
      throw new Error('Login failed - could not navigate away from signin page');
    }
    
    // Navigate to student management
    console.log('🎯 Navigating to Student Management...');
    console.log(`📍 Current URL after login: ${page.url()}`);
    
    const guideDashboardLink = await page.$('a[href="/guide"]:has-text("Guide Dashboard")');
    if (guideDashboardLink) {
      console.log('✅ Found Guide Dashboard link');
      await guideDashboardLink.click();
      await page.waitForTimeout(3000);
      console.log(`📍 URL after Guide Dashboard: ${page.url()}`);
      
      // Click on Student Management
      const studentManagementLink = await page.$('a[href="/guide/students"]');
      if (studentManagementLink) {
        console.log('✅ Found Student Management link');
        await studentManagementLink.click();
        
        // Wait for the student management page to fully load
        await page.waitForTimeout(5000);
        
        // Wait for the search input to be available
        await page.waitForSelector('input[placeholder*="Search"]', { timeout: 15000 });
        
        // Wait for the page to be fully interactive (no more JavaScript loading)
        await page.waitForLoadState('networkidle');
        
        console.log('✅ Reached Student Management page');
      } else {
        console.log('❌ Student Management link not found');
        console.log('🔍 Available links:', await page.$$eval('a', links => 
          links.slice(0, 10).map(link => ({ text: link.textContent.trim(), href: link.href }))
        ));
      }
    } else {
      console.log('❌ Guide Dashboard link not found');
      console.log('🔍 Available links:', await page.$$eval('a', links => 
        links.slice(0, 10).map(link => ({ text: link.textContent.trim(), href: link.href }))
      ));
    }
    
    // Search for each target email individually using the exact search element provided
    console.log('🔍 Searching for target students using specified search element...');
    
         // Use the working search element first, then fallback
     const searchSelectors = [
       'input[placeholder*="Search"]', // Working selector - use first
       'input#search[placeholder="Search..."][type="search"]' // Fallback
     ];
    
    // Track results as we scrape students immediately when found
    const results = [];
    let studentsProcessed = 0;
    
    for (const targetEmail of targetEmails) {
      console.log(`\n🔍 Searching for student (${studentsProcessed + 1}/${targetEmails.length})`);
      
      try {
        // Go to student management page for fresh search
        await page.goto('https://alpharead.alpha.school/guide/students');
        
        // Wait for page to fully load before searching
        await page.waitForTimeout(3000);
        await page.waitForSelector('input[placeholder*="Search"]', { timeout: 10000 });
        await page.waitForLoadState('networkidle');
        
        // Additional wait to ensure dynamic content is loaded
        await page.waitForTimeout(2000);
        
        // Verify we're on the right page and search elements are available
        const pageUrl = page.url();
        const hasSearchElements = await page.$('input[type="search"], input[placeholder*="Search"]');
        
        if (!hasSearchElements) {
          console.log(`⚠️  No search elements found on ${pageUrl}`);
          console.log('🔍 Available inputs:', await page.$$eval('input', inputs => 
            inputs.map(input => ({ type: input.type, placeholder: input.placeholder, id: input.id }))
          ));
        }
        
        let searchWorked = false;
        let searchAttempts = 0;
        const maxAttempts = 2; // Try each search method twice
        
        // Try the user's exact element first, then fallback - with retry logic
        for (const searchSelector of searchSelectors) {
          for (let attempt = 0; attempt < maxAttempts && !searchWorked; attempt++) {
            try {
              if (attempt > 0) {
                console.log(`🔄 Retry attempt ${attempt + 1} for selector: ${searchSelector}`);
                // Refresh the page for retry attempts
                await page.goto('https://alpharead.alpha.school/guide/students');
                await page.waitForTimeout(3000);
                await page.waitForSelector('input[placeholder*="Search"]', { timeout: 10000 });
                await page.waitForLoadState('networkidle');
                await page.waitForTimeout(2000);
              }
              
              console.log(`🔍 Trying search element: ${searchSelector}`);
              const searchInput = await page.$(searchSelector);
              
              if (searchInput) {
                console.log(`✅ Found search input`);
                
                // Clear existing search and enter the target email
                await searchInput.click();
                await searchInput.fill('');
                await page.waitForTimeout(500);
                await searchInput.type(targetEmail.email);
                
                // Trigger the search - try multiple methods
                await page.keyboard.press('Enter');
                await page.waitForTimeout(3000); // Wait for initial search
                
                // Also try clicking a search button if it exists
                const searchButton = await page.$('button[type="submit"]');
                if (searchButton) {
                  console.log('🔍 Found search button, clicking it too...');
                  await searchButton.click();
                  await page.waitForTimeout(3000);
                }
                
                // Wait for network activity to settle
                try {
                  await page.waitForLoadState('networkidle', { timeout: 10000 });
                } catch (networkError) {
                  console.log('⚠️ Network settle timeout, continuing...');
                }
                
                // Wait additional time for results to load
                await page.waitForTimeout(3000);
                
                // Check if URL updated with search parameter
                const currentUrl = page.url();
                // Hidden: Search URL
                
                // Debug: Check if search input still has the value
                const searchValue = await searchInput.inputValue();
                // Hidden: Search input value
                
                // Look for the student in search results
                const studentFound = await page.evaluate((email) => {
                const emailRegex = new RegExp(email.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                
                // Get page info for debugging
                const pageText = document.body.textContent;
                const hasEmailInPage = pageText.includes(email);
                
                // Find all Details buttons
                const allLinks = Array.from(document.querySelectorAll('a[href*="/guide/students/"]'));
                const detailsButtons = allLinks.filter(link => 
                  link.textContent.trim().toLowerCase().includes('details')
                );
                
                // Count table rows
                const tableRows = document.querySelectorAll('tbody tr');
                
                // Look for the student row containing this email
                for (const button of detailsButtons) {
                  const row = button.closest('tr');
                  if (row) {
                    const rowText = row.textContent;
                    if (emailRegex.test(rowText)) {
                      // Extract row data
                      const cells = Array.from(row.querySelectorAll('td'));
                      const rowData = cells.map(cell => cell.textContent.trim()).filter(text => text && text !== 'Details');
                      
                      return {
                        email: email,
                        detailsHref: button.href,
                        rowData: rowData,
                        found: true,
                        debug: {
                          hasEmailInPage: hasEmailInPage,
                          detailsButtonCount: detailsButtons.length,
                          tableRowCount: tableRows.length,
                          firstTableRow: tableRows[0]?.textContent?.trim() || 'No rows'
                        }
                      };
                    }
                  }
                }
                
                return { 
                  email: email, 
                  found: false,
                  debug: {
                    hasEmailInPage: hasEmailInPage,
                    detailsButtonCount: detailsButtons.length,
                    tableRowCount: tableRows.length,
                    firstTableRow: tableRows[0]?.textContent?.trim() || 'No rows',
                    pageTextSample: pageText.substring(0, 200)
                  }
                };
              }, targetEmail.email);
              
              // Hidden: Search results details
              
              if (studentFound.found) {
                console.log(`✅ Found target student`);
                searchWorked = true;
                
                // IMMEDIATELY SCRAPE THE STUDENT DATA
                try {
                  console.log(`🔗 Going to Details page for student`);
                  await page.goto(studentFound.detailsHref);
                  await page.waitForTimeout(3000);
                  
                  console.log('✅ Navigated to Details page');
                  
                  // Extract comprehensive student data
                  const rawStudentData = await extractStudentDetailData(page, targetEmail.email, studentFound.rowData);
                  
                  // Reorganize data to prioritize structured sections
                  const organizedStudentData = {
                    email: rawStudentData.email,
                    scrapedAt: rawStudentData.scrapedAt,
                    url: rawStudentData.url,
                    
                    // Clean structured profile data
                    profile: {
                      gradeLevel: rawStudentData.studentProfile?.gradeLevel || null,
                      readingLevel: rawStudentData.studentProfile?.readingLevel || null,
                      averageScore: rawStudentData.studentProfile?.averageScore || null,
                      sessionsThisMonth: rawStudentData.studentProfile?.sessionsThisMonth || null,
                      totalSessions: rawStudentData.studentProfile?.totalSessions || null,
                      timeReading: rawStudentData.studentProfile?.timeReading || null,
                      successRate: rawStudentData.studentProfile?.successRate || null,
                      lastActive: rawStudentData.studentProfile?.lastActive || null,
                      avgSessionTime: rawStudentData.studentProfile?.avgSessionTime || null,
                      currentCourse: rawStudentData.studentProfile?.currentCourse || null
                    }
                  };
                  
                  results.push(organizedStudentData);
                  studentsProcessed++;
                  
                  console.log(`📋 Successfully scraped data for student`);
                  // Hidden: Progress counter
                  
                } catch (scrapingError) {
                  console.log(`❌ Error scraping student:`, scrapingError.message);
                  results.push({
                    email: targetEmail.email,
                    error: scrapingError.message,
                    rowData: studentFound.rowData || [],
                    scrapedAt: new Date().toLocaleString('en-US', {
                      timeZone: 'America/Chicago',
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false
                    })
                  });
                  studentsProcessed++;
                }
                break; // Exit the selector loop since we found the student
              } else {
                console.log(`❌ Student not found with selector: ${searchSelector}`);
              }
              
              // Clear search to reset for next attempt
              await searchInput.fill('');
              await page.waitForTimeout(1000);
              
            } else {
              console.log(`❌ Search input not found with selector: ${searchSelector}`);
            }
          } catch (selectorError) {
            console.log(`❌ Error with selector ${searchSelector}:`, selectorError.message);
          }
        } // End of attempt loop
        } // End of selector loop
        
        if (!searchWorked) {
          console.log(`❌ Student not found with any search method`);
        }
        
      } catch (error) {
        console.log(`❌ Error searching for student:`, error.message);
      }
    }
    
    // Report final results
    console.log(`\n📈 FINAL RESULTS:`);
    console.log(`📋 Searched for: ${targetEmails.length} students`);
    console.log(`✅ Successfully processed: ${studentsProcessed} students`);
    console.log(`❌ Not found: ${targetEmails.length - studentsProcessed} students`);
    
    if (results.length === 0) {
      console.log('\n⚠️  No students were found and scraped');
      console.log('💡 Possible reasons:');
      console.log('   - Students not in this guide account');
      console.log('   - Different email format or spelling');
      console.log('   - Students may be archived or inactive');
      console.log('');
      console.log('🛑 No data to save');
      await browser.close();
      return;
    }
    
    // Save all results
    const timestamp = getCentralTimeForFilename();
    const outputFile = `student-data-${timestamp}.json`;
    
    fs.writeFileSync(outputFile, JSON.stringify({
      scrapedAt: new Date().toLocaleString('en-US', {
        timeZone: 'America/Chicago',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }),
      totalStudents: results.length,
      students: results
    }, null, 2));
    
    console.log(`\n💾 All data saved to: ${outputFile}`);
    console.log(`📊 Successfully processed ${results.length} students`);
    
    // Upload to Supabase if enabled
    if (enableDatabaseUpload && results.length > 0) {
      console.log(`\n🚀 Uploading data to Supabase database...`);
      const uploadResults = await uploadBatchToSupabase(results);
      
      if (uploadResults.successful > 0) {
        console.log(`🎉 Successfully uploaded ${uploadResults.successful} students to database!`);
      }
    } else if (enableDatabaseUpload) {
      console.log(`⚠️  No data to upload to database`);
    } else {
      console.log(`📄 Database upload is disabled (set ENABLE_DATABASE_UPLOAD=true in .env to enable)`);
    }
    
    return results;
    
  } catch (error) {
    console.error('💥 Multi-student scraping failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Browser closed');
  }
}

if (require.main === module) {
  scrapeMultipleStudents()
    .then(() => console.log('✅ Multi-student scraping completed'))
    .catch(error => console.error('💥 Multi-student scraping failed:', error));
}

module.exports = { 
  scrapeMultipleStudents, 
  getTargetEmails, 
  uploadToSupabase, 
  uploadBatchToSupabase 
}; 