# Single Table Setup Guide

## 🎯 Problem Solved
The enhanced scraper accidentally created a second table (`student_performance_summary`). This guide consolidates everything into the single `acely_students` table as requested.

## 🔧 Step 1: Run the Fix Script

In your Supabase SQL Editor, copy and paste the contents of `fix_single_table_schema.sql`:

```bash
# This script will:
# 1. DROP the extra student_performance_summary table
# 2. Add all necessary columns to acely_students table
# 3. Create proper indexes for performance
# 4. Ensure everything is in ONE table
```

## 🚀 Step 2: Test the Enhanced Scraper

After running the SQL script, test that everything works:

```bash
python3 acely_scraper_enhanced.py
```

## 📊 Step 3: Verify Single Table Structure

After running, you should have only ONE table with all data:

```sql
-- Check table structure
\d+ acely_students

-- View all data in single table
SELECT student_email, most_recent_score, 
       jsonb_array_length(mock_exam_results) as exam_count,
       activity_summary->>'total_active_days' as active_days
FROM acely_students;

-- Verify no extra tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%student%';
```

## ✅ Expected Result

After the fix:
- ✅ Only `acely_students` table exists
- ✅ All comprehensive data in one place
- ✅ Enhanced scraper uploads to single table
- ✅ All metrics available for querying

## 📋 Single Table Schema

The final `acely_students` table will contain:

### Original Columns
- `id`, `scrape_timestamp`, `student_email`, `most_recent_score`
- `student_name`, `join_date`, `this_week_questions`, `last_week_questions`
- `performance_by_topic`, `weekly_performance`, `daily_activity`
- `strongest_weakest_areas`, `analytics_data`, `assignments`
- `mock_exam_results`, `raw_sections`, `created_at`, `updated_at`

### Enhanced Columns Added
- `total_active_days`, `total_questions_attempted`, `data_richness_score`
- `activity_summary`, `performance_summary`, `exam_summary`
- `math_avg_score`, `reading_avg_score`, `overall_avg_score`
- `subject`, `last_activity_date`, `improvement_trend`
- And many more comprehensive tracking fields!

Everything consolidated into ONE powerful table! 🎯 