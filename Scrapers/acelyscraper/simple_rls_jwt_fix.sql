-- Simple RLS update for JWT access - Run in parts if needed
-- Part 1: Clean up existing policies

DROP POLICY IF EXISTS "authenticated_users_select" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_insert" ON acely_students;
DROP POLICY IF EXISTS "authenticated_users_update" ON acely_students;
DROP POLICY IF EXISTS "service_role_all" ON acely_students;