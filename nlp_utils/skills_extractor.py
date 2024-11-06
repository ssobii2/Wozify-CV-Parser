import re
from typing import List
import spacy
from langdetect import detect, LangDetectException

class SkillsExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies']
        }
        
        # List of skills to extract
        self.skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
            'kotlin', 'go', 'rust', 'typescript', 'scala', 'perl', 'r',
            'html', 'css', 'react', 'angular', 'vue', 'node', 'django', 'flask',
            'spring', 'asp.net', 'jquery', 'bootstrap', 'sass', 'less',
            'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis',
            'cassandra', 'elasticsearch', 'dynamodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'ansible', 'circleci', 'gitlab',
            'git', 'jira', 'confluence', 'slack', 'vscode', 'intellij', 'eclipse',
            'postman', 'webpack', 'npm', 'yarn'
        ]

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line contains a section header
            is_section_header = any(keyword in line.lower() for keyword in section_keywords)
            
            # Check if next line is a different section
            is_next_different_section = False
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                is_next_different_section = any(
                    keyword in next_line.lower() 
                    for keyword in ['education', 'experience', 'projects', 'languages']
                )
            
            if is_section_header:
                in_section = True
                continue
            
            if in_section and is_next_different_section:
                in_section = False
            
            if in_section:
                section_lines.append(line)
        
        return section_lines

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using NLP and fallback to static list."""
        skills = set()
        
        # Use NLP to extract skills
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        
        # Use spaCy's NER to find skill entities
        for ent in doc.ents:
            if ent.label_ == 'SKILL':
                skills.add(ent.text.lower())
        
        # Fallback to static list if no skills found
        if not skills:
            skills_section = self.extract_section(text, self.section_headers['skills'])
            for skill in self.skills:
                if re.search(r'\b' + skill + r'\b', text, re.IGNORECASE):
                    skills.add(skill)
        
        return sorted(skills)