import re
import spacy
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from nlp_utils.profile_extractor import ProfileExtractor
from nlp_utils.education_extractor import EducationExtractor
from nlp_utils.experience_extractor import ExperienceExtractor
from nlp_utils.skills_extractor import SkillsExtractor
from nlp_utils.language_extractor import LanguageExtractor
from nlp_utils.current_position_extractor import CurrentPositionExtractor

# Load the English language model with custom pipeline components
nlp = spacy.load('en_core_web_sm')

class CVExtractor:
    def __init__(self):
        self.profile_extractor = ProfileExtractor()
        self.education_extractor = EducationExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.skills_extractor = SkillsExtractor()
        self.language_extractor = LanguageExtractor()
        self.current_position_extractor = CurrentPositionExtractor()
        self.date_patterns = [
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
            r'Dec(?:ember)?)\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}'
        ]
        
        self.section_headers = {
            'education': ['education', 'academic background', 'qualifications', 'academic qualifications'],
            'experience': ['experience', 'work experience', 'employment history', 'work history', 'professional experience'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
            'languages': ['language', 'languages', 'language skills'],
        }

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text using various patterns."""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract content from a specific section."""
        content = []
        lines = text.split('\n')
        in_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    content.append(' '.join(current_entry))
                    current_entry = []
                continue

            # Check if this line is a section header
            if any(keyword in line.lower() for keyword in section_keywords):
                in_section = True
                continue
            elif any(keyword in line.lower() for keywords in self.section_headers.values() for keyword in keywords):
                in_section = False
                if current_entry:
                    content.append(' '.join(current_entry))
                    current_entry = []
                continue

            if in_section:
                current_entry.append(line)

        if current_entry:
            content.append(' '.join(current_entry))

        return content

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using SkillsExtractor."""
        return self.skills_extractor.extract_skills(text)

    def extract_entities(self, text: str) -> Dict:
        """Main method to extract all information from CV."""
        # Initialize the result dictionary with default empty values
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
        
        # Extract data and update only if values are found
        profile_data = self.extract_profile(text)
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

    def extract_profile(self, text: str) -> Dict[str, str]:
        """Extract profile information using ProfileExtractor."""
        return self.profile_extractor.extract_profile(text)

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages and their proficiency levels using LanguageExtractor."""
        return self.language_extractor.extract_languages(text)