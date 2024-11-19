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
            'Mrnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés'
        ]

        self.section_headers = {
            'education': ['tanulmányok', 'képzettség', 'iskolai végzettség', 'végzettség']
        }

        self.education_keywords = [
            'egyetem', 'főiskola', 'iskola', 'intézet', 'akadémia', 'diploma', 'képzés',
            'tanfolyam', 'program', 'bizonyítvány', 'szakképzés', 'továbbképzés'
        ]

        self.date_patterns = [
            r'(Jan(?:uár)?|Feb(?:ruár)?|Már(?:cius)?|Ápr(?:ilis)?|Máj(?:us)?|Jún(?:ius)?|'
            r'Júl(?:ius)?|Aug(?:usztus)?|Szep(?:tember)?|Okt(?:óber)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}',
            r'\d{2}\.\d{2}\.\d{4}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'(Nyár|Ősz|Tél|Tavasz) \d{4}',
            r'\d{1,2}\.\s*(?:Jan(?:uár)?|Feb(?:ruár)?|Már(?:cius)?|Ápr(?:ilis)?|Máj(?:us)?|Jún(?:ius)?|'
            r'Júl(?:ius)?|Aug(?:usztus)?|Szep(?:tember)?|Okt(?:óber)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}'
        ]

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
    
    def extract_gpa(self, text: str) -> Optional[str]:
        doc = self.nlp_hu(text)
        
        # Check for Hungarian grade notation
        grade_match = re.search(r'(?:Note|Jegy|Minősítés|Eredmény):\s*([\w]+)', text, re.IGNORECASE)
        if grade_match:
            grade = grade_match.group(1)
            grade_map = {
                'kitűnő': '5.0',
                'jeles': '5.0',
                'jó': '4.0',
                'közepes': '3.0',
                'elégséges': '2.0'
            }
            return grade_map.get(grade.lower(), grade)
        
        # Fallback to numerical GPA
        for ent in doc.ents:
            if ent.label_ == "CARDINAL" and re.match(r'^[0-5]\.\d{1,2}$', ent.text):
                return ent.text
        
        return None

    def extract_date(self, text: str) -> Optional[str]:
        doc = self.nlp_hu(text)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                year_match = re.search(r'(19|20)\d{2}', ent.text)
                return year_match.group(0) if year_match else ent.text

        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                year = re.search(r'(19|20)\d{2}', match.group(0))
                return year.group(0) if year else match.group(0)

        return None

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

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information."""
        education_data = []
        current_entry = None
        
        # Extract education section using section_headers
        education_lines = self.extract_section(text)
        
        if education_lines:
            for line in education_lines:
                # Skip section headers
                if any(header in line.lower() for header in self.section_headers['education']):
                    continue
                
                # Start new entry if school or significant education keyword found
                if self.has_school(line) or any(keyword in line.lower() for keyword in ['diploma', 'érettségi', 'végzettség', 'szakképesítés']):
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        education_data.append(current_entry)
                    
                    current_entry = {
                        'school': line if self.has_school(line) else '',
                        'degree': '',
                        'gpa': '',
                        'date': self.extract_date(line) or '',
                        'descriptions': self.extract_education_descriptions(line)
                    }
                    continue
                
                if current_entry is None:
                    current_entry = {
                        'school': '',
                        'degree': '',
                        'gpa': '',
                        'date': '',
                        'descriptions': []
                    }
                
                # Extract degree
                if self.has_degree(line) and not current_entry['degree']:
                    current_entry['degree'] = line
                    gpa = self.extract_gpa(line)
                    if gpa:
                        current_entry['gpa'] = gpa
                    continue
                
                # Extract date if not found
                if not current_entry['date']:
                    date = self.extract_date(line)
                    if date:
                        current_entry['date'] = date
                        continue
                
                # Extract GPA if not found
                if not current_entry['gpa']:
                    gpa = self.extract_gpa(line)
                    if gpa:
                        current_entry['gpa'] = gpa
                        continue
                
                # Add to descriptions if not already present
                if line not in [current_entry['school'], current_entry['degree']]:
                    current_entry['descriptions'].extend(self.extract_education_descriptions(line))
            
            # Don't forget to add the last entry
            if current_entry and (current_entry['school'] or current_entry['degree']):
                education_data.append(current_entry)
        
        # Clean up entries
        for entry in education_data:
            entry['descriptions'] = [
                desc for desc in entry['descriptions']
                if desc and not any([
                    desc == entry['school'],
                    desc == entry['degree'],
                    self.extract_date(desc) == entry['date'],
                    self.extract_gpa(desc) == entry['gpa']
                ])
            ]
        
        return education_data if education_data else [{
            'school': '',
            'degree': '',
            'gpa': '',
            'date': '',
            'descriptions': []
        }]