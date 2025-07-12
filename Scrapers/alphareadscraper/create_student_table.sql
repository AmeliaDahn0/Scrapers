-- SQL query to create the student_data table in Supabase
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS student_data (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    scraped_at TIMESTAMP NOT NULL,
    profile_url TEXT,
    grade_level INTEGER,
    reading_level INTEGER,
    average_score VARCHAR(10), -- Storing as string since it includes %
    sessions_this_month INTEGER,
    total_sessions INTEGER,
    time_reading VARCHAR(20), -- Storing as string like "2h 36m"
    success_rate VARCHAR(10), -- Storing as string since it includes %
    last_active VARCHAR(50), -- Storing as string since format varies like "Mar 6"
    avg_session_time VARCHAR(10), -- Storing as string like "10m"
    current_course TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_student_data_email ON student_data(email);
CREATE INDEX IF NOT EXISTS idx_student_data_scraped_at ON student_data(scraped_at);
CREATE INDEX IF NOT EXISTS idx_student_data_grade_level ON student_data(grade_level);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_student_data_updated_at 
    BEFORE UPDATE ON student_data 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a unique constraint to prevent duplicate entries for the same email and scrape time
CREATE UNIQUE INDEX IF NOT EXISTS idx_student_data_email_scraped_at 
ON student_data(email, scraped_at); 