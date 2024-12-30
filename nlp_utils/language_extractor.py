import re
from typing import Dict, List, Optional
import spacy
from langdetect import detect, LangDetectException

class LanguageExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'languages': [
                'language', 'languages', 'language skills', 'nyelv', 'nyelvek', 'nyelvtudás',
                'linguistic skills', 'linguistics', 'foreign languages', 'nyelvi készségek', 
                'idegen nyelvek', 'nyelvtudás szintje', 'nyelvi ismeretek', 'nyelvi kompetenciák'
            ]
        }
        
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
            'urdu': 'urdu',
            'punjabi': 'pandzsábi',
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
            'finnish': 'finn',
            'slovenian': 'szlovén',
            'estonian': 'észt',
            'latvian': 'lett',
            'lithuanian': 'litván',
            'icelandic': 'izlandi',
            'maltese': 'máltai',
            'basque': 'baszk',
            'galician': 'galíciai',
            'welsh': 'walesi',
            'irish': 'ír',
            'scottish': 'skót'
        }
        
        # Add common proficiency levels
        self.proficiency_levels = [
            'native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner',
            'professional', 'business', 'conversational', 'elementary',
            'mother tongue', 'proficient', 'excellent', 'good', 'fair', 'poor',
            'c1', 'c2', 'b1', 'b2', 'a1', 'a2',
            # Additional common proficiency levels
            'competent', 'capable', 'skilled', 'trained', 'qualified', 'experienced',
            'satisfactory', 'sufficient', 'limited', 'functional', 'basic communication',
            # Hungarian proficiency levels
            'anyanyelvi', 'folyékony', 'haladó', 'középhaladó', 'alapfokú', 'kezdő',
            'szakmai', 'üzleti', 'társalgási', 'alapfok', 'anyanyelv', 'kiváló', 'jó', 'közepes', 'gyenge',
            # Additional Hungarian proficiency levels
            'kompetens', 'képzett', 'szakképzett', 'tapasztalt', 'megfelelő', 'elégséges', 'korlátozott', 'funkcionális'
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
        
        try:
            # Try to use parsed sections first if available
            if parsed_sections and parsed_sections.get('languages'):
                languages_text = ' '.join(parsed_sections['languages'])
                if languages_text.strip():
                    # Split into individual language entries
                    entries = re.split(r'[,;]\s*|(?<=\w)\s*[-–]\s*(?=[A-ZÁÉÍÓÖŐÚÜŰ])', languages_text)
                    
                    for entry in entries:
                        entry = entry.strip()
                        if not entry:
                            continue
                            
                        # Look for language name
                        found_lang = None
                        found_prof = None
                        
                        for eng_name, hun_name in self.known_languages.items():
                            if eng_name in entry.lower() or hun_name.lower() in entry.lower():
                                found_lang = eng_name
                                # Get text after the language name
                                prof_text = entry[entry.lower().find(hun_name.lower()) + len(hun_name):] if hun_name.lower() in entry.lower() \
                                    else entry[entry.lower().find(eng_name.lower()) + len(eng_name):]
                                
                                # Clean up proficiency text
                                prof_text = prof_text.strip(' -–:,.')
                                
                                # Extract proficiency level
                                for level in self.proficiency_levels:
                                    if level.lower() in prof_text.lower():
                                        found_prof = level
                                        break
                                        
                                # Look for CEFR levels
                                cefr_match = re.search(r'\b(A1|A2|B1|B2|C1|C2)\b', prof_text, re.IGNORECASE)
                                if cefr_match:
                                    found_prof = cefr_match.group(1).upper()
                                
                                break
                        
                        if found_lang and found_lang not in found_languages:
                            languages.append({
                                'language': found_lang.title(),
                                'proficiency': found_prof.lower() if found_prof else ''
                            })
                            found_languages.add(found_lang)

            # Fallback to processing entire text if no languages found
            if not languages:
                section_lines = self.extract_section(text, self.section_headers['languages'])
                if section_lines:
                    section_text = ' '.join(section_lines)
                    # Use the same flexible matching logic for the fallback
                    for eng_name, hun_name in self.known_languages.items():
                        if eng_name not in found_languages and (
                            eng_name in section_text.lower() or 
                            hun_name.lower() in section_text.lower()
                        ):
                            proficiency = self._find_closest_proficiency(section_text, eng_name, hun_name)
                            languages.append({
                                'language': eng_name.title(),
                                'proficiency': proficiency.lower() if proficiency else ''
                            })
                            found_languages.add(eng_name)

        except Exception as e:
            print(f"Error extracting languages: {str(e)}")
            return [{'language': '', 'proficiency': ''}]
        
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
            'urdu': 'ur',
            'punjabi': 'pa',
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
            'finnish': 'fi',
            'maltese': 'mt',
            'basque': 'eu',
            'galician': 'gl',
            'welsh': 'cy',
            'irish': 'ga',
            'scottish': 'gd'
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

    def _clean_proficiency(self, text: str) -> str:
        """Clean up proficiency text and extract standardized level."""
        # Remove common noise words and phrases
        noise_words = [
            'szint', 'szinten', 'szintű', 'nyelvtudás', 'nyelv', 'beszéd', 'írás', 'olvasás',
            'kommunikáció', 'level', 'fokú', 'fok', 'vizsga', 'nyelvvizsga', 'komplex',
            'alapfokú', 'középfokú', 'felsőfokú', 'társalgási', 'tárgyalási'
        ]
        
        cleaned = text.lower()
        for word in noise_words:
            cleaned = re.sub(r'\b' + word + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace and punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(' ,-–:;.')
        
        return cleaned