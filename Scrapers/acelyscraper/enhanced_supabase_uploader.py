#!/usr/bin/env python3
"""
Enhanced Supabase Uploader for Comprehensive Acely Student Data

This script uploads ALL scraped Acely student data to a Supabase database,
including the enhanced metrics and comprehensive data capture.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import glob
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase package not found. Install it with:")
    print("pip install supabase")
    sys.exit(1)

# Load environment variables
load_dotenv()

class EnhancedSupabaseUploader:
    """Handles uploading comprehensive Acely student data to Supabase"""
    
    def __init__(self):
        # Get Supabase credentials from environment variables
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ Missing Supabase credentials!")
            print("Please add to your .env file:")
            print("SUPABASE_URL=your_supabase_project_url")
            print("SUPABASE_ANON_KEY=your_supabase_anon_key")
            sys.exit(1)
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            sys.exit(1)
    
    def _calculate_activity_summary(self, daily_activity: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for daily activity"""
        try:
            weekly_calendars = daily_activity.get("weekly_calendars", {})
            total_active_days = 0
            total_questions_attempted = 0
            active_weeks = 0
            weeks_with_activity = []
            
            for week_range, week_data in weekly_calendars.items():
                week_active_days = 0
                week_questions = 0
                
                active_days = week_data.get("active_days", [])
                for day in active_days:
                    if day.get("has_activity", False):
                        week_active_days += 1
                        total_active_days += 1
                    
                    questions = day.get("questions_attempted", 0)
                    week_questions += questions
                    total_questions_attempted += questions
                
                if week_active_days > 0:
                    active_weeks += 1
                    weeks_with_activity.append({
                        "week_range": week_range,
                        "active_days": week_active_days,
                        "questions_attempted": week_questions
                    })
            
            return {
                "total_active_days": total_active_days,
                "total_questions_attempted": total_questions_attempted,
                "total_weeks_tracked": len(weekly_calendars),
                "active_weeks": active_weeks,
                "weeks_with_activity": weeks_with_activity,
                "average_questions_per_active_day": round(total_questions_attempted / max(total_active_days, 1), 2)
            }
        except Exception as e:
            print(f"⚠️ Error calculating activity summary: {e}")
            return {}
    
    def _calculate_performance_summary(self, performance_by_topic: Dict[str, Any], mock_exam_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for performance"""
        try:
            summary = {
                "topics_tracked": len(performance_by_topic),
                "topic_averages": {},
                "overall_topic_average": 0,
                "mock_exam_summary": {}
            }
            
            # Calculate topic performance averages
            total_topic_score = 0
            topic_count = 0
            
            for topic, data in performance_by_topic.items():
                percentages = data.get("percentages", [])
                if percentages:
                    # Convert to integers and calculate average
                    numeric_percentages = []
                    for p in percentages:
                        try:
                            numeric_percentages.append(int(p))
                        except (ValueError, TypeError):
                            continue
                    
                    if numeric_percentages:
                        avg_score = sum(numeric_percentages) / len(numeric_percentages)
                        summary["topic_averages"][topic] = round(avg_score, 1)
                        total_topic_score += avg_score
                        topic_count += 1
            
            if topic_count > 0:
                summary["overall_topic_average"] = round(total_topic_score / topic_count, 1)
            
            # Calculate mock exam summary
            if mock_exam_results:
                math_scores = []
                reading_scores = []
                all_scores = []
                
                for exam in mock_exam_results:
                    if exam.get("raw_score"):
                        score = exam["raw_score"]
                        all_scores.append(score)
                        
                        exam_type = exam.get("exam_type", "").lower()
                        if "math" in exam_type:
                            math_scores.append(score)
                        elif "reading" in exam_type or "writing" in exam_type:
                            reading_scores.append(score)
                
                summary["mock_exam_summary"] = {
                    "total_exams": len(mock_exam_results),
                    "math_exam_count": len(math_scores),
                    "reading_exam_count": len(reading_scores),
                    "math_avg_score": round(sum(math_scores) / len(math_scores), 1) if math_scores else None,
                    "reading_avg_score": round(sum(reading_scores) / len(reading_scores), 1) if reading_scores else None,
                    "overall_avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else None,
                    "highest_score": max(all_scores) if all_scores else None,
                    "latest_score": all_scores[0] if all_scores else None  # Assuming first is most recent
                }
                
                # Add specific score fields for database mapping
                summary["math_latest_score"] = math_scores[0] if math_scores else None
                summary["reading_latest_score"] = reading_scores[0] if reading_scores else None
                summary["math_avg_score"] = round(sum(math_scores) / len(math_scores), 1) if math_scores else None
                summary["reading_avg_score"] = round(sum(reading_scores) / len(reading_scores), 1) if reading_scores else None
                summary["overall_avg_score"] = round(sum(all_scores) / len(all_scores), 1) if all_scores else None
            
            return summary
        except Exception as e:
            print(f"⚠️ Error calculating performance summary: {e}")
            return {}
    
    def _extract_subject_from_data(self, student_data: Dict[str, Any]) -> str:
        """Extract the subject/test type from student data"""
        try:
            # Check raw sections for SAT/ACT indicators
            raw_sections = student_data.get("raw_sections", {})
            for section_key, section_text in raw_sections.items():
                if isinstance(section_text, str):
                    if "SAT" in section_text:
                        return "SAT"
                    elif "ACT" in section_text:
                        return "ACT"
            
            # Check mock exam results
            mock_exams = student_data.get("mock_exam_results", [])
            if mock_exams:
                # Look for SAT/ACT patterns in exam types
                for exam in mock_exams:
                    exam_type = exam.get("exam_type", "").lower()
                    if "sat" in exam_type:
                        return "SAT"
                    elif "act" in exam_type:
                        return "ACT"
            
            # Default fallback
            return "SAT"  # Most common case
        except Exception:
            return "Unknown"
    
    def _create_extraction_metadata(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata about the extraction process"""
        try:
            daily_activity = student_data.get("daily_activity", {})
            
            metadata = {
                "extraction_timestamp": student_data.get("timestamp"),
                "data_completeness": {
                    "has_mock_exams": len(student_data.get("mock_exam_results", [])) > 0,
                    "has_performance_data": len(student_data.get("performance_by_topic", {})) > 0,
                    "has_daily_activity": len(daily_activity.get("weekly_calendars", {})) > 0,
                    "has_strongest_weakest": len(student_data.get("strongest_weakest_areas", {})) > 0,
                    "has_assignments": len(student_data.get("assignments", [])) > 0
                },
                "extraction_methods": {
                    "daily_activity_method": daily_activity.get("weekly_calendars", {}).get(list(daily_activity.get("weekly_calendars", {}).keys())[0], {}).get("extraction_method") if daily_activity.get("weekly_calendars") else None,
                    "scroll_positions_captured": len([k for k in student_data.get("raw_sections", {}).keys() if "scroll" in k])
                },
                "data_quality": {
                    "errors_encountered": student_data.get("errors", []),
                    "has_student_name": bool(student_data.get("student_name")),
                    "has_recent_score": bool(student_data.get("most_recent_score")),
                    "has_join_date": bool(student_data.get("join_date"))
                }
            }
            
            return metadata
        except Exception as e:
            print(f"⚠️ Error creating extraction metadata: {e}")
            return {}
    
    def _calculate_data_richness_score(self, student_data: Dict[str, Any]) -> float:
        """Calculate a data richness score based on available metrics"""
        try:
            score = 0.0
            max_score = 7.0  # Total categories to check
            
            # Check for different data categories
            if student_data.get("most_recent_score"):
                score += 1.0
            if len(student_data.get("mock_exam_results", [])) > 0:
                score += 1.0
            if len(student_data.get("performance_by_topic", {})) > 0:
                score += 1.0
            if len(student_data.get("daily_activity", {}).get("weekly_calendars", {})) > 0:
                score += 1.0
            if len(student_data.get("strongest_weakest_areas", {})) > 0:
                score += 1.0
            if student_data.get("this_week_questions") is not None:
                score += 1.0
            if student_data.get("join_date"):
                score += 1.0
            
            return round((score / max_score) * 100.0, 1)
        except Exception:
            return 0.0
    
    def _create_exam_summary(self, mock_exams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of exam performance"""
        try:
            if not mock_exams:
                return {}
            
            summary = {
                "total_exams": len(mock_exams),
                "exam_types": list(set([exam.get("exam_type", "Unknown") for exam in mock_exams])),
                "score_range": {
                    "min": min([exam.get("raw_score", 0) for exam in mock_exams if exam.get("raw_score")]),
                    "max": max([exam.get("raw_score", 0) for exam in mock_exams if exam.get("raw_score")])
                },
                "latest_exam": mock_exams[0] if mock_exams else None,
                "score_trend": "improving" if len(mock_exams) >= 2 and mock_exams[0].get("raw_score", 0) > mock_exams[-1].get("raw_score", 0) else "stable"
            }
            return summary
        except Exception:
            return {}
    
    def _create_weekly_summary(self, daily_activity: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of weekly activity patterns"""
        try:
            weekly_calendars = daily_activity.get("weekly_calendars", {})
            if not weekly_calendars:
                return {}
            
            total_weeks = len(weekly_calendars)
            active_weeks = sum(1 for week_data in weekly_calendars.values() 
                             if any(day.get("has_activity", False) for day in week_data.get("active_days", [])))
            
            summary = {
                "total_weeks_tracked": total_weeks,
                "active_weeks": active_weeks,
                "activity_consistency": round(active_weeks / total_weeks * 100, 1) if total_weeks > 0 else 0,
                "weekly_breakdown": {}
            }
            
            for week_range, week_data in weekly_calendars.items():
                week_questions = sum(day.get("questions_attempted", 0) for day in week_data.get("active_days", []))
                week_active_days = sum(1 for day in week_data.get("active_days", []) if day.get("has_activity", False))
                summary["weekly_breakdown"][week_range] = {
                    "questions": week_questions,
                    "active_days": week_active_days
                }
            
            return summary
        except Exception:
            return {}
    
    def _extract_last_activity_date(self, daily_activity: Dict[str, Any]) -> str:
        """Extract the most recent activity date"""
        try:
            weekly_calendars = daily_activity.get("weekly_calendars", {})
            latest_date = None
            
            for week_data in weekly_calendars.values():
                for day in week_data.get("active_days", []):
                    if day.get("has_activity", False):
                        date_key = day.get("date_key", "")
                        if date_key and ("Jul" in date_key or "Aug" in date_key):
                            # Convert "Jul 21" to "2025-07-21" format
                            try:
                                if "Jul" in date_key:
                                    day_num = date_key.replace("Jul ", "").strip()
                                    latest_date = f"2025-07-{day_num.zfill(2)}"
                                elif "Aug" in date_key:
                                    day_num = date_key.replace("Aug ", "").strip()
                                    latest_date = f"2025-08-{day_num.zfill(2)}"
                            except:
                                continue
            
            return latest_date
        except Exception:
            return None
    
    def _extract_peak_activity_date(self, daily_activity: Dict[str, Any]) -> str:
        """Extract the date with the most activity"""
        try:
            weekly_calendars = daily_activity.get("weekly_calendars", {})
            max_questions = 0
            peak_date = None
            
            for week_data in weekly_calendars.values():
                for day in week_data.get("active_days", []):
                    questions = day.get("questions_attempted", 0)
                    if questions > max_questions:
                        max_questions = questions
                        date_key = day.get("date_key", "")
                        if date_key and ("Jul" in date_key or "Aug" in date_key):
                            try:
                                if "Jul" in date_key:
                                    day_num = date_key.replace("Jul ", "").strip()
                                    peak_date = f"2025-07-{day_num.zfill(2)}"
                                elif "Aug" in date_key:
                                    day_num = date_key.replace("Aug ", "").strip()
                                    peak_date = f"2025-08-{day_num.zfill(2)}"
                            except:
                                continue
            
            return peak_date
        except Exception:
            return None
    
    def _calculate_improvement_trend(self, mock_exams: List[Dict[str, Any]]) -> str:
        """Calculate if scores are improving, declining, or stable"""
        try:
            if len(mock_exams) < 2:
                return "insufficient_data"
            
            # Sort by date and get scores
            scored_exams = [exam for exam in mock_exams if exam.get("raw_score")]
            if len(scored_exams) < 2:
                return "insufficient_data"
            
            latest_score = scored_exams[0].get("raw_score", 0)
            earliest_score = scored_exams[-1].get("raw_score", 0)
            
            if latest_score > earliest_score + 20:  # Significant improvement
                return "improving"
            elif latest_score < earliest_score - 20:  # Significant decline
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    def _extract_first_exam_date(self, mock_exams: List[Dict[str, Any]]) -> str:
        """Extract the first exam date"""
        try:
            if not mock_exams:
                return None
            
            # Return the last exam in the list (assuming chronological order)
            last_exam = mock_exams[-1]
            completion_date = last_exam.get("completion_date", "")
            
            # Convert "February 3, 2025" to "2025-02-03" format
            return self._convert_date_format(completion_date)
        except Exception:
            return None
    
    def _extract_latest_exam_date(self, mock_exams: List[Dict[str, Any]]) -> str:
        """Extract the most recent exam date"""
        try:
            if not mock_exams:
                return None
            
            # Return the first exam in the list (assuming reverse chronological order)
            latest_exam = mock_exams[0]
            completion_date = latest_exam.get("completion_date", "")
            
            # Convert "July 21, 2025" to "2025-07-21" format
            return self._convert_date_format(completion_date)
        except Exception:
            return None
    
    def _convert_date_format(self, date_str: str) -> str:
        """Convert 'Month Day, Year' to 'YYYY-MM-DD' format"""
        try:
            if not date_str:
                return None
            
            month_map = {
                "January": "01", "February": "02", "March": "03", "April": "04",
                "May": "05", "June": "06", "July": "07", "August": "08",
                "September": "09", "October": "10", "November": "11", "December": "12"
            }
            
            # Parse "July 21, 2025"
            parts = date_str.replace(",", "").split()
            if len(parts) == 3:
                month_name, day, year = parts
                month_num = month_map.get(month_name, "01")
                return f"{year}-{month_num}-{day.zfill(2)}"
                
            return None
        except Exception:
            return None
    
    def _calculate_score_improvement(self, mock_exams: List[Dict[str, Any]]) -> int:
        """Calculate score improvement from first to latest exam"""
        try:
            if len(mock_exams) < 2:
                return None
            
            scored_exams = [exam for exam in mock_exams if exam.get("raw_score")]
            if len(scored_exams) < 2:
                return None
            
            latest_score = scored_exams[0].get("raw_score", 0)
            earliest_score = scored_exams[-1].get("raw_score", 0)
            
            return latest_score - earliest_score
        except Exception:
            return None
    
    def _calculate_exam_frequency(self, mock_exams: List[Dict[str, Any]]) -> float:
        """Calculate average days between exams"""
        try:
            if len(mock_exams) < 2:
                return None
            
            # This would need proper date parsing for accurate calculation
            # For now, return a rough estimate based on exam count
            return round(365.0 / len(mock_exams), 1) if len(mock_exams) > 0 else None
        except Exception:
            return None
    
    def transform_student_data_enhanced(self, scrape_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform the scraped JSON data into enhanced database-ready format"""
        
        # Extract top-level scraping metadata - handle both old and new format
        scraping_metadata = scrape_data.get("scraping_metadata", {})
        scrape_timestamp = scraping_metadata.get("timestamp") or scrape_data.get("timestamp")
        total_students_requested = scraping_metadata.get("total_students_requested") or scrape_data.get("total_students_requested", 0)
        students_found = scraping_metadata.get("successful_scrapes") or scrape_data.get("students_found", 0)
        students_scraped = scraping_metadata.get("successful_scrapes") or scrape_data.get("students_scraped", 0)
        scrape_errors = scrape_data.get("errors", [])
        scrape_summary = scrape_data.get("summary", {})
        
        # Process each student's data
        student_records = []
        student_data = scrape_data.get("student_data", {})
        
        for email, data in student_data.items():
            # Handle error cases
            if "error" in data:
                record = {
                    # Scraping metadata
                    "scrape_timestamp": scrape_timestamp,
                    "total_students_requested": total_students_requested,
                    "students_found": students_found,
                    "students_scraped": students_scraped,
                    "scrape_errors": scrape_errors,
                    "scrape_summary": scrape_summary,
                    
                    # Student basic info
                    "student_email": email,
                    "student_timestamp": data.get("timestamp"),
                    "student_url": None,
                    "page_title": None,
                    
                    # Core profile data (set to null for error cases)
                    "most_recent_score": None,
                    "student_name": None,
                    "join_date": None,
                    "subject": "Unknown",
                    "this_week_questions": None,
                    "last_week_questions": None,
                    
                    # Complex nested data as JSON
                    "performance_by_topic": {},
                    "weekly_performance": {},
                    "daily_activity": {},
                    "strongest_weakest_areas": {},
                    "analytics_data": {},
                    "assignments": [],
                    "mock_exam_results": [],
                    "charts_data": {},
                    "raw_sections": {},
                    
                    # Enhanced fields
                    "extraction_metadata": {"error": str(data.get("error"))},
                    "activity_summary": {},
                    "performance_summary": {}
                }
                student_records.append(record)
                continue
            
            # Calculate enhanced summaries
            activity_summary = self._calculate_activity_summary(data.get("daily_activity", {}))
            performance_summary = self._calculate_performance_summary(
                data.get("performance_by_topic", {}),
                data.get("mock_exam_results", [])
            )
            subject = self._extract_subject_from_data(data)
            extraction_metadata = self._create_extraction_metadata(data)
            
            # Create the comprehensive database record
            record = {
                # Scraping metadata
                "scrape_timestamp": scrape_timestamp,
                "total_students_requested": total_students_requested,
                "students_found": students_found,
                "students_scraped": students_scraped,
                "scrape_errors": scrape_errors,
                "scrape_summary": scrape_summary,
                
                # Student basic info
                "student_email": email,
                "student_timestamp": data.get("timestamp"),
                "student_url": None,  # Could be extracted from metadata if available
                "page_title": None,   # Could be extracted from raw_sections if available
                
                # Core profile information
                "most_recent_score": data.get("most_recent_score"),
                "student_name": data.get("student_name"),
                "join_date": data.get("join_date"),
                "subject": subject,
                "this_week_questions": data.get("this_week_questions"),
                "last_week_questions": data.get("last_week_questions"),
                
                # Complex nested data as JSON (existing fields)
                "performance_by_topic": data.get("performance_by_topic", {}),
                "weekly_performance": data.get("weekly_performance", {}),
                "daily_activity": data.get("daily_activity", {}),
                "strongest_weakest_areas": data.get("strongest_weakest_areas", {}),
                "analytics_data": data.get("analytics_data", {}),
                "assignments": data.get("assignments", []),
                "mock_exam_results": data.get("mock_exam_results", []),
                "charts_data": data.get("charts_data", {}),
                "raw_sections": data.get("raw_sections", {}),
                
                # Enhanced fields - all new database columns
                "extraction_metadata": extraction_metadata,
                "total_active_days": activity_summary.get("total_active_days", 0),
                "total_questions_attempted": activity_summary.get("total_questions_attempted", 0),
                "data_richness_score": self._calculate_data_richness_score(data),
                "subjects_identified": [subject] if subject else [],
                
                # Activity and performance summary columns  
                "activity_summary": activity_summary,
                "performance_summary": performance_summary,
                "exam_summary": self._create_exam_summary(data.get("mock_exam_results", [])),
                "weekly_summary": self._create_weekly_summary(data.get("daily_activity", {})),
                
                # Enhanced tracking columns
                "scraping_session_id": f"session_{scrape_timestamp.replace(':', '').replace('-', '').replace('.', '')}" if scrape_timestamp else None,
                "comprehensive_data_version": "v1.0",
                "last_activity_date": self._extract_last_activity_date(data.get("daily_activity", {})),
                "peak_activity_date": self._extract_peak_activity_date(data.get("daily_activity", {})),
                "improvement_trend": self._calculate_improvement_trend(data.get("mock_exam_results", [])),
                
                # Math-specific performance columns
                "math_avg_score": performance_summary.get("math_avg_score"),
                "math_latest_score": performance_summary.get("math_latest_score"), 
                "reading_avg_score": performance_summary.get("reading_avg_score"),
                "reading_latest_score": performance_summary.get("reading_latest_score"),
                "overall_avg_score": performance_summary.get("overall_avg_score"),
                
                # Progress tracking columns
                "first_exam_date": self._extract_first_exam_date(data.get("mock_exam_results", [])),
                "latest_exam_date": self._extract_latest_exam_date(data.get("mock_exam_results", [])),
                "score_improvement": self._calculate_score_improvement(data.get("mock_exam_results", [])),
                "exam_frequency_days": self._calculate_exam_frequency(data.get("mock_exam_results", []))
            }
            
            student_records.append(record)
        
        return student_records
    
    def upload_data_direct(self, scrape_data: Dict[str, Any]) -> bool:
        """Upload scraped data directly to Supabase with enhanced metrics"""
        
        try:
            # Transform the data
            print("🔄 Transforming comprehensive data for database...")
            student_records = self.transform_student_data_enhanced(scrape_data)
            
            if not student_records:
                print("⚠️ No student records to upload")
                return False
            
            print(f"📊 Uploading {len(student_records)} enhanced student records...")
            
            # Insert data into Supabase
            result = self.supabase.table("acely_students").insert(student_records).execute()
            
            if result.data:
                print(f"✅ Successfully uploaded {len(result.data)} comprehensive records to Supabase!")
                
                # Print enhanced summary
                successful_students = [r for r in student_records if r.get("most_recent_score") is not None]
                error_students = [r for r in student_records if r.get("most_recent_score") is None]
                
                # Calculate additional statistics
                total_mock_exams = sum(len(r.get("mock_exam_results", [])) for r in successful_students)
                total_active_days = sum(r.get("activity_summary", {}).get("total_active_days", 0) for r in successful_students)
                total_questions = sum(r.get("activity_summary", {}).get("total_questions_attempted", 0) for r in successful_students)
                
                print(f"📈 Enhanced Summary:")
                print(f"   • Successful student profiles: {len(successful_students)}")
                print(f"   • Error cases: {len(error_students)}")
                print(f"   • Total records: {len(student_records)}")
                print(f"   • Total mock exams captured: {total_mock_exams}")
                print(f"   • Total active days tracked: {total_active_days}")
                print(f"   • Total questions attempted: {total_questions}")
                
                # Show sample of extracted subjects
                subjects = [r.get("subject") for r in successful_students if r.get("subject")]
                if subjects:
                    subject_counts = {}
                    for subject in subjects:
                        subject_counts[subject] = subject_counts.get(subject, 0) + 1
                    print(f"   • Subjects identified: {dict(subject_counts)}")
                
                return True
            else:
                print(f"❌ Upload failed: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading enhanced data to Supabase: {e}")
            return False
    
    def upload_data(self, json_file_path: str) -> bool:
        """Upload data from JSON file to Supabase with enhanced processing"""
        
        try:
            # Read the JSON file
            print(f"📖 Reading comprehensive data from: {json_file_path}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                scrape_data = json.load(f)
            
            return self.upload_data_direct(scrape_data)
                
        except Exception as e:
            print(f"❌ Error uploading data: {e}")
            return False
    
    def get_latest_json_file(self) -> str:
        """Find the most recent acely_student_data JSON file"""
        json_files = glob.glob("acely_student_data_*.json")
        if not json_files:
            print("❌ No acely_student_data_*.json files found in current directory")
            return None
        
        # Sort by filename (which includes timestamp)
        latest_file = max(json_files)
        print(f"🔍 Found latest file: {latest_file}")
        return latest_file

def main():
    """Main function"""
    print("🚀 Enhanced Acely Data Uploader to Supabase")
    print("=" * 60)
    
    # Initialize enhanced uploader
    uploader = EnhancedSupabaseUploader()
    
    # Determine which file to upload
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        if not os.path.exists(json_file):
            print(f"❌ File not found: {json_file}")
            sys.exit(1)
    else:
        json_file = uploader.get_latest_json_file()
        if not json_file:
            sys.exit(1)
    
    # Upload the data
    success = uploader.upload_data(json_file)
    
    if success:
        print("\n🎉 Enhanced upload completed successfully!")
        print("\n💡 You can now query your comprehensive data in Supabase with SQL like:")
        print("   SELECT student_name, most_recent_score, subject, (activity_summary->>'total_active_days')::int FROM acely_students;")
        print("   SELECT * FROM student_performance_summary ORDER BY most_recent_score DESC;")
        print("   SELECT student_email, jsonb_array_length(mock_exam_results) as exam_count FROM acely_students;")
        print("   SELECT * FROM acely_students WHERE (performance_summary->>'math_avg_score')::numeric > 80;")
    else:
        print("\n❌ Enhanced upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 