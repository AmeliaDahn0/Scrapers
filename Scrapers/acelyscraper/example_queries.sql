-- Comprehensive SQL Queries for Acely Student Data in Supabase
-- Copy and paste these into your Supabase SQL Editor

-- =====================================
-- BASIC STUDENT OVERVIEW
-- =====================================

-- 1. Basic student information
SELECT 
    student_name,
    student_email,
    most_recent_score,
    subject,
    this_week_questions,
    last_week_questions,
    join_date,
    created_at
FROM acely_students 
ORDER BY created_at DESC;

-- =====================================
-- PERFORMANCE ANALYSIS
-- =====================================

-- 2. Performance by topic breakdown
SELECT 
    student_name,
    topic_key as subject_area,
    topic_data->>'text' as performance_text,
    topic_data->'percentages' as percentages
FROM acely_students,
jsonb_each(performance_by_topic) as topic(topic_key, topic_data)
WHERE performance_by_topic != '{}'::jsonb
ORDER BY student_name, topic_key;

-- 3. Students with high performance (>90% in any topic)
SELECT 
    student_name,
    topic_key as subject_area,
    (topic_data->'percentages'->>0)::int as percentage
FROM acely_students,
jsonb_each(performance_by_topic) as topic(topic_key, topic_data)
WHERE (topic_data->'percentages'->>0)::int > 90
ORDER BY (topic_data->'percentages'->>0)::int DESC;

-- =====================================
-- MOCK EXAM RESULTS
-- =====================================

-- 4. All mock exam results with scores
SELECT 
    student_name,
    student_email,
    exam->>'exam_type' as exam_type,
    exam->>'completion_date' as completion_date,
    exam->>'score' as score,
    (exam->>'raw_score')::int as numeric_score
FROM acely_students,
jsonb_array_elements(mock_exam_results) as exam
WHERE jsonb_array_length(mock_exam_results) > 0
ORDER BY student_name, (exam->>'raw_score')::int DESC;

-- 5. Latest exam scores by type
SELECT 
    student_name,
    exam->>'exam_type' as exam_type,
    MAX((exam->>'raw_score')::int) as highest_score,
    COUNT(*) as total_attempts
FROM acely_students,
jsonb_array_elements(mock_exam_results) as exam
WHERE jsonb_array_length(mock_exam_results) > 0
GROUP BY student_name, exam->>'exam_type'
ORDER BY student_name, highest_score DESC;

-- =====================================
-- DAILY ACTIVITY ANALYSIS
-- =====================================

-- 6. Weekly activity summary
SELECT 
    student_name,
    week_range,
    calendar_data->>'extraction_method' as method,
    jsonb_array_length(calendar_data->'active_days') as days_tracked,
    (
        SELECT COUNT(*)
        FROM jsonb_array_elements(calendar_data->'active_days') as day
        WHERE (day->>'has_activity')::boolean = true
    ) as active_days_count
FROM acely_students,
jsonb_each(daily_activity->'weekly_calendars') as weeks(week_range, calendar_data)
WHERE daily_activity->'weekly_calendars' != '{}'::jsonb
ORDER BY student_name, week_range;

-- 7. Detailed daily activity with question counts
SELECT 
    student_name,
    week_range,
    day->>'day' as day_of_week,
    day->>'date_key' as date,
    (day->>'has_activity')::boolean as was_active,
    (day->>'questions_attempted')::int as questions_attempted,
    day->>'tooltip_text' as activity_details
FROM acely_students,
jsonb_each(daily_activity->'weekly_calendars') as weeks(week_range, calendar_data),
jsonb_array_elements(calendar_data->'active_days') as day
WHERE daily_activity->'weekly_calendars' != '{}'::jsonb
  AND (day->>'questions_attempted')::int > 0
ORDER BY student_name, week_range, (day->>'questions_attempted')::int DESC;

-- =====================================
-- LEARNING INSIGHTS
-- =====================================

-- 8. Strongest and weakest areas
SELECT 
    student_name,
    areas->>'strongest' as strongest_areas,
    areas->>'weakest' as weakest_areas
FROM acely_students,
jsonb_to_record(strongest_weakest_areas) as areas(strongest text, weakest text)
WHERE strongest_weakest_areas != '{}'::jsonb;

-- 9. Assignment completion tracking
SELECT 
    student_name,
    assignment->>'text' as assignment_type,
    assignment->>'element_type' as element_type
FROM acely_students,
jsonb_array_elements(assignments) as assignment
WHERE jsonb_array_length(assignments) > 0;

-- =====================================
-- COMPREHENSIVE STUDENT PROFILE
-- =====================================

-- 10. Complete student profile with all metrics
SELECT 
    student_name,
    student_email,
    most_recent_score,
    subject,
    join_date,
    
    -- Performance summary
    jsonb_object_keys(performance_by_topic) as performance_topics,
    jsonb_array_length(mock_exam_results) as total_exams_taken,
    jsonb_array_length(assignments) as assignments_found,
    
    -- Activity summary
    (
        SELECT COUNT(*)
        FROM jsonb_each(daily_activity->'weekly_calendars') as weeks(week_range, calendar_data)
    ) as weeks_of_activity_data,
    
    -- Recent activity
    this_week_questions,
    last_week_questions,
    
    -- Metadata
    scrape_timestamp,
    created_at
FROM acely_students
ORDER BY created_at DESC;

-- =====================================
-- ANALYTICS & INSIGHTS
-- =====================================

-- 11. Score progression analysis (if multiple exams)
SELECT 
    student_name,
    exam->>'exam_type' as exam_type,
    exam->>'completion_date' as date,
    (exam->>'raw_score')::int as score,
    LAG((exam->>'raw_score')::int) OVER (
        PARTITION BY student_name, exam->>'exam_type' 
        ORDER BY exam->>'completion_date'
    ) as previous_score,
    (exam->>'raw_score')::int - LAG((exam->>'raw_score')::int) OVER (
        PARTITION BY student_name, exam->>'exam_type' 
        ORDER BY exam->>'completion_date'
    ) as score_change
FROM acely_students,
jsonb_array_elements(mock_exam_results) as exam
ORDER BY student_name, exam->>'exam_type', exam->>'completion_date';

-- 12. Most active study days
SELECT 
    student_name,
    day->>'day' as day_of_week,
    SUM((day->>'questions_attempted')::int) as total_questions,
    COUNT(*) as active_sessions
FROM acely_students,
jsonb_each(daily_activity->'weekly_calendars') as weeks(week_range, calendar_data),
jsonb_array_elements(calendar_data->'active_days') as day
WHERE (day->>'has_activity')::boolean = true
GROUP BY student_name, day->>'day'
ORDER BY student_name, total_questions DESC;

-- =====================================
-- SEARCH & FILTER EXAMPLES
-- =====================================

-- 13. Find students with specific performance patterns
SELECT 
    student_name,
    most_recent_score
FROM acely_students 
WHERE most_recent_score > 1400
  AND jsonb_array_length(mock_exam_results) >= 3;

-- 14. Students who practiced this week
SELECT 
    student_name,
    this_week_questions,
    last_week_questions,
    (this_week_questions - last_week_questions) as weekly_change
FROM acely_students 
WHERE this_week_questions > 0
ORDER BY this_week_questions DESC; 