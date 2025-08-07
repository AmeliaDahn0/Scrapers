-- Migration Script: Remove Additional Unused Columns from acely_students table
-- Run this in your Supabase SQL Editor

-- Remove additional unused columns from acely_students table
ALTER TABLE acely_students DROP COLUMN IF EXISTS charts_data;
ALTER TABLE acely_students DROP COLUMN IF EXISTS student_url;
ALTER TABLE acely_students DROP COLUMN IF EXISTS subject;

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'acely_students' 
ORDER BY ordinal_position;

-- Optional: Add a comment about when this migration was run
COMMENT ON TABLE acely_students IS 'Student data from Acely scraper - additional columns removed for optimization'; 