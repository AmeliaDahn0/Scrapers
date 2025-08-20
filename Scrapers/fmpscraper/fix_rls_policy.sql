-- =====================================================
-- Fix RLS Policy for fastmath_students table
-- =====================================================
-- Run this in your Supabase SQL Editor to allow inserts
-- =====================================================

-- Option 1: Disable RLS completely (simplest solution)
ALTER TABLE public.fastmath_students DISABLE ROW LEVEL SECURITY;

-- OR Option 2: Create a permissive policy (if you want to keep RLS enabled)
-- Uncomment the lines below if you prefer to keep RLS and create a policy instead:

-- ALTER TABLE public.fastmath_students ENABLE ROW LEVEL SECURITY;
-- 
-- CREATE POLICY "Allow all operations for service role" ON public.fastmath_students
--     FOR ALL USING (true);
--
-- -- Or if you want to be more restrictive, only allow inserts:
-- CREATE POLICY "Allow inserts for all" ON public.fastmath_students
--     FOR INSERT WITH CHECK (true);
--
-- CREATE POLICY "Allow select for all" ON public.fastmath_students
--     FOR SELECT USING (true);

-- =====================================================
-- Choose one approach:
-- 1. Run the DISABLE RLS command above (recommended for now)
-- 2. OR enable RLS and create the policies (more secure)
-- =====================================================