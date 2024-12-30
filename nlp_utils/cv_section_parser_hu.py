import os
from typing import Dict, List
import logging
import re
import fasttext
from pathlib import Path
from langdetect import detect

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVSectionParserHu:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CVSectionParserHu, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            # Initialize patterns
            self._init_patterns()
            
            # Store current text being processed
            self.current_text = ""
            
            # Load the Hungarian FastText model
            try:
                self.model = fasttext.load_model("fasttext_output_v3/resume_classifier.ftz")
                logger.info("Loaded Hungarian text classification model")
            except Exception as e:
                self.model = None
                logger.warning(f"Hungarian text classification model not found, falling back to pattern matching only: {str(e)}")

    def _init_patterns(self):
        # Language-related patterns and keywords
        self.language_patterns = {
            'proficiency_levels': [
                r'(?i)(anyanyelv|folyékony|haladó|középszint|alapszint|kezdő)',
                r'(?i)(anyanyelvi\s*szint|üzleti\s*szint|munkavégzés\s*szintje)',
                r'(?i)\b(c2|c1|b2|b1|a2|a1)\b'
            ],
            'languages': [
                r'(?i)\b(magyar|angol|német|francia|spanyol|olasz|orosz|kínai|japán)\b'
            ],
            'section_indicators': [
                r'(?i)^nyelv(ek)?(\s+készségek?|\s+ismeretek|\s+szint)?:?\s*$',
                r'(?i)^nyelvtudás:?\s*$',
                r'(?i)^nyelvi\s+készségek:?\s*$'
            ]
        }
        
        # Technology-related keywords that indicate skills section content
        self.tech_keywords = {
            'programozás', 'szoftver', 'fejlesztés', 'technológiák', 'keretrendszerek',
            'eszközök', 'platformok', 'adatbázisok', 'módszertanok', 'tapasztalt',
            'ismeret', 'készségek', 'szakértelem', 'kompetenciák', 'technikai'
        }
        
        # Work experience indicators
        self.experience_indicators = [
            r'(?i)(20\d{2}\s*-\s*(20\d{2}|jelenleg|jelenlegi))',  # Year ranges
            r'(?i)(jan|feb|már|ápr|máj|jún|júl|aug|szep|okt|nov|dec)\s*\d{4}',  # Month Year
            r'(?i)(fejlesztett|vezetett|létrehozott|megvalósított|elért|növelte|csökkentette|támogatta)',  # Action verbs
            r'(?i)(gyakornok|fejlesztő|mérnök|vezető|koordinátor|asszisztens|specialista|elemző)',  # Job titles
            r'(?i)(\d+%|\d+\s*százalék)',  # Percentages
            r'(?i)(projekt|csapat|ügyfél|érdekelt|célkitűzés|cél)'  # Work-related terms
        ]
        
        # Common section headers in CVs - Adding more Hungarian variations and making patterns more flexible
        self.section_headers = {
            "summary": [
                r"(?i)^(szakmai\s+összefoglaló|szakmai\s+összefoglalás)[\s:]*$",
                r"(?i)^(összefoglaló|szakmai\s+célkitűzés|célkitűzések)[\s:]*$",
                r"(?i)^(bemutatkozás|szakmai\s+bemutatkozás|rövid\s+bemutatkozás)[\s:]*$",
                r"(?i)^(szakmai\s+háttér|szakmai\s+profil)[\s:]*$"
            ],
            "profile": [
                r"(?i)^(profil|bemutatkozás|személyes\s+adatok|kapcsolat)[\s:]*$",
                r"(?i)^(személyes\s+profil|elérhetőségek|kapcsolati\s+adatok)[\s:]*$",
                r"(?i)^(személyes\s+információk?|alapadatok)[\s:]*$"
            ],
            "education": [
                r"(?i)^(tanulmányok|oktatás|képzettség|végzettség)$",
                r"(?i)^(iskolai\s+végzettség|tanulmányi\s+háttér|képesítések)$"
            ],
            "experience": [
                r"(?i)^(tapasztalat|munkatapasztalat|szakmai\s+tapasztalat)$",
                r"(?i)^(munkahelyek|szakmai\s+háttér|munkatörténet|karriertörténet)$",
                r"(?i)^(szakmai\s+tapasztalat\s*/?\s*projektek?)$"
            ],
            "languages": [
                r"(?i)^(nyelvtudás|nyelv(ek)?|nyelvi\s+készségek)$",
                r"(?i)^(nyelvi\s+szint|nyelvismeretek?)$"
            ],
            "skills": [
                r"(?i)^(készségek|technikai\s+készségek|kompetenciák|szakértelem|informatikai\s+ismeretek)$",
                r"(?i)^(technikai\s+szakértelem|alapvető\s+kompetenciák|szakmai\s+készségek)$",
                r"(?i)^(fejlesztői\s+eszközök|programozási\s+ismeretek|technikai\s+stack)$",
                r"(?i)^(technológiák|eszközök(\s+és\s+technológiák)?|szoftverek)$"
            ],
            "projects": [
                r"(?i)^(projektek|személyes\s+projektek|szakmai\s+projektek)$",
                r"(?i)^(kiemelt\s+projektek|projekt\s+tapasztalat|technikai\s+projektek)$"
            ],
            "certifications": [
                r"(?i)^(tanúsítványok|bizonyítványok|szakmai\s+tanúsítványok)$",
                r"(?i)^(akkreditációk|képesítések|díjak\s+és\s+tanúsítványok)$"
            ],
            "awards": [
                r"(?i)^(díjak|kitüntetések|eredmények)$",
                r"(?i)^(elismerések|teljesítmények|díjak\s+és\s+eredmények)$"
            ],
            "publications": [
                r"(?i)^(publikációk|kutatás|tanulmányok|konferenciák)$",
                r"(?i)^(publikált\s+munkák|kutatási\s+munkák|tudományos\s+publikációk)$"
            ],
            "interests": [
                r"(?i)^(érdeklődési\s+körök|hobbi|tevékenységek|szabadidős\s+tevékenységek)$",
                r"(?i)^(személyes\s+érdeklődés|egyéb\s+tevékenységek)$"
            ],
            "references": [
                r"(?i)^(referenciák|ajánlások|szakmai\s+referenciák)$"
            ]
        }

        # Update section content indicators for better content classification
        self.section_content_indicators = {
            "summary": {
                "keywords": {
                    "év tapasztalat", "szakterület", "szakértelem", "specializáció",
                    "háttér", "tapasztalattal rendelkezik", "fejlesztő", "mérnök",
                    "szakember", "területen", "dolgozom", "foglalkozom"
                },
                "patterns": [
                    r"(?i)(\d+\+?\s+év(es)?\s+([^.]*(fejleszt[őé]|tapasztalat)))",
                    r"(?i)(szakmai\s+tapasztalattal\s+rendelkez[a-z]+)",
                    r"(?i)(szakterület[e|em].*(?:fejlesztés|programozás))",
                    r"(?i)(háttér.*(?:fejlesztés|programozás))",
                    r"(?i)^[^.]{10,}(vagyok|dolgozom)\b"  # Starts with at least 10 chars followed by "vagyok/dolgozom"
                ],
                "negative_patterns": [
                    r"(?i)(@|tel:|telefon:|mobil:|cím:|email:)",
                    r"(?i)(született|lakcím|telefonszám|születési)",
                    r"(?i)(anyja\s+neve|állampolgárság|családi\s+állapot)",
                    r"(?i)^[^.]{0,50}:\s*\+?\d"  # Short line with phone number
                ]
            },
            "profile": {
                "keywords": {
                    "név", "telefon", "email", "cím", "lakcím", "elérhetőség",
                    "mobil", "születési", "állampolgárság"
                },
                "patterns": [
                    r"(?i)(tel:|telefon:|mobil:|e-mail:|email:|cím:|lakcím:)",
                    r"(?i)(született:|születési\s+hely:|születési\s+idő:)",
                    r"(?i)(állampolgárság:|családi\s+állapot:)"
                ]
            }
        }

    def _wait_for_model(self):
        """Wait for the model to be ready."""
        pass

    def _identify_section_header(self, line: str, found_sections: set) -> str:
        """Identify if a line is a section header using pattern matching."""
        # Clean the line
        line = line.strip()
        if not line or len(line.split()) > 5:  # Headers are usually short
            return None
        
        # First try exact pattern matches
        for section, patterns in self.section_headers.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    # Special handling for summary vs profile
                    if section in ['summary', 'profile']:
                        # Look ahead for content type if possible
                        next_lines = self._get_next_content_lines(line, max_lines=3)
                        if next_lines:
                            detected_type = self._detect_section_content_type('\n'.join(next_lines))
                            found_sections.add(detected_type)
                            return detected_type
                    found_sections.add(section)
                    return section
                    
        return None

    def _get_next_content_lines(self, current_line: str, max_lines: int = 3) -> List[str]:
        """Get the next few non-empty content lines after the current line."""
        lines = []
        current_idx = 0
        text_lines = self.current_text.split('\n')
        
        # Find current line index
        for i, line in enumerate(text_lines):
            if line.strip() == current_line.strip():
                current_idx = i
                break
                
        # Get next content lines
        for line in text_lines[current_idx + 1:]:
            if line.strip() and not self._is_likely_new_section(line):
                lines.append(line.strip())
                if len(lines) >= max_lines:
                    break
                    
        return lines

    def _is_likely_new_section(self, line: str) -> bool:
        """Check if a line is likely to be a new section header."""
        # Skip empty lines
        if not line.strip():
            return False
            
        # Check for date patterns that often start experience entries
        date_patterns = [
            r"(?i)(19|20)\d{2}\s*[-–]\s*((19|20)\d{2}|jelenleg|jelenlegi)",  # Year ranges
            r"(?i)^(jan|feb|már|ápr|máj|jún|júl|aug|szep|okt|nov|dec)\s*\d{4}",  # Month Year
            r"(?i)\d{1,2}/\d{4}",  # MM/YYYY
            r"(?i)\d{1,2}\.\d{4}"  # MM.YYYY
        ]
        
        # Return False if line matches date patterns
        if any(re.search(pattern, line) for pattern in date_patterns):
            return False
            
        # Check for bullet points or list markers at start of line
        if line.strip().startswith(('•', '-', '•', '○', '●', '*', '→', '▪', '◦')):
            return False
            
        # Check if line is all caps and short (likely a header)
        if (line.isupper() and len(line.split()) <= 4 and 
            not any(char.isdigit() for char in line)):
            return True
            
        # Check if line is short and possibly a header
        words = line.split()
        if 1 <= len(words) <= 5:
            # Check if first word is capitalized and not a common sentence starter
            common_starters = {'a', 'az', 'és', 'vagy', 'de', 'mert', 'hogy', 'ez', 'az'}
            first_word = words[0].lower()
            
            # Additional check for common header words
            common_header_words = {
                'összefoglaló', 'profil', 'tapasztalat', 'tanulmányok', 'készségek',
                'projektek', 'eredmények', 'tanúsítványok', 'publikációk',
                'díjak', 'érdeklődés', 'referenciák', 'kapcsolat', 'személyes',
                'munka', 'foglalkoztatás', 'képesítés', 'célkitűzs', 'bemutatkozás',
                'nyelvek', 'szakértelem', 'szakmai'
            }
            
            if (words[0][0].isupper() and first_word not in common_starters and
                any(word.lower() in common_header_words for word in words)):
                return True
            
        return False

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove multiple newlines
        content = re.sub(r'\n\s*\n', '\n', content)
        # Remove multiple spaces
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def _is_language_line(self, text: str) -> bool:
        """Check if a line contains language information."""
        # Must contain both a language name and a proficiency level
        has_language_name = any(re.search(pattern, text.lower()) for pattern in self.language_patterns['languages'])
        has_proficiency = any(re.search(pattern, text.lower()) for pattern in self.language_patterns['proficiency_levels'])
        
        # Line must be relatively short (typical for language entries)
        is_short = len(text.split()) <= 12
        
        # Must not contain work experience indicators
        has_work_exp = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.experience_indicators)
        
        # Must not contain skill-related technical terms
        has_tech_terms = any(keyword in text.lower() for keyword in self.tech_keywords)
        
        # Must be in a typical language statement format
        typical_format = bool(re.search(
            r'(?i)\b(magyar|angol|német|francia|spanyol|olasz|orosz)\b[\s\-:]+\b(anyanyelv|folyékony|haladó|középszint|alapszint|kezdő|c1|c2|b1|b2|a1|a2)\b',
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

    def _classify_text_with_model(self, text: str) -> Dict[str, float]:
        """Classify text using the FastText model."""
        if not self.model:
            return {}
        
        try:
            # Preprocess text
            processed_text = ' '.join(line.strip() for line in text.split('\n') if line.strip())
            processed_text = processed_text.lower()
            processed_text = processed_text.replace(":", " : ")
            processed_text = processed_text.replace("/", " / ")
            processed_text = re.sub(r'[^a-zA-Z0-9áéíóöőúüűÁÉÍÓÖŐÚÜŰ\s\-]', ' ', processed_text)
            processed_text = re.sub(r'\s+', ' ', processed_text)
            processed_text = re.sub(r'(\w)\s*-\s*(\w)', r'\1-\2', processed_text)
            processed_text = processed_text.strip()
            
            # FastText prediction
            prediction = self.model.predict(processed_text, k=5)
            labels, scores = prediction
            
            # Hungarian to English label mapping
            hu_to_en = {
                'személyes': 'Profile',
                'összegzés': 'Summary',
                'tapasztalat': 'Experience',
                'tanulmányok': 'Education',
                'készségek': 'Skills',
                'egyéb': None
            }
            
            # Convert and map labels
            results = {}
            for label, score in zip(labels, scores):
                if isinstance(label, bytes):
                    label = label.decode('utf-8')
                label = label.replace("__label__", "")
                if label in hu_to_en and hu_to_en[label] is not None:
                    results[hu_to_en[label]] = float(score)
            
            return results
        except Exception as e:
            logger.warning(f"Error during text classification: {str(e)}")
            return {}

    def parse_sections(self, text: str) -> Dict[str, List[str]]:
        """Parse CV text into sections."""
        if not text:
            return {}
        
        logger.info("Starting Hungarian CV parsing...")

        # Initialize sections
        sections = {
            "summary": [],
            "profile": [],
            "education": [],
            "experience": [],
            "languages": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "awards": [],
            "publications": [],
            "interests": [],
            "references": []
        }

        # Split text into lines and process
        lines = text.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            
            # Skip empty lines if no section is active
            if not line and not current_section:
                continue

            # Check if line is a section header
            if self._is_likely_new_section(line):
                section = self._identify_section_header(line, set())
                
                # If we found a valid section header
                if section:
                    # Save content from previous section if exists
                    if current_section and current_content:
                        content = self._clean_content('\n'.join(current_content))
                        if content:
                            sections[current_section].append(content)
                    
                    # Start new section
                    current_section = section
                    current_content = []
                    continue

            # Add line to current section if we're in one
            if current_section and line:
                current_content.append(line)

        # Don't forget to save the last section
        if current_section and current_content:
            content = self._clean_content('\n'.join(current_content))
            if content:
                sections[current_section].append(content)

        return sections

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

    def _detect_section_content_type(self, text: str) -> str:
        """Determine if content is more likely to be summary or profile based on content analysis."""
        # First try model classification if available
        if self.model:
            predictions = self._classify_text_with_model(text)
            if predictions:
                section = max(predictions.items(), key=lambda x: x[1])[0]
                confidence = max(predictions.values())
                if section in ['Summary', 'Profile'] and confidence > 0.5:
                    return section.lower()
        
        # Enhanced pattern matching
        text_lower = text.lower()
        
        # Check for negative patterns first
        if any(re.search(pattern, text) for pattern in self.section_content_indicators["summary"]["negative_patterns"]):
            return "profile"
        
        # If text starts with typical profile information, classify as profile
        first_line = text.split('\n')[0].strip().lower()
        if any(keyword in first_line for keyword in self.section_content_indicators["profile"]["keywords"]):
            return "profile"
        
        # Check for summary-like content at the start
        if re.match(r"(?i)^[^.]{10,}(vagyok|dolgozom)\b", text):
            return "summary"
        
        # Score-based classification
        summary_score = 0
        profile_score = 0
        
        # Check keywords with weighted scoring
        summary_score += sum(2 for word in self.section_content_indicators["summary"]["keywords"] 
                            if word in text_lower)
        profile_score += sum(1.5 for word in self.section_content_indicators["profile"]["keywords"] 
                            if word in text_lower)
        
        # Check patterns
        summary_score += sum(2 for pattern in self.section_content_indicators["summary"]["patterns"] 
                            if re.search(pattern, text))
        profile_score += sum(2 for pattern in self.section_content_indicators["profile"]["patterns"] 
                            if re.search(pattern, text))
        
        # Length and content heuristics
        if len(text.split()) > 20 and not any(re.search(pattern, text) 
            for pattern in self.section_content_indicators["summary"]["negative_patterns"]):
            summary_score += 3
        
        return "summary" if summary_score > profile_score else "profile"