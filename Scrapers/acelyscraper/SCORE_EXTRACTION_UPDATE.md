# Data Extraction Enhancements

## 🎯 What's New

The `step3_extract_data.py` has been enhanced to extract additional metrics from each student's dashboard page:
- **Most Recent Score** - The student's latest test score
- **This Week Accuracy** - The accuracy percentage for the current week (just the number or "N/A")
- **Last Week Accuracy** - The accuracy percentage for the previous week (just the number or null)
- **Questions Answered This Week** - Number of questions answered in the current week
- **Questions Answered Last Week** - Number of questions answered in the previous week
- **Daily Activity Calendar** - Weekly calendar showing daily activity status and question counts
- **Strongest Area** - Academic area with highest accuracy and percentage
- **Weakest Area** - Academic area with lowest accuracy and percentage
- **Mock Exam Results** - All mock exam scores with titles, dates, and numbered sequence

## 📊 New Data Structure

The JSON output now includes all extracted metrics in the `data_extracted` section:

```json
{
  "scrape_session": {
    "timestamp": "2025-01-06T12:00:00.000000",
    "total_students_requested": 12,
    "students_found": 10,
    "students_not_found": 2
  },
  "students": {
    "student.email@2hourlearning.com": {
      "email": "student.email@2hourlearning.com",
      "name": "Student Name",
      "dashboard_url": "https://app.acely.ai/student-dashboard/user_...",
      "scrape_timestamp": "2025-01-06T12:00:00.000000",
      "data_extracted": {
        "join_date": "September 22, 2024",
        "most_recent_score": 870,
        "this_week_accuracy": "N/A",
        "last_week_accuracy": "67",
        "questions_answered_this_week": 0,
        "questions_answered_last_week": 6,
        "daily_activity_calendar": {
          "07/13 - 07/19": {
            "Sun": {"active": false, "questions_attempted": 0},
            "Mon": {"active": false, "questions_attempted": 0},
            "Tue": {"active": false, "questions_attempted": 0},
            "Wed": {"active": false, "questions_attempted": 0},
            "Thu": {"active": false, "questions_attempted": 0},
            "Fri": {"active": false, "questions_attempted": 0},
            "Sat": {"active": false, "questions_attempted": 0}
          },
          "07/20 - 07/26": {
            "Sun": {"active": false, "questions_attempted": 0},
            "Mon": {"active": true, "questions_attempted": 44},
            "Tue": {"active": false, "questions_attempted": 0},
            "Wed": {"active": false, "questions_attempted": 0},
            "Thu": {"active": false, "questions_attempted": 0},
            "Fri": {"active": true, "questions_attempted": 5},
            "Sat": {"active": false, "questions_attempted": 0}
          }
        },
        "strongest_area": {
          "area": "Right triangles and trigonometry",
          "accuracy": "100%"
        },
        "weakest_area": {
          "area": "Area and volume formulas", 
          "accuracy": "50%"
        },
        "mock_exam_results": [
          {
            "exam_number": 1,
            "exam_title": "Math Exam",
            "completion_date": "July 21, 2025",
            "score": "740"
          },
          {
            "exam_number": 2,
            "exam_title": "Reading and Writing Exam",
            "completion_date": "February 19, 2025",
            "score": "720"
          }
        ]
      }
    }
  }
}
```

## 🔧 Technical Details

### Target Elements

**Most Recent Score**:
```html
<span class="text-lg font-semibold underline decoration-yellow-800">870</span>
```

**This Week & Last Week Accuracy**:
```html
<div class="text-3xl font-medium text-navy-800">N/A vs. 67% last week</div>
```
*Parsed to extract: this_week_accuracy = "N/A", last_week_accuracy = "67"*

**Questions Answered This Week & Last Week**:
```html
<div class="text-3xl font-medium text-navy-800">0<span class="pl-2 text-base text-neutral-400">vs. 6 last week</span></div>
```
*Parsed to extract: questions_answered_this_week = 0, questions_answered_last_week = 6*

