import re
from typing import Dict, List, Optional
import spacy
from langdetect import detect, LangDetectException

class EducationExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        # Constants for both English and Hungarian keywords
        self.SCHOOLS = [
            # English
            'College', 'University', 'Institute', 'School', 'Academy', 'BASIS', 'Magnet',
            # Hungarian
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        self.DEGREES = [
            # English
            'Associate', 'Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'BA', 'MS', 'MSc', 'MBA',
            'Diploma', 'Engineer', 'Technician',
            # Hungarian
            'Mrnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés'
        ]
        
        self.section_headers = {
            'education': ['education', 'academic background', 'qualifications', 'academic qualifications']
        }

        self.education_keywords = [
            'university', 'college', 'institute', 'school', 'academy', 'degree', 'bachelor', 'master', 'phd', 'gpa',
            'coursework', 'course', 'program', 'diploma', 'certification', 'training'
        ]

        self.date_patterns = [
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?) \d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}',
            r'\d{2}\.\d{2}\.\d{4}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'(Summer|Fall|Winter|Spring) \d{4}',
            r'\d{1,2} (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),? \d{4}'
        ]

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line contains a section header
            is_section_header = any(keyword in line.lower() for keyword in section_keywords)
            
            # Check if next line is a different section
            is_next_different_section = False
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                is_next_different_section = any(
                    keyword in next_line.lower() 
                    for keyword in ['experience', 'skills', 'projects', 'languages']
                )
            
            if is_section_header:
                in_section = True
                continue
            
            if in_section and is_next_different_section:
                in_section = False
            
            if in_section:
                section_lines.append(line)
        
        return section_lines

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

    def has_school(self, text: str) -> bool:
        # Use spaCy to perform NER with the appropriate language model
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == {'ORG', 'FAC', 'GPE', 'LOC'}:  # Check if the entity is an organization
                return True
        
        # Fallback to the original logic
        return any(school.lower() in text.lower() for school in self.SCHOOLS)
    
    def has_degree(self, text: str) -> bool:
        # Use spaCy to perform NER with the appropriate language model
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "EDUCATION":  # Check if the entity is related to education
                return True
        
        # Check for exact matches of degree names
        degree_pattern = r'\b(?:' + '|'.join(re.escape(degree) for degree in self.DEGREES) + r')\b'
        if re.search(degree_pattern, text, re.IGNORECASE):
            return True
        
        # Check for common degree abbreviations
        if re.search(r'\b(?:B\.?A\.?|B\.?S\.?|M\.?A\.?|M\.?S\.?|Ph\.?D\.?)\b', text, re.IGNORECASE):
            return True
        
        return False
    
    def extract_gpa(self, text: str) -> Optional[str]:
        # Use spaCy to process the text
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        
        # Attempt to find GPA using spaCy's NER
        for ent in doc.ents:
            if ent.label_ == "CARDINAL" and re.match(r'^[0-5]\.\d{1,2}$', ent.text):
                return ent.text
        
        # Fallback to regex for GPA and grades
        gpa_match = re.search(r'GPA:?\s*([\d\.]+)', text, re.IGNORECASE)
        grade_match = re.search(r'(?:Note|Jegy|Minősítés):\s*([\w]+)', text, re.IGNORECASE)
        
        if gpa_match:
            return gpa_match.group(1)
        elif grade_match:
            grade = grade_match.group(1)
            # Convert Hungarian grades if needed
            grade_map = {
                'excellent': '5.0',
                'kitűnő': '5.0',
                'jeles': '5.0',
                'good': '4.0',
                'jó': '4.0',
                'satisfactory': '3.0',
                'közepes': '3.0'
            }
            return grade_map.get(grade.lower(), grade)
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
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
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        if date_entities:
            return ' to '.join(date_entities)

        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' to '.join(matches)

        return None

    def extract_education_descriptions(self, text: str) -> List[str]:
        """Extract detailed education descriptions using NLP and dependency parsing."""
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        descriptions = []

        # Define action verbs related to education
        action_verbs = {'study', 'graduate', 'complete', 'attend', 'enroll', 'achieve', 'earn', 'obtain'}

        for sent in doc.sents:
            # Use dependency parsing to find verbs related to education
            for token in sent:
                if token.dep_ in {'ROOT', 'advcl', 'xcomp'} and token.lemma_ in action_verbs:
                    descriptions.append(sent.text.strip())
                    break

            # Check for entities that are typically associated with education
            if any(ent.label_ in {'ORG', 'DATE', 'PERSON'} for ent in sent.ents):
                descriptions.append(sent.text.strip())

            # Handle bullet points and numbered lists
            if re.match(r'^[•*-]\s*', sent.text) or re.match(r'^\d+\.', sent.text):
                clean_description = sent.text.strip().lstrip('-•* ')
                if clean_description:  # Check if the description is not empty
                    descriptions.append(clean_description)

        return descriptions

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information."""
        education_data = []
        current_entry = None
        
        # Extract education section using section_headers
        education_lines = self.extract_section(text, self.section_headers['education'])
        
        if education_lines:
            for line in education_lines:
                # Skip section headers
                if any(header in line.lower() for header in self.section_headers['education']):
                    continue
                
                # Start new entry if school or significant education keyword found
                if self.has_school(line) or any(keyword in line.lower() for keyword in ['diploma', 'érettségi', 'final exam', 'leaving exam']):
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
                
                # Add to descriptions
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