import re
from typing import Dict
from langdetect import detect, LangDetectException
import spacy
from spacy.matcher import Matcher

class ProfileExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.matcher = Matcher(nlp_en.vocab)  # Initialize matcher for patterns
        self.add_email_patterns()

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

    def add_email_patterns(self):
        """Add patterns to matcher for emails."""
        email_pattern = [{"LIKE_EMAIL": True}]
        self.matcher.add("EMAIL", [email_pattern])

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

        # Extract name and location using NER
        profile_data['name'] = self.extract_name(text)
        profile_data['location'] = self.extract_location(text)

        # Process text with NLP model and Matcher
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)

        # Extract email using the matcher
        profile_data['email'] = self.extract_email(doc)

        # Extract phone and URL using regex
        profile_data['phone'] = self.extract_phone(text)
        profile_data['url'] = self.extract_url(text)

        # Extract summary
        profile_data['summary'] = self.extract_summary(text)

        return profile_data

    def extract_name(self, text: str) -> str:
        """Extract name using NER."""
        doc = self.get_nlp_model_for_text(text)(text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text
        return ""

    def extract_location(self, text: str) -> str:
        """Extract location using NER."""
        doc = self.get_nlp_model_for_text(text)(text)
        for ent in doc.ents:
            if ent.label_ == 'GPE':
                return ent.text
        return ""

    def extract_email(self, doc) -> str:
        """Extract email using spaCy matcher."""
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            if doc.vocab.strings[match_id] == "EMAIL":
                return doc[start:end].text
        return ""

    def extract_phone(self, text: str) -> str:
        """Extract phone number using regex."""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            return phone_match.group(0)
        return ""

    def extract_url(self, text: str) -> str:
        """Extract URL using regex."""
        url_pattern = r'(https?://[^\s]+)|(www\.[^\s]+)|(linkedin\.com/in/[^\s]+)|(github\.com/[^\s]+)'
        url_match = re.search(url_pattern, text, re.IGNORECASE)
        if url_match:
            return url_match.group(0)
        return ""

    def extract_summary(self, text: str) -> str:
        """Extract summary by detecting headers and capturing text until next section."""
        summary_headers = [
            "summary", "profile", "about me", "introduction", "objective", "overview"
        ]
        header_pattern = "|".join([fr"\b{header}\b" for header in summary_headers])
        section_pattern = re.compile(r'^(experience|education|skills|projects|work|employment|qualifications)', re.IGNORECASE)
        
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
                summary_text.append(line)

        return " ".join(summary_text).strip()
