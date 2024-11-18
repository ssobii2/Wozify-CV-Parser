import re
from typing import Dict, List, Optional
import spacy
from langdetect import detect, LangDetectException
import logging

class CurrentPositionExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor', 'senior', 'junior'
            # Hungarian job indicators
            'fejlesztő', 'mérnök', 'vezető', 'tanácsadó', 'elemző',
            'szakértő', 'koordinátor', 'asszisztens', 'igazgató', 'vezető',
            'gyakornok', 'tanuló', 'adminisztrátor', 'felügyelő', 'szenior', 'junior'
        ]

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

    def _parse_date(self, date_str: str) -> tuple:
        """Parse date string into a comparable tuple of (year, month)."""
        try:
            # Handle current position indicators
            current_indicators = ['Present', 'Current', 'Now', 'Jelenleg', 'Jelenlegi']
            if any(indicator in date_str for indicator in current_indicators):
                return (float('inf'), float('inf'))  # Will always be latest
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            year = int(year_match.group(0)) if year_match else 0
            
            # Extract month
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                # Hungarian months
                'jan': 1, 'feb': 2, 'már': 3, 'ápr': 4, 'máj': 5, 'jún': 6,
                'júl': 7, 'aug': 8, 'szep': 9, 'okt': 10, 'nov': 11, 'dec': 12
            }
            
            month = 0
            for month_str, month_num in month_map.items():
                if month_str in date_str.lower():
                    month = month_num
                    break
            
            return (year, month)
        except Exception:
            return (0, 0)  # Return lowest priority for unparseable dates

    def extract_current_position(self, text: str, work_experience: List[Dict]) -> Optional[str]:
        """Extract the most recent job title from experience section using pattern matching and fallback logic."""
        if not text or not work_experience:
            return None

        try:
            # Sort experiences by date, with current positions first
            def get_date_score(job):
                date = job.get('date', '')
                year, month = self._parse_date(date)
                # Return tuple for sorting: (year, month, original_date)
                # original_date is included to maintain stable sorting for same dates
                return (year, month, date)
            
            # Sort work experiences by date, most recent first
            sorted_experiences = sorted(work_experience, key=get_date_score, reverse=True)
            
            # Take the most recent position (should be first after sorting)
            if sorted_experiences:
                return sorted_experiences[0].get('job_title')
            
            return None

        except Exception as e:
            logging.warning(f"Warning: Current position extraction failed: {str(e)}")
            # Emergency fallback: Return the first job title from original list
            return work_experience[0].get('job_title') if work_experience else None