-- Setup Row Level Security (RLS) for acely_students table
-- This will remove the "Unrestricted" warning and secure the table

-- Enable Row Level Security on the acely_students table
ALTER TABLE acely_students ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (in case we're re-running this)
DROP POLICY IF EXISTS "Allow authenticated users to view student data" ON acely_students;
DROP POLICY IF EXISTS "Allow authenticated users to insert student data" ON acely_students;
DROP POLICY IF EXISTS "Allow authenticated users to update student data" ON acely_students;
DROP POLICY IF EXISTS "Allow service role to manage all data" ON acely_students;

-- Policy 1: Allow authenticated users to view all student data
CREATE POLICY "Allow authenticated users to view student data" 
ON acely_students
FOR SELECT 
TO authenticated
USING (true);

-- Policy 2: Allow authenticated users to insert new student data
CREATE POLICY "Allow authenticated users to insert student data" 
ON acely_students
FOR INSERT 
TO authenticated
WITH CHECK (true);

-- Policy 3: Allow authenticated users to update existing student data
CREATE POLICY "Allow authenticated users to update student data" 
ON acely_students
FOR UPDATE 
TO authenticated
USING (true)
WITH CHECK (true);

-- Policy 4: Allow service role (for your scripts) to do everything
CREATE POLICY "Allow service role to manage all data" 
ON acely_students
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Grant necessary permissions to authenticated users
GRANT SELECT, INSERT, UPDATE ON acely_students TO authenticated;

-- Grant full permissions to service role (for your automation scripts)
GRANT ALL ON acely_students TO service_role;

-- Grant usage on the sequence (for auto-incrementing id)
GRANT USAGE, SELECT ON SEQUENCE acely_students_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE acely_students_id_seq TO service_role;

-- Add a comment explaining the security setup
COMMENT ON TABLE acely_students IS 'Student data from Acely scraper - RLS enabled for security. Authenticated users can read/write, service role has full access for automation.';

-- Verify RLS is enabled (this will show in query results)
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'acely_students' AND schemaname = 'public';