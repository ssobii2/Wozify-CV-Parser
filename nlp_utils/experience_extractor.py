import re
from typing import Dict, List, Optional
import spacy

class ExperienceExtractor:
    def __init__(self, nlp_en):
        self.nlp = nlp_en
        self.section_headers = {
            'experience': [
                'experience', 'work experience', 'employment history', 'work history', 
                'professional experience', 'job experience', 'career history', 
                'previous employment', 'past roles', 'work background', 'employment record', 'work experiences', 'project experience'
            ]
        }
        
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead', 'internship',
            'intern', 'trainee', 'administrator', 'supervisor'
        ]
        
        self.company_indicators = ['inc', 'ltd', 'llc', 'corp', 'gmbh']

        # Define date patterns for date extraction
        self.date_patterns = [
            r'(Jan(?:uary)? \d{4} - (?:Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?) \d{4})',  # Jan 2014 - Feb 2015
            r'(Summer|Fall|Winter|Spring) \d{4}',  # Summer 2012
            r'\d{1,2} (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),? \d{4}',  # 1 January, 2014
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}',  # Year only
            r'\d{4}/\d{2}/\d{2}',  # Alternative format
            r'\d{2}/\d{2}/\d{4}'   # Alternative format
        ]

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords and NLP context."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        # Use NLP model to process the text
        doc = self.nlp(text)

        for sent in doc.sents:
            line = sent.text.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line contains a section header
            is_section_header = any(keyword in line.lower() for keyword in section_keywords)
            
            # Check if next line is a different section
            is_next_different_section = False
            if sent.nbor(1) is not None:  # Check if there is a next sentence
                next_line = sent.nbor(1).text.strip()
                is_next_different_section = any(
                    keyword in next_line.lower() 
                    for keyword in ['education', 'skills', 'projects', 'languages']
                )
            
            if is_section_header:
                in_section = True
                continue
            
            if in_section and is_next_different_section:
                in_section = False
            
            if in_section:
                section_lines.append(line)
        
        return section_lines

    def extract_date_range(self, text: str) -> Optional[str]:
        """Extract date range from text using NLP for language support."""
        doc = self.nlp(text)

        # Use spaCy's NER to find date entities
        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']

        # If date entities are found, return them as a single string
        if date_entities:
            return ' to '.join(date_entities)

        # Attempt to find date ranges using regex
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' to '.join(matches)  # Return the raw matches without normalization

        return None

    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name using NLP and additional heuristics."""
        # Skip if text is too long or too short
        if len(text.split()) > 8 or len(text.split()) < 1:
            return False
        
        # Skip if text contains typical description phrases
        skip_phrases = ['responsible for', 'worked on', 'developed', 'managed', 'led', 'using', 'including']
        if any(phrase in text.lower() for phrase in skip_phrases):
            return False

        doc = self.nlp(text)

        # Use spaCy's NER to find organization entities
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'GPE', 'PRODUCT'}:
                return True
        # Fallback to heuristic checks if no organization entities are found
        text_lower = text.lower()
        
        # Check for company legal suffixes
        if any(indicator in text_lower for indicator in self.company_indicators):
            return True
        
        # Check for capitalization patterns typical of company names
        if text.istitle() or text.isupper():
            # But exclude job titles
            if not any(indicator in text_lower for indicator in self.job_indicators):
                return True
            
        # Check for company-specific patterns
        company_patterns = [
            r'\b(?:Inc|Ltd|LLC|Corp|GmbH|Co|Company|Group|Solutions|Technologies|Systems)\b',
            r'\b(?:Software|Consulting|Services|International|Global|Digital|Tech)\b'
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in company_patterns):
            return True

        return False

    def is_valid_company_structure(self, text: str) -> bool:
        """Check if the text has a valid company name structure."""
        doc = self.nlp(text)

        if text[0].isupper():
            # Check for the presence of verbs or prepositions which are unlikely in company names
            for token in doc:
                if token.pos_ in {'VERB', 'ADP'}:  # ADP is for adpositions (prepositions)
                    return False

            # Additional check: Ensure the text is not overly descriptive
            if len(text.split()) > 5:
                return False

            return True
        return False

    def is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        # Skip if text is too long or contains typical non-title phrases
        if len(text.split()) > 6:
            return False
        
        skip_phrases = ['company', 'ltd', 'inc', 'corp', 'responsible for', 'using']
        if any(phrase in text.lower() for phrase in skip_phrases):
            return False

        # Extended job indicators
        extended_indicators = self.job_indicators + [
            'architect', 'designer', 'programmer', 'administrator', 'technician',
            'officer', 'executive', 'founder', 'head', 'chief', 'president',
            'vp', 'vice president', 'principal', 'senior', 'junior', 'associate',
            'full-stack', 'frontend', 'backend', 'software', 'web', 'mobile',
            'data', 'system', 'network', 'cloud', 'devops', 'qa', 'test'
        ]

        # Check for job title patterns
        job_patterns = [
            r'\b(?:Sr|Jr|Senior|Junior|Lead|Chief|Head|Principal)\b.*?(?:Developer|Engineer|Architect|Manager|Designer)',
            r'\b(?:Full[- ]Stack|Front[- ]End|Back[- ]End|Software|Web|Mobile|Cloud|DevOps)\b.*?(?:Developer|Engineer|Architect)',
            r'\b(?:Development|Engineering|Technical|Technology|Product|Project)\b.*?(?:Manager|Lead|Director|Coordinator)'
        ]

        text_lower = text.lower()
        
        # Check for job indicators
        if any(indicator in text_lower for indicator in extended_indicators):
            return True
        
        # Check for job title patterns
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in job_patterns):
            return True

        return False

    def extract_work_experience(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract detailed work experience information."""
        try:
            work_data = []
            current_entry = None
            
            # Check if we have experience data in parsed sections
            if parsed_sections and parsed_sections.get('experience'):
                experience_sections = parsed_sections.get('experience', [])
                experience_lines = []
                
                # Handle different possible formats of experience sections
                if isinstance(experience_sections, list):
                    for section in experience_sections:
                        if isinstance(section, str):
                            lines = re.split(r'(?:\n|(?<=\s)(?:[•\-\*\⚬\○\●\■\□\▪\▫]|\d+\.)\s*)', section)
                            experience_lines.extend([self._clean_description(line) for line in lines if line and line.strip()])
                elif isinstance(experience_sections, str):
                    lines = re.split(r'(?:\n|(?<=\s)(?:[•\-\*\⚬\○\●\■\□\▪\▫]|\d+\.)\s*)', experience_sections)
                    experience_lines.extend([self._clean_description(line) for line in lines if line and line.strip()])
                
                # Process the lines
                for i, line in enumerate(experience_lines):
                    # Skip empty lines and common section headers
                    if not line or re.match(r'(?i)^(work\s+experience|experience|employment|professional\s+background|work\s+history)$', line):
                        continue
                    
                    # Look for date ranges as primary entry points
                    date = self.extract_date_range(line)
                    
                    if date:
                        # Save previous entry if it exists
                        if current_entry:
                            work_data.append(current_entry)
                        
                        # Start new entry
                        current_entry = {
                            'company': '',
                            'job_title': '',
                            'date': date,
                            'descriptions': []
                        }
                        
                        # Look at surrounding lines for job title and company
                        for j in range(max(0, i-2), min(i+2, len(experience_lines))):
                            context_line = experience_lines[j].strip()
                            if not context_line or context_line == line:
                                continue
                                
                            # Skip if line contains a date
                            if self.extract_date_range(context_line):
                                continue
                                
                            # Try to identify job title first
                            if not current_entry['job_title'] and self.is_likely_job_title(context_line):
                                current_entry['job_title'] = self._clean_text(context_line)
                            # Then try to identify company
                            elif not current_entry['company'] and self.is_likely_company(context_line):
                                current_entry['company'] = self._clean_text(context_line)
                            elif not current_entry['company'] and self.is_valid_company_structure(context_line):
                                current_entry['company'] = self._clean_text(context_line)
                    elif current_entry:
                        # Process descriptions, removing bullets and standardizing format
                        cleaned_line = self._clean_description(line)
                        if len(cleaned_line) > 20:  # Minimum length for meaningful content
                            # Skip if line contains a date
                            if self.extract_date_range(cleaned_line):
                                continue
                                
                            # Try to identify missing job title or company
                            if not current_entry['job_title'] and self.is_likely_job_title(cleaned_line):
                                current_entry['job_title'] = self._clean_text(cleaned_line)
                            elif not current_entry['company'] and self.is_likely_company(cleaned_line):
                                current_entry['company'] = self._clean_text(cleaned_line)
                            elif not current_entry['company'] and self.is_valid_company_structure(cleaned_line):
                                current_entry['company'] = self._clean_text(cleaned_line)
                            else:
                                current_entry['descriptions'].append(cleaned_line)
                
                # Add the last entry
                if current_entry:
                    work_data.append(current_entry)
                
                # Return the work data if we have any entries
                if work_data:
                    return self._clean_work_data(work_data)
                
            # Only use fallback if no experience array exists or no entries were found
            print("No experience array found in parsed sections, using fallback")
            return self.fallback_extract_descriptions(text)
            
        except Exception as e:
            print(f"Error in extract_work_experience: {str(e)}")
            return []

    def _clean_description(self, text: str) -> str:
        """Clean and standardize description text."""
        # Remove bullet points and numbers at start
        text = re.sub(r'^[•\-\*\⚬\○\●\■\□\▪\▫]\s*', '', text.strip())
        text = re.sub(r'^\d+\.\s*', '', text)
        
        # Remove extra whitespace and standardize spacing
        text = ' '.join(text.split())
        
        # Capitalize first letter if it's a complete sentence
        if text and len(text) > 3 and text[0].isalpha():
            text = text[0].upper() + text[1:]
        
        return text

    def _clean_text(self, text: str) -> str:
        """Clean and standardize general text."""
        # Remove any bullet points or numbers
        text = re.sub(r'^[•\-\*\⚬\○\●\■\□\▪\▫]\s*', '', text.strip())
        text = re.sub(r'^\d+\.\s*', '', text)
        
        # Standardize spacing
        return ' '.join(text.split())

    def _clean_work_data(self, work_data: List[Dict]) -> List[Dict]:
        """Clean and validate the extracted work experience data."""
        cleaned_data = []
        for entry in work_data:
            if entry.get('descriptions'):
                # Remove duplicates while preserving order
                seen = set()
                entry['descriptions'] = [
                    desc for desc in entry['descriptions']
                    if desc and desc not in seen and not seen.add(desc)
                ]
                
                # Only include entries with meaningful content
                if entry['descriptions']:
                    cleaned_data.append({
                        'company': entry.get('company', ''),
                        'job_title': entry.get('job_title', ''),
                        'date': entry.get('date', ''),
                        'descriptions': entry['descriptions']
                    })
        
        return cleaned_data

    def is_relevant_description(self, text: str) -> bool:
        """Determine if a sentence is a relevant work experience description."""
        # Extended list of action verbs commonly found in work descriptions
        action_verbs = {
            'developed', 'managed', 'led', 'designed', 'implemented', 'created', 'improved',
            'optimized', 'coordinated', 'supervised', 'maintained', 'analyzed', 'established',
            'launched', 'built', 'achieved', 'increased', 'reduced', 'streamlined', 'automated',
            'collaborated', 'initiated', 'organized', 'planned', 'executed', 'delivered',
            'supported', 'trained', 'mentored', 'researched', 'resolved', 'enhanced',
            'generated', 'facilitated', 'monitored', 'evaluated', 'tested', 'deployed'
        }
        
        # Technical terms that indicate work-related content
        tech_terms = {
            'project', 'system', 'software', 'application', 'database', 'platform',
            'infrastructure', 'framework', 'api', 'service', 'solution', 'tool',
            'technology', 'process', 'methodology', 'architecture', 'code', 'development'
        }
        
        text_lower = text.lower()
        
        # Check for action verbs
        has_action_verb = any(verb in text_lower for verb in action_verbs)
        
        # Check for technical terms
        has_tech_term = any(term in text_lower for term in tech_terms)
        
        # Check for metrics or achievements
        has_metrics = bool(re.search(r'\d+%|\d+\s*percent|\$\d+|\d+\s*users|\d+\s*clients', text_lower))
        
        # Check for project or team-related content
        has_project_content = bool(re.search(r'team|client|stakeholder|project|product|deadline|milestone', text_lower))
        
        # Return True if the text contains meaningful work experience content
        return (has_action_verb or has_metrics or 
                (has_tech_term and has_project_content) or
                (len(text.split()) > 5 and (has_tech_term or has_project_content)))

    def fallback_extract_descriptions(self, text: str) -> List[Dict]:
        """Fallback method to extract descriptions using a simpler heuristic approach."""
        work_data = []
        current_entry = None
        
        # Extract work experience section
        work_pattern = r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY).*?(?=\n\s*(?:EDUCATION|SKILLS|PROJECTS|LANGUAGES|CERTIFICATIONS|INTERESTS|$))'
        work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if work_match:
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Skip section headers
                if re.match(r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY)', line, re.IGNORECASE):
                    continue
                
                # Look for date ranges
                date = self.extract_date_range(line)
                
                if date:
                    if current_entry and current_entry.get('descriptions'):
                        work_data.append(current_entry)
                    
                    # Initialize new entry with empty values
                    current_entry = {
                        'company': '',
                        'job_title': '',
                        'date': date,
                        'descriptions': []
                    }
                    
                    # Look at surrounding lines for job title and company
                    for j in range(max(0, i-2), i):
                        prev_line = lines[j].strip()
                        if not current_entry['job_title'] and self.is_likely_job_title(prev_line):
                            current_entry['job_title'] = prev_line
                        elif not current_entry['company'] and self.is_likely_company(prev_line):
                            current_entry['company'] = prev_line
                        elif not current_entry['company'] and self.is_valid_company_structure(prev_line):
                            current_entry['company'] = prev_line
                    continue
                
                if current_entry:
                    # Add bullet points and regular descriptions
                    if line.startswith(('•', '-', '✓', '*')) or re.match(r'^\d+\.\s', line):
                        current_entry['descriptions'].append(line)
                    elif len(line) > 30 and not self.extract_date_range(line):
                        # Check if this line might be a job title or company name
                        if not current_entry['job_title'] and self.is_likely_job_title(line):
                            current_entry['job_title'] = line
                        elif not current_entry['company'] and self.is_likely_company(line):
                            current_entry['company'] = line
                        elif not current_entry['company'] and self.is_valid_company_structure(line):
                            current_entry['company'] = line
                        else:
                            current_entry['descriptions'].append(line)
            
            # Add the last entry
            if current_entry and current_entry.get('descriptions'):
                work_data.append(current_entry)
        
        return work_data
