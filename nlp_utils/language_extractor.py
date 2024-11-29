import re
from typing import Dict, List, Optional
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

    def extract_languages(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict[str, str]]:
        """Extract languages and their proficiency levels using parsed sections."""
        languages = []
        found_languages = set()
        
        # Try to use parsed sections first if available
        if parsed_sections and parsed_sections.get('languages'):
            languages_text = ' '.join(parsed_sections['languages'])
            if languages_text.strip():
                # First try to find structured language-proficiency pairs
                matches = re.findall(r'(\b[A-Za-z]+\b)\s*[-–:]\s*(\b[A-Za-z\s]+)', languages_text)
                for match in matches:
                    language, proficiency = match
                    language = language.lower()
                    proficiency = proficiency.lower()
                    
                    # Check both English and Hungarian names
                    is_valid_language = (
                        language in self.predefined_languages or 
                        any(language == hun_name.lower() for hun_name in self.known_languages.values())
                    )
                    
                    if is_valid_language and any(level in proficiency for level in self.proficiency_levels):
                        # Convert Hungarian language name to English if needed
                        for eng_name, hun_name in self.known_languages.items():
                            if language == hun_name.lower():
                                language = eng_name
                                break
                            
                        if language not in found_languages:
                            languages.append({
                                'language': language.title(),
                                'proficiency': proficiency.lower()
                            })
                            found_languages.add(language)
                
                # Then look for language mentions with nearby proficiency levels
                for language, hungarian_name in self.known_languages.items():
                    if language not in found_languages and (
                        language in languages_text.lower() or 
                        hungarian_name.lower() in languages_text.lower()
                    ):
                        # Find the closest proficiency level
                        proficiency = self._find_closest_proficiency(languages_text, language, hungarian_name)
                        if proficiency:
                            languages.append({
                                'language': language.title(),
                                'proficiency': proficiency.lower()
                            })
                            found_languages.add(language)
                
                # If we found languages in the parsed section, return them
                if languages:
                    return languages
        
        # Only fallback to processing entire text if no languages found in parsed sections
        if not languages:
            section_lines = self.extract_section(text, self.section_headers['languages'])
            if section_lines:
                section_text = ' '.join(section_lines)
                # Reuse the same logic as above for the fallback
                matches = re.findall(r'(\b[A-Za-z]+\b)\s*[-–:]\s*(\b[A-Za-z\s]+)', section_text)
                for match in matches:
                    language, proficiency = match
                    language = language.lower()
                    if language in self.predefined_languages and language not in found_languages:
                        languages.append({
                            'language': language.title(),
                            'proficiency': proficiency.lower()
                        })
                        found_languages.add(language)
        
        return languages if languages else [{'language': '', 'proficiency': ''}]

    def _find_closest_proficiency(self, text: str, language: str, hungarian_name: str) -> str:
        """Find the closest proficiency level to a language mention."""
        # Split text into sentences
        sentences = text.split('.')
        
        # Find sentences containing the language
        for sentence in sentences:
            if language in sentence.lower() or hungarian_name.lower() in sentence.lower():
                # Look for proficiency levels in the same sentence
                for level in self.proficiency_levels:
                    if level in sentence.lower():
                        return level
        
        return ''
    
    @property
    def predefined_languages(self):
        """A predefined list of languages with their ISO codes."""
        return {
            'english': 'en',
            'hungarian': 'hu',
            'german': 'de',
            'french': 'fr',
            'spanish': 'es',
            'italian': 'it',
            'russian': 'ru',
            'chinese': 'zh',
            'japanese': 'ja',
            'korean': 'ko',
            'arabic': 'ar',
            'hindi': 'hi',
            'portuguese': 'pt',
            'dutch': 'nl',
            'polish': 'pl',
            'turkish': 'tr',
            'vietnamese': 'vi',
            'thai': 'th',
            'czech': 'cs',
            'slovak': 'sk',
            'romanian': 'ro',
            'bulgarian': 'bg',
            'croatian': 'hr',
            'serbian': 'sr',
            'ukrainian': 'uk',
            'greek': 'el',
            'swedish': 'sv',
            'norwegian': 'no',
            'danish': 'da',
            'finnish': 'fi'
        }
    
    def extract_proficiency_from_context(self, doc, language):
        """Extract proficiency level from the context of the detected language."""
        proficiency = ''
        for sent in doc.sents:
            if language in sent.text.lower():
                for level in self.proficiency_levels:
                    if level in sent.text.lower():
                        proficiency = level
                        break
        return proficiency