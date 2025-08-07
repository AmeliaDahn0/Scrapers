-- SQL Script to Alter acely_students Table for Enhanced Metrics
-- Run this in Supabase SQL Editor to add additional columns for comprehensive data capture

-- Add new columns for enhanced data capture
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS total_students_requested INTEGER,
ADD COLUMN IF NOT EXISTS students_found INTEGER,
ADD COLUMN IF NOT EXISTS students_scraped INTEGER,
ADD COLUMN IF NOT EXISTS scrape_errors JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS scrape_summary JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS student_url TEXT,
ADD COLUMN IF NOT EXISTS page_title TEXT,
ADD COLUMN IF NOT EXISTS subject TEXT,
ADD COLUMN IF NOT EXISTS charts_data JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS extraction_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS activity_summary JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS performance_summary JSONB DEFAULT '{}'::jsonb;

-- Add comments to document the new columns
COMMENT ON COLUMN public.acely_students.total_students_requested IS 'Total number of students requested in the scraping session';
COMMENT ON COLUMN public.acely_students.students_found IS 'Number of students found during scraping';
COMMENT ON COLUMN public.acely_students.students_scraped IS 'Number of students successfully scraped';
COMMENT ON COLUMN public.acely_students.scrape_errors IS 'Array of errors encountered during scraping';
COMMENT ON COLUMN public.acely_students.scrape_summary IS 'Summary statistics for the scraping session';
COMMENT ON COLUMN public.acely_students.student_url IS 'URL of the student profile page';
COMMENT ON COLUMN public.acely_students.page_title IS 'Title of the student profile page';
COMMENT ON COLUMN public.acely_students.subject IS 'Primary subject or test type (e.g., SAT, ACT)';
COMMENT ON COLUMN public.acely_students.charts_data IS 'Extracted chart and visualization data from student profile';
COMMENT ON COLUMN public.acely_students.extraction_metadata IS 'Metadata about the extraction process (scroll positions, methods used, etc.)';
COMMENT ON COLUMN public.acely_students.activity_summary IS 'Summary of daily/weekly activity metrics';
COMMENT ON COLUMN public.acely_students.performance_summary IS 'Summary of performance metrics across topics';

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_acely_students_subject ON public.acely_students USING btree (subject);
CREATE INDEX IF NOT EXISTS idx_acely_students_scrape_summary_gin ON public.acely_students USING gin (scrape_summary);
CREATE INDEX IF NOT EXISTS idx_acely_students_charts_data_gin ON public.acely_students USING gin (charts_data);
CREATE INDEX IF NOT EXISTS idx_acely_students_extraction_metadata_gin ON public.acely_students USING gin (extraction_metadata);
CREATE INDEX IF NOT EXISTS idx_acely_students_activity_summary_gin ON public.acely_students USING gin (activity_summary);
CREATE INDEX IF NOT EXISTS idx_acely_students_performance_summary_gin ON public.acely_students USING gin (performance_summary);

-- Update the trigger to handle the new updated_at column
-- (The existing trigger should already handle this, but confirming)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Ensure the trigger exists
DROP TRIGGER IF EXISTS update_acely_students_updated_at ON public.acely_students;
CREATE TRIGGER update_acely_students_updated_at 
    BEFORE UPDATE ON public.acely_students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add a view for easy querying of student performance summaries
CREATE OR REPLACE VIEW public.student_performance_summary AS
SELECT 
    id,
    student_email,
    student_name,
    most_recent_score,
    subject,
    join_date,
    this_week_questions,
    last_week_questions,
    scrape_timestamp,
    -- Extract key performance metrics from JSONB
    (performance_summary->>'math_avg_score')::numeric AS math_avg_score,
    (performance_summary->>'reading_avg_score')::numeric AS reading_avg_score,
    (activity_summary->>'total_active_days')::integer AS total_active_days,
    (activity_summary->>'total_questions_attempted')::integer AS total_questions_attempted,
    -- Extract mock exam count
    jsonb_array_length(COALESCE(mock_exam_results, '[]'::jsonb)) AS total_mock_exams,
    -- Extract latest mock exam score
    CASE 
        WHEN jsonb_array_length(COALESCE(mock_exam_results, '[]'::jsonb)) > 0 
        THEN (mock_exam_results->0->>'raw_score')::integer 
        ELSE NULL 
    END AS latest_exam_score,
    created_at,
    updated_at
FROM public.acely_students
ORDER BY scrape_timestamp DESC, most_recent_score DESC NULLS LAST;

-- Grant appropriate permissions
GRANT SELECT ON public.student_performance_summary TO authenticated;
GRANT ALL ON public.acely_students TO authenticated;

-- Display the updated table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    col_description(pgc.oid, pa.attnum) as column_comment
FROM 
    information_schema.columns isc
    LEFT JOIN pg_class pgc ON pgc.relname = isc.table_name
    LEFT JOIN pg_attribute pa ON pa.attrelid = pgc.oid AND pa.attname = isc.column_name
WHERE 
    isc.table_schema = 'public' 
    AND isc.table_name = 'acely_students'
ORDER BY isc.ordinal_position; 