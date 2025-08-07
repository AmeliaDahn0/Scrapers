# Supabase Integration Setup Guide

This guide will help you set up automatic upload of Acely scraped data to Supabase.

## 🚀 Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Wait for the project to be ready (usually 1-2 minutes)

### 2. Get Your Supabase Credentials

1. In your Supabase dashboard, go to **Settings** > **API**
2. Copy these two values:
   - **Project URL** (looks like `https://abcdefg.supabase.co`)
   - **anon/public key** (long string starting with `eyJ...`)

### 3. Create the Database Table

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy and paste the entire contents of `supabase_setup.sql`
3. Click **Run** to create the table and indexes

### 4. Install Dependencies

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install the supabase package
pip install supabase
```

### 5. Update Your .env File

Add these lines to your `.env` file:

```env
# Existing Acely credentials
ACELY_EMAIL=your_gmail@gmail.com
ACELY_PASSWORD=your_google_password
HEADLESS_MODE=True
WAIT_TIMEOUT=10
DOWNLOAD_DELAY=1

# NEW: Add Supabase credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 📊 Usage Options

### Option 1: Run Scraper with Auto-Upload (Recommended)

```bash
source venv/bin/activate
python3 acely_scraper_with_supabase.py
```

This will:
- Scrape student data
- Save JSON file locally
- Automatically upload to Supabase
- Show upload status

### Option 2: Manual Upload of Existing JSON Files

```bash
source venv/bin/activate

# Upload the latest JSON file
python3 supabase_uploader.py

# Upload a specific JSON file
python3 supabase_uploader.py acely_student_data_20250804_160059.json
```

### Option 3: Original Scraper (No Upload)

```bash
source venv/bin/activate
python3 acely_scraper.py
# Then manually upload later with supabase_uploader.py
```

## 🔍 Querying Your Data in Supabase

Once uploaded, you can query your data in the Supabase **SQL Editor**:

### Basic Queries

```sql
-- View all students
SELECT student_name, student_email, most_recent_score, subject, created_at 
FROM acely_students 
ORDER BY created_at DESC;

-- Students with high scores
SELECT student_name, most_recent_score, subject
FROM acely_students 
WHERE most_recent_score > 1400
ORDER BY most_recent_score DESC;

-- Count students by subject
SELECT subject, COUNT(*) as student_count
FROM acely_students 
GROUP BY subject;

-- Latest scraping session
SELECT scrape_timestamp, total_students_requested, students_scraped
FROM acely_students 
ORDER BY scrape_timestamp DESC 
LIMIT 1;
```

### Advanced JSON Queries

```sql
-- Students with mock exam results
SELECT 
    student_name,
    student_email,
    jsonb_array_length(mock_exam_results) as total_exams
FROM acely_students 
WHERE jsonb_array_length(mock_exam_results) > 0;

-- Get specific exam scores
SELECT 
    student_name,
    exam->>'exam_type' as exam_type,
    exam->>'score' as score,
    exam->>'completion_date' as date
FROM acely_students,
jsonb_array_elements(mock_exam_results) as exam
WHERE exam->>'exam_type' = 'Math Exam'
ORDER BY (exam->>'raw_score')::int DESC;

-- Performance by topic breakdown
SELECT 
    student_name,
    topic_key,
    topic_value->>'percentages' as percentages
FROM acely_students,
jsonb_each(performance_by_topic) as topic(topic_key, topic_value)
WHERE topic_value->>'percentages' IS NOT NULL;
```

## 🛠️ Database Schema

The `acely_students` table includes:

### Core Fields
- `student_email` - Primary identifier
- `student_name` - Student's name
- `most_recent_score` - Latest test score
- `subject` - SAT, ACT, etc.
- `scrape_timestamp` - When data was scraped

### JSON Fields (for complex data)
- `performance_by_topic` - Performance by subject area
- `daily_activity` - Activity calendars with question counts
- `mock_exam_results` - All exam results with scores
- `strongest_weakest_areas` - Performance analysis
- `assignments` - Assignment data
- `raw_sections` - Complete page text

## 🔒 Security Notes

- Your `.env` file is already in `.gitignore` and won't be committed
- The Supabase anon key is safe to use in client applications
- Row Level Security is enabled on the table
- Consider setting up more restrictive policies for production use

## 📈 Monitoring and Analytics

You can build dashboards and analytics on top of your data:

1. **Supabase Dashboard**: Use the built-in charts and metrics
2. **External Tools**: Connect tools like Metabase, Grafana, or Retool
3. **Custom Apps**: Build React/Next.js apps with Supabase client libraries

## 🆘 Troubleshooting

### Common Issues

1. **"Missing Supabase credentials"**
   - Check your `.env` file has `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Verify the values are correct (no extra spaces)

2. **"Table 'acely_students' doesn't exist"**
   - Run the SQL script from `supabase_setup.sql` in your Supabase SQL editor

3. **"Permission denied"**
   - Check that Row Level Security policies allow your operations
   - Verify your anon key is correct

4. **Upload fails silently**
   - Check the Supabase logs in your dashboard
   - Ensure your project isn't over the free tier limits

### Support

- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Community**: [discord.gg/supabase](https://discord.gg/supabase)

## 🎯 Next Steps

1. Set up the table and credentials
2. Run a test scrape with auto-upload
3. Explore your data in the Supabase dashboard
4. Build custom queries for your specific needs
5. Consider setting up automated scraping with cron jobs 