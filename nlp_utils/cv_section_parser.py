import os
from typing import Dict, List
import requests
from dotenv import load_dotenv
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class CVSectionParser:
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Common section headers in CVs
        self.section_headers = {
            "profile": [
                r"(?i)^(about\s*me|profile|summary|personal\s+information|introduction|objective)$",
                r"(?i)^(professional\s+summary|personal\s+details|personal\s+profile)$"
            ],
            "education": [
                r"(?i)^(education|academic|qualifications?|studies)$",
                r"(?i)^(educational\s+background|academic\s+history|academic\s+qualifications?)$"
            ],
            "experience": [
                r"(?i)^(experience|employment|work|career|professional\s+experience)$",
                r"(?i)^(work\s+history|employment\s+history|work\s+experience|professional\s+background)$",
                r"(?i)^(work\s+experience\s*/?\s*projects?)$" 
            ],
            "languages": [
                r"(?i)^(languages?|language\s+skills?)$",
                r"(?i)^(language\s+proficiency|linguistic\s+skills?)$"
            ],
            "skills": [
                r"(?i)^(skills?|technical\s+skills?|competencies|expertise|it\s+knowledge)$",
                r"(?i)^(technical\s+expertise|core\s+competencies|professional\s+skills|technical\s+proficiencies|technical\s+skills)$",
                r"(?i)^(development\s+tools?|programming\s+knowledge|technical\s+stack)$",
                r"(?i)^(technologies|tools?(\s+and\s+technologies)?|software|hardware)$"
            ],
            "projects": [
                r"(?i)^(projects?|personal\s+projects?|academic\s+projects?)$",
                r"(?i)^(key\s+projects?|project\s+experience|technical\s+projects?)$",
                r"(?i)^(selected\s+projects?|notable\s+projects?)$"
            ],
            "certifications": [
                r"(?i)^(certifications?|certificates?|professional\s+certifications?)$",
                r"(?i)^(accreditations?|qualifications?|awards?\s+and\s+certifications?)$"
            ],
            "awards": [
                r"(?i)^(awards?|honors?|achievements?)$",
                r"(?i)^(recognitions?|accomplishments?|awards?\s+and\s+achievements?)$"
            ],
            "publications": [
                r"(?i)^(publications?|research|papers?|conferences?)$",
                r"(?i)^(published\s+works?|research\s+papers?|scientific\s+publications?)$"
            ],
            "interests": [
                r"(?i)^(interests?|hobbies|activities|interests?,?\s+commitment)$",
                r"(?i)^(personal\s+interests?|extracurricular|other\s+activities)$"
            ],
            "references": [
                r"(?i)^(references?|recommendations?)$",
                r"(?i)^(professional\s+references?)$"
            ]
        }
        
        # Technology-related keywords that indicate skills section content
        self.tech_keywords = {
            'programming', 'software', 'development', 'technologies', 'frameworks', 'languages',
            'tools', 'platforms', 'databases', 'methodologies', 'proficient', 'experienced',
            'knowledge', 'skills', 'expertise', 'competencies', 'stack', 'technical'
        }
        
        # Initialize the model
        logger.info("Initializing CV Section Parser...")
        self._wait_for_model()
    
    def _wait_for_model(self):
        """Wait for the model to be ready."""
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": "test"})
            if response.status_code == 200:
                response_data = response.json()
                if isinstance(response_data, list):
                    logger.info("Model is ready")
                    return
                elif isinstance(response_data, dict) and response_data.get("error", "").startswith("Model"):
                    logger.info("Model is loading, waiting...")
                    time.sleep(20)  # Wait longer for model to load
            else:
                logger.warning(f"Unexpected response status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking model status: {str(e)}")
    
    def _identify_section_header(self, line: str) -> str:
        """Identify if a line is a section header."""
        # Clean the line
        line = line.strip()
        if not line or len(line.split()) > 5:  # Headers are usually short
            return None
            
        # Check against our header patterns
        for section, patterns in self.section_headers.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    logger.info(f"Found section header: {line} -> {section}")
                    return section
        
        return None
    
    def _is_likely_new_section(self, line: str) -> bool:
        """Check if a line is likely to be a new section header."""
        # Skip empty lines
        if not line.strip():
            return False
            
        # Check for date patterns that often start experience entries
        date_patterns = [
            r"(?i)(19|20)\d{2}\s*[-–]\s*((19|20)\d{2}|present|current)",  # Year ranges
            r"(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}",  # Month Year
            r"(?i)\d{1,2}/\d{4}",  # MM/YYYY
            r"(?i)\d{1,2}\.\d{4}"  # MM.YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line.lower()):
                return False
            
        # Check for bullet points or list markers
        if line.strip().startswith(('•', '-', '•', '○', '●', '*', '→')):
            return False
            
        # Check if line is short and possibly a header
        words = line.split()
        if 1 <= len(words) <= 5:
            # Check if first word is capitalized and not a common sentence starter
            common_starters = {'i', 'we', 'they', 'he', 'she', 'it', 'the', 'a', 'an'}
            first_word = words[0].lower()
            if words[0][0].isupper() and first_word not in common_starters:
                return True
            
        return False
        
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove multiple newlines
        content = re.sub(r'\n\s*\n', '\n', content)
        # Remove multiple spaces
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    
    def _is_skills_content(self, text: str) -> bool:
        """Check if the content is likely to be skills-related."""
        # Convert to lowercase for comparison
        text_lower = text.lower()
        
        # Count technology-related keywords
        keyword_count = sum(1 for keyword in self.tech_keywords if keyword in text_lower)
        
        # Check for common skill listing patterns
        has_skill_patterns = bool(re.search(r'(?i)(proficient|experienced|knowledge|expertise) in:', text))
        has_tech_list = bool(re.search(r'(?i)(java|python|c\+\+|javascript|sql|html|css|git|docker|kubernetes|aws|azure)', text))
        has_rating_pattern = bool(re.search(r'(?i)(basic|intermediate|advanced|expert|good|very good|specialist)', text))
        
        # Return True if multiple indicators are present
        return (keyword_count >= 2) or (has_skill_patterns and has_tech_list) or (has_rating_pattern and has_tech_list)

    def parse_sections(self, text: str) -> Dict[str, List[str]]:
        """Parse a CV text into different sections."""
        logger.info("Starting CV parsing...")
        
        # Initialize sections with all possible section types
        sections = {
            "profile": [],
            "education": [],
            "experience": [],
            "languages": [],
            "skills": []
        }
        
        # Add optional sections
        for section in self.section_headers.keys():
            if section not in sections:
                sections[section] = []
        
        lines = text.split('\n')
        current_section = None
        buffer = []
        
        # Handle content before first section as profile
        initial_buffer = []
        for line in lines:
            if self._is_likely_new_section(line) and self._identify_section_header(line):
                if initial_buffer:
                    content = self._clean_content('\n'.join(initial_buffer))
                    if content:
                        sections["profile"].append(content)
                break
            initial_buffer.append(line)
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines at the start
            if not line and not current_section and not buffer:
                continue
            
            # Check if this line is a section header
            if self._is_likely_new_section(line):
                section = self._identify_section_header(line)
                
                if section:
                    # Save previous section content if exists
                    if current_section and buffer:
                        content = self._clean_content('\n'.join(buffer))
                        if content:
                            sections[current_section].append(content)
                        buffer = []
                    
                    current_section = section
                    buffer = [line]
                    continue
            
            # If we have a current section, add to buffer
            if current_section:
                buffer.append(line)
            elif not current_section and line.strip():
                # If no section identified yet and line is not empty, treat as profile
                current_section = "profile"
                buffer.append(line)
            
            # If we hit a significant gap between content, save current buffer
            if not line and buffer and len(buffer) > 1:
                content = self._clean_content('\n'.join(buffer))
                if content:
                    sections[current_section].append(content)
                buffer = []
        
        # Don't forget the last section
        if current_section and buffer:
            content = self._clean_content('\n'.join(buffer))
            if content:
                sections[current_section].append(content)
        
        # Remove duplicates while preserving order
        for section in sections:
            if sections[section]:
                seen = set()
                sections[section] = [x for x in sections[section] if not (x in seen or seen.add(x))]
        
        # Ensure required sections are present and add optional sections with content
        required_sections = {
            "profile": sections.get("profile", []),
            "education": sections.get("education", []),
            "experience": sections.get("experience", []),
            "languages": sections.get("languages", []),
            "skills": sections.get("skills", [])
        }
        
        # Add optional sections that have content
        for section, content in sections.items():
            if section not in required_sections and content:
                required_sections[section] = content
        
        logger.info(f"Finished parsing CV into {len(required_sections)} sections")
        return required_sections
