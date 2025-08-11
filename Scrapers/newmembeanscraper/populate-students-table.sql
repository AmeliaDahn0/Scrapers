-- Add students to your existing students table
-- Run this in Supabase SQL Editor if you don't have these students yet

-- Check if any students already exist first
-- SELECT COUNT(*) FROM public.students;

-- Insert students (will create duplicates if run multiple times)
INSERT INTO public.students (name) VALUES
('Attia, Olivia'),
('Chandrakumar, Hasini'),
('Chelani, Ridhima'),
('Fass, Lawson'),
('Ford, Layla'),
('Gupta, Keyen'),
('Jagadeesan, Jashwanth'),
('Koya, Dilan'),
('Koya, Jaiden'),
('Parelly, Geetesh'),
('Peesu, Ananya'),
('Vudumu, Shrika'),
('Vudumu, Sloka'),
('Williams, Zara');