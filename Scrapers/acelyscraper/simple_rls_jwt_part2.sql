-- Part 2: Create new JWT-friendly policies

CREATE POLICY "jwt_users_select"
ON acely_students
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "service_role_access"
ON acely_students
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);