import re
from typing import Optional, List, Dict, Tuple
import spacy
import logging

class EducationExtractorHu:
    def __init__(self, nlp_hu):
        self.nlp_hu = nlp_hu
        self.SCHOOLS = [
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        self.DEGREES = [
            'Mérnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés', 
            'BSc', 'MSc', 'PhD', 'BA', 'MA', 'Dr.', 'Doktor',
            'Szakmérnök', 'Üzemmérnök', 'Okleveles', 'Felsőfokú', 'Középfokú',
            'Bizonyítvány', 'Tanúsítvány', 'Képesítés'
        ]

        self.DEGREE_FIELDS = [
            'Informatika', 'Programtervező', 'Gazdasági', 'Műszaki', 'Gépész', 'Villamos',
            'Közgazdász', 'Matematika', 'Fizika', 'Kémia', 'Biológia', 'Környezetvédelem',
            'Kommunikáció', 'Marketing', 'Menedzsment', 'Logisztika', 'Turizmus',
            'Jog', 'Jogász', 'Mérnök informatikus', 'Programozó', 'Rendszergazda',
            'Szoftverfejlesztő', 'Frontend fejlesztő', 'Backend fejlesztő', 'Full stack'
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
        try:
            # Try main extraction first
            if parsed_sections and 'education' in parsed_sections and parsed_sections['education']:
                education_data = []
                
                # Process each education section
                for section in parsed_sections['education']:
                    # First clean the section text
                    cleaned_section = self.clean_text(section)
                    
                    # Split into entries
                    entries = self._split_into_entries(cleaned_section)
                    
                    # If no entries found, treat whole section as one entry
                    if not entries:
                        entries = [cleaned_section]
                    
                    # Process each entry
                    for entry in entries:
                        if entry.strip():
                            school, degree, descriptions = self._parse_entry_parts(entry)
                            date = self._extract_date(entry)
                            
                            # Create entry even if we only have partial information
                            edu_entry = {
                                'school': school.strip(),
                                'degree': degree.strip(),
                                'gpa': self.extract_gpa(entry) or '',
                                'date': date.strip(),
                                'descriptions': descriptions
                            }
                            # Only filter out completely empty entries
                            if any([school, degree, date, descriptions]):
                                education_data.append(edu_entry)
                
                # If main extraction returned empty results, try fallback
                if not education_data:
                    return self._extract_education_fallback(text)
                
                return education_data

            # If no parsed sections or empty education section, use fallback
            return self._extract_education_fallback(text)

        except Exception as e:
            logging.warning(f"Education extraction failed: {str(e)}, trying fallback")
            return self._extract_education_fallback(text)

    def _parse_entry_parts(self, text: str) -> Tuple[str, str, List[str]]:
        """Parse entry text into school, degree and descriptions using NLP."""
        school = ''
        degree = ''
        descriptions = []
        
        try:
            cleaned_text = self.clean_text(text)
            doc = self.nlp_hu(cleaned_text)
            
            # Only use NER for school detection
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    school = self.clean_text(ent.text)
                    break
            
            # Extract degree using dependency parsing
            remaining_text = cleaned_text.replace(school, '') if school else cleaned_text
            remaining_doc = self.nlp_hu(remaining_text)
            
            # Look for degree keywords in noun phrases
            for token in remaining_doc:
                if token.pos_ == 'NOUN' and any(keyword.lower() in token.text.lower() 
                    for keyword in self.DEGREES + self.DEGREE_FIELDS):
                    # Get the full noun phrase containing the degree
                    phrase = []
                    for t in token.subtree:
                        if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                            phrase.append(t.text)
                    if phrase:
                        potential_degree = self.clean_text(' '.join(phrase))
                        if len(potential_degree.split()) <= 6:
                            degree = potential_degree
                            break
            
            # Get descriptions from remaining text
            desc_text = remaining_text
            if degree:
                desc_text = desc_text.replace(degree, '')
            
            # Split into sentences and filter meaningful ones
            for sent in doc.sents:
                sent_text = self.clean_text(sent.text)
                if (sent_text and 
                    sent_text not in [school, degree] and
                    len(sent_text.split()) > 2 and  # Reduced minimum length
                    not any(keyword.lower() in sent_text.lower() 
                           for keyword in self.NON_EDUCATION_KEYWORDS)):
                    descriptions.append(sent_text)

        except Exception as e:
            logging.warning(f"NLP parsing failed: {str(e)}")
            
        return school, degree, descriptions

    def _extract_education_fallback(self, text: str) -> List[Dict]:
        """Fallback method to extract education information."""
        if not text:
            return []

        education_data = []
        
        try:
            # First try to find education section with more keywords
            edu_pattern = r'(?:TANULMÁNYOK|VÉGZETTSÉG|KÉPZETTSÉG|ISKOLAI\s*VÉGZETTSÉG|KÉPESÍTÉS|OKTATÁS|TANULMÁNYI\s*ADATOK|ISKOLÁK)[\s:]*.*?(?=\n\s*(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT|KÉSZSÉGEK|NYELVTUDÁS|EGYÉB|MUNKAHELYEK|$))'
            edu_match = re.search(edu_pattern, text, re.DOTALL | re.IGNORECASE)
            
            text_to_process = edu_match.group(0) if edu_match else text

            # Split text into lines and clean them
            lines = [self.clean_text(line) for line in text_to_process.split('\n') if line.strip()]
            education_entries = []
            current_entry = []

            for line in lines:
                # Skip non-education related lines with more strict filtering
                if self.is_non_education(line) or len(line.split()) < 2:
                    continue

                doc = self.nlp_hu(line)
                
                # Enhanced new entry detection
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

            # Add the last entry
            if current_entry:
                education_entries.append(' '.join(current_entry))

            # Process each education entry
            for entry_text in education_entries:
                school, degree, descriptions = self._parse_entry_parts(entry_text)
                date = self._extract_date(entry_text)
                
                # Try to extract school/degree from descriptions if missing
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

                # Only add entry if it has meaningful information
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
            logging.warning(f"Education fallback extraction failed: {str(e)}")
            return []

        return education_data

    def _split_into_entries(self, text: str) -> List[str]:
        """Split text into education entries."""
        entries = []
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Try different splitting approaches
        split_methods = [
            # Method 1: Split by pipe
            lambda t: [p.strip() for p in t.split('|') if p.strip()],
            
            # Method 2: Split by year patterns
            lambda t: [p.strip() for p in re.split(r'(?=\b(?:19|20)\d{2}[-–]|(?:19|20)\d{2}\b)', t) if p.strip()],
            
            # Method 3: Split by school keywords with capitalization
            lambda t: [p.strip() for p in re.split(r'(?=[A-ZÉÍÓÖŐÚÜŰ][^.!?]*(?:egyetem|főiskola|iskola|intézet|akadémia))', t, flags=re.IGNORECASE) if p.strip()],
            
            # Method 4: Split by bullet points and similar markers
            lambda t: [p.strip() for p in re.split(r'\s*[•■⚫●]\s*', t) if p.strip()]
        ]
        
        # Try each splitting method until we find entries
        for split_method in split_methods:
            potential_entries = split_method(cleaned_text)
            
            if potential_entries:
                for entry in potential_entries:
                    doc = self.nlp_hu(entry)
                    
                    # Verify entry has education-related content
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
        
        # If no entries found, return original text as single entry
        if not entries:
            entries = [cleaned_text]
        
        return entries

    def _clean_entry_text(self, text: str, date: str) -> str:
        """Clean entry text by removing date and unnecessary characters."""
        text = text.replace(date, '').strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        match = re.search(year_pattern, text)
        return match.group(0) if match else ''