# Math Academy Teacher Dashboard Scraper

This script uses Playwright to log into Math Academy and extract information from the teacher dashboard.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Configure your credentials:
   - Copy the contents of `.env.example` to a new file named `.env`
   - Update the `.env` file with your Math Academy credentials and Supabase service key:
     ```
     MATH_ACADEMY_USERNAME=your_username
     MATH_ACADEMY_PASSWORD=your_password
     SUPABASE_URL=your_supabase_project_url
     SUPABASE_SERVICE_KEY=your_supabase_service_key
     ```
     
   **⚠️ IMPORTANT SECURITY NOTES:**
   - Use `SUPABASE_SERVICE_KEY` (not the anon key) for backend operations
   - The service key bypasses Row Level Security (RLS) policies
   - **NEVER expose the service key in frontend code or client-side applications**
   - Keep your `.env` file secure and never commit it to version control
   - The `.env` file is already in `.gitignore` for security

## Security Configuration

### Getting Your Supabase Service Key

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy the **service_role** key (NOT the anon key)
4. Add it to your `.env` file as `SUPABASE_SERVICE_KEY`

### Environment Variables Structure

Create a `.env` file with the following structure:
```
MATH_ACADEMY_USERNAME=your_username
MATH_ACADEMY_PASSWORD=your_password
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## Usage

### 1. Test Your Configuration

Before running the scraper, test your setup:
```bash
python test_connection.py
```

This will verify:
- Your Supabase service key is working
- You have write access to the database
- Your Math Academy credentials are configured

### 2. Run the Scraper

Once the test passes, run the scraper:
```bash
python scraper.py
```

The script will:
1. Launch a browser window (headless mode)
2. Log into Math Academy using your credentials
3. Navigate to the teacher dashboard
4. Extract comprehensive student information and save it to Supabase

## Notes

- The script runs in headless mode for production use
- All data is automatically saved to your Supabase database
- Each run creates new records with timestamps for historical tracking 