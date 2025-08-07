-- Simple RLS setup for acely_students table
-- Run this in your Supabase SQL Editor to secure the table

-- Enable Row Level Security
ALTER TABLE acely_students ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to view all student data
CREATE POLICY "authenticated_users_select" 
ON acely_students
FOR SELECT 
TO authenticated
USING (true);

-- Allow authenticated users to insert new student data
CREATE POLICY "authenticated_users_insert" 
ON acely_students
FOR INSERT 
TO authenticated
WITH CHECK (true);

-- Allow authenticated users to update existing student data
CREATE POLICY "authenticated_users_update" 
ON acely_students
FOR UPDATE 
TO authenticated
USING (true)
WITH CHECK (true);

-- Allow service role full access (for your automation scripts)
CREATE POLICY "service_role_all" 
ON acely_students
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON acely_students TO authenticated;
GRANT ALL ON acely_students TO service_role;

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'acely_students' AND schemaname = 'public';