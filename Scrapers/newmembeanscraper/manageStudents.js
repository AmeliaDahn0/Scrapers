#!/usr/bin/env node

const StudentsManager = require('./studentsManager');

const studentsManager = new StudentsManager();

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0];

function showHelp() {
    console.log(`
📚 Students Manager - Help

Usage: node manageStudents.js <command> [options]

Commands:
  list                    Show all current students
  add <name>             Add a new student (enabled by default)
  add <name> <notes>     Add a new student with notes
  disable <name>         Disable a student
  enable <name>          Enable a student
  help                   Show this help message

Examples:
  node manageStudents.js list
  node manageStudents.js add "John Smith"
  node manageStudents.js add "Jane Doe" "Needs extra attention"
  node manageStudents.js disable "John Smith"
  node manageStudents.js enable "John Smith"

Files:
  students.json          Main configuration file (JSON format)
  students.txt           Simple text file (one name per line)
  
Note: The scraper will read from students.json first, then fall back to students.txt
    `);
}

function addStudent(name, notes = '') {
    if (!name) {
        console.error('Error: Student name is required');
        console.log('Usage: node manageStudents.js add "<student name>" [notes]');
        return;
    }
    
    studentsManager.addStudent(name, true, notes);
    console.log(`✅ Added student: ${name}`);
    if (notes) {
        console.log(`   Notes: ${notes}`);
    }
}

function toggleStudent(name, enabled) {
    if (!name) {
        console.error('Error: Student name is required');
        return;
    }
    
    const action = enabled ? 'enable' : 'disable';
    studentsManager.addStudent(name, enabled, '');
    console.log(`${enabled ? '✅' : '❌'} ${enabled ? 'Enabled' : 'Disabled'} student: ${name}`);
}

// Main command processing
switch (command) {
    case 'list':
    case 'show':
    case 'display':
        studentsManager.displayStudents();
        break;
        
    case 'add':
        const studentName = args[1];
        const studentNotes = args[2] || '';
        addStudent(studentName, studentNotes);
        break;
        
    case 'enable':
        toggleStudent(args[1], true);
        break;
        
    case 'disable':
        toggleStudent(args[1], false);
        break;
        
    case 'help':
    case '--help':
    case '-h':
        showHelp();
        break;
        
    default:
        if (!command) {
            studentsManager.displayStudents();
        } else {
            console.error(`Unknown command: ${command}`);
            console.log('Run "node manageStudents.js help" for available commands');
        }
        break;
}