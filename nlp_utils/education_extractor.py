import re
from typing import Dict, List, Optional, Tuple

class EducationExtractor:
    def __init__(self, nlp_en):
        """Initialize EducationExtractor with spaCy model and define constants."""
        self.nlp = nlp_en

        # Educational institution types
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
        
        # Academic degrees and qualifications
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
        
        # Academic honors and distinctions
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
        
        # Section headers for identifying education sections
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

        # Keywords for education-related content
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

        # Date extraction patterns
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

    # MAIN EXTRACTION METHODS
    def extract_education(self, text: str, parsed_sections: Dict[str, List[str]] = None) -> List[Dict]:
        """Extract detailed education information from text."""
        education_data = []
        current_entry = None
        
        education_lines = []
        used_fallback = False
        
        if parsed_sections and 'education' in parsed_sections:
            section_lines = [line.strip() for line in parsed_sections['education'] if line.strip()]
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
            else:
                used_fallback = True
        
        if (not parsed_sections or not 'education' in parsed_sections) and (not education_lines or used_fallback):
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

        if not education_lines and not parsed_sections:
            text_lines = text.split('\n')
            for line in text_lines:
                if any(keyword in line.lower() for keyword in ['university', 'college', 'bachelor', 'master', 'phd', 'degree', 'diploma']):
                    if not any(keyword in line.lower() for keyword in ['experience', 'skill', 'project']):
                        education_lines.append(line.strip())

        if education_lines:
            for line in education_lines:
                if not line or any(re.search(pattern, line, re.IGNORECASE) for pattern in self.section_headers['education']):
                    continue
                
                if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', line, re.IGNORECASE):
                    continue
                
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
                
                if self._is_coursework(line):
                    current_entry['descriptions'].append(line)
                elif self.has_degree(line) and not current_entry['degree']:
                    current_entry['degree'] = self._clean_degree(line)
                else:
                    if not current_entry['gpa']:
                        gpa = self._extract_gpa_from_description(line)
                        if gpa:
                            current_entry['gpa'] = gpa
                            continue
                    
                    if not current_entry['date']:
                        date = self.extract_date(line)
                        if date:
                            current_entry['date'] = date
                            continue
                    
                    if len(line.split()) > 2:
                        current_entry['descriptions'].append(line)
            
            if current_entry and (current_entry['school'] or current_entry['degree']):
                current_entry['descriptions'] = self._clean_descriptions(current_entry['descriptions'])
                education_data.append(current_entry)
        
        cleaned_data = []
        for entry in education_data:
            if entry.get('school') and any(keyword in entry['school'].lower() for keyword in ['html', 'css', 'javascript', 'sql', 'windows', 'linux', 'http']):
                continue
            
            if not entry.get('school') and not entry.get('degree'):
                continue
            
            if not entry.get('school') and not entry.get('degree') and entry.get('descriptions'):
                for desc in entry['descriptions']:
                    if any(keyword in desc.lower() for keyword in ['university', 'college', 'institute', 'school']):
                        parts = desc.split(',', 1)
                        entry['school'] = parts[0].strip()
                        if len(parts) > 1:
                            entry['degree'] = parts[1].strip()
                        break
            
            if entry.get('school') or entry.get('degree'):
                cleaned_data.append(entry)
        
        return cleaned_data if cleaned_data else []

    def extract_education_descriptions(self, text: str) -> List[str]:
        """Extract detailed education descriptions using NLP and dependency parsing."""
        doc = self.nlp(text)
        descriptions = []

        action_verbs = {'study', 'graduate', 'complete', 'attend', 'enroll', 'achieve', 'earn', 'obtain'}

        for sent in doc.sents:
            for token in sent:
                if token.dep_ in {'ROOT', 'advcl', 'xcomp'} and token.lemma_ in action_verbs:
                    descriptions.append(sent.text.strip())
                    break

            if any(ent.label_ in {'ORG', 'DATE', 'PERSON'} for ent in sent.ents):
                descriptions.append(sent.text.strip())

            if re.match(r'^[•*-]\s*', sent.text) or re.match(r'^\d+\.', sent.text):
                clean_description = sent.text.strip().lstrip('-•* ')
                if clean_description:
                    descriptions.append(clean_description)

        return descriptions

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            is_section_header = any(keyword in line.lower() for keyword in section_keywords)
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

    def extract_honors(self, text: str) -> List[str]:
        """Extract academic honors and awards."""
        honors = []
        
        for honor in self.HONORS:
            if re.search(r'\b' + re.escape(honor) + r'\b', text, re.IGNORECASE):
                honors.append(honor.title())
        
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

    # HELPER METHODS FOR EXTRACTION
    def extract_gpa(self, text: str) -> Optional[str]:
        """Extract GPA or grade information from text."""
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "CARDINAL" and re.match(r'^[0-5]\.\d{1,2}$', ent.text):
                return ent.text
        
        gpa_patterns = [
            r'GPA:?\s*([\d\.]+)(?:/[\d\.]+)?',
            r'(?:Note|Grade):\s*([\w\.]+)',
            r'([\d\.]+)\s*/\s*[\d\.]+',
            r'([\d,]+)/20',
            r'([\d,]+)/10',
            r'Grade:\s*(A\+?|B\+?|C\+?|D\+?|F)',
        ]
        
        for pattern in gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grade = match.group(1)
                grade = grade.replace(',', '.')
                
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
        """Extract date from text."""
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
        """Extract date range from text with support for ongoing education."""
        doc = self.nlp(text)
        
        ongoing_patterns = [
            r'(?:current|ongoing|present|now)',
            r'\b(?:studying|enrolled|pursuing)\b',
            r'(?:expected|anticipated|planned)\s+(?:graduation|completion).*?(\d{4})',
        ]
        
        for pattern in ongoing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    return f"{self.extract_date(text)} to {match.group(1)}"
                return f"{self.extract_date(text)} to Present"

        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        if date_entities:
            return ' to '.join(date_entities)

        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' to '.join(matches)

        return None

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

    # VALIDATION AND CLEANING METHODS
    def has_school(self, text: str) -> bool:
        """Check if text contains a school name."""
        if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', text, re.IGNORECASE):
            return False
            
        if text.strip().startswith(('•', '-', '*')):
            return False
            
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'FAC'} and any(school.lower() in ent.text.lower() for school in self.SCHOOLS):
                return True
        
        text_lower = text.lower()
        return any(school.lower() in text_lower for school in self.SCHOOLS)

    def has_degree(self, text: str) -> bool:
        """Check if text contains a degree."""
        if re.search(r'\b(?:HTML5?|CSS|JavaScript|Node\.js|SQL|SAP|Windows|Linux|Mac|Office)\b', text, re.IGNORECASE):
            return False
            
        if text.strip().startswith(('•', '-', '*')):
            return False
            
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

    def _validate_section_data(self, section_lines: List[str]) -> bool:
        """Validate if the section data is meaningful and contains education information."""
        if not section_lines:
            return False
        
        education_indicators = [
            r'\b(?:University|College|Institute|School|Academy)\b',
            r'\b(?:Bachelor|Master|PhD|BSc|MSc|BA|MA|MBA|BBA)\b',
            r'\b(?:Degree|Diploma|Certificate)\b',
            r'\b(?:Major|Minor|Specialization)\b',
            r'\b(?:Education|Study|Studies)\b',
            r'(?:Computer Science|Engineering|Informatics)\b'
        ]
        
        has_education_content = False
        for line in section_lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in education_indicators):
                has_education_content = True
                break
                
        return has_education_content

    def _clean_school_name(self, text: str) -> Tuple[str, str, str]:
        """Clean and separate school name from degree and GPA information."""
        text = re.sub(r'^[-•*]\s*', '', text.strip())
        text = re.sub(r'^\d{4}\s*[-–]\s*\d{4}:\s*', '', text)
        text = re.sub(r'^\d{4}\s*[-–]\s*(?:Present|Current|Now):\s*', '', text)
        text = re.sub(r'^\d{4}:\s*', '', text)
        
        gpa = ''
        gpa_match = re.search(r'(?:GPA|Grade|CGPA):\s*([\d\.]+)\s*(?:/\s*[\d\.]+)?', text, re.IGNORECASE)
        if gpa_match:
            gpa = gpa_match.group(1)
            text = text.replace(gpa_match.group(0), '').strip()
        
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
            if any(keyword in text.lower() for keyword in ['university', 'college', 'institute', 'school']):
                school_name = text
                degree = ''
            else:
                school_name = ''
                degree = text
        
        school_name = re.sub(r'\s*\([^)]*\)', '', school_name)
        school_name = re.sub(r'\s+,.*$', '', school_name)
        school_name = school_name.strip(' -,')
        
        if degree:
            degree = re.sub(r'\s*\(\s*\)', '', degree)
            degree = re.sub(r'\s*\([^)]*\)', '', degree)
            degree = degree.strip(' -,')
        
        return school_name, degree, gpa

    def _clean_degree(self, text: str) -> str:
        """Clean and normalize degree information."""
        text = re.sub(r'^[-•*]\s*', '', text.strip())
        text = re.sub(r'^\d{4}\s*[-–]\s*\d{4}:\s*', '', text)
        text = re.sub(r'^\d{4}\s*[-–]\s*(?:Present|Current|Now):\s*', '', text)
        text = re.sub(r'^\d{4}:\s*', '', text)
        text = re.sub(r'(?i)relevant\s+coursework:.*$', '', text)
        text = re.sub(r'(?i)courses?:.*$', '', text)
        text = re.sub(r'(?i)(?:GPA|Grade):\s*[\d\.]+\s*(?:/\s*[\d\.]+)?', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*,\s*$', '', text)
        text = re.sub(r'\s*-\s*$', '', text)
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
            desc = re.sub(r'^[-•*]\s*', '', desc.strip())
            
            if re.match(r'^[\d\s\-–/\.]+$', desc):
                continue
                
            if re.match(r'^[A-Za-z\s,]+$', desc) and len(desc.split()) <= 3:
                continue
                
            if any(d.strip() == desc.strip() for d in cleaned):
                continue
                
            cleaned.append(desc)
        
        return cleaned