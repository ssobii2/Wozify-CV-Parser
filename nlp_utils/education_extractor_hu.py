import re
from typing import Optional, List, Dict
import spacy

class EducationExtractorHu:
    def __init__(self, nlp_hu):
        self.nlp_hu = nlp_hu
        self.SCHOOLS = [
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        self.DEGREES = [
            'Mérnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés', 'BSc', 'MSc'
        ]

        self.DEGREE_FIELDS = [
            'Informatika', 'Programtervező', 'Gazdasági', 'Műszaki', 'Gépész', 'Villamos',
            'Közgazdász', 'Matematika', 'Fizika', 'Kémia', 'Biológia', 'Környezetvédelem',
            'Kommunikáció', 'Marketing', 'Menedzsment', 'Logisztika', 'Turizmus'
        ]

        self.NON_EDUCATION_KEYWORDS = [
            'windows', 'ms office', 'sap', 'nyelv', 'német', 'angol', 'francia', 'orosz',
            'fejlesztő', 'programozó', 'tapasztalat', 'év'
        ]

        self.section_headers = {
            'education': ['tanulmányok', 'képzettség', 'iskolai végzettség', 'végzettség', 'végzettségem']
        }

        self.education_keywords = [
            'egyetem', 'főiskola', 'iskola', 'intézet', 'akadémia', 'diploma', 'képzés',
            'tanfolyam', 'program', 'bizonyítvány', 'szakképzés', 'továbbképzés', 'vizsga'
        ]

        self.date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',  # 2002-2007
            r'(\d{4})\s*[-–]\s*(?:jelen|folyamatban)',  # 2002-present
            r'(\d{4})\.',  # 2004.
            r'(\d{4})',  # Just year
        ]

        self.gpa_patterns = [
            r'([1-5][.,]\d{1,2})',  # 4.5, 4,5
            r'(jeles|kitűnő|kiváló|jó|közepes|elégséges)',  # Text-based grades
            r'summa cum laude|cum laude',  # Latin honors
        ]

        self.gpa_mapping = {
            'jeles': '5.0',
            'kitűnő': '5.0',
            'kiváló': '5.0',
            'jó': '4.0',
            'közepes': '3.0',
            'elégséges': '2.0',
            'summa cum laude': '5.0',
            'cum laude': '4.5'
        }

    def clean_text(self, text: str) -> str:
        """Remove unwanted Unicode artifacts and normalize text."""
        # Remove specific Unicode characters and bullet points
        text = re.sub(r'[\uf0b7\uf0d8\uf020\u2013\u2022\u2023\u25aa•▪]+', '', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove spaces before/after dashes
        text = re.sub(r'\s*[-–]\s*', ' - ', text)
        return text.strip()

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords and NLP context."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        doc = self.nlp_hu(text)

        for sent in doc.sents:
            line = sent.text.strip()
            
            if not line:
                continue
            
            is_section_header = any(keyword in line.lower() for keyword in section_keywords)
            
            is_next_different_section = False
            if sent.nbor(1) is not None:
                next_line = sent.nbor(1).text.strip()
                is_next_different_section = any(
                    keyword in next_line.lower() 
                    for keyword in ['tapasztalat', 'készségek', 'projektek', 'nyelvek', 'munka']
                )
            
            if is_section_header:
                in_section = True
                continue
            
            if in_section and is_next_different_section:
                in_section = False
            
            if in_section:
                section_lines.append(line)
        
        return section_lines

    def has_school(self, text: str) -> bool:
        doc = self.nlp_hu(text)
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'FAC', 'GPE', 'LOC'}:
                return True
        return any(school.lower() in text.lower() for school in self.SCHOOLS)
    
    def has_degree(self, text: str) -> bool:
        return any(degree.lower() in text.lower() for degree in self.DEGREES)

    def has_degree_field(self, text: str) -> bool:
        return any(field.lower() in text.lower() for field in self.DEGREE_FIELDS)

    def is_non_education(self, text: str) -> bool:
        return any(keyword in text.lower() for keyword in self.NON_EDUCATION_KEYWORDS)

    def extract_date(self, text: str) -> Optional[str]:
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def extract_gpa(self, text: str) -> Optional[str]:
        for pattern in self.gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grade = match.group(1).lower()
                return self.gpa_mapping.get(grade, grade)
        return None

    def extract_descriptions(self, text: str) -> List[str]:
        """Extract additional descriptions from education entry."""
        descriptions = []
        lines = text.split('\n')
        for line in lines:
            line = self.clean_text(line.strip())
            if line and not self.has_school(line) and not self.has_degree(line) and not self.extract_date(line):
                descriptions.append(line)
        return descriptions

    def extract_education(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract education information from text."""
        education_data = []
        current_entry = None

        # Try to use parsed sections first if available
        if parsed_sections and parsed_sections.get('education'):
            education_lines = []
            for section in parsed_sections['education']:
                education_lines.extend([self.clean_text(line.strip()) for line in section.split('\n') if line.strip()])

            if education_lines:
                for line in education_lines:
                    # Check if line contains a school name
                    if self.has_school(line):
                        if current_entry:
                            education_data.append(current_entry)
                        current_entry = {
                            'school': line,
                            'degree': '',
                            'gpa': '',
                            'date': '',
                            'descriptions': []
                        }
                        continue

                    if current_entry:
                        # Extract date if present
                        date = self.extract_date(line)
                        if date and not current_entry['date']:
                            current_entry['date'] = date
                            continue

                        # Extract degree if present
                        if self.has_degree(line) and not current_entry['degree']:
                            current_entry['degree'] = line
                            continue

                        # Extract GPA if present
                        gpa = self.extract_gpa(line)
                        if gpa and not current_entry['gpa']:
                            current_entry['gpa'] = gpa
                            continue

                        # If none of the above, add as description
                        if not self.is_non_education(line):
                            current_entry['descriptions'].append(line)

                if current_entry:
                    education_data.append(current_entry)

                return education_data

        # Fallback to direct extraction if no parsed sections or if parsing failed
        return self._extract_education_fallback(text)

    def _parse_education_entry(self, text: str) -> Dict:
        """Parse a single education entry to extract school, degree, and date."""
        entry = {
            'school': '',
            'degree': '',
            'gpa': '',
            'date': '',
            'descriptions': []
        }

        # Clean the text
        text = self.clean_text(text)

        # Extract date first (it's usually at the end in parentheses)
        date_match = re.search(r'\((\d{4}(?:\s*[-–]\s*(?:\d{4}|jelen|folyamatban))?)\)', text)
        if date_match:
            entry['date'] = date_match.group(1)
            # Remove the date from text to simplify further processing
            text = text.replace(date_match.group(0), '').strip()
        else:
            # Try finding date without parentheses
            date_match = re.search(r'\b(\d{4}\s*[-–]\s*(?:\d{4}|jelen|folyamatban)|\d{4})\b', text)
            if date_match:
                entry['date'] = date_match.group(1)
                text = text.replace(date_match.group(1), '').strip()

        # Split by dash if present
        parts = [p.strip() for p in re.split(r'\s*-\s*', text) if p.strip()]
        
        if len(parts) >= 2:
            # If we have multiple parts, assume degree - school format
            entry['degree'] = parts[0]
            entry['school'] = parts[1]
        else:
            # If no clear separation, try to identify if it's a school or degree
            text = parts[0] if parts else text
            if any(keyword.lower() in text.lower() for keyword in self.SCHOOLS):
                entry['school'] = text
            elif any(keyword.lower() in text.lower() for keyword in self.DEGREES):
                entry['degree'] = text
            else:
                entry['school'] = text

        return entry

    def _extract_education_fallback(self, text: str) -> List[Dict]:
        """Fallback method to extract education information."""
        if not text:
            return []

        education_data = []
        
        try:
            # Split text into lines and clean them
            lines = [self.clean_text(line) for line in text.split('\n') if line.strip()]
            education_entries = []
            current_entry = []

            for line in lines:
                # Skip non-education related lines
                if any(keyword.lower() in line.lower() for keyword in 
                    ['nyelvtudás', 'számítógépes', 'windows', 'ms office', 'készségek', 
                     'érdeklődési', 'erősségek', 'egyéb ismeretek']):
                    continue

                # Check if it's a new entry
                if (any(keyword.lower() in line.lower() for keyword in self.SCHOOLS + self.DEGREES) or
                    re.search(r'\b\d{4}\b', line)):
                    if current_entry:
                        education_entries.append(' '.join(current_entry))
                        current_entry = []
                    current_entry.append(line)
                elif current_entry:
                    current_entry.append(line)

            # Add the last entry
            if current_entry:
                education_entries.append(' '.join(current_entry))

            # Process each education entry
            for entry_text in education_entries:
                entry = self._parse_education_entry(entry_text)
                if entry['school'] or entry['degree']:
                    # Skip entries that are clearly not education-related
                    if not any(keyword.lower() in entry['school'].lower() for keyword in 
                             ['backend', 'frontend', 'sql', 'docker', 'git', 'office']):
                        education_data.append(entry)

        except Exception as e:
            print(f"Warning: Education extraction failed: {str(e)}")
            return []

        return education_data