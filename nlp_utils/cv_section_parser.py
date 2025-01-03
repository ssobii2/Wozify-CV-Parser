import re
import spacy
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVSectionParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(CVSectionParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize CVSectionParser with patterns and models."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._init_patterns()
            self.current_text = ""
            try:
                self.model = spacy.load("models/textcat_model/model-best")
                logger.info("Loaded English text classification model")
            except Exception as e:
                self.model = None
                logger.warning(f"English text classification model not found, falling back to pattern matching only: {str(e)}")

    # Main parsing methods
    def parse_sections(self, text: str) -> Dict[str, List[str]]:
        """Parse CV text into sections.
        
        This is the main public interface for section parsing.
        """
        try:
            self.current_text = text
            sections = self.detect_sections(text)
            # Initialize all possible sections with empty lists
            all_sections = {
                "summary": [], "profile": [], "education": [], "experience": [],
                "languages": [], "skills": [], "projects": [], "certifications": [],
                "awards": [], "publications": [], "interests": [], "references": []
            }
            # Update with detected sections
            all_sections.update(sections)
            return all_sections
            
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}")
            return {}

    def detect_sections(self, text: str) -> Dict[str, List[str]]:
        """Main method to detect and extract sections from CV text."""
        if not text:
            return {}
        
        logger.info("Starting CV parsing...")
        self.current_text = text
        text = self._preprocess_text(text)
        
        sections = {
            "summary": [], "profile": [], "education": [], "experience": [],
            "languages": [], "skills": [], "projects": [], "certifications": [],
            "awards": [], "publications": [], "interests": [], "references": []
        }
        
        found_sections = set()
        current_section = None
        buffer = []
        lines = text.split('\n')
        current_idx = 0

        while current_idx < len(lines):
            line = lines[current_idx].strip()
            
            if not line and not current_section and not buffer:
                current_idx += 1
                continue

            if self._is_likely_new_section(line):
                section = self._identify_section_header(line, found_sections)
                
                if section:
                    if current_section and buffer:
                        content = self._clean_content('\n'.join(buffer))
                        if content:
                            if self._contains_language_info(content):
                                language_content, remaining_content = self._extract_language_content(content)
                                if language_content:
                                    sections['languages'].append(language_content)
                                    found_sections.add('languages')
                                if remaining_content and current_section != 'languages':
                                    sections[current_section].append(remaining_content)
                            else:
                                sections[current_section].append(content)
                        buffer = []
                    
                    current_section = section
                    current_idx += 1
                    continue

            if current_section:
                if line and not self._is_likely_separator(line, 
                    lines[current_idx + 1] if current_idx + 1 < len(lines) else ""):
                    buffer.append(line)
                else:
                    if buffer:
                        content = self._clean_content('\n'.join(buffer))
                        if content:
                            if current_section in ['summary', 'profile']:
                                detected_type = self._detect_section_content_type(content)
                                sections[detected_type].append(content)
                                found_sections.add(detected_type)
                            elif self._contains_language_info(content):
                                language_content, remaining_content = self._extract_language_content(content)
                                if language_content:
                                    sections['languages'].append(language_content)
                                    found_sections.add('languages')
                                if remaining_content and current_section != 'languages':
                                    sections[current_section].append(remaining_content)
                            else:
                                sections[current_section].append(content)
                        buffer = []
                    if line:
                        buffer.append(line)
            elif line:
                content = line.strip()
                if content:
                    detected_type = self._detect_section_content_type(content)
                    current_section = detected_type
                    found_sections.add(detected_type)
                    buffer.append(line)

            current_idx += 1

        if current_section and buffer:
            content = self._clean_content('\n'.join(buffer))
            if content:
                if self._contains_language_info(content):
                    language_content, remaining_content = self._extract_language_content(content)
                    if language_content:
                        sections['languages'].append(language_content)
                        found_sections.add('languages')
                    if remaining_content and current_section != 'languages':
                        sections[current_section].append(remaining_content)
                else:
                    sections[current_section].append(content)

        return sections

    # Pattern initialization methods
    def _init_patterns(self):
        """Initialize all pattern dictionaries and constants."""
        self.language_patterns = {
            'proficiency_levels': [
                r'(?i)(native|fluent|advanced|intermediate|basic|beginner|elementary|proficient)',
                r'(?i)(mother\s*tongue|business\s*level|working\s*knowledge|professional\s*working)',
                r'(?i)\b(c2|c1|b2|b1|a2|a1)\b'
            ],
            'languages': [
                r'(?i)\b(english|german|french|spanish|chinese|japanese|korean|arabic|russian|italian|portuguese|dutch|hindi|urdu|bengali|punjabi|tamil|telugu|marathi|gujarati|kannada|malayalam|thai|vietnamese|indonesian|malay|turkish|persian|polish|czech|slovak|romanian|bulgarian|croatian|serbian|slovenian|ukrainian|greek|hebrew|swedish|norwegian|danish|finnish|estonian|latvian|lithuanian)\b'
            ],
            'section_indicators': [
                r'(?i)^languages?(\s+skills?|\s+proficiency|\s+knowledge)?:?\s*$',
                r'(?i)^language\s+(skills?|proficiency|knowledge)\s*:?\s*$'
            ]
        }
        
        self.tech_keywords = {
            'programming', 'software', 'development', 'technologies', 'frameworks', 'languages',
            'tools', 'platforms', 'databases', 'methodologies', 'proficient', 'experienced',
            'knowledge', 'skills', 'expertise', 'competencies', 'stack', 'technical'
        }
        
        self.experience_indicators = [
            r'(?i)(20\d{2}\s*-\s*(20\d{2}|present|current))',
            r'(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}',
            r'(?i)(improved|developed|managed|led|created|implemented|achieved|increased|reduced|supported)',
            r'(?i)(intern|developer|engineer|manager|coordinator|assistant|specialist|analyst)',
            r'(?i)(\d+%|\d+\s*percent)',
            r'(?i)(project|team|client|stakeholder|objective|goal)'
        ]
        
        self.section_headers = {
            "summary": [
                r"(?i)^(professional\s+summary|executive\s+summary|career\s+summary|summary\s+of\s+qualifications)$",
                r"(?i)^(summary|career\s+objective|professional\s+objective)$"
            ],
            "profile": [
                r"(?i)^(profile|about\s*me|personal\s+information|introduction|contact\s+information)$",
                r"(?i)^(personal\s+details|personal\s+profile|contact|contact\s+details)$"
            ],
            "education": [
                r"(?i)^(education|academic|qualifications?|studies)$",
                r"(?i)^(educational\s+background|academic\s+history|academic\s+qualifications?)$"
            ],
            "experience": [
                r"(?i)^(experience|expertise|employment|work|career|professional\s+experience)$",
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

        self.section_content_indicators = {
            "summary": {
                "keywords": {
                    "years of experience", "expertise in", "background in", "specialized in",
                    "proven track record", "professional experience", "skilled in", "focus on"
                },
                "patterns": [
                    r"(?i)(\d+\+?\s+years?\s+of\s+experience\s+in)",
                    r"(?i)(proven\s+track\s+record\s+in)",
                    r"(?i)(specialized\s+in\s+developing|expertise\s+in\s+developing)",
                    r"(?i)(background\s+in\s+[a-z\s]+development)"
                ],
                "negative_patterns": [
                    r"(?i)(@|tel:|phone:|mobile:|address:|email:)",
                    r"(?i)(20\d{2}\s*[-–]\s*(20\d{2}|present|current))",
                    r"(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}"
                ]
            },
            "profile": {
                "keywords": {
                    "email", "phone", "address", "mobile", "linkedin", "github", "contact",
                    "birth", "nationality", "gender", "marital", "driving license"
                },
                "patterns": [
                    r"(?i)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    r"(?i)(\+\d{1,2}[-\s]?\d{1,}[-\s]?\d{1,}[-\s]?\d{1,})",
                    r"(?i)(linkedin\.com|github\.com)",
                    r"(?i)(date\s+of\s+birth|driving\s+license|marital\s+status)"
                ]
            }
        }

    # Section identification methods
    def _identify_section_header(self, line: str, found_sections: set) -> str:
        """Identify if a line is a section header using pattern matching."""
        line = line.strip()
        if not line or len(line.split()) > 5:
            return None
        
        for section, patterns in self.section_headers.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    if section in ['summary', 'profile']:
                        next_lines = self._get_next_content_lines(line, max_lines=3)
                        if next_lines:
                            detected_type = self._detect_section_content_type('\n'.join(next_lines))
                            found_sections.add(detected_type)
                            return detected_type
                    found_sections.add(section)
                    return section
                    
        return None

    def _is_likely_new_section(self, line: str) -> bool:
        """Enhanced check if a line is likely to be a new section header."""
        if not line.strip():
            return False
            
        date_patterns = [
            r"(?i)(19|20)\d{2}\s*[-–]\s*((19|20)\d{2}|present|current)",
            r"(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}",
            r"(?i)\d{1,2}/\d{4}",
            r"(?i)\d{1,2}\.\d{4}",
            r"(?i)\d{4}\s*[-–]\s*(?:Present|Current|Now|\d{4})",
            r"(?i)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–]",
            r"(?i)\d{2}/\d{4}\s*[-–]"
        ]
        
        if any(re.search(pattern, line) for pattern in date_patterns):
            return False
            
        if line.strip().startswith(('•', '-', '•', '○', '●', '*', '→', '▪', '◦')):
            return False
            
        if (line.isupper() and len(line.split()) <= 4 and 
            not any(char.isdigit() for char in line)):
            return True
            
        words = line.split()
        if 1 <= len(words) <= 5:
            common_starters = {'i', 'we', 'they', 'he', 'she', 'it', 'the', 'a', 'an', 'my', 'our', 'your'}
            first_word = words[0].lower()
            
            common_header_words = {
                'summary', 'profile', 'experience', 'education', 'skills',
                'projects', 'achievements', 'certifications', 'publications',
                'awards', 'interests', 'references', 'contact', 'personal',
                'work', 'employment', 'qualification', 'objective', 'about', 'work experience',
                'languages', 'expertise', 'professional'
            }
            
            if (words[0][0].isupper() and first_word not in common_starters and
                any(word.lower() in common_header_words for word in words)):
                return True
            
        return False

    def _is_likely_separator(self, line: str, next_line: str = "") -> bool:
        """Check if a line is likely a natural separator in the CV."""
        date_patterns = [
            r'\d{4}\s*[-–]\s*(?:Present|Current|Now|\d{4})',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–]',
            r'\d{2}/\d{4}\s*[-–]',
            r'\d{1,2}\.\d{4}',
            r'\d{1,2}/\d{4}'
        ]
        
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in date_patterns):
            return True
        
        if line.strip().startswith(('•', '-', '*', '▪', '◦', '○', '●', '→')):
            return True
        
        if (line.isupper() and len(line.split()) <= 4 and 
            not any(char.isdigit() for char in line)):
            return True
        
        if not line.strip() and not next_line.strip():
            return True
        
        return False

    # Content analysis methods
    def _detect_section_content_type(self, text: str) -> str:
        """Detect the type of content in a section."""
        text_lower = text.lower()
        
        if any(re.search(pattern, text) for pattern in self.section_content_indicators["summary"]["negative_patterns"]):
            return "profile"
            
        summary_score = 0
        profile_score = 0
        
        summary_score += sum(1 for word in self.section_content_indicators["summary"]["keywords"] 
                           if word in text_lower) * 2
        profile_score += sum(1 for word in self.section_content_indicators["profile"]["keywords"] 
                           if word in text_lower) * 1.5
        
        summary_score += sum(1 for pattern in self.section_content_indicators["summary"]["patterns"] 
                           if re.search(pattern, text)) * 2
        profile_score += sum(1 for pattern in self.section_content_indicators["profile"]["patterns"] 
                           if re.search(pattern, text)) * 2
        
        if len(text.split()) > 30 and not any(re.search(pattern, text) 
            for pattern in self.section_content_indicators["summary"]["negative_patterns"]):
            summary_score += 3
            
        if any(re.search(pattern, text) for pattern in self.experience_indicators):
            summary_score -= 2
            
        return "summary" if summary_score > profile_score else "profile"

    def _contains_language_info(self, text: str) -> bool:
        """Check if text contains language-related information."""
        has_section_indicator = any(
            re.search(pattern, text, re.IGNORECASE) 
            for pattern in self.language_patterns['section_indicators']
        )
        
        if not has_section_indicator:
            return False
        
        lines = text.split('\n')
        return any(self._is_language_line(line) for line in lines)

    def _is_language_line(self, text: str) -> bool:
        """Check if a line contains language information."""
        has_language_name = any(re.search(pattern, text.lower()) for pattern in self.language_patterns['languages'])
        has_proficiency = any(re.search(pattern, text.lower()) for pattern in self.language_patterns['proficiency_levels'])
        is_short = len(text.split()) <= 12
        has_work_exp = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.experience_indicators)
        has_tech_terms = any(keyword in text.lower() for keyword in self.tech_keywords)
        
        typical_format = bool(re.search(
            r'(?i)\b(english|german|french|spanish|hungarian|chinese|japanese|korean|arabic|russian|italian|portuguese|dutch|magyar|angol|német|francia|spanyol)\b[\s\-:]+\b(native|fluent|advanced|intermediate|basic|beginner|c1|c2|b1|b2|a1|a2)\b',
            text
        ))
        
        return (
            has_language_name 
            and has_proficiency 
            and is_short 
            and not has_work_exp 
            and not has_tech_terms
            and typical_format
        )

    # Text processing methods
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to handle two-column layouts."""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            if not line.strip():
                processed_lines.append(line)
                continue
            
            splits = re.split(r'\s{3,}|\t+', line)
            if len(splits) > 1:
                for split in splits:
                    if split.strip():
                        processed_lines.append(split.strip())
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def _get_next_content_lines(self, current_line: str, max_lines: int = 3) -> List[str]:
        """Get the next few non-empty content lines after the current line."""
        lines = []
        current_idx = 0
        text_lines = self.current_text.split('\n')
        
        for i, line in enumerate(text_lines):
            if line.strip() == current_line.strip():
                current_idx = i
                break
                
        for line in text_lines[current_idx + 1:]:
            if line.strip() and not self._is_likely_new_section(line):
                lines.append(line.strip())
                if len(lines) >= max_lines:
                    break
                    
        return lines
    
    def _clean_language_content(self, text: str) -> tuple[str, str]:
        """Clean and validate language section content, separating languages from work experience."""
        lines = text.split('\n')
        valid_language_lines = []
        work_experience_lines = []
        current_block = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_block:
                    self._process_content_block(current_block, valid_language_lines, work_experience_lines)
                    current_block = []
                continue
            
            current_block.append(line)
        
        if current_block:
            self._process_content_block(current_block, valid_language_lines, work_experience_lines)
        
        return ('\n'.join(valid_language_lines) if valid_language_lines else "", 
                '\n'.join(work_experience_lines) if work_experience_lines else "")
    
    def _process_content_block(self, block: list, language_lines: list, experience_lines: list):
        """Process a block of text to determine if it's language or work experience content."""
        block_text = ' '.join(block)
        
        has_language = any(re.search(pattern, block_text) for pattern in self.language_patterns['languages'])
        has_proficiency = any(re.search(pattern, block_text) for pattern in self.language_patterns['proficiency_levels'])
        has_work_exp = any(re.search(pattern, block_text) for pattern in self.experience_indicators)
        
        if has_language and has_proficiency and len(block_text.split()) <= 8:
            language_lines.extend(block)
        elif has_work_exp or len(block_text.split()) > 8:
            experience_lines.extend(block)

    def _extract_language_content(self, text: str) -> tuple[str, str]:
        """Extract language-related content from text.
        Returns: (language_content, remaining_content)"""
        lines = text.split('\n')
        language_lines = []
        other_lines = []
        
        for line in lines:
            if self._is_language_line(line):
                language_lines.append(line)
            else:
                other_lines.append(line)
        
        return (
            '\n'.join(language_lines) if language_lines else "",
            '\n'.join(other_lines) if other_lines else ""
        )

    # Model-related methods
    def _wait_for_model(self):
        """Wait for the model to be ready."""
        pass

    def _classify_text_with_model(self, text: str) -> Dict[str, float]:
        """Classify text using the spaCy model."""
        if not self.model:
            return {}
        
        try:
            doc = self.model(text)
            return doc.cats
        except Exception as e:
            logger.warning(f"Error during text classification: {str(e)}")
            return {}
