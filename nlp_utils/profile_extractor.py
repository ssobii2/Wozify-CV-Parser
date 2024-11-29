import re
from typing import Dict
from langdetect import detect, LangDetectException
import spacy
from spacy.matcher import Matcher

class ProfileExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        # Initialize matchers for both languages
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

    def extract_profile(self, text: str) -> Dict[str, str]:
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
            # Extract name and location using NER
            profile_data['name'] = self.extract_name(text)
            profile_data['location'] = self.extract_location(text)

            # Process text with appropriate NLP model and Matcher
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)

            # Extract email using the matcher
            profile_data['email'] = self.extract_email(doc)

            # Extract phone and URL using regex
            profile_data['phone'] = self.extract_phone(text)
            profile_data['url'] = self.extract_url(text)

            # Extract summary
            profile_data['summary'] = self.extract_summary(text)

        except Exception as e:
            print(f"Warning: Error in profile extraction: {str(e)}")

        return profile_data

    def extract_name(self, text: str) -> str:
        """Extract name using NER and additional validation."""
        try:
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)
            
            # First try NER
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    # Validate the name - check it's not a metadata artifact
                    name = ent.text.strip()
                    if self._is_valid_name(name):
                        return name
            
            # Fallback: Try to find name at the start of the document
            lines = text.strip().split('\n')
            for line in lines[:3]:  # Check first 3 lines
                line = line.strip()
                if line and len(line.split()) <= 4:  # Names are usually 1-4 words
                    # Check if it looks like a name (capitalized words)
                    words = line.split()
                    if all(word[0].isupper() for word in words if word):
                        if self._is_valid_name(line):
                            return line
            
            return ""
        except Exception as e:
            print(f"Warning: Error extracting name: {str(e)}")
            return ""

    def _is_valid_name(self, name: str) -> bool:
        """Validate if the extracted text is likely a real name."""
        # Skip if empty or too short
        if not name or len(name) < 2:
            return False
        
        # Skip common metadata patterns
        invalid_patterns = [
            r'^cid:',           # Common metadata prefix
            r'^\d+$',          # Just numbers
            r'^[a-f0-9]+$',    # Hexadecimal
            r'^#',             # Starts with hash
            r'^id:',           # ID prefix
            r'^\[.*\]$',       # Square brackets
            r'^<.*>$',         # Angle brackets
            r'^\{.*\}$',       # Curly braces
            r'^\d+[A-Za-z]+$'  # Number followed by letters
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False
        
        # Check for valid name characters
        valid_name_pattern = r'^[A-Za-z\u00C0-\u017F\s\'-]+$'  # Letters, spaces, hyphens, apostrophes, and accented characters
        if not re.match(valid_name_pattern, name):
            return False
        
        # Additional validation for minimum word structure
        words = name.split()
        if len(words) < 1 or len(words) > 4:  # Names typically have 1-4 words
            return False
        
        # Check each word is properly capitalized and long enough
        for word in words:
            if len(word) < 2 or not word[0].isupper():
                return False
        
        return True

    def extract_location(self, text: str) -> str:
        """Extract location using NER."""
        try:
            nlp = self.get_nlp_model_for_text(text)
            doc = nlp(text)
            
            # Common Hungarian cities and location indicators
            hu_cities = {'budapest', 'debrecen', 'szeged', 'pécs', 'győr', 'nyíregyháza', 'miskolc'}
            location_indicators = {'cím:', 'lakhely:', 'város:', 'address:', 'location:', 'city:'}
            
            # First try NER
            for ent in doc.ents:
                if ent.label_ in {'GPE', 'LOC'}:
                    return ent.text
            
            # Fallback: Look for location indicators
            lines = text.lower().split('\n')
            for line in lines:
                line = line.strip()
                # Check for location indicators
                if any(indicator in line for indicator in location_indicators):
                    # Return everything after the indicator
                    for indicator in location_indicators:
                        if indicator in line:
                            return line.split(indicator)[1].strip().title()
                
                # Check for known cities
                words = set(re.findall(r'\w+', line.lower()))
                for city in hu_cities:
                    if city in words:
                        return city.title()
            
            return ""
        except Exception as e:
            print(f"Warning: Error extracting location: {str(e)}")
            return ""

    def extract_email(self, doc) -> str:
        """Extract email using spaCy matcher."""
        try:
            # Try both matchers
            matcher = self.matcher_hu if doc.vocab == self.nlp_hu.vocab else self.matcher_en
            matches = matcher(doc)
            
            for match_id, start, end in matches:
                if doc.vocab.strings[match_id] == "EMAIL":
                    return doc[start:end].text
            
            # Fallback: Use regex
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
            # Hungarian and international phone patterns
            phone_patterns = [
                r'(?:\+36|06)[-\s]?(?:20|30|70|1)[-\s]?\d{3}[-\s]?\d{4}',  # Hungarian mobile
                r'(?:\+36|06)[-\s]?\d{1}[-\s]?\d{3}[-\s]?\d{4}',  # Hungarian landline
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # International
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

    def extract_summary(self, text: str) -> str:
        """Extract summary by detecting headers and capturing text until next section."""
        try:
            # English and Hungarian summary headers
            summary_headers = [
                "summary", "profile", "about me", "introduction", "objective", "overview",
                "összefoglaló", "bemutatkozás", "profil", "rólam", "szakmai célok", "áttekintés",
                "szakmai profil", "szakmai bemutatkozás"
            ]
            
            # Section headers in both languages
            section_headers = [
                'experience', 'education', 'skills', 'projects', 'work', 'employment', 'qualifications',
                'tapasztalat', 'tanulmányok', 'képzettség', 'készségek', 'projektek', 'munka', 'végzettség'
            ]
            
            header_pattern = "|".join([fr"\b{header}\b" for header in summary_headers])
            section_pattern = re.compile(f'^({"|".join(section_headers)})', re.IGNORECASE)
            
            summary_text = []
            capturing = False

            for line in text.splitlines():
                line = line.strip()
                # Detect the summary header
                if re.search(header_pattern, line, re.IGNORECASE):
                    capturing = True
                    continue

                # If capturing summary, add lines until reaching a new section
                if capturing:
                    if section_pattern.match(line):
                        break  # Stop capturing at a new section
                    if line:  # Only add non-empty lines
                        summary_text.append(line)

            return " ".join(summary_text).strip()
        except Exception as e:
            print(f"Warning: Error extracting summary: {str(e)}")
            return ""
