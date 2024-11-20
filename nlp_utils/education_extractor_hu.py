import re
from typing import Optional, List, Dict
import spacy

class EducationExtractorHu:
    def __init__(self, nlp_hu):
        self.nlp_hu = nlp_hu
        self.SCHOOLS = [
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum',
            'Kar', 'Intézet', 'Akadémia'
        ]
        
        self.DEGREES = [
            'Mérnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés', 'BSc', 'MSc', 'PhD',
            'Alapképzés', 'Mesterképzés', 'Doktori', 'Oklevél', 'Bizonyítvány', 'OKJ',
            'Felsőfokú', 'Középfokú', 'Alapfokú'
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
            'education': ['tanulmányok', 'képzettség', 'iskolai végzettség', 'végzettség', 'oktatás']
        }

        self.education_keywords = [
            'egyetem', 'főiskola', 'iskola', 'intézet', 'akadémia', 'diploma', 'képzés',
            'tanfolyam', 'program', 'bizonyítvány', 'szakképzés', 'továbbképzés', 'kar'
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

    def extract_section(self, text: str) -> List[str]:
        """Extract education section from Hungarian text."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
            
            is_section_header = any(keyword in line.lower() for keyword in self.section_headers['education'])
            
            is_next_different_section = False
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
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
        doc = self.nlp_hu(text)
        for ent in doc.ents:
            if ent.label_ == "EDUCATION":
                return True
        
        degree_pattern = r'\b(?:' + '|'.join(re.escape(degree) for degree in self.DEGREES) + r')\b'
        if re.search(degree_pattern, text, re.IGNORECASE):
            return True
            
        return False
    
    def extract_degree(self, text: str) -> str:
        """Extract degree information from text."""
        text_lower = text.lower()
        
        # First check for degree types
        for degree in self.DEGREES:
            if degree.lower() in text_lower:
                # Try to find associated field
                for field in self.DEGREE_FIELDS:
                    if field.lower() in text_lower:
                        return f"{degree} {field}"
                return degree
        
        # Check for field-specific degrees
        for field in self.DEGREE_FIELDS:
            if field.lower() in text_lower:
                if any(keyword in text_lower for keyword in ['szak', 'szakirány', 'képzés']):
                    return f"{field} szak"
        
        return ""

    def extract_gpa(self, text: str) -> str:
        """Extract GPA or grade information from text."""
        text_lower = text.lower()
        
        # Check for numeric GPA
        for pattern in self.gpa_patterns:
            match = re.search(pattern, text_lower)
            if match:
                grade = match.group(1)
                # Convert text-based grades to numeric
                if grade in self.gpa_mapping:
                    return self.gpa_mapping[grade]
                # Clean up numeric grades
                if re.match(r'[1-5][.,]\d{1,2}', grade):
                    return grade.replace(',', '.')
        
        return ""

    def extract_date(self, text: str) -> str:
        """Extract the earliest date from text."""
        all_dates = []
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Extract first group if it exists, otherwise take the whole match
                date = match.group(1) if match.groups() else match.group(0)
                all_dates.append(date.strip())
        
        return min(all_dates) if all_dates else ""

    def extract_date_range(self, text: str) -> Optional[str]:
        doc = self.nlp_hu(text)
        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        if date_entities:
            return ' - '.join(date_entities)

        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' - '.join(matches)

        return None

    def extract_descriptions(self, text: str) -> List[str]:
        """Extract relevant descriptions from education entry."""
        descriptions = []
        doc = self.nlp_hu(text)
        
        # Split into sentences and analyze each
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Skip if sentence is too short or contains unwanted keywords
            if len(sent_text) < 5 or any(keyword.lower() in sent_text.lower() for keyword in self.NON_EDUCATION_KEYWORDS):
                continue
            
            # Check if sentence contains relevant information
            if any(keyword.lower() in sent_text.lower() for keyword in self.DEGREE_FIELDS + ['specializáció', 'szakirány', 'tanulmányok']):
                descriptions.append(sent_text)
        
        return descriptions

    def extract_education_descriptions(self, text: str) -> List[str]:
        """Extract detailed education descriptions using NLP and dependency parsing."""
        doc = self.nlp_hu(text)
        descriptions = []

        # Hungarian education-related action verbs
        action_verbs = {'tanul', 'végez', 'befejez', 'jár', 'beiratkozik', 'teljesít', 'szerez', 'kap'}

        for sent in doc.sents:
            # Use dependency parsing to find verbs related to education
            for token in sent:
                if token.dep_ in {'ROOT', 'advcl', 'xcomp'} and token.lemma_ in action_verbs:
                    descriptions.append(sent.text.strip())
                    break

            # Check for entities that are typically associated with education
            if any(ent.label_ in {'ORG', 'DATE', 'PERSON'} for ent in sent.ents):
                descriptions.append(sent.text.strip())

        return descriptions

    def clean_school_name(self, text: str) -> str:
        """Clean school name by removing dates and unnecessary information."""
        # Remove dates
        for pattern in self.date_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove bullet points and special characters at start
        text = re.sub(r'^[\s•\-\u2022\uf0b7]+', '', text)
        
        # Split by common separators and take the meaningful part
        parts = re.split(r'\s*[\|,]\s*', text)
        text = parts[0] if parts else text
        
        return text.strip()

    def is_valid_education(self, text: str) -> bool:
        """Check if the text represents valid education information."""
        text_lower = text.lower()
        
        # Check for non-education keywords
        if any(keyword.lower() in text_lower for keyword in self.NON_EDUCATION_KEYWORDS):
            return False
            
        # Must contain either a school keyword or education keyword
        has_school_keyword = any(school.lower() in text_lower for school in self.SCHOOLS)
        has_education_keyword = any(keyword in text_lower for keyword in self.education_keywords)
        
        return has_school_keyword or has_education_keyword

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information from text."""
        education_entries = []
        section_lines = self.extract_section(text)
        
        current_entry = None
        
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip if line contains non-education information
            if not self.is_valid_education(line):
                continue
            
            # Create new education entry
            entry = {
                "school": self.clean_school_name(line),
                "degree": self.extract_degree(line),
                "gpa": self.extract_gpa(line),
                "date": self.extract_date(line),
                "descriptions": self.extract_descriptions(line)
            }
            
            if entry["school"] or entry["degree"]:
                education_entries.append(entry)
        
        # Sort entries by date (most recent first)
        education_entries.sort(key=lambda x: x["date"] if x["date"] else "0", reverse=True)
        
        return education_entries if education_entries else []