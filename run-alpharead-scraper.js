#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logStep(step, message) {
  log(`${step}. ${message}`, 'blue');
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

async function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: 'inherit',
      shell: true,
      ...options
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

async function checkPrerequisites() {
  logStep(1, 'Checking prerequisites...');
  
  const scraperDir = path.join(__dirname, 'Scrapers', 'alphareadscraper');
  
  // Check if scraper directory exists
  if (!fs.existsSync(scraperDir)) {
    logError('AlphaRead scraper directory not found!');
    process.exit(1);
  }

  // Check if package.json exists
  const packageJsonPath = path.join(scraperDir, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    logError('package.json not found in AlphaRead scraper directory!');
    process.exit(1);
  }

  // Check if .env file exists
  const envPath = path.join(scraperDir, '.env');
  if (!fs.existsSync(envPath)) {
    logWarning('.env file not found. Please create it with your credentials.');
    logWarning('You can copy from env.template and fill in your details.');
  }

  logSuccess('Prerequisites check passed');
  return scraperDir;
}

async function installDependencies(scraperDir) {
  logStep(2, 'Installing dependencies...');
  
  try {
    await runCommand('npm', ['ci'], { cwd: scraperDir });
    logSuccess('Dependencies installed successfully');
  } catch (error) {
    logError('Failed to install dependencies');
    throw error;
  }
}

async function installPlaywright(scraperDir) {
  logStep(3, 'Installing Playwright browsers...');
  
  try {
    await runCommand('npx', ['playwright', 'install', 'chromium'], { cwd: scraperDir });
    logSuccess('Playwright browsers installed successfully');
  } catch (error) {
    logError('Failed to install Playwright browsers');
    throw error;
  }
}

async function runScraper(scraperDir, scraperType = 'multi') {
  logStep(4, `Running AlphaRead scraper (${scraperType})...`);
  
  try {
    const command = scraperType === 'multi' ? 'scrape-students' : 'scrape';
    
    // Set environment variable for table name
    const env = {
      ...process.env,
      TABLE_NAME: 'alpharead_students'
    };
    
    await runCommand('npm', ['run', command], { 
      cwd: scraperDir,
      env: env
    });
    logSuccess('Scraper completed successfully');
  } catch (error) {
    logError('Scraper failed to run');
    throw error;
  }
}

async function main() {
  log('🚀 AlphaRead Scraper Runner', 'bold');
  log('================================', 'blue');
  
  try {
    const scraperDir = await checkPrerequisites();
    
    // Check if node_modules exists
    const nodeModulesPath = path.join(scraperDir, 'node_modules');
    if (!fs.existsSync(nodeModulesPath)) {
      await installDependencies(scraperDir);
    } else {
      logSuccess('Dependencies already installed');
    }
    
    // Check if we need to install Playwright
    const playwrightPath = path.join(scraperDir, 'node_modules', '@playwright');
    if (!fs.existsSync(playwrightPath)) {
      await installPlaywright(scraperDir);
    } else {
      logSuccess('Playwright already installed');
    }
    
    // Parse command line arguments
    const args = process.argv.slice(2);
    const scraperType = args.includes('--single') ? 'single' : 'multi';
    
    if (scraperType === 'single') {
      log('Running single student scraper...', 'yellow');
    } else {
      log('Running multi-student scraper...', 'yellow');
    }
    
    await runScraper(scraperDir, scraperType);
    
    log('🎉 All done!', 'green');
    
  } catch (error) {
    logError(`Runner failed: ${error.message}`);
    process.exit(1);
  }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  log('AlphaRead Scraper Runner', 'bold');
  log('Usage: node run-alpharead-scraper.js [options]', 'blue');
  log('');
  log('Options:');
  log('  --single     Run single student scraper (default: multi-student)');
  log('  --help, -h   Show this help message');
  log('');
  log('Examples:');
  log('  node run-alpharead-scraper.js           # Run multi-student scraper');
  log('  node run-alpharead-scraper.js --single  # Run single student scraper');
  process.exit(0);
}

if (require.main === module) {
  main();
} 