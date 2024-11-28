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
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
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
        work_data = []
        current_entry = None
        
        # Try to use parsed sections first if available
        if parsed_sections and parsed_sections.get('experience'):
            experience_lines = []
            for section in parsed_sections['experience']:
                experience_lines.extend([line.strip() for line in section.split('\n') if line.strip()])
            
            if self._validate_section_data(experience_lines):
                return self._process_experience_lines(experience_lines)
            print("Parsed section data invalid or insufficient, using fallback")
        
        # Fallback to regex-based extraction
        work_pattern = r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY).*?(?=\n\s*(?:EDUCATION|SKILLS|PROJECTS|LANGUAGES|CERTIFICATIONS|INTERESTS|$))'
        work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if work_match:
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            return self._process_experience_lines(lines)
        
        return [{
            'company': '',
            'job_title': '',
            'date': '',
            'descriptions': []
        }]

    def _validate_section_data(self, lines: List[str]) -> bool:
        """Validate that the section data contains meaningful experience information."""
        if not lines:
            return False
        
        # Check for presence of dates
        has_dates = any(self.extract_date_range(line) for line in lines)
        
        # Check for presence of job titles
        has_job_titles = any(self.is_likely_job_title(line) for line in lines)
        
        # Check for presence of companies
        has_companies = any(self.is_likely_company(line) for line in lines)
        
        # Check for presence of descriptions
        has_descriptions = any(len(line) > 30 and not any(keyword in line.lower() 
            for keyword in ['education', 'skills', 'projects', 'languages']) 
            for line in lines)
        
        return has_dates and (has_job_titles or has_companies) and has_descriptions

    def _process_experience_lines(self, lines: List[str]) -> List[Dict]:
        """Process experience lines into structured data."""
        work_data = []
        current_entry = None
        
        # First pass: identify main entry points and structure
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip section headers and empty lines
            if (re.match(r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY)', 
                line, re.IGNORECASE) or not line.strip()):
                continue
            
            # Look for date ranges as primary entry points
            date = self.extract_date_range(line)
            
            # If we find a date, it's likely a new experience entry
            if date:
                # Save previous entry if it exists and has required fields
                if current_entry and current_entry.get('descriptions'):
                    if current_entry.get('job_title') or current_entry.get('company'):
                        work_data.append(current_entry)
                
                # Initialize new entry
                current_entry = {
                    'company': '',
                    'job_title': '',
                    'date': date,
                    'descriptions': []
                }
                
                # Look for job titles and companies in surrounding context
                context_start = max(0, i-3)  # Look up to 3 lines before
                context_end = min(len(lines), i+2)  # Look up to 2 lines after
                
                # First try to find job title, then company
                for j in range(context_start, context_end):
                    if j == i:  # Skip the date line itself
                        continue
                    
                    context_line = lines[j].strip().lstrip('-•* ')
                    
                    # Skip if line is too short, contains a date, or is a section header
                    if (len(context_line) < 3 or 
                        self.extract_date_range(context_line) or 
                        any(header in context_line.lower() for header in 
                            ['education', 'skills', 'languages', 'projects'])):
                        continue
                    
                    # First try to identify job title
                    if not current_entry['job_title'] and self.is_likely_job_title(context_line):
                        current_entry['job_title'] = context_line
                        continue
                    
                    # Then try to identify company
                    if not current_entry['company'] and self.is_likely_company(context_line):
                        current_entry['company'] = context_line
                        continue
                
                continue
            
            # If we have a current entry, process the line
            if current_entry:
                clean_line = line.strip().lstrip('-•* ')
                
                # Skip empty lines and section headers
                if not clean_line or any(header in clean_line.lower() for header in 
                    ['education', 'skills', 'languages', 'projects']):
                    continue
                
                # If line is a bullet point or starts with action verb, it's likely a description
                if (clean_line.startswith(('•', '-', '✓', '*', '→')) or 
                    re.match(r'^\d+\.', clean_line) or
                    any(verb in clean_line.lower() for verb in [
                        'developed', 'managed', 'led', 'created', 'implemented',
                        'designed', 'improved', 'built', 'maintained', 'responsible',
                        'achieved', 'increased', 'reduced', 'supported', 'coordinated'
                    ])):
                    if len(clean_line) > 10:  # Minimum meaningful length
                        current_entry['descriptions'].append(clean_line)
                    continue
                
                # If not a description, try to identify missing job title or company
                if not current_entry['job_title'] and self.is_likely_job_title(clean_line):
                    current_entry['job_title'] = clean_line
                elif not current_entry['company'] and self.is_likely_company(clean_line):
                    current_entry['company'] = clean_line
                elif len(clean_line) > 10:  # If still not identified, add as description
                    current_entry['descriptions'].append(clean_line)
        
        # Add the last entry if it exists and has required fields
        if current_entry and current_entry.get('descriptions'):
            if current_entry.get('job_title') or current_entry.get('company'):
                work_data.append(current_entry)
        
        # Post-process entries
        processed_data = []
        for entry in work_data:
            # Clean up entries
            cleaned_entry = {
                'company': entry.get('company', '').strip().rstrip(',.:;'),
                'job_title': entry.get('job_title', '').strip().rstrip(',.:;'),
                'date': entry.get('date', ''),
                'descriptions': []
            }
            
            # Clean and deduplicate descriptions
            seen_descriptions = set()
            for desc in entry.get('descriptions', []):
                desc = desc.strip().rstrip(',.:;')
                if (len(desc) > 10 and  # Minimum meaningful length
                    desc.lower() not in seen_descriptions and  # Not a duplicate
                    not self.is_likely_job_title(desc) and  # Not a job title
                    not self.is_likely_company(desc)):  # Not a company name
                    cleaned_entry['descriptions'].append(desc)
                    seen_descriptions.add(desc.lower())
            
            # Only add entries that have required fields
            if ((cleaned_entry['job_title'] or cleaned_entry['company']) and 
                cleaned_entry['descriptions']):
                processed_data.append(cleaned_entry)
        
        return processed_data if processed_data else [{
            'company': '',
            'job_title': '',
            'date': '',
            'descriptions': []
        }]

    def is_relevant_description(self, text: str) -> bool:
        """Determine if a sentence is a relevant work experience description."""
        action_verbs = {'developed', 'managed', 'led', 'designed', 'implemented', 'created', 'improved', 'optimized'}
        return any(verb in text.lower() for verb in action_verbs)

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
