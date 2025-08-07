-- Supabase Table Setup for Acely Student Data
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for clean setup)
DROP TABLE IF EXISTS acely_students;

-- Create the main table for storing scraped student data
CREATE TABLE acely_students (
    id BIGSERIAL PRIMARY KEY,
    
    -- Scraping session metadata
    scrape_timestamp TIMESTAMPTZ NOT NULL,
    total_students_requested INTEGER,
    students_found INTEGER,
    students_scraped INTEGER,
    scrape_errors JSONB DEFAULT '[]'::jsonb,
    scrape_summary JSONB DEFAULT '{}'::jsonb,
    
    -- Individual student data
    student_email TEXT NOT NULL,
    student_timestamp TIMESTAMPTZ,
    student_url TEXT,
    page_title TEXT,
    
    -- Core profile information (flattened for easy querying)
    most_recent_score INTEGER,
    student_name TEXT,
    join_date TEXT,
    this_week_questions INTEGER,
    last_week_questions INTEGER,
    subject TEXT,
    
    -- Complex nested data stored as JSONB for flexibility
    performance_by_topic JSONB DEFAULT '{}'::jsonb,
    weekly_performance JSONB DEFAULT '{}'::jsonb,
    daily_activity JSONB DEFAULT '{}'::jsonb,
    strongest_weakest_areas JSONB DEFAULT '{}'::jsonb,
    analytics_data JSONB DEFAULT '{}'::jsonb,
    assignments JSONB DEFAULT '[]'::jsonb,
    charts_data JSONB DEFAULT '{}'::jsonb,
    mock_exam_results JSONB DEFAULT '[]'::jsonb,
    raw_sections JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_acely_students_email ON acely_students(student_email);
CREATE INDEX idx_acely_students_scrape_timestamp ON acely_students(scrape_timestamp);
CREATE INDEX idx_acely_students_student_name ON acely_students(student_name);
CREATE INDEX idx_acely_students_most_recent_score ON acely_students(most_recent_score);
CREATE INDEX idx_acely_students_subject ON acely_students(subject);

-- Create GIN indexes for JSONB columns for fast JSON queries
CREATE INDEX idx_acely_students_performance_gin ON acely_students USING GIN(performance_by_topic);
CREATE INDEX idx_acely_students_daily_activity_gin ON acely_students USING GIN(daily_activity);
CREATE INDEX idx_acely_students_mock_exams_gin ON acely_students USING GIN(mock_exam_results);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_acely_students_updated_at 
    BEFORE UPDATE ON acely_students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (optional, but recommended)
ALTER TABLE acely_students ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on acely_students" ON acely_students
    FOR ALL USING (true) WITH CHECK (true);

-- Grant permissions (adjust role as needed)
GRANT ALL ON acely_students TO authenticated;
GRANT ALL ON acely_students TO anon;

COMMENT ON TABLE acely_students IS 'Stores scraped student data from Acely admin console';
COMMENT ON COLUMN acely_students.scrape_timestamp IS 'When the scraping session was initiated';
COMMENT ON COLUMN acely_students.student_email IS 'Primary identifier for the student';
COMMENT ON COLUMN acely_students.most_recent_score IS 'Student''s most recent test score';
COMMENT ON COLUMN acely_students.performance_by_topic IS 'JSON data containing performance metrics by subject topic';
COMMENT ON COLUMN acely_students.daily_activity IS 'JSON data containing daily activity calendars and question counts';
COMMENT ON COLUMN acely_students.mock_exam_results IS 'JSON array containing all mock exam results with scores and dates'; 