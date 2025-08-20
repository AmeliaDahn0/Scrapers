-- =====================================================
-- FastMath Students Table Creation Script for Supabase
-- =====================================================
-- Run this script in your Supabase SQL Editor to create 
-- the Fastmath_students table with all necessary fields
-- =====================================================

-- Drop table if it exists (optional - remove this line if you want to keep existing data)
DROP TABLE IF EXISTS Fastmath_students;

-- Create the Fastmath_students table
CREATE TABLE Fastmath_students (
    -- Primary key and metadata
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Student identification
    student_name TEXT NOT NULL,
    scrape_timestamp TIMESTAMPTZ NOT NULL,
    
    -- Campus information (consistent across all tabs)
    campus TEXT,
    last_active TEXT,
    
    -- Time Spent tab data
    time_spent_active_track TEXT,
    time_spent_time_today TEXT,
    time_spent_time_last_7_days TEXT,
    
    -- Progress tab data  
    progress_last_active TEXT,
    
    -- CQPM tab data
    cqpm_last_active TEXT,
    cqpm_latest_score TEXT,
    cqpm_previous_score TEXT,
    
    -- Constraints
    UNIQUE(student_name, scrape_timestamp)
);

-- Create indexes for better query performance
CREATE INDEX idx_fastmath_students_name ON Fastmath_students(student_name);
CREATE INDEX idx_fastmath_students_timestamp ON Fastmath_students(scrape_timestamp);
CREATE INDEX idx_fastmath_students_campus ON Fastmath_students(campus);
CREATE INDEX idx_fastmath_students_created_at ON Fastmath_students(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE Fastmath_students ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations for authenticated users
-- (Adjust this policy based on your security requirements)
CREATE POLICY "Allow all operations for authenticated users" ON Fastmath_students
    FOR ALL USING (auth.role() = 'authenticated');

-- Alternatively, if you want to allow public access (not recommended for production):
-- CREATE POLICY "Allow all operations for everyone" ON Fastmath_students
--     FOR ALL USING (true);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update updated_at on record changes
CREATE TRIGGER update_fastmath_students_updated_at 
    BEFORE UPDATE ON Fastmath_students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add some helpful comments to the table
COMMENT ON TABLE Fastmath_students IS 'FastMath student dashboard data scraped from admin interface';
COMMENT ON COLUMN Fastmath_students.student_name IS 'Full name of the student';
COMMENT ON COLUMN Fastmath_students.scrape_timestamp IS 'When this data was scraped from the dashboard';
COMMENT ON COLUMN Fastmath_students.campus IS 'Student campus (e.g., alpha-high-school, high-school-sat-prep)';
COMMENT ON COLUMN Fastmath_students.time_spent_active_track IS 'Current active track from Time Spent tab';
COMMENT ON COLUMN Fastmath_students.cqpm_latest_score IS 'Latest CQPM score';
COMMENT ON COLUMN Fastmath_students.cqpm_previous_score IS 'Previous CQPM score';

-- Display table structure (run this separately if you want to see table details)
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'fastmath_students';

-- =====================================================
-- Script completed successfully!
-- 
-- Your Fastmath_students table is now ready to receive
-- data from your scraper.
--
-- Next steps:
-- 1. Verify the table was created: SELECT * FROM Fastmath_students;
-- 2. Adjust RLS policies if needed for your security requirements
-- 3. Update your scraper to insert data into this table
-- =====================================================