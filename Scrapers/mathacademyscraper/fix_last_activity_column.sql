-- Fix last_activity column type to handle casual date strings
-- Change from timestamp with time zone to text to accommodate formats like "Fri, Aug 8"

-- Change the column type from timestamp to text
ALTER TABLE public.math_academy_students 
ALTER COLUMN last_activity TYPE text;

-- Update any existing null values to empty string if desired (optional)
-- UPDATE public.math_academy_students 
-- SET last_activity = '' 
-- WHERE last_activity IS NULL;

-- Verify the change
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'math_academy_students' 
    AND table_schema = 'public'
    AND column_name = 'last_activity';