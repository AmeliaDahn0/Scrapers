# Alpha Read Scraper

A Playwright-based web scraper for the Alpha Read sign-in page at https://alpharead.alpha.school/signin.

## Features

- Scrapes page content including headings, forms, links, and meta data
- **Login functionality** - Can automatically log in with provided credentials
- **Database integration** - Automatic upload to Supabase database
- Takes full-page screenshots (before and after login)
- Saves scraped data to JSON format
- Handles sign-in page elements detection
- User-agent spoofing to avoid bot detection
- Environment variable support for secure credential storage
- Batch processing with error handling and retry logic

## Setup

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npm run install-browsers
```

3. Configure credentials (optional for login functionality):

The `.env` file should already be created. Edit it with your actual credentials:
```
ALPHAREAD_EMAIL=your.actual.email@example.com
ALPHAREAD_PASSWORD=your_actual_password
ENABLE_LOGIN=true
SHOW_BROWSER=false
```

## Usage

Run the scraper:
```bash
npm run scrape
```

Run the multi-student scraper:
```bash
npm run scrape-students
```

Upload existing data to database:
```bash
npm run upload-existing
```

Or directly with Node.js:
```bash
node scraper.js          # Single page scraping
node multi-email-scraper.js  # Multi-student scraping
```

## Output

### Single Page Scraper
- `alpharead-data.json` - Complete scraped data in JSON format
- `alpharead-screenshot.png` - Full-page screenshot of the website
- Console output with summary of scraped data

### Multi-Student Scraper
- `student-data-[timestamp].json` - All student data in one file
- `student-[email]-profile.png` - Individual screenshots for each student
- Console output with progress for each student

## Data Collected

The scraper extracts:
- Page title and URL
- All headings (h1-h6)
- Form elements (inputs, buttons)
- Sign-in options and buttons
- All links on the page
- Meta tags
- Screenshots for visual reference

## Configuration

### Environment Variables (.env file)
- `ALPHAREAD_EMAIL` - Your Alpha Read account email
- `ALPHAREAD_PASSWORD` - Your Alpha Read account password  
- `ENABLE_LOGIN=true` - Enable automatic login functionality
- `SHOW_BROWSER=true` - Show browser window (useful for debugging)

### Code Configuration (scraper.js and config.js)
- Modify `config.js` for general settings
- Set browser options (headless mode, timing)
- Customize selectors to target specific elements
- Adjust wait conditions and timeouts

## Login Functionality

The scraper can automatically log in to Alpha Read if you provide credentials:

1. Set `ENABLE_LOGIN=true` in your `.env` file
2. Add your email and password to the `.env` file
3. Run the scraper - it will automatically:
   - Fill in the email and password fields
   - Click the sign-in button
   - Wait for successful login/redirect
   - Continue scraping the authenticated page

### Debugging Login Issues
- Set `SHOW_BROWSER=true` to watch the login process
- Check console output for detailed login status
- The scraper will detect and report login errors

## Multi-Student Scraping

To scrape data for multiple students:

1. **Setup your database** with student records:
   - **Primary method**: Add students to the `students` table in your Supabase database
   - **Fallback method**: Use `emails.txt` or `emails.json` files (not recommended for production)

2. **Test your database connection**:
```bash
npm run test-students-db
```

3. **Run the multi-student scraper**:
```bash
npm run scrape-students
```

### Database Method (Recommended)

The scraper now fetches student lists from your Supabase database for security reasons. Add students to your `students` table:

```sql
-- Add students to your database
INSERT INTO students (name, email) VALUES 
  ('John Doe', 'john.doe@example.com'),
  ('Jane Smith', 'jane.smith@example.com');
```

**Benefits of database method:**
- ✅ **Security**: No student data stored in code repository
- ✅ **Centralized**: Single source of truth for student lists  
- ✅ **Flexible**: Easy to add/remove students via database
- ✅ **Scalable**: No file size limitations

### File-Based Method (Fallback)

**emails.txt format:**
```
student1@example.com
student2@example.com
student3@example.com
```

**emails.json format:**
```json
{
  "emails": [
    {
      "email": "student1@example.com",
      "name": "Student One",
      "notes": "Grade 10 student"
    }
  ]
}
```

⚠️ **Note**: File-based methods are kept as fallback but not recommended for production use due to security concerns.

### How It Works

The multi-student scraper will:
1. **Fetch student list** from database (or files as fallback)
2. **Log in once** with your credentials
3. **Navigate** to Student Management
4. **Search** for each student individually
5. **Extract** their profile data
6. **Take screenshots** of each profile
7. **Save** all data to a timestamped JSON file
8. **Upload** to database (if enabled)

## Notes

- The scraper respects the website's structure as of the time it was created
- Some dynamic content might require additional wait conditions
- Login credentials are stored securely in environment variables
- The scraper can work both with and without login functionality

## Supabase Database Integration

The scraper can automatically upload student data to a Supabase database for easy analysis and storage.

### Setup Supabase

1. **Create a Supabase project** at https://app.supabase.com

2. **Create the required database tables** by running this SQL in your Supabase SQL Editor:
```sql
-- Copy and paste the contents of create_student_table.sql

-- Also create the students table for the student list:
CREATE TABLE IF NOT EXISTS students (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT NULL,
  created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT timezone('utc'::text, now()),
  CONSTRAINT students_pkey PRIMARY KEY (id),
  CONSTRAINT students_email_key UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_students_name ON students USING btree (name);
CREATE INDEX IF NOT EXISTS idx_students_email ON students USING btree (email);
```

3. **Get your credentials** from Project Settings > API:
   - Project URL (looks like: `https://your-project-ref.supabase.co`)
   - Anon key (for basic operations)
   - Service role key (for admin operations - recommended)

4. **Configure your .env file**:
```bash
# Copy env.template to .env and add your credentials
cp env.template .env
```

Then edit `.env` with your actual Supabase credentials:
```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
ENABLE_DATABASE_UPLOAD=true
```

**⚠️ Important Security Note**: The service role key has admin privileges and bypasses all Row Level Security (RLS) policies. It should only be used in backend scripts like this scraper. Never expose it in frontend code or client-side applications.

5. **Verify your configuration**:
```bash
npm run verify-service-role
```

### Database Features

- **Automatic upload** - Data is uploaded after each scraping session
- **Duplicate prevention** - Won't create duplicate records for same email/time
- **Error handling** - Failed uploads are logged and can be retried
- **Existing data upload** - Can upload previously scraped JSON files

### Upload Commands

```bash
# Upload during scraping (automatic if enabled)
npm run scrape-students

# Verify service role key configuration
npm run verify-service-role
```

# Upload existing JSON files
npm run upload-existing                           # Most recent file
npm run upload-existing student-data-*.json      # Specific file
```

### Database Schema

The `student_data` table includes:
- Student profile information (grade, reading level, scores)
- Progress metrics (sessions, time reading, success rate)
- Timestamps and metadata
- Automatic indexing for efficient queries

## Legal Notice

Please ensure you comply with the website's terms of service and robots.txt when scraping. This tool is for educational and legitimate research purposes only. 