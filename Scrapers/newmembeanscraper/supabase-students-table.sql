-- Create students table for managing student list in Supabase
-- Run this script in the Supabase SQL Editor

-- Create the students table
CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT true,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Policy for allowing authenticated users to manage students
CREATE POLICY "Allow authenticated users to manage students" ON students
FOR ALL USING (auth.role() = 'authenticated');

-- Add indexes for performance
CREATE INDEX idx_students_name ON students (name);
CREATE INDEX idx_students_enabled ON students (enabled);

-- Add trigger to update 'updated_at' timestamp on row update
CREATE OR REPLACE FUNCTION update_students_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_students_updated_at
BEFORE UPDATE ON students
FOR EACH ROW EXECUTE FUNCTION update_students_updated_at_column();

-- Insert the current student list from students.txt
INSERT INTO students (name, enabled) VALUES
('Attia, Olivia', true),
('Chandrakumar, Hasini', true),
('Chelani, Ridhima', true),
('Fass, Lawson', true),
('Ford, Layla', true),
('Gupta, Keyen', true),
('Jagadeesan, Jashwanth', true),
('Koya, Dilan', true),
('Koya, Jaiden', true),
('Parelly, Geetesh', true),
('Peesu, Ananya', true),
('Vudumu, Shrika', true),
('Vudumu, Sloka', true),
('Williams, Zara', true)
ON CONFLICT (name) DO NOTHING;