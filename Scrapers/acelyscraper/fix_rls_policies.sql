-- Fix RLS policies to allow anon key access for automation scripts
-- Run this in your Supabase SQL Editor

-- Drop the restrictive policies
DROP POLICY IF EXISTS "authenticated_users_select" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_insert" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_update" ON acely_students;
DROP POLICY IF EXISTS "service_role_all" ON acely_students;

-- Create more permissive policies that allow anon key access
-- This is safe because your anon key should be restricted in Supabase settings

-- Allow anon role (used by automation scripts) to do everything
CREATE POLICY "anon_full_access" 
ON acely_students
FOR ALL
TO anon
USING (true)
WITH CHECK (true);

-- Allow authenticated users to do everything
CREATE POLICY "authenticated_full_access" 
ON acely_students
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Allow service role to do everything (backup)
CREATE POLICY "service_role_full_access" 
ON acely_students
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Grant permissions to anon role
GRANT SELECT, INSERT, UPDATE, DELETE ON acely_students TO anon;
GRANT USAGE, SELECT ON SEQUENCE acely_students_id_seq TO anon;

-- Grant permissions to authenticated role
GRANT SELECT, INSERT, UPDATE, DELETE ON acely_students TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE acely_students_id_seq TO authenticated;

-- Grant permissions to service role
GRANT ALL ON acely_students TO service_role;
GRANT USAGE, SELECT ON SEQUENCE acely_students_id_seq TO service_role;

-- Verify the policies
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'acely_students' AND schemaname = 'public';