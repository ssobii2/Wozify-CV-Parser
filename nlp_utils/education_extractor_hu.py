import re
from typing import Optional, List, Dict, Tuple

class EducationExtractorHu:
    def __init__(self, nlp_hu):
        """Initialize EducationExtractorHu with spaCy model and define constants."""
        self.nlp_hu = nlp_hu
        
        # Educational institution types
        self.SCHOOLS = [
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        # Academic degrees and qualifications
        self.DEGREES = [
            'Mérnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés', 
            'BSc', 'MSc', 'PhD', 'BA', 'MA', 'Dr.', 'Doktor',
            'Szakmérnök', 'Üzemmérnök', 'Okleveles', 'Felsőfokú', 'Középfokú',
            'Bizonyítvány', 'Tanúsítvány', 'Képesítés'
        ]

        # Fields of study
        self.DEGREE_FIELDS = [
            'Informatika', 'Programtervező', 'Gazdasági', 'Műszaki', 'Gépész', 'Villamos',
            'Közgazdász', 'Matematika', 'Fizika', 'Kémia', 'Biológia', 'Környezetvédelem',
            'Kommunikáció', 'Marketing', 'Menedzsment', 'Logisztika', 'Turizmus',
            'Jog', 'Jogász', 'Mérnök informatikus', 'Programozó', 'Rendszergazda',
            'Szoftverfejlesztő', 'Frontend fejlesztő', 'Backend fejlesztő', 'Full stack'
        ]

        # Non-education related keywords
        self.NON_EDUCATION_KEYWORDS = [
            'windows', 'ms office', 'sap', 'nyelv', 'német', 'angol', 'francia', 'orosz',
            'fejlesztő', 'programozó', 'tapasztalat', 'év'
        ]

        # Section headers for identifying education sections
        self.section_headers = {
            'education': ['tanulmányok', 'képzettség', 'iskolai végzettség', 'végzettség', 'végzettségem']
        }

        # Keywords related to education
        self.education_keywords = [
            'egyetem', 'főiskola', 'iskola', 'intézet', 'akadémia', 'diploma', 'képzés',
            'tanfolyam', 'program', 'bizonyítvány', 'szakképzés', 'továbbképzés', 'vizsga'
        ]

        # Date patterns for extracting education dates
        self.date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',
            r'(\d{4})\s*[-–]\s*(?:jelen|folyamatban)',
            r'(\d{4})\.',
            r'(\d{4})'
        ]

        # GPA patterns for extracting grades
        self.gpa_patterns = [
            r'([1-5][.,]\d{1,2})',
            r'(jeles|kitűnő|kiváló|jó|közepes|elégséges)',
            r'summa cum laude|cum laude'
        ]

        # Mapping of text-based grades to numeric values
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

    # Main extraction methods
    def extract_education(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract education information from text."""
        try:
            if parsed_sections and 'education' in parsed_sections and parsed_sections['education']:
                education_data = []
                
                for section in parsed_sections['education']:
                    cleaned_section = self.clean_text(section)
                    entries = self._split_into_entries(cleaned_section)
                    
                    if not entries:
                        entries = [cleaned_section]
                    
                    for entry in entries:
                        if entry.strip():
                            school, degree, descriptions = self._parse_entry_parts(entry)
                            date = self._extract_date(entry)
                            
                            edu_entry = {
                                'school': school.strip(),
                                'degree': degree.strip(),
                                'gpa': self.extract_gpa(entry) or '',
                                'date': date.strip(),
                                'descriptions': descriptions
                            }
                            education_data.append(edu_entry)
                
                return education_data

            return self._extract_education_fallback(text)

        except Exception as e:
            print(f"Education extraction failed: {str(e)}")
            return []

    def _extract_education_fallback(self, text: str) -> List[Dict]:
        """Fallback method to extract education information."""
        if not text:
            return []

        education_data = []
        
        try:
            edu_pattern = r'(?:TANULMÁNYOK|VÉGZETTSÉG|KÉPZETTSÉG|ISKOLAI\s*VÉGZETTSÉG|KÉPESÍTÉS|OKTATÁS|TANULMÁNYI\s*ADATOK|ISKOLÁK)[\s:]*.*?(?=\n\s*(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT|KÉSZSÉGEK|NYELVTUDÁS|EGYÉB|MUNKAHELYEK|$))'
            edu_match = re.search(edu_pattern, text, re.DOTALL | re.IGNORECASE)
            
            text_to_process = edu_match.group(0) if edu_match else text

            lines = [self.clean_text(line) for line in text_to_process.split('\n') if line.strip()]
            education_entries = []
            current_entry = []

            for line in lines:
                if self.is_non_education(line) or len(line.split()) < 2:
                    continue

                doc = self.nlp_hu(line)
                
                is_new_entry = (
                    self.has_school(line) or
                    self.has_degree(line) or
                    self.has_degree_field(line) or
                    bool(re.search(r'\b(?:19|20)\d{2}\b', line)) or
                    any(ent.label_ == 'ORG' for ent in doc.ents)
                )

                if is_new_entry and len(line.split()) > 2:
                    if current_entry:
                        education_entries.append(' '.join(current_entry))
                        current_entry = []
                    current_entry.append(line)
                elif current_entry:
                    current_entry.append(line)

            if current_entry:
                education_entries.append(' '.join(current_entry))

            for entry_text in education_entries:
                school, degree, descriptions = self._parse_entry_parts(entry_text)
                date = self._extract_date(entry_text)
                
                if not school and not degree and descriptions:
                    for desc in descriptions:
                        if self.has_school(desc):
                            school = desc
                            descriptions.remove(desc)
                            break
                        elif self.has_degree(desc):
                            degree = desc
                            descriptions.remove(desc)
                            break

                if any([school, degree, descriptions]):
                    edu_entry = {
                        'school': school.strip(),
                        'degree': degree.strip(),
                        'gpa': self.extract_gpa(entry_text) or '',
                        'date': date.strip(),
                        'descriptions': descriptions
                    }
                    education_data.append(edu_entry)

        except Exception as e:
            print(f"Education extraction failed: {str(e)}")
            return []

        return education_data

    # Entity detection methods
    def has_school(self, text: str) -> bool:
        """Check if text contains a school or educational institution."""
        doc = self.nlp_hu(text)
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'FAC', 'GPE', 'LOC'}:
                return True
        return any(school.lower() in text.lower() for school in self.SCHOOLS)
    
    def has_degree(self, text: str) -> bool:
        """Check if text contains a degree."""
        return any(degree.lower() in text.lower() for degree in self.DEGREES)

    def has_degree_field(self, text: str) -> bool:
        """Check if text contains a field of study."""
        return any(field.lower() in text.lower() for field in self.DEGREE_FIELDS)

    def is_non_education(self, text: str) -> bool:
        """Check if text contains non-education related keywords."""
        return any(keyword in text.lower() for keyword in self.NON_EDUCATION_KEYWORDS)

    # Text processing methods
    def clean_text(self, text: str) -> str:
        """Remove unwanted Unicode artifacts and normalize text."""
        text = re.sub(r'[\uf0b7\uf0d8\uf020\u2013\u2022\u2023\u25aa•▪]+', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*[-–]\s*', ' - ', text)
        return text.strip()

    def _clean_entry_text(self, text: str, date: str) -> str:
        """Clean entry text by removing date and unnecessary characters."""
        text = text.replace(date, '').strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def _split_into_entries(self, text: str) -> List[str]:
        """Split text into education entries."""
        entries = []
        cleaned_text = self.clean_text(text)
        
        split_methods = [
            lambda t: [p.strip() for p in t.split('|') if p.strip()],
            lambda t: [p.strip() for p in re.split(r'(?=\b(?:19|20)\d{2}[-–]|(?:19|20)\d{2}\b)', t) if p.strip()],
            lambda t: [p.strip() for p in re.split(r'(?=[A-ZÉÍÓÖŐÚÜŰ][^.!?]*(?:egyetem|főiskola|iskola|intézet|akadémia))', t, flags=re.IGNORECASE) if p.strip()],
            lambda t: [p.strip() for p in re.split(r'\s*[•■⚫●]\s*', t) if p.strip()]
        ]
        
        for split_method in split_methods:
            potential_entries = split_method(cleaned_text)
            
            if potential_entries:
                for entry in potential_entries:
                    doc = self.nlp_hu(entry)
                    
                    has_school = any(keyword.lower() in entry.lower() 
                                   for keyword in self.SCHOOLS + ['egyetem', 'főiskola', 'iskola', 'intézet'])
                    has_org = any(ent.label_ == 'ORG' for ent in doc.ents)
                    has_degree = any(keyword.lower() in entry.lower() 
                                   for keyword in self.DEGREES + self.DEGREE_FIELDS)
                    has_date = bool(re.search(r'\b(?:19|20)\d{2}\b', entry))
                    
                    if (has_school or has_org) or (has_degree and has_date):
                        entries.append(entry)
                
                if entries:
                    break
        
        if not entries:
            entries = [cleaned_text]
        
        return entries

    def _parse_entry_parts(self, text: str) -> Tuple[str, str, List[str]]:
        """Parse entry text into school, degree, and descriptions using NLP."""
        school = ""
        degree = ""
        descriptions = []
        
        try:
            cleaned_text = self.clean_text(text)
            doc = self.nlp_hu(cleaned_text)
            
            for ent in doc.ents:
                if ent.label_ == 'ORG' and not school:
                    school = self.clean_text(ent.text)
                    break
            
            remaining_text = cleaned_text.replace(school, '') if school else cleaned_text
            remaining_doc = self.nlp_hu(remaining_text)
            
            for token in remaining_doc:
                if token.pos_ == 'NOUN' and any(keyword.lower() in token.text.lower() 
                    for keyword in self.DEGREES + self.DEGREE_FIELDS):
                    phrase = []
                    for t in token.subtree:
                        if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                            phrase.append(t.text)
                    if phrase:
                        potential_degree = self.clean_text(' '.join(phrase))
                        if len(potential_degree.split()) <= 6:
                            degree = potential_degree
                            break
            
            desc_text = remaining_text
            if degree:
                desc_text = desc_text.replace(degree, '')
            
            for sent in doc.sents:
                sent_text = self.clean_text(sent.text)
                if (sent_text and 
                    sent_text not in [school, degree] and
                    len(sent_text.split()) > 2 and
                    not any(keyword.lower() in sent_text.lower() 
                           for keyword in self.NON_EDUCATION_KEYWORDS)):
                    descriptions.append(sent_text)

        except Exception as e:
            print(f"Education extraction failed: {str(e)}")
            return "", "", []
            
        return school, degree, descriptions

    # Section extraction methods
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

    # Date and GPA extraction methods
    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        match = re.search(year_pattern, text)
        return match.group(0) if match else ''

    def extract_gpa(self, text: str) -> Optional[str]:
        """Extract GPA from text."""
        for pattern in self.gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grade = match.group(1).lower()
                return self.gpa_mapping.get(grade, grade)
        return None