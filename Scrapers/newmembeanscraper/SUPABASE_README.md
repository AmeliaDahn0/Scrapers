# Supabase Setup for Membean Scraper

This guide will help you set up Supabase to store your Membean student training data.

## 🚀 Quick Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up/login and create a new project
3. Wait for the project to be ready

### 2. Run the SQL Setup Script
1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the contents of `supabase-setup.sql` 
3. Paste it in the SQL Editor and click **Run**
4. This will create the `membean_students` table with proper security

### 3. Configure Environment Variables
1. In Supabase dashboard, go to **Settings** → **API**
2. Copy your **Project URL** and **anon public key**
3. Update your `.env` file:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### 4. Install Dependencies
```bash
npm install
```

## 📊 Database Schema

The `membean_students` table contains:

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key (auto-generated) |
| `url` | TEXT | Student's Membean profile URL |
| `timestamp` | TIMESTAMPTZ | When the data was scraped |
| `student_name` | TEXT | Student's name from Membean |
| `recent_training` | JSONB | Array of training sessions |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

### Recent Training JSON Structure
```json
[
  {
    "startedAt": "Aug 7, 2025 at 3:15 pm",
    "length": "9 mins",
    "accuracy": "84%"
  }
]
```

## 🔐 Security (RLS Policies)

The table has Row Level Security enabled with policies that allow:
- ✅ **INSERT** - Anyone can add new data
- ✅ **SELECT** - Anyone can read data  
- ✅ **UPDATE** - Anyone can modify data
- ✅ **DELETE** - Anyone can delete data

*Note: Adjust these policies in production for proper access control*

## 🎯 Usage

### Upload Latest Scraped Data
```bash
npm run upload
```

### Scrape and Upload in One Command
```bash
npm run scrape-and-upload
```

### Upload Specific File
```bash
node upload-to-supabase.js students-data-2025-08-11T02-36-34-854Z.json
```

## 📈 Querying Your Data

### View All Students
```sql
SELECT student_name, timestamp, 
       jsonb_array_length(recent_training) as session_count
FROM membean_students 
ORDER BY timestamp DESC;
```

### Get Students with No Recent Training
```sql
SELECT student_name, timestamp
FROM membean_students 
WHERE jsonb_array_length(recent_training) = 0;
```

### Find Students by Training Session Count
```sql
SELECT student_name, 
       jsonb_array_length(recent_training) as sessions
FROM membean_students 
WHERE jsonb_array_length(recent_training) >= 5
ORDER BY sessions DESC;
```

### Extract Individual Training Sessions
```sql
SELECT 
    student_name,
    session->>'startedAt' as started_at,
    session->>'length' as duration,
    session->>'accuracy' as accuracy
FROM membean_students,
     jsonb_array_elements(recent_training) as session
ORDER BY student_name, started_at;
```

## 🔧 Troubleshooting

### "Missing Supabase configuration" Error
- Make sure you've added `SUPABASE_URL` and `SUPABASE_ANON_KEY` to your `.env` file
- Check that the values don't have extra spaces or quotes

### "Table doesn't exist" Error  
- Run the `supabase-setup.sql` script in your Supabase SQL Editor
- Make sure the script completed without errors

### Upload Fails
- Check your internet connection
- Verify your Supabase project is active
- Ensure the API key has the correct permissions

## 🎉 Success!

Once set up, you can:
- Automatically upload all scraped data to Supabase
- Query and analyze student training patterns over time
- Build dashboards and reports using your data
- Export data for further analysis