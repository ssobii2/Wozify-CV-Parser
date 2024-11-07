from .profile_extractor import ProfileExtractor
from .education_extractor import EducationExtractor
from .experience_extractor import ExperienceExtractor
from .skills_extractor import SkillsExtractor
from .language_extractor import LanguageExtractor
from .current_position_extractor import CurrentPositionExtractor

import re
import spacy
from langdetect import detect
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Load English and Hungarian models
# spacy.require_gpu()
# spacy.prefer_gpu()
nlp_en = spacy.load('en_core_web_sm')
nlp_hu = spacy.load('hu_core_news_md')

class CVExtractor:
    def __init__(self):
        self.profile_extractor = ProfileExtractor(nlp_en, nlp_hu)
        self.education_extractor = EducationExtractor(nlp_en, nlp_hu)
        self.experience_extractor = ExperienceExtractor(nlp_en, nlp_hu)
        self.skills_extractor = SkillsExtractor(nlp_en, nlp_hu)
        self.language_extractor = LanguageExtractor(nlp_en, nlp_hu)
        self.current_position_extractor = CurrentPositionExtractor(nlp_en, nlp_hu)
        
        # Define date patterns for date extraction
        self.date_patterns = [
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
            r'Dec(?:ember)?)\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}'
        ]
        
        # Section headers for English and Hungarian
        self.section_headers = {
            'profile': ['profile', 'personal information', 'contact information', 'contact details', 'personal details', 'about me', 'summary'],
            'education': ['education', 'academic background', 'qualifications', 'academic qualifications', 'tanulmányok', 'képzettség'],
            'experience': ['experience', 'work experience', 'employment history', 'work history', 'professional experience', 'munkatapasztalat', 'szakmai tapasztalat'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies', 'készségek', 'kompetenciák'],
            'languages': ['language', 'languages', 'language skills', 'nyelvtudás', 'nyelvek'],
        }

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return nlp_hu if language == 'hu' else nlp_en
        except:
            # Default to English if detection fails
            return nlp_en

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text using various patterns."""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))

    def extract_section_with_language_detection(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract content from a specific section, processing each section with the correct language model."""
        content = []
        lines = text.split('\n')
        in_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    combined_text = ' '.join(current_entry)
                    nlp = self.get_nlp_model_for_text(combined_text)
                    doc = nlp(combined_text)
                    content.append(doc.text)
                    current_entry = []
                continue

            # Check if this line is a section header
            if any(keyword in line.lower() for keyword in section_keywords):
                in_section = True
                continue
            elif any(keyword in line.lower() for keywords in self.section_headers.values() for keyword in keywords):
                in_section = False
                if current_entry:
                    combined_text = ' '.join(current_entry)
                    nlp = self.get_nlp_model_for_text(combined_text)
                    doc = nlp(combined_text)
                    content.append(doc.text)
                    current_entry = []
                continue

            if in_section:
                current_entry.append(line)

        if current_entry:
            combined_text = ' '.join(current_entry)
            nlp = self.get_nlp_model_for_text(combined_text)
            doc = nlp(combined_text)
            content.append(doc.text)

        return content

    def extract_entities(self, text: str) -> Dict:
        """Main method to extract all information from CV."""
        extracted_data = {
            'profile': {
                'name': '',
                'email': '',
                'phone': '',
                'location': '',
                'url': '',
                'summary': ''
            },
            'education': [],
            'experience': [],
            'skills': [],
            'current_position': '',
            'languages': [{
                'language': '',
                'proficiency': ''
            }]
        }
        
        # Extract each section with language-specific processing
        profile_data = self.profile_extractor.extract_profile(text)
        if profile_data:
            extracted_data['profile'].update(profile_data)

        education_data = self.education_extractor.extract_education(text)
        if education_data:
            extracted_data['education'] = education_data

        experience_data = self.experience_extractor.extract_work_experience(text)
        if experience_data:
            extracted_data['experience'] = experience_data

        skills = self.extract_skills(text)
        if skills:
            extracted_data['skills'] = skills

        current_position = self.extract_current_position(text)
        if current_position:
            extracted_data['current_position'] = current_position

        languages = self.extract_languages(text)
        if languages:
            extracted_data['languages'] = languages

        return extracted_data

    def extract_current_position(self, text: str) -> Optional[str]:
        """Extract the most recent job title using CurrentPositionExtractor."""
        work_experience = self.experience_extractor.extract_work_experience(text)
        return self.current_position_extractor.extract_current_position(text, work_experience)

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information using EducationExtractor."""
        return self.education_extractor.extract_education(text)

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information using ExperienceExtractor."""
        return self.experience_extractor.extract_work_experience(text)

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using SkillsExtractor."""
        return self.skills_extractor.extract_skills(text)

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages and their proficiency levels using LanguageExtractor."""
        return self.language_extractor.extract_languages(text)

__all__ = [
    'ProfileExtractor', 'EducationExtractor', 'ExperienceExtractor', 
    'SkillsExtractor', 'LanguageExtractor', 'CurrentPositionExtractor', 'CVExtractor'
]