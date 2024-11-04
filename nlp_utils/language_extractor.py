import re
from typing import Dict, List

class LanguageExtractor:
    def __init__(self):
        self.section_headers = {
            'languages': ['language', 'languages', 'language skills']
        }
        
        # Add a list of known languages to filter results
        self.known_languages = [
            'english', 'hungarian', 'german', 'french', 'spanish', 'italian', 
            'russian', 'chinese', 'japanese', 'korean', 'arabic', 'hindi',
            'portuguese', 'dutch', 'polish', 'turkish', 'vietnamese', 'thai',
            'czech', 'slovak', 'romanian', 'bulgarian', 'croatian', 'serbian',
            'ukrainian', 'greek', 'swedish', 'norwegian', 'danish', 'finnish'
        ]
        
        # Add common proficiency levels
        self.proficiency_levels = [
            'native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner',
            'professional', 'business', 'conversational', 'elementary',
            'mother tongue', 'proficient', 'excellent', 'good', 'fair', 'poor',
            'c1', 'c2', 'b1', 'b2', 'a1', 'a2'
        ]

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
        """Extract languages and their proficiency levels."""
        languages_section = self.extract_section(text, self.section_headers['languages'])
        languages = []

        for line in languages_section:
            # Use regex to find language-proficiency pairs
            matches = re.findall(r'(\b[A-Za-z]+\b)\s*[-–:]\s*(\b[A-Za-z\s]+)', line)
            for match in matches:
                language, proficiency = match
                language = language.lower()
                proficiency = proficiency.lower()
                
                # Only add if it's a known language and has a valid proficiency level
                if (language in self.known_languages and 
                    any(level in proficiency for level in self.proficiency_levels)):
                    languages.append({
                        'language': language.title(),  # Capitalize first letter
                        'proficiency': proficiency.lower()
                    })
            
            # Also check for standalone language mentions with common proficiency indicators
            for language in self.known_languages:
                if language in line.lower():
                    for level in self.proficiency_levels:
                        if level in line.lower():
                            lang_dict = {
                                'language': language.title(),
                                'proficiency': level.lower()
                            }
                            if lang_dict not in languages:
                                languages.append(lang_dict)

        return languages if languages else [{
            'language': '',
            'proficiency': ''
        }]