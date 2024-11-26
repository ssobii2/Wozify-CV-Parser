import re
from typing import Dict, List, Optional, Tuple
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

    def _clean_school_name(self, text: str) -> Tuple[str, str, str]:
        """Clean and separate school name from degree and GPA information.
        Returns: (school_name, degree, gpa)"""
        # Remove common prefixes that might appear
        text = re.sub(r'^[-•*]\s*', '', text.strip())
        
        # Try to extract GPA if present
        gpa = ''
        gpa_match = re.search(r'(?:GPA|Grade|CGPA):\s*([\d\.]+)\s*(?:/\s*[\d\.]+)?', text, re.IGNORECASE)
        if gpa_match:
            gpa = gpa_match.group(1)
            text = text.replace(gpa_match.group(0), '').strip()
        
        # First try to find common degree patterns
        degree_patterns = [
            r'(Bachelor\s+of\s+[^,]+)',
            r'(Master\s+of\s+[^,]+)',
            r'(Ph\.?D\.?\s+[^,]*)',
            r'(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?)\s+in\s+([^,]+)',
            r'(BSc|MSc|MBA|BA|MA)\s+in\s+([^,]+)'
        ]
        
        degree = ''
        remaining_text = text
        for pattern in degree_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                degree = match.group(0)
                remaining_text = text.replace(degree, '').strip(' ,')
                break
        
        # If we found a degree, the remaining text is likely the school
        if degree:
            school_name = remaining_text
        else:
            # Otherwise, try to split by common separators
            parts = re.split(r'\s*(?:[-–|,]|\bin\b)\s*', text, maxsplit=1)
            school_name = parts[0].strip()
            if len(parts) > 1:
                degree = parts[1].strip()
        
        # Clean up school name
        school_name = re.sub(r'\s*\([^)]*\)', '', school_name).strip()  # Remove parenthetical info
        school_name = re.sub(r'\s+,.*$', '', school_name).strip()  # Remove location after comma
        
        # Clean up degree
        if degree:
            degree = re.sub(r'\s*\(\s*\)', '', degree).strip()  # Remove empty parentheses
            degree = re.sub(r'\s*\([^)]*\)', '', degree).strip()  # Remove parenthetical info
        
        return school_name, degree, gpa

    def _extract_gpa_from_description(self, text: str) -> Optional[str]:
        """Extract GPA from description text."""
        gpa_patterns = [
            r'(?:GPA|Grade|CGPA):\s*([\d\.]+)\s*(?:/\s*[\d\.]+)?',
            r'(?:GPA|Grade|CGPA)\s*(?:of)?\s*([\d\.]+)\s*(?:/\s*[\d\.]+)?',
            r'([\d\.]+)\s*/\s*[\d\.]+\s*(?:GPA|Grade|CGPA)',
        ]
        
        for pattern in gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _clean_degree(self, text: str) -> str:
        """Clean and normalize degree information."""
        # Remove common prefixes
        text = re.sub(r'^[-•*]\s*', '', text.strip())
        
        # Remove any coursework-related information
        text = re.sub(r'(?i)relevant\s+coursework:.*$', '', text)
        text = re.sub(r'(?i)courses?:.*$', '', text)
        
        # Remove GPA information if present
        text = re.sub(r'(?i)(?:GPA|Grade):\s*[\d\.]+\s*(?:/\s*[\d\.]+)?', '', text)
        
        return text.strip()

    def _is_coursework(self, text: str) -> bool:
        """Check if the text is likely to be coursework information."""
        coursework_indicators = [
            r'(?i)relevant\s+coursework',
            r'(?i)courses?:',
            r'(?i)subjects?:',
            r'(?i)^(?:including|covered):',
            r'(?i)studied:',
        ]
        return any(re.search(pattern, text) for pattern in coursework_indicators)

    def _clean_descriptions(self, descriptions: List[str]) -> List[str]:
        """Clean and filter education descriptions."""
        cleaned = []
        for desc in descriptions:
            # Remove common prefixes
            desc = re.sub(r'^[-•*]\s*', '', desc.strip())
            
            # Skip if it's just a date
            if re.match(r'^[\d\s\-–/\.]+$', desc):
                continue
                
            # Skip if it's just a location
            if re.match(r'^[A-Za-z\s,]+$', desc) and len(desc.split()) <= 3:
                continue
                
            # Skip if it's a duplicate of school or degree
            if any(d.strip() == desc.strip() for d in cleaned):
                continue
                
            cleaned.append(desc)
        
        return cleaned

    def _validate_section_data(self, section_lines: List[str]) -> bool:
        """Validate if the section data is meaningful and contains education information."""
        if not section_lines:
            return False
            
        # Check if we have more than just section headers
        if len(section_lines) <= 1:
            return False
            
        # Check if any line contains education-related keywords
        education_indicators = [
            r'\b(?:University|College|Institute|School|Academy)\b',
            r'\b(?:Bachelor|Master|PhD|BSc|MSc|BA|MA|MBA|BBA)\b',
            r'\b(?:Degree|Diploma|Certificate)\b',
            r'\b(?:Major|Minor|Specialization)\b',
            r'\b(?:Education|Study|Studies)\b'
        ]
        
        has_education_content = False
        for line in section_lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in education_indicators):
                has_education_content = True
                break
                
        return has_education_content

    def extract_education(self, text: str, parsed_sections: Dict[str, List[str]] = None) -> List[Dict]:
        """Extract detailed education information."""
        education_data = []
        current_entry = None
        
        # Get education lines from parsed sections or fallback to extraction
        education_lines = []
        used_fallback = False
        
        if parsed_sections and 'education' in parsed_sections:
            section_lines = [line.strip() for line in parsed_sections['education'] if line.strip()]
            if self._validate_section_data(section_lines):
                education_lines = section_lines
                print(f"Found {len(education_lines)} valid lines in parsed education section")
            else:
                print("Parsed section data invalid or insufficient, using fallback")
                used_fallback = True
        
        # If no valid education lines found, try fallback extraction
        if not education_lines or used_fallback:
            # Look for education section using various patterns
            education_patterns = [
                r'(?:EDUCATION|ACADEMIC|QUALIFICATION)S?(?:\s+(?:&|AND)\s+TRAINING)?',
                r'STUDIES?(?:\s+(?:&|AND)\s+EDUCATION)?',
                r'ACADEMIC\s+BACKGROUND',
                r'EDUCATIONAL\s+(?:HISTORY|BACKGROUND)',
            ]
            
            for pattern in education_patterns:
                section_text = self.extract_section(text, [pattern])
                if section_text:
                    education_lines.extend([line.strip() for line in section_text if line.strip()])
            
            print(f"Extracted {len(education_lines)} lines using fallback method")

        if education_lines:
            for line in education_lines:
                # Skip empty lines and section headers
                if not line or any(re.search(pattern, line, re.IGNORECASE) for pattern in self.section_headers['education']):
                    continue
                
                # Skip lines that look like skills or technologies
                if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', line, re.IGNORECASE):
                    continue
                
                # Try to identify education entries by looking for key indicators
                education_indicators = [
                    r'\b(?:University|College|Institute|School|Academy)\b',
                    r'\b(?:Bachelor|Master|PhD|BSc|MSc|BA|MA|MBA|BBA)\b',
                    r'\b(?:Degree|Diploma|Certificate)\b',
                    r'\b(?:Major|Minor|Specialization)\b'
                ]
                
                is_education_line = any(re.search(pattern, line, re.IGNORECASE) for pattern in education_indicators)
                
                if is_education_line:
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        current_entry['descriptions'] = self._clean_descriptions(current_entry['descriptions'])
                        education_data.append(current_entry)
                    
                    school_name, degree_info, gpa = self._clean_school_name(line)
                    current_entry = {
                        'school': school_name,
                        'degree': degree_info,
                        'gpa': gpa or self.extract_gpa(line) or '',
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
                
                # Handle additional information
                if self._is_coursework(line):
                    current_entry['descriptions'].append(line)
                elif self.has_degree(line) and not current_entry['degree']:
                    current_entry['degree'] = self._clean_degree(line)
                else:
                    # Try to extract GPA if not found
                    if not current_entry['gpa']:
                        gpa = self._extract_gpa_from_description(line)
                        if gpa:
                            current_entry['gpa'] = gpa
                            continue
                    
                    # Try to extract date if not found
                    if not current_entry['date']:
                        date = self.extract_date(line)
                        if date:
                            current_entry['date'] = date
                            continue
                    
                    # Add as description if it contains relevant information
                    if len(line.split()) > 2:  # Skip very short lines
                        current_entry['descriptions'].append(line)
            
            # Add the last entry
            if current_entry and (current_entry['school'] or current_entry['degree']):
                current_entry['descriptions'] = self._clean_descriptions(current_entry['descriptions'])
                education_data.append(current_entry)
        
        # Clean up entries
        cleaned_data = []
        for entry in education_data:
            # Skip entries that look like skills or contact info
            if entry.get('school') and any(keyword in entry['school'].lower() for keyword in ['html', 'css', 'javascript', 'sql', 'windows', 'linux', 'http']):
                continue
            
            # Clean up entries
            if entry.get('degree') and self._is_coursework(entry['degree']):
                entry['descriptions'].insert(0, entry['degree'])
                entry['degree'] = ''
            
            # Try to extract GPA from descriptions if not found
            if not entry.get('gpa'):
                for desc in entry.get('descriptions', []):
                    gpa = self._extract_gpa_from_description(desc)
                    if gpa:
                        entry['gpa'] = gpa
                        break
            
            # Remove duplicate descriptions
            entry['descriptions'] = self._clean_descriptions(entry.get('descriptions', []))
            
            # Only add entries that have either school or degree information
            if entry.get('school') or entry.get('degree'):
                cleaned_data.append(entry)
        
        print(f"Final education entries: {len(cleaned_data)}")
        return cleaned_data if cleaned_data else []