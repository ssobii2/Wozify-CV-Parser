import re
from typing import Dict, Optional, List
from langdetect import detect, LangDetectException
from spacy.matcher import Matcher

class ProfileExtractor:
    def __init__(self, nlp_en, nlp_hu):
        """Initialize ProfileExtractor with spaCy models and matchers."""
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.matcher_en = Matcher(nlp_en.vocab)
        self.matcher_hu = Matcher(nlp_hu.vocab)
        self.add_email_patterns()

    def add_email_patterns(self):
        """Add patterns to matcher for emails."""
        email_pattern = [{"LIKE_EMAIL": True}]
        self.matcher_en.add("EMAIL", [email_pattern])
        self.matcher_hu.add("EMAIL", [email_pattern])

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

    # MAIN EXTRACTION METHOD
    def extract_profile(self, text: str, parsed_sections: Optional[Dict] = None) -> Dict[str, str]:
        """Extract profile information using pattern matching and NLP."""
        profile_data = {
            'name': "",
            'email': "",
            'phone': "",
            'location': "",
            'url': "",
            'summary': ""
        }

        try:
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)

            profile_data['name'] = self.extract_name(text)
            profile_data['location'] = self.extract_location(text)
            profile_data['email'] = self.extract_email(doc)
            profile_data['phone'] = self.extract_phone(text)
            profile_data['url'] = self.extract_url(text)
            profile_data['summary'] = self.extract_summary(text, parsed_sections)

        except Exception as e:
            print(f"Warning: Error in profile extraction: {str(e)}")

        return profile_data

    # ENTITY EXTRACTION METHODS
    def extract_name(self, text: str) -> str:
        """Extract name using NER and additional validation."""
        try:
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)
            
            for ent in doc.ents:
                if ent.label_ == 'PER':
                    name = ent.text.strip()
                    if self._is_valid_name(name):
                        return name
            
            lines = text.strip().split('\n')
            for line in lines[:3]:
                line = line.strip()
                if line and len(line.split()) <= 4:
                    words = line.split()
                    if all(word[0].isupper() for word in words if word):
                        if self._is_valid_name(line):
                            return line
            
            return ""
        except Exception as e:
            print(f"Warning: Error extracting name: {str(e)}")
            return ""

    def extract_location(self, text: str) -> str:
        """Extract location using NER."""
        try:
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)
            
            for ent in doc.ents:
                if ent.label_ in {'LOC', 'GPE', 'FAC'}:
                    return ent.text.strip()
            
            lines = text.strip().split('\n')
            for line in lines[:5]:
                line = line.strip()
                if line and any(loc in line.lower() for loc in ['budapest', 'debrecen', 'szeged', 'hungary', 'magyarország']):
                    return line
            
            return ""
        except Exception as e:
            print(f"Warning: Error extracting location: {str(e)}")
            return ""

    # CONTACT INFORMATION EXTRACTION METHODS
    def extract_email(self, doc) -> str:
        """Extract email using spaCy token attributes and regex fallback."""
        try:
            # First try using spaCy's built-in email detection
            for token in doc:
                if token.like_email:
                    return token.text
            
            # Fallback to regex pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_match = re.search(email_pattern, doc.text)
            if email_match:
                return email_match.group(0)
            
            return ""
        except Exception as e:
            print(f"Warning: Error extracting email: {str(e)}")
            return ""

    def extract_phone(self, text: str) -> str:
        """Extract phone number using regex."""
        try:
            phone_patterns = [
                r'(?:\+36|06)[-\s]?(?:20|30|70|1)[-\s]?\d{3}[-\s]?\d{4}',
                r'(?:\+36|06)[-\s]?\d{1}[-\s]?\d{3}[-\s]?\d{4}',
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text)
                if phone_match:
                    return phone_match.group(0)
            return ""
        except Exception as e:
            print(f"Warning: Error extracting phone: {str(e)}")
            return ""

    def extract_url(self, text: str) -> str:
        """Extract URL using regex."""
        try:
            url_pattern = r'(https?://[^\s]+)|(www\.[^\s]+)|(linkedin\.com/in/[^\s]+)|(github\.com/[^\s]+)'
            url_match = re.search(url_pattern, text, re.IGNORECASE)
            if url_match:
                return url_match.group(0)
            return ""
        except Exception as e:
            print(f"Warning: Error extracting URL: {str(e)}")
            return ""

    # VALIDATION METHODS
    def _is_valid_name(self, name: str) -> bool:
        """Validate if the extracted text is likely a real name."""
        if not name or len(name) < 2:
            return False
        
        invalid_patterns = [
            r'^cid:',
            r'^\d+$',
            r'^[a-f0-9]+$',
            r'^#',
            r'^id:',
            r'^\[.*\]$',
            r'^<.*>$',
            r'^\{.*\}$',
            r'^\d+[A-Za-z]+$'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False
        
        valid_name_pattern = r'^[A-Za-z\u00C0-\u017F\s\'-]+$'
        if not re.match(valid_name_pattern, name):
            return False
        
        words = name.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        for word in words:
            if len(word) < 2 or not word[0].isupper():
                return False
        
        return True

    # SUMMARY EXTRACTION METHOD
    def extract_summary(self, text: str, parsed_sections: Optional[Dict] = None) -> str:
        """Extract summary with priority: dedicated summary section > profile section > fallback."""
        try:
            def clean_and_join(lines: List[str]) -> str:
                filtered_lines = []
                for line in lines:
                    line = line.strip()
                    if (re.search(r'[\w\.-]+@[\w\.-]+', line) or
                        re.search(r'[\+\d\s\(\)-]{10,}', line) or
                        re.search(r'https?://', line) or
                        len(line.split()) < 3):
                        continue
                    filtered_lines.append(line)
                return ' '.join(filtered_lines).strip()

            if parsed_sections and parsed_sections.get('summary'):
                summary_text = clean_and_join(parsed_sections['summary'])
                if summary_text:
                    lines = summary_text.split()
                    summary_end_idx = len(lines)
                    
                    for i, word in enumerate(lines):
                        if any(marker in word.lower() for marker in ['tapasztalat', 'munkahely', 'munka:']):
                            next_words = ' '.join(lines[i:i+3])
                            if (re.search(r'\b(20\d{2}|19\d{2})\b', next_words) or
                                re.search(r'\b(kft|zrt|bt|nyrt)\b', next_words.lower()) or
                                'munkahely' in next_words.lower()):
                                summary_end_idx = i
                                break
                    
                    return ' '.join(lines[:summary_end_idx])

                return summary_text

            if parsed_sections and parsed_sections.get('profile'):
                profile_text = clean_and_join(parsed_sections['profile'])
                if profile_text:
                    return profile_text

            summary_headers = [
                "summary", "profile", "about me", "introduction", "objective", "overview",
                "összefoglaló", "bemutatkozás", "profil", "rólam", "szakmai célok", "áttekintés",
                "szakmai profil", "szakmai bemutatkozás", "career summary", "professional summary", 
                "personal statement", "executive summary", "key qualifications", "highlights", 
                "skills summary", "career objective", "mission statement", "self-introduction", 
                "biography", "background", "experience summary", "value proposition"
            ]
            
            section_headers = [
                'experience', 'education', 'skills', 'projects', 'work', 'employment', 'qualifications',
                'tapasztalat', 'tanulmányok', 'képzettség', 'készségek', 'projektek', 'munka', 'végzettség',
                'summary', 'certifications', 'awards', 'publications', 'interests', 'references', 'professional experience',
                'job history', 'career', 'training', 'internships', 'volunteer experience', 'achievements', 'competencies'
            ]
            
            header_pattern = "|".join([fr"\b{header}\b" for header in summary_headers])
            section_pattern = re.compile(f'^({"|".join(section_headers)})', re.IGNORECASE)
            
            summary_text = []
            capturing = False

            for line in text.splitlines():
                line = line.strip()
                if re.search(header_pattern, line, re.IGNORECASE):
                    capturing = True
                    continue

                if capturing:
                    if section_pattern.match(line):
                        break
                    if line:
                        summary_text.append(line)

            fallback_text = clean_and_join(summary_text)
            if fallback_text:
                return fallback_text

            return ""
            
        except Exception as e:
            print(f"Warning: Error extracting summary: {str(e)}")
            return ""
