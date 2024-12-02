import os
from typing import Dict, List
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from dotenv import load_dotenv
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class CVSectionParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CVSectionParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            # Load model and tokenizer locally
            logger.info("Loading BART-large-MNLI model locally...")
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli").to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli")
            logger.info(f"Model loaded successfully on {self.device}")
            
            # Load mBERT model for Hungarian language
            logger.info("Loading mBERT model for Hungarian language...")
            self.mbert_model = AutoModelForSequenceClassification.from_pretrained("bert-base-multilingual-cased").to(self.device)
            self.mbert_tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
            logger.info("mBERT model loaded successfully")

            # Language-related patterns and keywords
            self.language_patterns = {
                'proficiency_levels': [
                    r'(?i)(native|fluent|advanced|intermediate|basic|beginner|elementary|proficient|anyanyelv|folyékony|haladó|középszint|alapszint|kezdő)',
                    r'(?i)(mother\s*tongue|business\s*level|working\s*knowledge|professional\s*working|anyanyelvi\s*szint|üzleti\s*szint|munkavégzés\s*szintje)',
                    r'(?i)\b(c2|c1|b2|b1|a2|a1)\b'
                ],
                'languages': [
                    r'(?i)\b(english|german|french|spanish|hungarian|chinese|japanese|korean|arabic|russian|italian|portuguese|dutch|hindi|urdu|bengali|punjabi|tamil|telugu|marathi|gujarati|kannada|malayalam|thai|vietnamese|indonesian|malay|turkish|persian|polish|czech|slovak|romanian|bulgarian|croatian|serbian|slovenian|ukrainian|greek|hebrew|swedish|norwegian|danish|finnish|estonian|latvian|lithuanian|magyar|angol|német|francia|spanyol|olasz|orosz|kínai|japán)\b'
                ],
                'section_indicators': [
                    r'(?i)^languages?(\s+skills?|\s+proficiency|\s+knowledge)?:?\s*$',
                    r'(?i)^language\s+(skills?|proficiency|knowledge)\s*:?\s*$',
                    r'(?i)^nyelv(ek)?(\s+készségek?|\s+ismeretek|\s+szint)?:?\s*$'
                ]
            }
            
            # Technology-related keywords that indicate skills section content
            self.tech_keywords = {
                'programming', 'software', 'development', 'technologies', 'frameworks', 'languages',
                'tools', 'platforms', 'databases', 'methodologies', 'proficient', 'experienced',
                'knowledge', 'skills', 'expertise', 'competencies', 'stack', 'technical'
            }
            
            # Work experience indicators
            self.experience_indicators = [
                r'(?i)(20\d{2}\s*-\s*(20\d{2}|present|current))',  # Year ranges
                r'(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}',  # Month Year
                r'(?i)(improved|developed|managed|led|created|implemented|achieved|increased|reduced|supported)',  # Action verbs
                r'(?i)(intern|developer|engineer|manager|coordinator|assistant|specialist|analyst)',  # Job titles
                r'(?i)(\d+%|\d+\s*percent)',  # Percentages
                r'(?i)(project|team|client|stakeholder|objective|goal)'  # Work-related terms
            ]
            
            # Common section headers in CVs
            self.section_headers = {
                "profile": [
                    r"(?i)^(about\s*me|profile|summary|personal\s+information|introduction|objective|bemutatkozás|profil|összefoglalás|személyes\s+információk|bevezetés|célkitűzés)$",
                    r"(?i)^(professional\s+summary|personal\s+details|personal\s+profile|szakmai\s+összefoglalás|személyes\s+adatok|személyes\s+profil)$"
                ],
                "education": [
                    r"(?i)^(education|academic|qualifications?|studies|oktatás|akadémiai|képesítések?|tanulmányok)$",
                    r"(?i)^(educational\s+background|academic\s+history|academic\s+qualifications?|oktatási\s+hátter|akadémiai\s+előzmények|akadémiai\s+képesítések?)$"
                ],
                "experience": [
                    r"(?i)^(experience|employment|work|career|professional\s+experience|tapasztalat|foglalkoztatás|munka|karrier|szakmai\s+tapasztalat)$",
                    r"(?i)^(work\s+history|employment\s+history|work\s+experience|professional\s+background|munkatörténet|foglalkoztatási\s+történet|munkatapasztalat|szakmai\s+hátter)$",
                    r"(?i)^(work\s+experience\s*/?\s*projects?|munkatapasztalat\s*/?\s*projektek?)$"
                ],
                "languages": [
                    r"(?i)^(languages?|language\s+skills?|nyelv(ek)?|nyelvi\s+készségek?)$",
                    r"(?i)^(language\s+proficiency|linguistic\s+skills?|nyelvi\s+szint|nyelvi\s+készségek?)$"
                ],
                "skills": [
                    r"(?i)^(skills?|technical\s+skills?|competencies|expertise|it\s+knowledge|készségek?|technikai\s+készségek?|kompetenciák|szakértelem|it\s+ismeretek)$",
                    r"(?i)^(technical\s+expertise|core\s+competencies|professional\s+skills|technical\s+proficiencies|technical\s+skills|technikai\s+szakértelem|alapvető\s+kompetenciák|szakmai\s+készségek|technikai\s+ismeretek|technikai\s+készségek)$",
                    r"(?i)^(development\s+tools?|programming\s+knowledge|technical\s+stack|fejlesztési\s+eszközök?|programozási\s+ismeretek|technikai\s+halmaz)$",
                    r"(?i)^(technologies|tools?(\s+and\s+technologies)?|software|hardware|technológiák|eszközök?(\s+és\s+technológiák)?|szoftver|hardver)$"
                ],
                "projects": [
                    r"(?i)^(projects?|personal\s+projects?|academic\s+projects?|projektek?|személyes\s+projektek?|akadémiai\s+projektek?)$",
                    r"(?i)^(key\s+projects?|project\s+experience|technical\s+projects?|kulcsfontosságú\s+projektek?|projekt\s+tapasztalat|technikai\s+projektek?)$",
                    r"(?i)^(selected\s+projects?|notable\s+projects?|kiválasztott\s+projektek?|jelentős\s+projektek?)$"
                ],
                "certifications": [
                    r"(?i)^(certifications?|certificates?|professional\s+certifications?|tanúsítványok?|bizonyítványok?|szakmai\s+tanúsítványok?)$",
                    r"(?i)^(accreditations?|qualifications?|awards?\s+and\s+certifications?|akkreditációk?|képesítések?|díjak?\s+és\s+tanúsítványok?)$"
                ],
                "awards": [
                    r"(?i)^(awards?|honors?|achievements?|díjak?|kitüntetések?|eredmények?)$",
                    r"(?i)^(recognitions?|accomplishments?|awards?\s+and\s+achievements?|elismerések?|teljesítmények?|díjak?\s+és\s+eredmények?)$"
                ],
                "publications": [
                    r"(?i)^(publications?|research|papers?|conferences?|publikációk?|kutatás|tanulmányok?|konferenciák?)$",
                    r"(?i)^(published\s+works?|research\s+papers?|scientific\s+publications?|publikált\s+munkák?|kutatási\s+tanulmányok?|tudományos\s+publikációk?)$"
                ],
                "interests": [
                    r"(?i)^(interests?|hobbies|activities|interests?,?\s+commitment|érdeklődési\s+körök?|hobbi|tevékenységek?|érdeklődési\s+körök?,?\s+elkötelezettség)$",
                    r"(?i)^(personal\s+interests?|extracurricular|other\s+activities|személyes\s+érdeklődés?|tanórán\s+kívüli|egyéb\s+tevékenységek)$"
                ],
                "references": [
                    r"(?i)^(references?|recommendations?|referenciák?|ajánlások?)$",
                    r"(?i)^(professional\s+references?|szakmai\s+referenciák?)$"
                ]
            }
            
    def _wait_for_model(self):
        """Wait for the model to be ready."""
        pass
    
    def _identify_section_header(self, line: str, found_sections: set) -> str:
        """Identify if a line is a section header."""
        # Clean the line
        line = line.strip()
        if not line or len(line.split()) > 5:  # Headers are usually short
            return None
        
        # Detect language and select model
        language = self._detect_language(line)
        model, tokenizer = self._get_model_and_tokenizer(language)

        # Check against our header patterns first
        for section, patterns in self.section_headers.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    logger.info(f"Found section header: {line} -> {section}")
                    found_sections.add(section)
                    return section
                    
        # If no direct match found, only use model inference for unfound sections
        unfound_sections = set(self.section_headers.keys()) - found_sections
        if unfound_sections:
            with torch.no_grad():
                # Prepare candidate sections - only use unfound ones
                candidates = list(unfound_sections)
                scores = []
                
                # Create input pairs for each unfound candidate section
                for candidate in candidates:
                    # Format input for entailment task
                    premise = line
                    hypothesis = f"This is a {candidate} section header"
                    
                    # Tokenize
                    inputs = tokenizer(
                        premise,
                        hypothesis,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=128
                    ).to(self.device)
                    
                    # Get model prediction
                    outputs = model(**inputs)
                    logits = outputs.logits
                    
                    # Log logits shape for debugging
                    logger.debug(f"Logits shape: {logits.shape}")

                    # Get probability of entailment (last dimension)
                    probs = torch.softmax(logits, dim=1)
                    if probs.shape[1] > 2:
                        entail_prob = probs[0][2].item()  # Index 2 is entailment
                    else:
                        entail_prob = probs[0][1].item()  # Adjust if only two classes
                    scores.append(entail_prob)
                
                # Find best matching section
                if scores:  # Only if we had candidates
                    max_score = max(scores)
                    if max_score > 0.7:  # Confidence threshold
                        best_section = candidates[scores.index(max_score)]
                        logger.info(f"Model identified section header: {line} -> {best_section} (confidence: {max_score:.2f})")
                        found_sections.add(best_section)
                        return best_section
        
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
        
        # Process the last block
        if current_block:
            self._process_content_block(current_block, valid_language_lines, work_experience_lines)
        
        return ('\n'.join(valid_language_lines) if valid_language_lines else "", 
                '\n'.join(work_experience_lines) if work_experience_lines else "")
    
    def _process_content_block(self, block: list, language_lines: list, experience_lines: list):
        """Process a block of text to determine if it's language or work experience content."""
        block_text = ' '.join(block)
        
        # Check if block contains language information
        has_language = any(re.search(pattern, block_text) for pattern in self.language_patterns['languages'])
        has_proficiency = any(re.search(pattern, block_text) for pattern in self.language_patterns['proficiency_levels'])
        
        # Check if block contains work experience indicators
        has_work_exp = any(re.search(pattern, block_text) for pattern in self.experience_indicators)
        
        # If it's a language entry (contains language name and proficiency, and is relatively short)
        if has_language and has_proficiency and len(block_text.split()) <= 8:
            language_lines.extend(block)
        # If it looks like work experience
        elif has_work_exp or len(block_text.split()) > 8:
            experience_lines.extend(block)
    
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

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to handle two-column layouts."""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                processed_lines.append(line)
                continue
            
            # Check for potential column split indicators
            splits = re.split(r'\s{3,}|\t+', line)
            if len(splits) > 1:
                # Process each column separately
                for split in splits:
                    if split.strip():
                        processed_lines.append(split.strip())
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)

    def parse_sections(self, text: str) -> Dict[str, List[str]]:
        """Parse a CV text into different sections."""
        logger.info("Starting CV parsing...")
        
        # Preprocess text to handle two-column layouts
        text = self._preprocess_text(text)
        
        # Initialize sections with all possible section types
        sections = {
            "profile": [],
            "education": [],
            "experience": [],
            "languages": [],
            "skills": []
        }
        
        # Track which sections we've found to avoid unnecessary ML
        found_sections = set()
        
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
            if self._is_likely_new_section(line) and self._identify_section_header(line, found_sections):
                if initial_buffer:
                    content = self._clean_content('\n'.join(initial_buffer))
                    if content:
                        sections["profile"].append(content)
                        found_sections.add("profile")
                break
            initial_buffer.append(line)
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines at the start
            if not line and not current_section and not buffer:
                continue
            
            # Check if this line is a section header
            if self._is_likely_new_section(line):
                section = self._identify_section_header(line, found_sections)
                
                if section:
                    # Save previous section content if exists
                    if current_section and buffer:
                        content = self._clean_content('\n'.join(buffer))
                        if content:
                            # Check for language content within other sections
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
                    # Check for language content
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
        
        # Don't forget the last section
        if current_section and buffer:
            content = self._clean_content('\n'.join(buffer))
            if content:
                # Check for language content in the last section
                if self._contains_language_info(content):
                    language_content, remaining_content = self._extract_language_content(content)
                    if language_content:
                        sections['languages'].append(language_content)
                        found_sections.add('languages')
                    if remaining_content and current_section != 'languages':
                        sections[current_section].append(remaining_content)
                else:
                    sections[current_section].append(content)
        
        # Remove duplicates while preserving order
        for section in sections:
            if sections[section]:
                seen = set()
                sections[section] = [x for x in sections[section] if not (x in seen or seen.add(x))]
        
        logger.info(f"Finished parsing CV into {len(sections)} sections")
        return sections

    def _contains_language_info(self, text: str) -> bool:
        """Check if text contains language-related information."""
        # Language indicators
        language_patterns = [
            r'\b(?:language|nyelv)[s]?\b',  # Language headers
            r'\b(?:english|hungarian|german|french|spanish)\b',  # Common languages
            r'\b(?:angol|magyar|német|francia|spanyol)\b',  # Hungarian language names
            r'\b(?:native|fluent|advanced|intermediate|basic)\b',  # Proficiency levels
            r'\b(?:anyanyelv|folyékony|haladó|középszint|alapszint)\b',  # Hungarian proficiency
            r'\b[ABC][12]\b'  # CEFR levels
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in language_patterns)

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

    def _is_language_line(self, text: str) -> bool:
        """Check if a line contains language information."""
        # Common language patterns
        language_patterns = [
            r'\b(?:english|hungarian|german|french|spanish|italian|russian|chinese|japanese)\b',
            r'\b(?:angol|magyar|német|francia|spanyol|olasz|orosz|kínai|japán)\b',
            r'\b(?:native|fluent|advanced|intermediate|basic|beginner)\b',
            r'\b(?:anyanyelv|folyékony|haladó|középszint|alapszint|kezdő)\b',
            r'\b[ABC][12]\b',
            r'(?:language|nyelv)[s]?\s*:',
            r'\b(?:mother tongue|business level|working knowledge)\b',
            r'\b(?:anyanyelvi szint|üzleti szint|munkavégzés szintje)\b'
        ]
        
        text_lower = text.lower()
        
        # Check for language patterns
        has_language = any(re.search(pattern, text_lower) for pattern in language_patterns)
        
        # Check for typical language line structure (Language - Level)
        has_structure = bool(re.search(r'\w+\s*[-–:]\s*\w+', text))
        
        return has_language or has_structure

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on presence of Hungarian keywords."""
        hungarian_keywords = [
            'magyar', 'nyelv', 'folyékony', 'haladó', 'középszint', 'alapszint'
        ]
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in hungarian_keywords):
            return 'hungarian'
        return 'english'

    def _get_model_and_tokenizer(self, language: str):
        """Return the appropriate model and tokenizer based on the language."""
        if language == 'hungarian':
            return self.mbert_model, self.mbert_tokenizer
        return self.model, self.tokenizer
