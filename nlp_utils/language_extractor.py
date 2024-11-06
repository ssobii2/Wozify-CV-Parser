import re
from typing import Dict, List
import spacy
from langdetect import detect, LangDetectException

class LanguageExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'languages': ['language', 'languages', 'language skills', 'nyelv', 'nyelvek', 'nyelvtudás']
        }
        
        # Add a list of known languages to filter results, including Hungarian translations
        self.known_languages = {
            'english': 'angol',
            'hungarian': 'magyar',
            'german': 'német',
            'french': 'francia',
            'spanish': 'spanyol',
            'italian': 'olasz',
            'russian': 'orosz',
            'chinese': 'kínai',
            'japanese': 'japán',
            'korean': 'koreai',
            'arabic': 'arab',
            'hindi': 'hindi',
            'portuguese': 'portugál',
            'dutch': 'holland',
            'polish': 'lengyel',
            'turkish': 'török',
            'vietnamese': 'vietnámi',
            'thai': 'thai',
            'czech': 'cseh',
            'slovak': 'szlovák',
            'romanian': 'román',
            'bulgarian': 'bolgár',
            'croatian': 'horvát',
            'serbian': 'szerb',
            'ukrainian': 'ukrán',
            'greek': 'görög',
            'swedish': 'svéd',
            'norwegian': 'norvég',
            'danish': 'dán',
            'finnish': 'finn'
        }
        
        # Add common proficiency levels
        self.proficiency_levels = [
            'native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner',
            'professional', 'business', 'conversational', 'elementary',
            'mother tongue', 'proficient', 'excellent', 'good', 'fair', 'poor',
            'c1', 'c2', 'b1', 'b2', 'a1', 'a2',
            # Hungarian proficiency levels
            'anyanyelvi', 'folyékony', 'haladó', 'középhaladó', 'alapfokú', 'kezdő',
            'szakmai', 'üzleti', 'társalgási', 'alapfok', 'anyanyelv', 'kiváló', 'jó', 'közepes', 'gyenge'
        ]

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

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

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages and their proficiency levels using NLP and fallback logic."""
        languages = []
        found_languages = set()
        
        # Use NLP to extract languages
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        
        # Use spaCy's NER to find language entities
        for ent in doc.ents:
            if ent.label_ == 'LANGUAGE':
                language = ent.text.lower()
                # Check for proficiency in the same sentence
                proficiency = ''
                for sent in doc.sents:
                    if language in sent.text.lower():
                        for level in self.proficiency_levels:
                            if level in sent.text.lower():
                                proficiency = level
                                break
                if language not in found_languages:
                    languages.append({
                        'language': language.title(),
                        'proficiency': proficiency
                    })
                    found_languages.add(language)

        # Always run the fallback logic to catch any missed languages
        languages_section = self.extract_section(text, self.section_headers['languages'])
        for line in languages_section:
            matches = re.findall(r'(\b[A-Za-z]+\b)\s*[-–:]\s*(\b[A-Za-z\s]+)', line)
            for match in matches:
                language, proficiency = match
                language = language.lower()
                proficiency = proficiency.lower()
                
                # Check both English and Hungarian language names
                if (language in self.known_languages or language in self.known_languages.values()) and \
                   any(level in proficiency for level in self.proficiency_levels) and \
                   language not in found_languages:
                    languages.append({
                        'language': language.title(),
                        'proficiency': proficiency.lower()
                    })
                    found_languages.add(language)
            
            for language, hungarian_name in self.known_languages.items():
                if (language in line.lower() or hungarian_name in line.lower()) and language not in found_languages:
                    for level in self.proficiency_levels:
                        if level in line.lower():
                            lang_dict = {
                                'language': language.title(),
                                'proficiency': level.lower()
                            }
                            if lang_dict not in languages:
                                languages.append(lang_dict)
                                found_languages.add(language)

        return languages if languages else [{
            'language': '',
            'proficiency': ''
        }]