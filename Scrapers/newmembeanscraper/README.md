# Membean Dashboard Scraper

A Node.js scraper built with Playwright to extract data from the Membean dashboard.

## Features

- ✅ Automated login to Membean
- ✅ Dashboard data extraction
- ✅ Full-page screenshot capture
- ✅ JSON data export
- ✅ Support for multiple browsers (Chromium, Firefox, WebKit)
- ✅ Configurable headless/headed mode
- ✅ Environment-based credential management

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Install Browser Binaries

```bash
npm run install-browsers
```

### 3. Configure Credentials

Edit the `.env` file and replace the placeholder values with your actual Membean credentials:

```env
MEMBEAN_USERNAME=your_actual_username
MEMBEAN_PASSWORD=your_actual_password
HEADLESS=true
BROWSER=chromium
```

**Important:** Keep your `.env` file secure and never commit it to version control.

## Usage

### Run the Scraper

```bash
npm start
```

or

```bash
node scraper.js
```

### Output Files

The scraper generates two files:

1. **`dashboard-data.json`** - Contains extracted dashboard data in JSON format
2. **`dashboard-screenshot.png`** - Full-page screenshot of the dashboard

### Configuration Options

You can customize the scraper behavior by modifying the `.env` file:

- **`HEADLESS`**: Set to `false` to see the browser in action (useful for debugging)
- **`BROWSER`**: Choose between `chromium`, `firefox`, or `webkit`

## Data Structure

The scraper extracts the following information from the dashboard:

```json
{
  "url": "https://membean.com/dashboard",
  "title": "Dashboard - Membean",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "user": "Username",
  "progress": [...],
  "activities": [...],
  "vocabulary": [...],
  "pageText": "Complete page text content"
}
```

## Error Handling

The scraper includes comprehensive error handling:

- ❌ Missing or invalid credentials
- ❌ Login failures
- ❌ Network timeouts
- ❌ Page load errors

## Troubleshooting

### Login Issues
- Verify your username and password in the `.env` file
- Check if your Membean account is active
- Try running in headed mode (`HEADLESS=false`) to see what's happening

### Browser Issues
- Run `npm run install-browsers` to ensure browser binaries are installed
- Try different browsers by changing the `BROWSER` setting

### Network Issues
- Check your internet connection
- Verify that Membean is accessible from your network

## Development

### Using the Scraper as a Module

```javascript
const MembeanScraper = require('./scraper');

const scraper = new MembeanScraper();
scraper.scrape()
  .then(data => {
    console.log('Scraped data:', data);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

### Extending the Scraper

The scraper is designed to be easily extensible. You can modify the `scrapeDashboard()` method to extract additional data or customize the extraction logic.

## Legal Notice

This scraper is for educational and personal use only. Make sure you comply with Membean's Terms of Service and use this tool responsibly. Always respect rate limits and avoid overloading their servers.

## License

MIT License