**Daily Activity Calendar**:
```html
<div class="flex flex-col gap-8 w-full">
  <div class="flex flex-row items-center w-full justify-between">
    <div class="text-sm font-medium text-neutral-600 pr-2">07/20 - 07/26</div>
    <!-- Day columns with SVG activity bubbles -->
    <div class="flex flex-col items-center">
      <div class="text-xs text-neutral-600 pb-0.5">Mon</div>
      <svg class="text-green-200" height="20" width="20">...</svg> <!-- Active: green/lime/yellow -->
    </div>
    <div class="flex flex-col items-center">
      <div class="text-xs text-neutral-600 pb-0.5">Tue</div>
      <svg class="text-neutral-200" height="20" width="20">...</svg> <!-- Inactive: grey/neutral -->
    </div>
  </div>
</div>
```
*Parsed to extract: Weekly calendar with daily activity status and question counts*

**Strongest Area**:
```html
<div class="rounded-lg border border-gray-300 py-4 px-6 drop-shadow-sm bg-white w-full flex flex-col gap-1.5">
  <div class="text-sm font-medium text-neutral-800">Strongest</div>
  <div class="text-lg font-medium text-navy-800 truncate">Right triangles and trigonometry</div>
  <div class="text-base text-neutral-400 font-medium">with 100% accuracy</div>
</div>
```
*Parsed to extract: area = "Right triangles and trigonometry", accuracy = "100%"*

**Weakest Area**:
```html
<div class="rounded-lg border border-gray-300 py-4 px-6 drop-shadow-sm bg-white w-full flex flex-col gap-1.5">
  <div class="text-sm font-medium text-neutral-800">Weakest</div>
  <div class="text-lg font-medium text-navy-800 truncate">Area and volume formulas</div>
  <div class="text-base text-neutral-400 font-medium">with 50% accuracy</div>
</div>
```
*Parsed to extract: area = "Area and volume formulas", accuracy = "50%"*

**Mock Exam Results**:
```html
<li>
  <div class="rounded-lg border border-gray-300 px-8 pt-6 pb-4 md:p-6 drop-shadow-sm bg-white w-full">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div class="flex gap-3 items-center md:gap-6">
        <div class="flex flex-col md:w-60">
          <h3 class="text-heading-3">Math Exam</h3>
          <div class="flex items-center gap-1.5 text-xs md:text-sm text-gray-600">
            <span>Completed July 21, 2025</span>
          </div>
        </div>
      </div>
      <div class="flex flex-col md:flex-row md:items-center gap-4">
        <span class="flex flex-col text-center md:text-left md:w-40">
          <span class="font-readex font-medium text-4xl md:text-3xl">740</span>
          <span class="text-xs md:text-sm text-gray-600">Score</span>
        </span>
      </div>
    </div>
  </div>
</li>
```
*Parsed to extract: exam_number = 1, exam_title = "Math Exam", completion_date = "July 21, 2025", score = "740"*

### Extraction Methods

**Most Recent Score** (`extract_most_recent_score()`):
1. **Primary selector**: Exact class match for the specific element
2. **Fallback selectors**: Alternative patterns for robustness
3. **Context-aware selectors**: Look for "Most Recent Score:" text and find nearby score elements

**This Week & Last Week Accuracy** (`extract_this_week_accuracy()` & `extract_last_week_accuracy()`):
1. **Primary selector**: Exact class match for the accuracy div element
2. **Context-aware selectors**: Look within "This Week" and "Accuracy" sections  
3. **Smart parsing**: Uses regex to extract numbers from text like "N/A vs. 67% last week"
4. **Formats**: Returns just the number (e.g., "67") or "N/A", no percentage signs or extra text

**Questions Answered This Week & Last Week** (`extract_questions_answered_this_week()` & `extract_questions_answered_last_week()`):
1. **Container targeting**: Looks within the Questions Answered rounded container
2. **Context-aware selectors**: Finds elements within Questions Answered section
3. **Smart parsing**: Uses regex to extract numbers from text like "0 vs. 6 last week" 
4. **Formats**: Returns integers (e.g., 0, 6) for both this week and last week

**Daily Activity Calendar** (`extract_daily_activity_calendar()`):
1. **Calendar container targeting**: Finds the weekly calendar view with flex layout
2. **Week row processing**: Iterates through each week row to extract date ranges
3. **SVG color analysis**: Analyzes SVG bubble colors to determine activity status
   - **Active**: `text-green-200`, `text-yellow-200`, `text-lime-200` classes
   - **Inactive**: `text-neutral-200` class
4. **Tooltip parsing**: Extracts question counts from tooltip data attributes
5. **Formats**: Returns nested JSON with week ranges containing daily activity data

