-- Update acely_students table to allow historical records
-- Run this in your Supabase SQL Editor

-- Remove the unique constraint on email to allow multiple records per student
ALTER TABLE acely_students DROP CONSTRAINT IF EXISTS acely_students_email_key;

-- Add a scrape_timestamp column to track when each record was created
ALTER TABLE acely_students ADD COLUMN IF NOT EXISTS scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create a new index for better performance on queries
CREATE INDEX IF NOT EXISTS idx_acely_students_email_timestamp ON acely_students (email, scrape_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_acely_students_scrape_timestamp ON acely_students (scrape_timestamp DESC);

-- Update the comment to reflect the new purpose
COMMENT ON TABLE acely_students IS 'Historical student data from Acely scraper - Each scrape creates new records for complete tracking over time';

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'acely_students' 
ORDER BY ordinal_position;