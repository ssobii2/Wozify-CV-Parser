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
            # English job indicators
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor', 'senior', 'junior',
            'architect', 'designer', 'programmer', 'technician', 'officer',
            'executive', 'founder', 'head', 'chief', 'president', 'principal',
            'full-stack', 'frontend', 'backend', 'software', 'web', 'mobile',
            'data', 'system', 'network', 'cloud', 'devops', 'qa', 'test',
            # Enhanced Hungarian job indicators
            'fejlesztő', 'mérnök', 'vezető', 'tanácsadó', 'elemző',
            'szakértő', 'koordinátor', 'asszisztens', 'igazgató',
            'gyakornok', 'adminisztrátor', 'felügyelő', 'szenior', 'junior',
            'architekt', 'tervező', 'programozó', 'technikus', 'tisztviselő',
            'ügyvezető', 'alapító', 'vezérigazgató', 'elnök', 'főmérnök',
            'projektmenedzser', 'csoportvezető', 'osztályvezető', 'részlegvezető',
            'alkalmazás', 'rendszer', 'hálózati', 'adatbázis', 'minőségbiztosítási',
            'szoftverfejlesztő', 'webfejlesztő', 'mobilfejlesztő', 'full-stack fejlesztő',
            'frontend fejlesztő', 'backend fejlesztő', 'rendszergazda', 'üzemeltető',
            'informatikus', 'műszaki', 'technológiai', 'kutató', 'oktató'
        ]
        
        # Current position indicators
        self.current_indicators = [
            # English
            'present', 'current', 'now', 'ongoing', 'to date',
            # Enhanced Hungarian indicators
            'jelenlegi', 'jelenleg', 'mostani', 'folyamatban', 'napjainkig',
            'mai napig', 'jelen', 'aktuális', 'folyó', '-', '–'  # Hungarian often uses dashes for current positions
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
            if any(indicator.lower() in date_str.lower() for indicator in self.current_indicators):
                return (float('inf'), float('inf'))  # Will always be latest
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            year = int(year_match.group(0)) if year_match else 0
            
            # Extract month
            month_map = {
                # English months
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                # Hungarian months
                'január': 1, 'február': 2, 'március': 3, 'április': 4, 'május': 5, 'június': 6,
                'július': 7, 'augusztus': 8, 'szeptember': 9, 'október': 10, 'november': 11, 'december': 12,
                # Short Hungarian months
                'jan': 1, 'feb': 2, 'már': 3, 'ápr': 4, 'máj': 5, 'jún': 6,
                'júl': 7, 'aug': 8, 'szept': 9, 'okt': 10, 'nov': 11, 'dec': 12
            }
            
            month = 0
            for month_str, month_num in month_map.items():
                if month_str.lower() in date_str.lower():
                    month = month_num
                    break
            
            return (year, month)
        except Exception as e:
            logging.warning(f"Date parsing failed: {str(e)}")
            return (0, 0)  # Return lowest priority for unparseable dates

    def extract_current_position(self, text: str, work_experience: List[Dict]) -> Optional[str]:
        """Extract the most recent job title from experience section."""
        if not text or not work_experience:
            return None

        try:
            # Sort experiences by date, with current positions first
            def get_date_score(job):
                date = job.get('date', '')
                date_range = job.get('date_range', '')
                
                # First check if this is a current position
                date_text = (date + date_range).lower()
                if any(indicator.lower() in date_text for indicator in self.current_indicators):
                    return (float('inf'), float('inf'), date)
                
                # Handle Hungarian date formats
                if re.search(r'\b\d{4}\.\s*-\s*(jelenleg|napjainkig|folyamatban)', date_text):
                    return (float('inf'), float('inf'), date)
                
                # Then try to parse the date
                year, month = self._parse_date(date if date else date_range)
                return (year, month, date)
            
            # Sort work experiences by date, most recent first
            sorted_experiences = sorted(
                [exp for exp in work_experience if exp.get('job_title') or exp.get('company')],
                key=get_date_score,
                reverse=True
            )
            
            # Take the most recent position
            if sorted_experiences:
                most_recent = sorted_experiences[0]
                
                # Prefer job_title if available, otherwise try to extract from company
                if most_recent.get('job_title'):
                    return most_recent['job_title']
                elif most_recent.get('company'):
                    # Try to extract job title from company description
                    for indicator in self.job_indicators:
                        if indicator.lower() in most_recent['company'].lower():
                            return most_recent['company']
            
            return None

        except Exception as e:
            logging.warning(f"Current position extraction failed: {str(e)}")
            # Emergency fallback: Return the first job title from original list
            for exp in work_experience:
                if exp.get('job_title'):
                    return exp['job_title']
            return None