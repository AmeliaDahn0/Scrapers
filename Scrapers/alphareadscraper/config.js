// Configuration file for Alpha Read Scraper
require('dotenv').config();

module.exports = {
  // Target URL
  url: 'https://alpharead.alpha.school/signin',
  
  // Browser settings (can be overridden by environment variables)
  browser: {
    headless: process.env.SHOW_BROWSER !== 'true', // Can be overridden by SHOW_BROWSER env var
    slowMo: 1000,   // Slow down operations (in milliseconds)
    timeout: 30000  // Page load timeout (in milliseconds)
  },
  
  // Login settings
  login: {
    enabled: process.env.ENABLE_LOGIN === 'true',
    email: process.env.ALPHAREAD_EMAIL,
    password: process.env.ALPHAREAD_PASSWORD
  },
  
  // User agent to avoid bot detection
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  
  // Output settings
  output: {
    screenshot: 'alpharead-screenshot.png',
    dataFile: 'alpharead-data.json',
    fullPageScreenshot: true
  },
  
  // What to scrape
  scrapeOptions: {
    title: true,
    headings: true,
    forms: true,
    links: true,
    metaTags: true,
    signInOptions: true,
    inputFields: true,
    screenshots: true
  },
  
  // Custom selectors (modify these to target specific elements)
  selectors: {
    mainHeading: 'h1',
    allHeadings: 'h1, h2, h3, h4, h5, h6',
    forms: 'form',
    inputs: 'input',
    buttons: 'button',
    links: 'a',
    signInElements: 'button, a', // Elements that might be sign-in related
    // Alpha Read specific selectors
    emailInput: 'input[type="email"][placeholder="you@example.com"]',
    passwordInput: 'input[type="password"][placeholder="Password"]',
    submitButton: 'button[type="submit"]:has-text("Sign in")',
    googleSignInButton: 'button:has-text("Sign in with") svg'
  },
  
  // Keywords to identify sign-in elements
  signInKeywords: ['sign', 'google', 'login', 'signin', 'log in'],
  
  // Wait conditions
  waitConditions: {
    networkIdle: true,
    domContentLoaded: false,
    load: false
  }
}; 