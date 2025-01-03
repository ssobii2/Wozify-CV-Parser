import re
from typing import Dict, List, Optional
from langdetect import detect, LangDetectException

class CurrentPositionExtractor:
    def __init__(self, nlp_en, nlp_hu):
        """Initialize CurrentPositionExtractor with spaCy models and define job indicators."""
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        
        # Job role indicators in English and Hungarian
        self.job_indicators = [
            # English job indicators
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor', 'senior', 'junior',
            'architect', 'designer', 'programmer', 'technician', 'officer',
            'executive', 'founder', 'head', 'chief', 'president', 'principal',
            'full-stack', 'frontend', 'backend', 'software', 'web', 'mobile',
            'data', 'system', 'network', 'cloud', 'devops', 'qa', 'test',
            # Hungarian job indicators
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
        
        # Current position time indicators
        self.current_indicators = [
            # English indicators
            'present', 'current', 'now', 'ongoing', 'to date',
            # Hungarian indicators
            'jelenlegi', 'jelenleg', 'mostani', 'folyamatban', 'napjainkig',
            'mai napig', 'jelen', 'aktuális', 'folyó', '-', '–'
        ]

    # MAIN EXTRACTION METHOD
    def extract_current_position(self, text: str, work_experience: List[Dict]) -> Optional[str]:
        """Extract the most recent job title from experience section."""
        if not text or not work_experience:
            return None

        try:
            def get_date_score(job):
                date = job.get('date', '')
                date_range = job.get('date_range', '')
                
                date_text = (date + date_range).lower()
                if any(indicator.lower() in date_text for indicator in self.current_indicators):
                    return (float('inf'), float('inf'), date)
                
                if re.search(r'\b\d{4}\.\s*-\s*(jelenleg|napjainkig|folyamatban)', date_text):
                    return (float('inf'), float('inf'), date)
                
                year, month = self._parse_date(date if date else date_range)
                return (year, month, date)
            
            sorted_experiences = sorted(
                [exp for exp in work_experience if exp.get('job_title') or exp.get('company')],
                key=get_date_score,
                reverse=True
            )
            
            if sorted_experiences:
                most_recent = sorted_experiences[0]
                
                if most_recent.get('job_title'):
                    return most_recent['job_title']
                elif most_recent.get('company'):
                    for indicator in self.job_indicators:
                        if indicator.lower() in most_recent['company'].lower():
                            return most_recent['company']
            
            return None

        except Exception as e:
            print(f"Current position extraction failed: {str(e)}")
            for exp in work_experience:
                if exp.get('job_title'):
                    return exp['job_title']
            return None

    # HELPER METHODS
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
            if any(indicator.lower() in date_str.lower() for indicator in self.current_indicators):
                return (float('inf'), float('inf'))
            
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            year = int(year_match.group(0)) if year_match else 0
            
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
            print(f"Date parsing failed: {str(e)}")
            return (0, 0)