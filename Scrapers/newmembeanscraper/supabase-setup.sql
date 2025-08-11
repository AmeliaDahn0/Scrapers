-- Supabase Table Setup for Membean Students Data
-- Run this script in the Supabase SQL Editor

-- Create the membean_students table
CREATE TABLE IF NOT EXISTS membean_students (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    student_name TEXT NOT NULL,
    recent_training JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_membean_students_timestamp ON membean_students(timestamp);
CREATE INDEX IF NOT EXISTS idx_membean_students_student_name ON membean_students(student_name);
CREATE INDEX IF NOT EXISTS idx_membean_students_created_at ON membean_students(created_at);

-- Create a GIN index for JSONB queries on recent_training
CREATE INDEX IF NOT EXISTS idx_membean_students_recent_training ON membean_students USING GIN(recent_training);

-- Enable Row Level Security (RLS)
ALTER TABLE membean_students ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Policy to allow anyone to insert data
CREATE POLICY "Allow insert for all users" ON membean_students
    FOR INSERT
    WITH CHECK (true);

-- Policy to allow anyone to select/view data
CREATE POLICY "Allow select for all users" ON membean_students
    FOR SELECT
    USING (true);

-- Policy to allow anyone to update data
CREATE POLICY "Allow update for all users" ON membean_students
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Policy to allow anyone to delete data (optional - remove if you don't want delete access)
CREATE POLICY "Allow delete for all users" ON membean_students
    FOR DELETE
    USING (true);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update updated_at on row updates
CREATE TRIGGER update_membean_students_updated_at
    BEFORE UPDATE ON membean_students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add some helpful comments
COMMENT ON TABLE membean_students IS 'Stores Membean student training data scraped from the dashboard';
COMMENT ON COLUMN membean_students.url IS 'Student profile URL from Membean';
COMMENT ON COLUMN membean_students.timestamp IS 'When the data was scraped';
COMMENT ON COLUMN membean_students.student_name IS 'Student name from Membean profile';
COMMENT ON COLUMN membean_students.recent_training IS 'JSON array of recent training sessions with startedAt, length, and accuracy';
COMMENT ON COLUMN membean_students.created_at IS 'When this record was first created';
COMMENT ON COLUMN membean_students.updated_at IS 'When this record was last updated';

-- Verify the table was created successfully
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'membean_students' 
ORDER BY ordinal_position;