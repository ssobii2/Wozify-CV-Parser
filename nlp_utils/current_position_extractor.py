import re
from typing import Dict, List, Optional
import spacy
from langdetect import detect, LangDetectException

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

    def extract_current_position(self, text: str, work_experience: List[Dict]) -> Optional[str]:
        """Extract the most recent job title from experience section using NLP and fallback logic."""
        # Use NLP to extract job titles
        nlp = self.get_nlp_model_for_text(text)
        most_recent_job = None
        most_recent_date = None
        
        for job in work_experience:
            date = job.get('date')
            job_title = job.get('job_title')
            
            # Use NLP to verify job title
            if job_title:
                doc = nlp(job_title)
                for ent in doc.ents:
                    if ent.label_ == 'JOB_TITLE':
                        job_title = ent.text
                        break
            
            # Check if the job is current
            if date and ('Present' in date or 'Current' in date or 'Now' in date or 'Jelenleg' in date):
                return job_title
            
            # Parse the date to find the most recent one
            if date:
                # Extract the end year from the date range
                end_year_match = re.search(r'\b\d{4}\b', date.split('-')[-1])
                if end_year_match:
                    end_year = int(end_year_match.group(0))
                    if most_recent_date is None or end_year > most_recent_date:
                        most_recent_date = end_year
                        most_recent_job = job_title
        
        return most_recent_job