const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

class StudentsManager {
    constructor() {
        this.jsonFile = path.join(__dirname, 'students.json');
        this.txtFile = path.join(__dirname, 'students.txt');
        
        // Initialize Supabase client
        this.supabaseUrl = process.env.SUPABASE_URL;
        this.supabaseKey = process.env.SUPABASE_ANON_KEY;
        this.supabase = null;
        
        if (this.supabaseUrl && this.supabaseKey) {
            this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
        }
    }

    /**
     * Read students from Supabase database
     * @returns {Array} Array of enabled student names (strings)
     */
    async readStudentsFromSupabase() {
        try {
            if (!this.supabase) {
                console.log('⚠️  Supabase not configured. Please check your .env file.');
                return [];
            }

            console.log('📊 Fetching students from Supabase...');
            
            const { data, error } = await this.supabase
                .from('students')
                .select('name')
                .order('name');

            if (error) {
                console.error('❌ Error fetching students from Supabase:', error.message);
                return [];
            }

            // Transform names from "First Last" to "Last, First" format for Membean
            const studentNames = data.map(student => {
                const name = student.name.trim();
                const parts = name.split(' ');
                
                if (parts.length >= 2) {
                    // Take the last part as surname, everything else as first name
                    const lastName = parts[parts.length - 1];
                    const firstName = parts.slice(0, -1).join(' ');
                    return `${lastName}, ${firstName}`;
                } else {
                    // If only one name part, return as-is
                    return name;
                }
            });
            
            console.log(`✅ Found ${studentNames.length} students in Supabase (transformed to Membean format)`);
            
            return studentNames;
        } catch (error) {
            console.error('❌ Error connecting to Supabase:', error.message);
            return [];
        }
    }

    /**
     * Read students from JSON file
     * @returns {Array} Array of student objects with name, enabled, and notes properties
     */
    readStudentsFromJSON() {
        try {
            if (!fs.existsSync(this.jsonFile)) {
                console.log('📄 students.json not found - skipping local JSON file');
                return [];
            }

            const data = fs.readFileSync(this.jsonFile, 'utf8');
            const config = JSON.parse(data);
            
            return config.students.filter(student => student.enabled);
        } catch (error) {
            console.error('Error reading students.json:', error.message);
            return [];
        }
    }

    /**
     * Read students from text file
     * @returns {Array} Array of student names (strings)
     */
    readStudentsFromTXT() {
        try {
            if (!fs.existsSync(this.txtFile)) {
                console.log('📄 students.txt not found - skipping local text file');
                return [];
            }

            const data = fs.readFileSync(this.txtFile, 'utf8');
            const lines = data.split('\n');
            
            return lines
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'))
                .filter(line => line !== 'Student Name 1' && line !== 'Student Name 2'); // Filter out examples
        } catch (error) {
            console.error('Error reading students.txt:', error.message);
            return [];
        }
    }

    /**
     * Get all enabled students (tries Supabase first, then falls back to local files)
     * @returns {Promise<Array>} Array of student names
     */
    async getEnabledStudents() {
        // Try Supabase first
        if (this.supabase) {
            const supabaseStudents = await this.readStudentsFromSupabase();
            if (supabaseStudents.length > 0) {
                return supabaseStudents;
            }
        }

        console.log('⚠️  Falling back to local files...');
        
        // Fall back to TXT file
        const txtStudents = this.readStudentsFromTXT();
        if (txtStudents.length > 0) {
            console.log(`Found ${txtStudents.length} students in students.txt`);
            return txtStudents;
        }

        // Final fallback to JSON
        const jsonStudents = this.readStudentsFromJSON();
        if (jsonStudents.length > 0) {
            console.log(`Found ${jsonStudents.length} enabled students in students.json`);
            return jsonStudents.map(student => student.name);
        }

        console.log('❌ No students found in any source (Supabase, students.txt, or students.json)');
        console.log('💡 Please either:');
        console.log('   1. Run the SQL script in Supabase to create the students table');
        console.log('   2. Create a students.txt file with student names');
        return [];
    }

