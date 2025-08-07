-- SQL Script to Fix Single Table Schema for Acely Students
-- This script removes the extra table and consolidates everything into acely_students
-- Run this in Supabase SQL Editor

-- 1. Drop the extra view that was created
DROP VIEW IF EXISTS public.student_performance_summary CASCADE;

-- 2. Ensure all necessary columns exist in acely_students table
-- (This will add any missing columns without affecting existing data)

-- Basic metadata columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS total_students_requested INTEGER,
ADD COLUMN IF NOT EXISTS students_found INTEGER,
ADD COLUMN IF NOT EXISTS students_scraped INTEGER,
ADD COLUMN IF NOT EXISTS scrape_errors JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS scrape_summary JSONB DEFAULT '{}'::jsonb;

-- Student profile columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS student_url TEXT,
ADD COLUMN IF NOT EXISTS page_title TEXT,
ADD COLUMN IF NOT EXISTS subject TEXT,
ADD COLUMN IF NOT EXISTS charts_data JSONB DEFAULT '{}'::jsonb;

-- Enhanced data extraction columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS extraction_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS total_active_days INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_questions_attempted INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS data_richness_score NUMERIC(5,2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS subjects_identified JSONB DEFAULT '[]'::jsonb;

-- Activity and performance summary columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS activity_summary JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS performance_summary JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS exam_summary JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS weekly_summary JSONB DEFAULT '{}'::jsonb;

-- Enhanced tracking columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS scraping_session_id TEXT,
ADD COLUMN IF NOT EXISTS comprehensive_data_version TEXT DEFAULT 'v1.0',
ADD COLUMN IF NOT EXISTS last_activity_date DATE,
ADD COLUMN IF NOT EXISTS peak_activity_date DATE,
ADD COLUMN IF NOT EXISTS improvement_trend TEXT;

-- Math-specific performance columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS math_avg_score NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS math_latest_score INTEGER,
ADD COLUMN IF NOT EXISTS reading_avg_score NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS reading_latest_score INTEGER,
ADD COLUMN IF NOT EXISTS overall_avg_score NUMERIC(5,2);

-- Progress tracking columns
ALTER TABLE public.acely_students 
ADD COLUMN IF NOT EXISTS first_exam_date DATE,
ADD COLUMN IF NOT EXISTS latest_exam_date DATE,
ADD COLUMN IF NOT EXISTS score_improvement INTEGER,
ADD COLUMN IF NOT EXISTS exam_frequency_days NUMERIC(8,2);

-- 3. Create additional indexes for the new columns (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_acely_students_total_active_days 
ON public.acely_students(total_active_days);

CREATE INDEX IF NOT EXISTS idx_acely_students_total_questions 
ON public.acely_students(total_questions_attempted);

CREATE INDEX IF NOT EXISTS idx_acely_students_data_richness 
ON public.acely_students(data_richness_score);

CREATE INDEX IF NOT EXISTS idx_acely_students_subject 
ON public.acely_students(subject);

CREATE INDEX IF NOT EXISTS idx_acely_students_last_activity 
ON public.acely_students(last_activity_date);

CREATE INDEX IF NOT EXISTS idx_acely_students_math_score 
ON public.acely_students(math_avg_score);

CREATE INDEX IF NOT EXISTS idx_acely_students_overall_score 
ON public.acely_students(overall_avg_score);

-- 4. Add GIN indexes for enhanced JSONB search capabilities
CREATE INDEX IF NOT EXISTS idx_acely_students_activity_summary_gin 
ON public.acely_students USING gin(activity_summary);

CREATE INDEX IF NOT EXISTS idx_acely_students_performance_summary_gin 
ON public.acely_students USING gin(performance_summary);

CREATE INDEX IF NOT EXISTS idx_acely_students_exam_summary_gin 
ON public.acely_students USING gin(exam_summary);

CREATE INDEX IF NOT EXISTS idx_acely_students_subjects_gin 
ON public.acely_students USING gin(subjects_identified);

-- 5. Update the existing trigger to handle new updated_at behavior
-- (This ensures the updated_at column is properly maintained)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Recreate the trigger to ensure it works with all new columns
DROP TRIGGER IF EXISTS update_acely_students_updated_at ON public.acely_students;
CREATE TRIGGER update_acely_students_updated_at 
    BEFORE UPDATE ON public.acely_students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 6. Optional: Add a comment to the table describing its comprehensive purpose
COMMENT ON TABLE public.acely_students IS 'Comprehensive Acely student data including profile information, performance metrics, mock exam results, daily activity tracking, and enhanced analytics. All student data is consolidated into this single table.';

-- 7. Success message
SELECT 'SUCCESS: Single table schema fixed! Extra table dropped, all fields consolidated into acely_students table.' AS status; 