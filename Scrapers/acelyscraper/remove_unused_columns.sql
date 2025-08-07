-- Migration Script: Remove Unused Columns from acely_students table
-- Run this in your Supabase SQL Editor

-- Remove unused columns from acely_students table
ALTER TABLE acely_students DROP COLUMN IF EXISTS students_found;
ALTER TABLE acely_students DROP COLUMN IF EXISTS total_students_requested;
ALTER TABLE acely_students DROP COLUMN IF EXISTS page_title;
ALTER TABLE acely_students DROP COLUMN IF EXISTS students_scraped;
ALTER TABLE acely_students DROP COLUMN IF EXISTS scrape_errors;
ALTER TABLE acely_students DROP COLUMN IF EXISTS scrape_summary;

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'acely_students' 
ORDER BY ordinal_position;

-- Optional: Add a comment about when this migration was run
COMMENT ON TABLE acely_students IS 'Student data from Acely scraper - unused metadata columns removed'; 