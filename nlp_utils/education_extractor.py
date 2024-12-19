import re
from typing import Dict, List, Optional, Tuple
import spacy

class EducationExtractor:
    def __init__(self, nlp_en):
        self.nlp = nlp_en
        # Constants for English
        self.SCHOOLS = [
            'College', 'University', 'Institute', 'School', 'Academy', 'BASIS', 'Magnet',
            'Polytechnic', 'Seminary', 'Conservatory', 'Community College', 'Technical College',
            'Vocational School', 'Graduate School', 'Postgraduate Institute', 'Online University',
            'Distance Learning Institute', 'Adult Education Center', 'Training Institute',
            'Career College', 'Specialized School', 'Art School', 'Music School', 'Language School',
            'Nursing School', 'Business School', 'Law School', 'Medical School', 'Engineering School',
            'Science Institute', 'Research Institute', 'Fashion School', 'Culinary School',
            'Design School', 'Film School', 'Theater School', 'Sports Academy', 'Military Academy',
            'Flight School', 'Beauty School', 'Cosmetology School', 'Massage Therapy School',
            'Pharmacy School', 'Dental School', 'Optometry School', 'Public Health School',
            'Environmental School', 'Information Technology School', 'Cybersecurity School',
            'Data Science Institute', 'Artificial Intelligence Institute', 'Blockchain Academy'
        ]
        
        self.DEGREES = [
            'Associate', 'Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'BA', 'MS', 'MSc', 'MBA',
            'Diploma', 'Engineer', 'Technician', 'BEng', 'MEng', 'BBA', 'DBA', 'MD', 'JD',
            'LLB', 'LLM', 'EdD', 'DPhil', 'MPhil', 'MAcc', 'MFA', 'BFA',
            'Certificate', 'Advanced Diploma', 'Higher National Diploma', 'Foundation Degree',
            'Postgraduate Certificate', 'Postgraduate Diploma', 'Doctor of Education', 'Doctor of Philosophy',
            'Master of Arts', 'Master of Science', 'Master of Business Administration', 'Bachelor of Arts',
            'Bachelor of Science', 'Bachelor of Engineering', 'Bachelor of Fine Arts', 'Bachelor of Music',
            'Master of Fine Arts', 'Master of Public Administration', 'Master of Public Health', 'Master of Social Work',
            'Master of Education', 'Master of Architecture', 'Master of Laws', 'Master of International Business',
            'Doctor of Medicine', 'Doctor of Jurisprudence', 'Doctor of Nursing Practice', 'Doctor of Pharmacy',
            'Doctor of Veterinary Medicine', 'Doctor of Optometry', 'Doctor of Dental Surgery', 'Doctor of Physical Therapy'
        ]
        
        self.HONORS = [
            'summa cum laude', 'magna cum laude', 'cum laude', 'with honors', 'with distinction',
            'first class', 'second class', 'merit', 'distinction', 'dean\'s list', 'highest honors',
            'high honors', 'honors', 'honors graduate', 'graduated with honors', 'top of the class',
            'valedictorian', 'president\'s list', 'chancellor\'s list', 'academic excellence',
            'academic achievement', 'outstanding achievement', 'recognition of excellence',
            'scholar', 'honor roll', 'exemplary performance', 'distinguished scholar', 
            'academic distinction', 'summa cum laude graduate', 'magna cum laude graduate',
            'cum laude graduate', 'with high honors', 'with great distinction', 'with special honors',
            'with commendation', 'with accolades', 'top honors', 'honorary mention', 'academic merit',
            'recognized for excellence', 'notable achievement', 'academic honors', 'scholastic honors'
        ]
        
        self.section_headers = {
            'education': [
                'education', 'academic background', 'qualifications', 'academic qualifications',
                'educational background', 'education and training', 'academic history',
                'education details', 'academic details', 'education & qualifications',
                'academic profile', 'studies', 'learning', 'training history', 'schooling',
                'coursework', 'degree information', 'educational qualifications', 'certifications',
                'academic achievements', 'professional development', 'educational experience'
            ]
        }

        self.education_keywords = [
            'university', 'college', 'institute', 'school', 'academy', 'degree', 'bachelor', 
            'master', 'phd', 'gpa', 'coursework', 'course', 'program', 'diploma', 
            'certification', 'training', 'higher education', 'vocational training', 
            'associate degree', 'graduate degree', 'postgraduate degree', 'online course', 
            'distance learning', 'certificate program', 'professional development', 
            'academic program', 'educational institution', 'learning experience', 
            'curriculum', 'academic achievement', 'scholarship', 'internship', 
            'apprenticeship', 'continuing education', 'adult education'
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
        
        # Enhanced GPA patterns
        gpa_patterns = [
            r'GPA:?\s*([\d\.]+)(?:/[\d\.]+)?',  # Standard GPA format
            r'(?:Note|Grade):\s*([\w\.]+)',      # Text-based grades
            r'([\d\.]+)\s*/\s*[\d\.]+',          # Fractional format
            r'([\d,]+)/20',                      # French system
            r'([\d,]+)/10',                      # Indian/European system
            r'Grade:\s*(A\+?|B\+?|C\+?|D\+?|F)',  # Letter grades
        ]
        
        for pattern in gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grade = match.group(1)
                # Convert comma to dot for decimal numbers
                grade = grade.replace(',', '.')
                
                # Convert letter grades to numeric values
                grade_map = {
                    'A+': '4.0', 'A': '4.0', 'A-': '3.7',
                    'B+': '3.3', 'B': '3.0', 'B-': '2.7',
                    'C+': '2.3', 'C': '2.0', 'C-': '1.7',
                    'D+': '1.3', 'D': '1.0', 'F': '0.0',
                    'excellent': '5.0', 'very good': '4.0',
                    'good': '3.0', 'satisfactory': '2.0',
                    'pass': '1.0'
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
        """Enhanced date range extraction with support for ongoing education."""
        doc = self.nlp(text)
        
        # Check for ongoing education indicators
        ongoing_patterns = [
            r'(?:current|ongoing|present|now)',
            r'\b(?:studying|enrolled|pursuing)\b',
            r'(?:expected|anticipated|planned)\s+(?:graduation|completion).*?(\d{4})',
        ]
        
        for pattern in ongoing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # If there's a future year mentioned, use it
                if match.groups():
                    return f"{self.extract_date(text)} to {match.group(1)}"
                return f"{self.extract_date(text)} to Present"

        # Fall back to standard date range extraction
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
        
        # Remove date patterns from the start
        text = re.sub(r'^\d{4}\s*[-–]\s*\d{4}:\s*', '', text)
        text = re.sub(r'^\d{4}\s*[-–]\s*(?:Present|Current|Now):\s*', '', text)
        text = re.sub(r'^\d{4}:\s*', '', text)
        
        # Try to extract GPA if present
        gpa = ''
        gpa_match = re.search(r'(?:GPA|Grade|CGPA):\s*([\d\.]+)\s*(?:/\s*[\d\.]+)?', text, re.IGNORECASE)
        if gpa_match:
            gpa = gpa_match.group(1)
            text = text.replace(gpa_match.group(0), '').strip()
        
        # Split on common degree indicators
        degree_indicators = [
            r'\s*-\s*(?=Doctor|Ph\.?D|Master|Bachelor|BSc|MSc|MBA|BA|MA)',
            r'\s*,\s*(?=Doctor|Ph\.?D|Master|Bachelor|BSc|MSc|MBA|BA|MA)',
            r'\s+(?=Doctor|Ph\.?D|Master|Bachelor|BSc|MSc|MBA|BA|MA)'
        ]
        
        parts = text
        for indicator in degree_indicators:
            parts = re.split(indicator, text, maxsplit=1)
            if len(parts) > 1:
                break
        
        if len(parts) > 1:
            school_name = parts[0].strip()
            degree = parts[1].strip()
        else:
            # If no clear split found, try to identify if the text is more likely a school or degree
            if any(keyword in text.lower() for keyword in ['university', 'college', 'institute', 'school']):
                school_name = text
                degree = ''
            else:
                school_name = ''
                degree = text
        
        # Clean up school name
        school_name = re.sub(r'\s*\([^)]*\)', '', school_name)  # Remove parenthetical info
        school_name = re.sub(r'\s+,.*$', '', school_name)       # Remove location after comma
        school_name = school_name.strip(' -,')                  # Remove trailing separators
        
        # Clean up degree
        if degree:
            degree = re.sub(r'\s*\(\s*\)', '', degree)         # Remove empty parentheses
            degree = re.sub(r'\s*\([^)]*\)', '', degree)       # Remove parenthetical info
            degree = degree.strip(' -,')                        # Remove trailing separators
        
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
        # Remove common prefixes and dates
        text = re.sub(r'^[-•*]\s*', '', text.strip())
        text = re.sub(r'^\d{4}\s*[-–]\s*\d{4}:\s*', '', text)
        text = re.sub(r'^\d{4}\s*[-–]\s*(?:Present|Current|Now):\s*', '', text)
        text = re.sub(r'^\d{4}:\s*', '', text)
        
        # Remove any coursework-related information
        text = re.sub(r'(?i)relevant\s+coursework:.*$', '', text)
        text = re.sub(r'(?i)courses?:.*$', '', text)
        
        # Remove GPA information if present
        text = re.sub(r'(?i)(?:GPA|Grade):\s*[\d\.]+\s*(?:/\s*[\d\.]+)?', '', text)
        
        # Clean up common formatting issues
        text = re.sub(r'\s+', ' ', text)                    # Normalize whitespace
        text = re.sub(r'\s*,\s*$', '', text)               # Remove trailing comma
        text = re.sub(r'\s*-\s*$', '', text)               # Remove trailing dash
        text = text.strip()
        
        return text

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
        
        # Check if any line contains education-related keywords
        education_indicators = [
            r'\b(?:University|College|Institute|School|Academy)\b',
            r'\b(?:Bachelor|Master|PhD|BSc|MSc|BA|MA|MBA|BBA)\b',
            r'\b(?:Degree|Diploma|Certificate)\b',
            r'\b(?:Major|Minor|Specialization)\b',
            r'\b(?:Education|Study|Studies)\b',
            r'(?:Computer Science|Engineering|Informatics)\b'  # Added common fields
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
            # Only use lines from the education section, don't mix with other text
            section_lines = [line.strip() for line in parsed_sections['education'] if line.strip()]
            # Filter out lines that look like they belong to other sections
            section_lines = [
                line for line in section_lines 
                if not any(keyword in line.lower() for keyword in [
                    'experience:', 'skills:', 'languages:', 'projects:', 
                    'certifications:', 'awards:', 'publications:', 'interests:',
                    'references:', 'profile:', 'summary:'
                ])
            ]
            if self._validate_section_data(section_lines):
                education_lines = section_lines
                print(f"Found {len(education_lines)} valid lines in parsed education section")
            else:
                print("Parsed section data invalid or insufficient, using fallback")
                used_fallback = True
        
        # Only use fallback if no parsed sections provided
        if (not parsed_sections or not 'education' in parsed_sections) and (not education_lines or used_fallback):
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

        # Only use full text scan if no education section found and no parsed sections provided
        if not education_lines and not parsed_sections:
            text_lines = text.split('\n')
            for line in text_lines:
                if any(keyword in line.lower() for keyword in ['university', 'college', 'bachelor', 'master', 'phd', 'degree', 'diploma']):
                    if not any(keyword in line.lower() for keyword in ['experience', 'skill', 'project']):
                        education_lines.append(line.strip())

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
                        'date_range': self.extract_date_range(line) or '',
                        'honors': self.extract_honors(line),
                        'descriptions': []
                    }
                    continue
                
                if current_entry is None:
                    current_entry = {
                        'school': '',
                        'degree': '',
                        'gpa': '',
                        'date': '',
                        'date_range': '',
                        'honors': [],
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
            
            # Additional validation for empty entries
            if not entry.get('school') and not entry.get('degree'):
                continue
            
            # Try to extract meaningful info from descriptions if school/degree empty
            if not entry.get('school') and not entry.get('degree') and entry.get('descriptions'):
                for desc in entry['descriptions']:
                    if any(keyword in desc.lower() for keyword in ['university', 'college', 'institute', 'school']):
                        parts = desc.split(',', 1)
                        entry['school'] = parts[0].strip()
                        if len(parts) > 1:
                            entry['degree'] = parts[1].strip()
                        break
            
            # Only add entries that have either school or degree information
            if entry.get('school') or entry.get('degree'):
                cleaned_data.append(entry)
        
        print(f"Final education entries: {len(cleaned_data)}")
        return cleaned_data if cleaned_data else []

    def extract_honors(self, text: str) -> List[str]:
        """Extract academic honors and awards."""
        honors = []
        
        # Check for standard honors
        for honor in self.HONORS:
            if re.search(r'\b' + re.escape(honor) + r'\b', text, re.IGNORECASE):
                honors.append(honor.title())
        
        # Look for other award patterns
        award_patterns = [
            r'(?:received|awarded|earned|granted)\s+(?:the\s+)?([^,.]+?(?:award|prize|medal|scholarship))',
            r'(?:award|prize|medal|scholarship):\s*([^,.]+)',
            r'(?:first|second|third)\s+(?:place|prize|rank)',
        ]
        
        for pattern in award_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                honor = match.group(1).strip() if match.groups() else match.group(0).strip()
                if honor and honor not in honors:
                    honors.append(honor.title())
        
        return honors

    def _standardize_date(self, date_str: str) -> str:
        """Standardize date format to DD/MM/YYYY."""
        # Handle month names
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11',
            'dec': '12'
        }
        
        # Handle seasons
        season_map = {
            'spring': '03',
            'summer': '06',
            'fall': '09',
            'autumn': '09',
            'winter': '12'
        }
        
        date_str = date_str.lower().strip()
        
        # Handle "Present" or "Current"
        if any(word in date_str.lower() for word in ['present', 'current', 'now']):
            from datetime import datetime
            today = datetime.now()
            return f"{today.day:02d}/{today.month:02d}/{today.year}"
        
        # Extract year
        year_match = re.search(r'\d{4}', date_str)
        if not year_match:
            return date_str  # Return original if no year found
        
        year = year_match.group()
        
        # Handle seasons
        for season, month in season_map.items():
            if season in date_str:
                return f"01/{month}/{year}"

        # Handle month names
        for month_name, month_num in month_map.items():
            if month_name in date_str:
                # Try to extract day
                day_match = re.search(r'\b(\d{1,2})\b', date_str)
                day = day_match.group() if day_match else '01'
                return f"{int(day):02d}/{month_num}/{year}"
        
        # Handle numeric formats
        numeric_match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', date_str)
        if numeric_match:
            day, month, year = numeric_match.groups()
            # Assume DD/MM/YYYY format (European)
            return f"{int(day):02d}/{int(month):02d}/{year}"
        
        # If only year is found, use January 1st
        return f"01/01/{year}"