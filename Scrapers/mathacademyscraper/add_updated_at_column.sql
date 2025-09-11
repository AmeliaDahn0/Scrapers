-- Add updated_at column to math_academy_students table
-- This script adds the updated_at column and sets up automatic timestamp updates

-- Add the updated_at column with default value
ALTER TABLE public.math_academy_students 
ADD COLUMN updated_at timestamp with time zone DEFAULT timezone('utc'::text, now());

-- Update existing rows to have the current timestamp
UPDATE public.math_academy_students 
SET updated_at = timezone('utc'::text, now()) 
WHERE updated_at IS NULL;

-- Create or replace the function to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create the trigger to automatically update updated_at on row updates
DROP TRIGGER IF EXISTS update_math_academy_students_updated_at ON public.math_academy_students;
CREATE TRIGGER update_math_academy_students_updated_at
    BEFORE UPDATE ON public.math_academy_students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add an index on the updated_at column for better query performance
CREATE INDEX IF NOT EXISTS idx_math_academy_updated_at 
ON public.math_academy_students USING btree (updated_at DESC) 
TABLESPACE pg_default;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'math_academy_students' 
    AND table_schema = 'public'
    AND column_name = 'updated_at';

-- Show sample of existing data with new column
SELECT 
    student_id, 
    name, 
    created_at, 
    updated_at 
FROM public.math_academy_students 
LIMIT 5;