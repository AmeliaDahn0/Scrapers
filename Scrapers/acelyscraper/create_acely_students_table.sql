-- Create acely_students table for Supabase
-- This table stores comprehensive student data extracted from Acely dashboards

CREATE TABLE IF NOT EXISTS acely_students (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    url TEXT,
    join_date TEXT,
    most_recent_score INTEGER,
    this_week_accuracy TEXT,
    last_week_accuracy TEXT,
    questions_answered_this_week INTEGER,
    questions_answered_last_week INTEGER,
    daily_activity JSONB,
    strongest_area TEXT,
    weakest_area TEXT,
    strongest_area_accuracy TEXT,
    weakest_area_accuracy TEXT,
    mock_exam_results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_acely_students_email ON acely_students(email);
CREATE INDEX IF NOT EXISTS idx_acely_students_name ON acely_students(name);
CREATE INDEX IF NOT EXISTS idx_acely_students_created_at ON acely_students(created_at);

-- Add comments for documentation
COMMENT ON TABLE acely_students IS 'Stores comprehensive student data extracted from Acely dashboards';
COMMENT ON COLUMN acely_students.name IS 'Student full name';
COMMENT ON COLUMN acely_students.email IS 'Student email address (unique identifier)';
COMMENT ON COLUMN acely_students.url IS 'Student dashboard URL';
COMMENT ON COLUMN acely_students.join_date IS 'Date when student joined (as text)';
COMMENT ON COLUMN acely_students.most_recent_score IS 'Most recent test score';
COMMENT ON COLUMN acely_students.this_week_accuracy IS 'Accuracy percentage for current week';
COMMENT ON COLUMN acely_students.last_week_accuracy IS 'Accuracy percentage for previous week';
COMMENT ON COLUMN acely_students.questions_answered_this_week IS 'Questions answered in current week';
COMMENT ON COLUMN acely_students.questions_answered_last_week IS 'Questions answered in previous week';
COMMENT ON COLUMN acely_students.daily_activity IS 'Weekly calendar showing daily activity status (JSON)';
COMMENT ON COLUMN acely_students.strongest_area IS 'Academic area with highest performance';
COMMENT ON COLUMN acely_students.weakest_area IS 'Academic area with lowest performance';
COMMENT ON COLUMN acely_students.strongest_area_accuracy IS 'Accuracy percentage for strongest area';
COMMENT ON COLUMN acely_students.weakest_area_accuracy IS 'Accuracy percentage for weakest area';
COMMENT ON COLUMN acely_students.mock_exam_results IS 'Array of all mock exam results (JSON)';
COMMENT ON COLUMN acely_students.created_at IS 'Timestamp when record was created';

-- Enable Row Level Security (RLS) if needed
-- ALTER TABLE acely_students ENABLE ROW LEVEL SECURITY;

-- Sample policy (uncomment if you want to enable RLS)
-- CREATE POLICY "Users can view all student data" ON acely_students
--     FOR SELECT USING (true);

-- CREATE POLICY "Users can insert student data" ON acely_students
--     FOR INSERT WITH CHECK (true);

-- CREATE POLICY "Users can update student data" ON acely_students
--     FOR UPDATE USING (true);