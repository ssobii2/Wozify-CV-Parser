from .profile_extractor import ProfileExtractor
from .education_extractor import EducationExtractor
from .education_extractor_hu import EducationExtractorHu
from .experience_extractor import ExperienceExtractor
from .experience_extractor_hu import ExperienceExtractorHu
from .skills_extractor import SkillsExtractor
from .language_extractor import LanguageExtractor
from .current_position_extractor import CurrentPositionExtractor
from .cv_section_parser import CVSectionParser

import re
import spacy
import huspacy
from langdetect import detect
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Load spaCy models
nlp_en = spacy.load('en_core_web_sm')
nlp_hu = huspacy.load('hu_core_news_md')

class CVExtractor:
    def __init__(self):
        self.profile_extractor = ProfileExtractor(nlp_en, nlp_hu)
        self.education_extractor = EducationExtractor(nlp_en)
        self.education_extractor_hu = EducationExtractorHu(nlp_hu)
        self.experience_extractor = ExperienceExtractor(nlp_en)
        self.experience_extractor_hu = ExperienceExtractorHu(nlp_hu)
        self.skills_extractor = SkillsExtractor(nlp_en, nlp_hu)
        self.language_extractor = LanguageExtractor(nlp_en, nlp_hu)
        self.current_position_extractor = CurrentPositionExtractor(nlp_en, nlp_hu)
        self.section_parser = CVSectionParser()
        
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

        self._cached_sections = {}  # Add this line to store parsed sections

    def _get_parsed_sections(self, text: str) -> Optional[Dict]:
        """Get parsed sections with caching to avoid multiple parses."""
        # Use text hash as cache key
        cache_key = hash(text)
        
        if cache_key in self._cached_sections:
            return self._cached_sections[cache_key]
        
        try:
            parsed_sections = self.section_parser.parse_sections(text)
            self._cached_sections[cache_key] = parsed_sections
            return parsed_sections
        except Exception as e:
            print(f"Section parsing failed, using direct extraction: {str(e)}")
            self._cached_sections[cache_key] = None
            return None

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            if language == 'hu':
                # For Hungarian text, first try to clean it
                cleaned_text = text.encode('utf-8', errors='ignore').decode('utf-8')
                # If the text contains many Hungarian-specific characters, use Hungarian model
                hungarian_chars = set('áéíóöőúüűÁÉÍÓÖŐÚÜŰ')
                if any(c in hungarian_chars for c in cleaned_text):
                    try:
                        # Try processing a small sample first
                        sample = cleaned_text[:100]
                        _ = nlp_hu(sample)
                        return nlp_hu
                    except Exception as e:
                        print(f"Warning: Hungarian model failed, falling back to English: {str(e)}")
                        return nlp_en
            return nlp_en
        except Exception as e:
            print(f"Warning: Language detection failed, using English model: {str(e)}")
            return nlp_en

    def safe_nlp_process(self, text: str, nlp_model):
        """Safely process text with NLP model, handling potential vocabulary issues."""
        try:
            # First try processing the whole text
            return nlp_model(text)
        except Exception as e:
            if "Can't retrieve string for hash" in str(e):
                # If vocabulary error occurs, try processing sentence by sentence
                sentences = text.split('.')
                processed_docs = []
                for sentence in sentences:
                    try:
                        if sentence.strip():
                            doc = nlp_model(sentence.strip())
                            processed_docs.append(doc)
                    except Exception as sent_error:
                        print(f"Warning: Skipping sentence due to error: {str(sent_error)}")
                        continue

                # Combine the successfully processed sentences
                if processed_docs:
                    return processed_docs[0].doc.from_docs(processed_docs)

            # If all else fails, return a basic processed version
            return nlp_en(text)

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
        try:
            language = detect(text)
        except:
            language = 'en'
        
        # Parse sections once at the start
        _ = self._get_parsed_sections(text)
        
        # Get appropriate NLP model
        nlp_model = self.get_nlp_model_for_text(text)
        
        # Process text with NLP model
        doc = self.safe_nlp_process(text, nlp_model)
        
        # Extract all information
        profile_data = self.profile_extractor.extract_profile(text)
        current_position = self.extract_current_position(text)
        education = self.extract_education(text)
        experience = self.extract_work_experience(text)
        skills = self.extract_skills(text)
        languages = self.extract_languages(text)
        
        # Clear the cache after processing
        self._cached_sections.clear()
        
        # Return extracted data with language information
        return {
            "language": language,
            "profile": profile_data,
            "current_position": current_position,
            "education": education,
            "experience": experience,
            "skills": skills,
            "languages": languages
        }

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information using the appropriate ExperienceExtractor."""
        try:
            language = detect(text)
            parsed_sections = self._get_parsed_sections(text)

            if language == 'hu':
                # Use Hungarian experience extractor
                return self.experience_extractor_hu.extract_work_experience(text, parsed_sections)
            else:
                # Use English experience extractor
                return self.experience_extractor.extract_work_experience(text, parsed_sections)

        except Exception as e:
            print(f"Error extracting work experience: {str(e)}")
            return []

    def extract_current_position(self, text: str) -> Optional[str]:
        """Extract the most recent job title using CurrentPositionExtractor."""
        work_experience = self.extract_work_experience(text)
        return self.current_position_extractor.extract_current_position(text, work_experience)

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information using EducationExtractor."""
        try:
            language = detect(text)
            
            if language == 'hu':
                # For Hungarian, we don't yet have section parser integration
                return self.education_extractor_hu.extract_education(text)
            
            # Get parsed sections from cache or parse new
            parsed_sections = self._get_parsed_sections(text)
            
            # For English, use the education extractor with parsed sections
            return self.education_extractor.extract_education(text, parsed_sections)
            
        except Exception as e:
            print(f"Error extracting education: {str(e)}")
            return []

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using SkillsExtractor."""
        try:
            # Get parsed sections from cache or parse new
            parsed_sections = self._get_parsed_sections(text)
            
            # Pass parsed sections to skills extractor
            return self.skills_extractor.extract_skills(text, parsed_sections)
            
        except Exception as e:
            print(f"Error extracting skills: {str(e)}")
            return []

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages and their proficiency levels using LanguageExtractor."""
        try:
            # Get parsed sections from cache or parse new
            parsed_sections = self._get_parsed_sections(text)
            
            # Pass parsed sections to language extractor
            return self.language_extractor.extract_languages(text, parsed_sections)
            
        except Exception as e:
            print(f"Error extracting languages: {str(e)}")
            return [{'language': '', 'proficiency': ''}]

__all__ = [
    'ProfileExtractor', 'EducationExtractor', 'EducationExtractorHu', 'ExperienceExtractor', 'ExperienceExtractorHu',
    'SkillsExtractor', 'LanguageExtractor', 'CurrentPositionExtractor', 'CVExtractor'
]