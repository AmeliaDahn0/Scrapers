-- Update RLS policies for acely_students table to allow JWT-based access
-- Run this in your Supabase SQL Editor to allow authenticated users with JWT to read data

-- First, drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "authenticated_users_select" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_insert" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_update" ON acely_students;
DROP POLICY IF EXISTS "service_role_all" ON acely_students;

-- Create new policies that allow JWT-authenticated users to read data
-- This allows any authenticated user (with valid JWT) to view student data
CREATE POLICY "jwt_authenticated_users_select"
ON acely_students
FOR SELECT
TO authenticated
USING (true);

-- Allow JWT-authenticated users to insert new records (for the scraper)
CREATE POLICY "jwt_authenticated_users_insert"
ON acely_students
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Allow JWT-authenticated users to update records if needed
CREATE POLICY "jwt_authenticated_users_update"
ON acely_students
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- Keep service role access for automation scripts
CREATE POLICY "service_role_all_access"
ON acely_students
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Also allow anonymous access for public sites (optional - uncomment if needed)
-- CREATE POLICY "anonymous_users_select"
-- ON acely_students
-- FOR SELECT
-- TO anon
-- USING (true);

-- Grant necessary permissions to authenticated role
GRANT SELECT, INSERT, UPDATE ON acely_students TO authenticated;
GRANT ALL ON acely_students TO service_role;

-- Optional: Grant read access to anonymous users (uncomment if needed for public access)
-- GRANT SELECT ON acely_students TO anon;

-- Verify RLS is still enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'acely_students' AND schemaname = 'public';

-- Show current policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'acely_students' AND schemaname = 'public';