-- =====================================================
-- Setup RLS Policies with JWT Authentication
-- =====================================================
-- Run this in your Supabase SQL Editor
-- =====================================================

-- First, enable RLS on the table
ALTER TABLE public.fastmath_students ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies to start fresh
DROP POLICY IF EXISTS "Allow all operations for service role" ON public.fastmath_students;
DROP POLICY IF EXISTS "Allow inserts for all" ON public.fastmath_students;
DROP POLICY IF EXISTS "Allow select for all" ON public.fastmath_students;

-- Policy 1: Allow service role to do everything (for your scraper)
CREATE POLICY "Service role full access" ON public.fastmath_students
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy 2: Allow authenticated users to view all records
CREATE POLICY "Authenticated users can view" ON public.fastmath_students
    FOR SELECT 
    TO authenticated
    USING (true);

-- Policy 3: Allow authenticated users to insert records
CREATE POLICY "Authenticated users can insert" ON public.fastmath_students
    FOR INSERT 
    TO authenticated
    WITH CHECK (true);

-- Policy 4: Allow authenticated users to update records
CREATE POLICY "Authenticated users can update" ON public.fastmath_students
    FOR UPDATE 
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policy 5: Optional - Allow anon users to view (if you want public read access)
-- Uncomment the line below if you want anonymous users to be able to read data:
-- CREATE POLICY "Anonymous users can view" ON public.fastmath_students
--     FOR SELECT 
--     TO anon
--     USING (true);

-- Grant necessary permissions
GRANT ALL ON public.fastmath_students TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.fastmath_students TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

-- Optional: Grant select to anon if you want public read access
-- GRANT SELECT ON public.fastmath_students TO anon;
-- GRANT USAGE ON SCHEMA public TO anon;

-- =====================================================
-- Summary of Policies Created:
-- 1. Service role: Full access (for your scraper)
-- 2. Authenticated users: Can view, insert, and update
-- 3. Anonymous users: No access (unless you uncomment the anon policy)
--
-- Your scraper will use the service_role key and have full access
-- Regular users with JWT tokens can view and modify data
-- =====================================================