    /**
     * Add a new student to the JSON file
     * @param {string} name - Student name
     * @param {boolean} enabled - Whether student is enabled for scraping
     * @param {string} notes - Optional notes about the student
     */
    addStudent(name, enabled = true, notes = '') {
        try {
            const config = JSON.parse(fs.readFileSync(this.jsonFile, 'utf8'));
            
            // Check if student already exists
            const existingIndex = config.students.findIndex(s => s.name === name);
            
            if (existingIndex >= 0) {
                config.students[existingIndex] = { name, enabled, notes };
                console.log(`Updated existing student: ${name}`);
            } else {
                config.students.push({ name, enabled, notes });
                console.log(`Added new student: ${name}`);
            }

            config.scraping_config.last_updated = new Date().toISOString().split('T')[0];
            
            fs.writeFileSync(this.jsonFile, JSON.stringify(config, null, 2));
        } catch (error) {
            console.error('Error adding student:', error.message);
        }
    }

    /**
     * Create default JSON file
     */
    createDefaultJSON() {
        const defaultConfig = {
            "class_name": "SAT Blitz - 2 Hour Learning",
            "class_id": "345817",
            "students": [
                {
                    "name": "Student Name 1",
                    "enabled": true,
                    "notes": "Add any notes about this student here"
                },
                {
                    "name": "Student Name 2", 
                    "enabled": true,
                    "notes": ""
                },
                {
                    "name": "Student Name 3",
                    "enabled": false,
                    "notes": "Disabled - not currently scraping this student"
                }
            ],
            "scraping_config": {
                "scrape_all_enabled": true,
                "last_updated": new Date().toISOString().split('T')[0],
                "notes": "Replace the example student names above with actual student names from your class"
            }
        };

        fs.writeFileSync(this.jsonFile, JSON.stringify(defaultConfig, null, 2));
    }

    /**
     * Create default TXT file
     */
    createDefaultTXT() {
        const defaultContent = `# Students to Scrape - SAT Blitz - 2 Hour Learning Class
# 
# Instructions:
# - Add one student name per line
# - Lines starting with # are comments and will be ignored
# - Remove the # from a line to enable scraping for that student
# - Add # at the beginning of a line to disable scraping for that student
#
# Example format:
# Student Name 1
# Student Name 2
# #Student Name 3 (this student is disabled)

# Add your actual student names below (remove these example lines):
Student Name 1
Student Name 2
#Student Name 3 (disabled example)
`;

        fs.writeFileSync(this.txtFile, defaultContent);
    }

    /**
     * Display current students configuration
     */
    displayStudents() {
        console.log('\\n=== CURRENT STUDENTS CONFIGURATION ===');
        
        // Try JSON first
        try {
            const config = JSON.parse(fs.readFileSync(this.jsonFile, 'utf8'));
            console.log(`Class: ${config.class_name} (ID: ${config.class_id})`);
            console.log(`Last Updated: ${config.scraping_config.last_updated}`);
            console.log('\\nStudents:');
            
            config.students.forEach((student, index) => {
                const status = student.enabled ? '✅ ENABLED' : '❌ DISABLED';
                const notes = student.notes ? ` (${student.notes})` : '';
                console.log(`  ${index + 1}. ${student.name} - ${status}${notes}`);
            });
            
            const enabledCount = config.students.filter(s => s.enabled).length;
            console.log(`\\nTotal: ${config.students.length} students, ${enabledCount} enabled for scraping`);
            
        } catch (error) {
            console.log('Could not read students.json, checking students.txt...');
            
            const txtStudents = this.readStudentsFromTXT();
            if (txtStudents.length > 0) {
                console.log('Students from students.txt:');
                txtStudents.forEach((name, index) => {
                    console.log(`  ${index + 1}. ${name}`);
                });
                console.log(`\\nTotal: ${txtStudents.length} students`);
            } else {
                console.log('No students found in either file.');
            }
        }
        
        console.log('=====================================\\n');
    }
}

module.exports = StudentsManager;