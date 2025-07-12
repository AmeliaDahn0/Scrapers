# Supabase Security Setup Guide

## 🔐 Service Role Key Configuration for Backend-Only Use

This guide explains how to properly configure your Supabase service role key for secure backend operations that bypass Row Level Security (RLS) policies.

## ⚠️ Security Warning

**NEVER expose the service role key in frontend code or client-side applications.** The service role key has admin privileges and can bypass all RLS policies. It should only be used in:
- Server-side applications
- Backend scripts (like this scraper)
- API routes
- Serverless functions

## 🛠️ Setup Steps

### 1. Get Your Service Role Key

1. Go to your Supabase project dashboard: https://app.supabase.com
2. Navigate to **Settings** → **API**
3. Copy your **Service Role Key** (not the anon key)
4. The service role key starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 2. Configure Environment Variables

1. Copy the environment template:
```bash
cp env.template .env
```

2. Edit your `.env` file and add your service role key:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-service-role-key-here
ENABLE_DATABASE_UPLOAD=true
```

### 3. Verify Configuration

Test your database connection:
```bash
npm run test-students-db
```

You should see:
```
✅ Supabase client initialized
✅ Database connection successful
```

## 🔒 Security Best Practices

### ✅ Do This (Backend/Script Usage)
- Use service role key in Node.js scripts
- Use service role key in server-side API routes
- Use service role key in serverless functions
- Store service role key in environment variables
- Use service role key for admin operations

### ❌ Never Do This (Frontend/Client Usage)
- Don't use service role key in React/Vue/Angular apps
- Don't use service role key in browser JavaScript
- Don't expose service role key in client-side code
- Don't commit service role key to version control
- Don't use service role key for user-facing operations

## 🏗️ RLS Policy Setup

With your service role key, you can now set up proper RLS policies for your tables:

### Example RLS Policies

```sql
-- Enable RLS on your tables
ALTER TABLE student_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Policy for student_data table
CREATE POLICY "Allow authenticated users to read their own data" ON student_data
  FOR SELECT USING (auth.uid()::text = email);

-- Policy for students table  
CREATE POLICY "Allow authenticated users to read students" ON students
  FOR SELECT USING (auth.role() = 'authenticated');

-- Policy for service role to bypass RLS (automatic with service role key)
-- No additional policy needed - service role key bypasses all RLS
```

## 🧪 Testing Your Setup

### Test Database Connection
```bash
npm run test-students-db
```

### Test Upload Functionality
```bash
npm run test-upload
```

### Test Full Scraper
```bash
npm run scrape-students
```

## 🔍 Troubleshooting

### Common Issues

1. **"Database upload is disabled"**
   - Check that `ENABLE_DATABASE_UPLOAD=true` in your `.env`
   - Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set

2. **"Supabase credentials not found"**
   - Ensure your `.env` file exists and has the correct variables
   - Check that the service role key is copied correctly

3. **"Permission denied" errors**
   - Verify you're using the service role key (not anon key)
   - Check that your Supabase project has the correct tables created

4. **RLS policy blocking operations**
   - The service role key should bypass RLS automatically
   - If you're still getting RLS errors, double-check you're using the service role key

### Debug Commands

```bash
# Test database connection
npm run test-students-db

# Test upload functionality  
npm run test-upload

# Debug table structure
npm run debug-table

# Test login functionality
npm run test-login
```

## 📋 Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for admin operations | ✅ |
| `ENABLE_DATABASE_UPLOAD` | Enable/disable database uploads | ✅ |
| `TABLE_NAME` | Name of the table to upload to | ❌ (defaults to 'student_data') |

## 🔄 Key Rotation

If you need to rotate your service role key:

1. Go to Supabase dashboard → Settings → API
2. Click "Regenerate" next to Service Role Key
3. Update your `.env` file with the new key
4. Test the connection: `npm run test-students-db`

## 📚 Additional Resources

- [Supabase Service Role Key Documentation](https://supabase.com/docs/guides/auth/row-level-security#service-role-key)
- [RLS Policy Examples](https://supabase.com/docs/guides/auth/row-level-security#examples)
- [Environment Variables Best Practices](https://supabase.com/docs/guides/getting-started/environment-variables) 