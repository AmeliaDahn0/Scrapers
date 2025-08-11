const { chromium, firefox, webkit } = require('playwright');
const StudentsManager = require('./studentsManager');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

class MembeanScraper {
    constructor() {
        this.browser = null;
        this.page = null;
        this.username = process.env.MEMBEAN_USERNAME;
        this.password = process.env.MEMBEAN_PASSWORD;
        this.headless = process.env.HEADLESS === 'true';
        this.browserType = process.env.BROWSER || 'chromium';
        this.studentsManager = new StudentsManager();
        this.allStudentData = [];
        
        // Initialize Supabase client
        this.supabaseUrl = process.env.SUPABASE_URL;
        this.supabaseKey = process.env.SUPABASE_ANON_KEY;
        this.supabase = null;
        
        if (this.supabaseUrl && this.supabaseKey) {
            this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
        }
    }

    async init() {
        // Validate credentials
        if (!this.username || !this.password) {
            throw new Error('Please set MEMBEAN_USERNAME and MEMBEAN_PASSWORD in your .env file');
        }

        if (this.username === 'your_username_here' || this.password === 'your_password_here') {
            throw new Error('Please update the .env file with your actual Membean credentials');
        }

        // Launch browser
        const browserEngine = this.getBrowserEngine();
        this.browser = await browserEngine.launch({ 
            headless: this.headless,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        
        // Set user agent to avoid detection
        await this.page.setExtraHTTPHeaders({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        
        console.log(`Browser initialized: ${this.browserType} (headless: ${this.headless})`);
    }

    getBrowserEngine() {
        switch (this.browserType.toLowerCase()) {
            case 'firefox':
                return firefox;
            case 'webkit':
                return webkit;
            case 'chromium':
            default:
                return chromium;
        }
    }

    async login() {
        console.log('Navigating to Membean login page...');
        
        // Navigate to login page
        await this.page.goto('https://membean.com/login', { 
            waitUntil: 'networkidle' 
        });

        // Debug: Take a screenshot of login page
        await this.page.screenshot({ path: 'login-page.png' });
        console.log('Login page screenshot saved as login-page.png');

        // Debug: Log the page content to understand the structure
        const pageContent = await this.page.content();
        console.log('Page URL:', this.page.url());
        
        // Look for different possible login field selectors
        const possibleSelectors = [
            '#user_login',
            '#username',
            '#email',
            'input[name="username"]',
            'input[name="email"]',
            'input[name="user_login"]',
            'input[type="email"]',
            'input[type="text"]'
        ];

        let loginSelector = null;
        for (const selector of possibleSelectors) {
            try {
                await this.page.waitForSelector(selector, { timeout: 2000 });
                loginSelector = selector;
                console.log(`Found login field with selector: ${selector}`);
                break;
            } catch (e) {
                // Continue to next selector
            }
        }

        if (!loginSelector) {
            // Print available input elements
            const inputs = await this.page.$$eval('input', elements => 
                elements.map(el => ({
                    type: el.type,
                    name: el.name,
                    id: el.id,
                    className: el.className,
                    placeholder: el.placeholder
                }))
            );
            console.log('Available input elements:', JSON.stringify(inputs, null, 2));
            throw new Error('Could not find login field. Check login-page.png for visual inspection.');
        }

        console.log('Filling login credentials...');
        
        // Find password field
        const possiblePasswordSelectors = [
            '#user_password',
            '#password',
            'input[name="password"]',
            'input[name="user_password"]',
            'input[type="password"]'
        ];

        let passwordSelector = null;
        for (const selector of possiblePasswordSelectors) {
            try {
                await this.page.waitForSelector(selector, { timeout: 2000 });
                passwordSelector = selector;
                console.log(`Found password field with selector: ${selector}`);
                break;
            } catch (e) {
                // Continue to next selector
            }
        }

        if (!passwordSelector) {
            throw new Error('Could not find password field');
        }

        // Fill login form
        await this.page.fill(loginSelector, this.username);
        await this.page.fill(passwordSelector, this.password);

        // Find and click login button
        const possibleButtonSelectors = [
            'input[type="submit"][value="Log in"]',
            'input[type="submit"]',
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'button:has-text("Login")',
            '.btn:has-text("Log in")',
            '.btn:has-text("Login")'
        ];

        let buttonSelector = null;
        for (const selector of possibleButtonSelectors) {
            try {
                await this.page.waitForSelector(selector, { timeout: 2000 });
                buttonSelector = selector;
                console.log(`Found login button with selector: ${selector}`);
                break;
            } catch (e) {
                // Continue to next selector
            }
        }

        if (!buttonSelector) {
            const buttons = await this.page.$$eval('button, input[type="submit"]', elements => 
                elements.map(el => ({
                    type: el.type,
                    value: el.value,
                    textContent: el.textContent,
                    className: el.className
                }))
            );
            console.log('Available buttons:', JSON.stringify(buttons, null, 2));
            throw new Error('Could not find login button');
        }

        await this.page.click(buttonSelector);

        // Wait for navigation to complete
        await this.page.waitForNavigation({ waitUntil: 'networkidle' });

        // Check if login was successful
        const currentUrl = this.page.url();
        if (currentUrl.includes('/login')) {
            throw new Error('Login failed. Please check your credentials.');
        }

        console.log('Login successful!');
    }

    async navigateToClass() {
        console.log('Navigating to dashboard...');
        
        // Navigate to dashboard
        await this.page.goto('https://membean.com/dashboard', { 
            waitUntil: 'networkidle' 
        });

        // Wait for dashboard content to load
        await this.page.waitForSelector('body', { timeout: 10000 });

        console.log('Looking for SAT Blitz - 2 Hour Learning class...');
        
        // Navigate directly to the class URL we know
        console.log('Navigating directly to class URL: https://membean.com/tclasses/345817');
        await this.page.goto('https://membean.com/tclasses/345817', { waitUntil: 'networkidle' });
        
        console.log('Navigated to class dashboard. Current URL:', this.page.url());
    }

    async navigateToStudentsTab() {
        console.log('Looking for Students tab...');
        
        // Wait for the tab navigation to be visible
        await this.page.waitForSelector('#students-tab-link', { timeout: 10000 });
        
        // Click on the Students tab
        console.log('Clicking on Students tab...');
        await this.page.click('#students-tab-link');
        
        // Wait for the students content to load
        await this.page.waitForSelector('#_students', { timeout: 10000 });
        await this.page.waitForTimeout(2000); // Give it a moment to fully load
        
        console.log('Successfully navigated to Students tab');
        console.log('Current URL:', this.page.url());
    }

    async clickStudentByName(studentName) {
        console.log(`Looking for student: ${studentName}`);
        
        // Quick click without waiting for full navigation
        const studentFound = await this.page.evaluate((name) => {
            const rows = document.querySelectorAll('#_students table tbody tr, #_students table tr');
            for (const row of rows) {
                if (row.textContent.includes(name)) {
                    const link = row.querySelector('a');
                    if (link) {
                        link.click();
                        return true;
                    }
                }
            }
            return false;
        }, studentName);

        if (studentFound) {
            console.log(`✓ Clicked student: ${studentName}`);
            // Just wait a short time for the page to start loading
            await this.page.waitForTimeout(1500);
            return true;
        } else {
            console.log(`✗ Could not find student: ${studentName}`);
            return false;
        }
    }

    async scrapeStudentData(studentName) {
        console.log(`📊 Collecting data for: ${studentName}`);
        
        // Wait a bit for the page to load
        await this.page.waitForTimeout(1000);
        
        // Extract student profile and training data (streamlined)
        const studentData = await this.page.evaluate(() => {
            const data = {
                url: window.location.href,
                timestamp: new Date().toISOString()
            };

            try {
                // Extract student name
                const nameElement = document.querySelector('h1, .student-name');
                data.studentName = nameElement ? nameElement.textContent.trim() : 'Unknown';

                // Extract Recent Training table data (only what we need)
                const trainingTable = document.querySelector('table');
                data.recentTraining = [];

                if (trainingTable) {
                    const rows = trainingTable.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        if (cells.length >= 3) {
                            const session = {
                                startedAt: cells[0] ? cells[0].textContent.trim() : '',
                                length: cells[1] ? cells[1].textContent.trim() : '',
                                accuracy: cells[2] ? cells[2].textContent.trim() : ''
                            };
                            data.recentTraining.push(session);
                        }
                    });

                    console.log(`Found ${data.recentTraining.length} training sessions`);
                } else {
                    console.log('No training table found');
                }

            } catch (error) {
                data.error = 'Error extracting data: ' + error.message;
            }

            return data;
        });

        // Take screenshot after data collection
        try {
            await this.page.screenshot({ 
                path: `student-${studentName.replace(/[^a-zA-Z0-9]/g, '_')}-screenshot.png`,
                fullPage: false
            });
            console.log(`✓ Data collected for: ${studentName} (${studentData.recentTraining ? studentData.recentTraining.length : 0} sessions)`);
        } catch (error) {
            console.log(`✗ Screenshot failed for: ${studentName}`);
        }

        return studentData;
    }

    async navigateBackToClass() {
        console.log('🔙 Going back to class...');
        
        // Fast navigation back - just go directly to the URL
        try {
            await this.page.goto('https://membean.com/tclasses/345817', { 
                waitUntil: 'domcontentloaded', // Faster than networkidle
                timeout: 5000 
            });
            console.log('✓ Back at class page');
        } catch (error) {
            console.log('✗ Navigation back failed:', error.message);
        }
    }

    async scrapeAllStudents() {
        // Get students from Supabase or local files
        const studentsToScrape = await this.studentsManager.getEnabledStudents();
        
        if (studentsToScrape.length === 0) {
            console.log('No students found in any source. Please add student names to Supabase students table, students.txt, or students.json');
            return { students: [], message: 'No students to scrape' };
        }

        console.log(`Found ${studentsToScrape.length} students to scrape:`, studentsToScrape);

        // Navigate to the class first
        await this.navigateToClass();

        // Take initial screenshot
        await this.page.screenshot({ 
            path: 'main-class-screenshot.png',
            fullPage: true 
        });

        for (let i = 0; i < studentsToScrape.length; i++) {
            const studentName = studentsToScrape[i];
            console.log(`\\n[${i + 1}/${studentsToScrape.length}] ${studentName}`);

            try {
                // Navigate to students tab
                await this.navigateToStudentsTab();

                // Click on the student
                const studentClicked = await this.clickStudentByName(studentName);
                
                if (studentClicked) {
                    // Quick screenshot and data collection
                    const studentData = await this.scrapeStudentData(studentName);
                    this.allStudentData.push(studentData);

                    // Quick navigation back
                    await this.navigateBackToClass();
                } else {
                    console.log(`⏭️  Skipping ${studentName} - not found`);
                    this.allStudentData.push({
                        studentName: studentName,
                        error: 'not_found',
                        timestamp: new Date().toISOString()
                    });
                }

            } catch (error) {
                console.log(`⚠️  Error with ${studentName}: ${error.message}`);
                this.allStudentData.push({
                    studentName: studentName,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                
                // Quick recovery - go back to class
                await this.navigateBackToClass();
            }
        }

        console.log(`\\n=== Completed scraping ${studentsToScrape.length} students ===`);
        
        return {
            totalStudents: studentsToScrape.length,
            studentsProcessed: this.allStudentData.length,
            studentsData: this.allStudentData
        };
    }

    async uploadToSupabase(data) {
        if (!this.supabase) {
            console.log('⚠️  Supabase not configured. Skipping upload...');
            return false;
        }

        try {
            console.log('🚀 Uploading data directly to Supabase...');
            
            if (!data.studentsData || !Array.isArray(data.studentsData)) {
                throw new Error('Invalid data format: studentsData array not found');
            }
            
            // Transform data for Supabase
            const supabaseData = data.studentsData
                .filter(student => student.studentName && !student.error)
                .map(student => ({
                    url: student.url,
                    timestamp: student.timestamp,
                    student_name: student.studentName,
                    recent_training: student.recentTraining || []
                }));
            
            console.log(`✅ Prepared ${supabaseData.length} valid student records`);
            
            if (supabaseData.length === 0) {
                console.log('⚠️  No valid student data to upload');
                return false;
            }
            
            const { data: result, error } = await this.supabase
                .from('membean_students')
                .insert(supabaseData);
            
            if (error) {
                throw error;
            }
            
            console.log('✅ Successfully uploaded student data to Supabase!');
            console.log(`📊 Uploaded ${supabaseData.length} student records`);
            
            const sessionCounts = supabaseData.map(s => s.recent_training.length);
            const totalSessions = sessionCounts.reduce((sum, count) => sum + count, 0);
            
            console.log(`📈 Upload Summary:`);
            console.log(`- Students: ${supabaseData.length}`);
            console.log(`- Total training sessions: ${totalSessions}`);
            console.log(`- Average sessions per student: ${(totalSessions / supabaseData.length).toFixed(1)}`);
            
            return true;
        } catch (error) {
            console.error('❌ Error uploading to Supabase:', error.message);
            if (error.details) console.error('Details:', error.details);
            if (error.hint) console.error('Hint:', error.hint);
            return false;
        }
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.log('Browser closed');
        }
    }

    async scrape() {
        try {
            await this.init();
            await this.login();
            const data = await this.scrapeAllStudents();
            
            console.log(`✅ Scraping completed - uploading to Supabase...`);
            
            // Upload directly to Supabase
            const uploadSuccess = await this.uploadToSupabase(data);
            
            if (uploadSuccess) {
                console.log(`🎉 Complete! Data scraped and uploaded to Supabase.`);
            } else {
                console.log(`⚠️  Scraping completed but upload failed. Check Supabase configuration.`);
            }
            
            return data;
        } catch (error) {
            console.error('Scraping failed:', error.message);
            throw error;
        } finally {
            await this.close();
        }
    }
}

// Run the scraper if this file is executed directly
if (require.main === module) {
    const scraper = new MembeanScraper();
    
    scraper.scrape()
        .then((data) => {
            console.log('\\n=== SCRAPING COMPLETED ===');
            console.log('Data extracted:', Object.keys(data));
            console.log('Total students processed:', data.totalStudents);
            console.log('Successfully scraped:', data.studentsProcessed);
            
            // Show training data summary
            if (data.studentsData) {
                const successfulStudents = data.studentsData.filter(s => s.recentTraining);
                const totalSessions = successfulStudents.reduce((sum, student) => sum + (student.recentTraining?.length || 0), 0);
                console.log(`Total training sessions found: ${totalSessions}`);
                
                console.log('\\nStudent Training Summary:');
                successfulStudents.forEach(student => {
                    const sessions = student.recentTraining?.length || 0;
                    console.log(`- ${student.studentName}: ${sessions} sessions`);
                });
            }
            
            console.log('\\nScreenshots created:');
            console.log('- main-class-screenshot.png (class dashboard screenshot)');
            
            // List individual student screenshots
            if (data.studentsData) {
                const successfulStudents = data.studentsData.filter(s => s.studentName);
                successfulStudents.forEach(student => {
                    const fileName = `student-${student.studentName.replace(/[^a-zA-Z0-9]/g, '_')}-screenshot.png`;
                    console.log(`- ${fileName} (${student.studentName} screenshot)`);
                });
            }
        })
        .catch((error) => {
            console.error('\\n=== SCRAPING FAILED ===');
            console.error('Error:', error.message);
            process.exit(1);
        });
}

module.exports = MembeanScraper;