**Strongest Area** (`extract_strongest_area()`):
1. **Container targeting**: Finds rounded container with "Strongest" label
2. **Area name extraction**: Extracts subject area from navy text element
3. **Accuracy extraction**: Parses percentage from accuracy text
4. **Formats**: Returns object with `{"area": "subject name", "accuracy": "percentage"}`

**Weakest Area** (`extract_weakest_area()`):
1. **Container targeting**: Finds rounded container with "Weakest" label
2. **Area name extraction**: Extracts subject area from navy text element
3. **Accuracy extraction**: Parses percentage from accuracy text
4. **Formats**: Returns object with `{"area": "subject name", "accuracy": "percentage"}`

**Mock Exam Results** (`extract_mock_exam_results()`):
1. **List container targeting**: Finds Mock Exam Results section and exam list items
2. **Multiple exam processing**: Iterates through all exam containers found
3. **Comprehensive data extraction**: Extracts title, completion date, and score for each exam
4. **Sequential numbering**: Assigns exam_number starting from 1 for proper ordering
5. **Robust selectors**: Multiple fallback patterns for different exam layouts
6. **Formats**: Returns array of objects with `{"exam_number": int, "exam_title": "string", "completion_date": "string", "score": "string"}`

### Data Types
- **Integer scores**: Extracted as `int` (e.g., `870`)
- **Decimal scores**: Extracted as `float` (e.g., `87.5`)  
- **This week accuracy**: Extracted as `string` - just the number (e.g., `"67"`) or `"N/A"`
- **Last week accuracy**: Extracted as `string` - just the number (e.g., `"67"`) or `null` if not available
- **Questions answered this week**: Extracted as `int` (e.g., `0`)
- **Questions answered last week**: Extracted as `int` (e.g., `6`) or `null` if not available
- **Daily activity calendar**: Extracted as `object` with nested structure:
  - **Week keys**: `string` (e.g., `"07/20 - 07/26"`)
  - **Day objects**: `{"active": boolean, "questions_attempted": int}`
  - **Active status**: `boolean` - `true` if student was active, `false` if inactive
  - **Questions attempted**: `int` - number of questions attempted that day
- **Strongest area**: Extracted as `object` with structure:
  - **Area name**: `string` (e.g., `"Right triangles and trigonometry"`)
  - **Accuracy**: `string` (e.g., `"100%"`)
- **Weakest area**: Extracted as `object` with structure:
  - **Area name**: `string` (e.g., `"Area and volume formulas"`)
  - **Accuracy**: `string` (e.g., `"50%"`)
- **Mock exam results**: Extracted as `array` of exam objects:
  - **Exam number**: `int` (e.g., `1`, `2`, `3`) - sequential numbering
  - **Exam title**: `string` (e.g., `"Math Exam"`, `"Reading and Writing Exam"`)
  - **Completion date**: `string` (e.g., `"July 21, 2025"`)
  - **Score**: `string` (e.g., `"740"`, `"400-400"`) - supports both single scores and ranges
- **Missing values**: Stored as `null` in JSON

## 🚀 Usage

### Run Normal Data Extraction
```bash
# Run the enhanced step 3 extraction
python3 step3_extract_data.py
```

### Test Score Extraction Only
```bash
# Run the test script to verify score extraction works
python3 test_score_extraction.py
```

## 🔍 Logging

The extraction process provides detailed logging:

**Most Recent Score**:
- `✅ Most recent score: 870` - Score successfully extracted
- `⚠️ Most recent score not found` - Score element not found on page
- `❌ Failed to extract most recent score: error` - Extraction error

**This Week Accuracy**:
- `✅ This week accuracy: N/A` - Accuracy successfully extracted
- `⚠️ This week accuracy not found` - Accuracy element not found on page
- `❌ Failed to extract this week accuracy: error` - Extraction error

## 📈 What's Next

This enhancement is part of expanding the data extraction capabilities. Future additions may include:
- Activity statistics (questions answered per week)
- Performance by topic
- Mock exam results
- Detailed analytics data

## 🛠️ Troubleshooting

If score extraction fails:
1. Check if the student dashboard loaded completely
2. Verify the student has a recent score displayed
3. Run in non-headless mode to visually inspect the page
4. Check the logs for specific selector failures

The extraction is designed to be fault-tolerant - if the score can't be found, the scraper continues with other data extraction.