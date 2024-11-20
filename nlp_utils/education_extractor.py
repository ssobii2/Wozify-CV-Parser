import re
from typing import Dict, List, Optional
import spacy

class EducationExtractor:
    def __init__(self, nlp_en):
        self.nlp = nlp_en
        # Constants for English
        self.SCHOOLS = [
            'College', 'University', 'Institute', 'School', 'Academy', 'BASIS', 'Magnet',
        ]
        
        self.DEGREES = [
            'Associate', 'Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'BA', 'MS', 'MSc', 'MBA',
            'Diploma', 'Engineer', 'Technician',
        ]
        
        self.section_headers = {
            'education': [
                'education', 'academic background', 'qualifications', 'academic qualifications',
                'educational background', 'education and training', 'academic history',
                'education details', 'academic details', 'education & qualifications',
                'academic profile', 'studies'
            ]
        }

        self.education_keywords = [
            'university', 'college', 'institute', 'school', 'academy', 'degree', 'bachelor', 
            'master', 'phd', 'gpa', 'coursework', 'course', 'program', 'diploma', 
            'certification', 'training'
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

    def has_school(self, text: str) -> bool:
        """Check if text contains a school name."""
        # Skip if text looks like a skill or technology
        if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', text, re.IGNORECASE):
            return False
            
        # Skip if text starts with a bullet point or dash
        if text.strip().startswith(('•', '-', '*')):
            return False
            
        # Use spaCy to perform NER
        doc = self.nlp(text)
        
        # Check for organization entities
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'FAC'} and any(school.lower() in ent.text.lower() for school in self.SCHOOLS):
                return True
        
        # Fallback to keyword matching
        text_lower = text.lower()
        return any(school.lower() in text_lower for school in self.SCHOOLS)

    def has_degree(self, text: str) -> bool:
        """Check if text contains a degree."""
        # Skip if text looks like a skill or technology
        if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', text, re.IGNORECASE):
            return False
            
        # Skip if text starts with a bullet point or dash
        if text.strip().startswith(('•', '-', '*')):
            return False
            
        # Check for degree patterns
        degree_patterns = [
            r'\b(?:Bachelor|Master|PhD|Ph\.D|BSc|BA|MS|MSc|MBA|Associate|Diploma)\b',
            r'\b(?:B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?)\b',
            r'\b(?:Engineer|Engineering|Technician)\b',
            r'\b(?:Computer Science|Information Technology|IT|CS)\b'
        ]
        
        for pattern in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        return False

    def extract_gpa(self, text: str) -> Optional[str]:
        # Use spaCy to process the text
        doc = self.nlp(text)
        
        # Attempt to find GPA using spaCy's NER
        for ent in doc.ents:
            if ent.label_ == "CARDINAL" and re.match(r'^[0-5]\.\d{1,2}$', ent.text):
                return ent.text
        
        # Fallback to regex for GPA and grades
        gpa_match = re.search(r'GPA:?\s*([\d\.]+)', text, re.IGNORECASE)
        grade_match = re.search(r'(?:Note):\s*([\w]+)', text, re.IGNORECASE)
        
        if gpa_match:
            return gpa_match.group(1)
        elif grade_match:
            grade = grade_match.group(1)
            # Convert grades to numeric values
            grade_map = {
                'excellent': '5.0',
                'good': '4.0',
                'satisfactory': '3.0',
            }
            return grade_map.get(grade.lower(), grade)
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        doc = self.nlp(text)
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
        doc = self.nlp(text)
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
        doc = self.nlp(text)
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
                line = line.strip()
                
                # Skip empty lines and section headers
                if not line or any(header in line.lower() for header in self.section_headers['education']):
                    continue
                    
                # Skip lines that look like skills or technologies
                if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', line, re.IGNORECASE):
                    continue
                
                # Start new entry if school found
                if self.has_school(line):
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        education_data.append(current_entry)
                    
                    # Extract degree if in same line as school
                    degree = ''
                    if ',' in line:  # Try to separate school and degree
                        parts = line.split(',', 1)
                        if self.has_degree(parts[1]):
                            line = parts[0]
                            degree = parts[1].strip()
                    
                    current_entry = {
                        'school': line,
                        'degree': degree,
                        'gpa': self.extract_gpa(line) or '',
                        'date': self.extract_date(line) or '',
                        'descriptions': []
                    }
                    continue
                
                # Start new entry if degree found
                if self.has_degree(line) and (current_entry is None or current_entry['degree']):
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        education_data.append(current_entry)
                    
                    current_entry = {
                        'school': '',
                        'degree': line,
                        'gpa': self.extract_gpa(line) or '',
                        'date': self.extract_date(line) or '',
                        'descriptions': []
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
                
                # Update degree if found and not set
                if not current_entry['degree'] and self.has_degree(line):
                    current_entry['degree'] = line
                    continue
                
                # Extract GPA if not found
                if not current_entry['gpa']:
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
                
                # Add description if line contains relevant information
                if (
                    line.startswith(('•', '-', '*')) or
                    'course' in line.lower() or
                    'study' in line.lower() or
                    'major' in line.lower()
                ):
                    current_entry['descriptions'].append(line.lstrip('•-* '))
            
            # Add the last entry
            if current_entry and (current_entry['school'] or current_entry['degree']):
                education_data.append(current_entry)
        
        # Clean up entries
        cleaned_data = []
        for entry in education_data:
            # Skip entries that look like skills or contact info
            if any(keyword in entry['school'].lower() for keyword in ['html', 'css', 'javascript', 'sql', 'windows', 'linux', 'http']):
                continue
                
            # Remove duplicate descriptions
            entry['descriptions'] = list(dict.fromkeys(entry['descriptions']))
            
            # Remove descriptions that are just dates or locations
            entry['descriptions'] = [
                desc for desc in entry['descriptions']
                if not (
                    re.match(r'^\d{4}$', desc.strip()) or  # Just a year
                    re.match(r'^[A-Za-z]+,\s*[A-Za-z]+$', desc.strip()) or  # Just a location
                    desc.strip() in [entry['school'], entry['degree']]  # Duplicate of school or degree
                )
            ]
            
            cleaned_data.append(entry)
        
        return cleaned_data if cleaned_data else [{
            'school': '',
            'degree': '',
            'gpa': '',
            'date': '',
            'descriptions': []
        }]