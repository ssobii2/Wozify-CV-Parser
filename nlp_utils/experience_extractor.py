import re
from typing import Dict, List, Optional

class ExperienceExtractor:
    def __init__(self, nlp_en):
        """Initialize ExperienceExtractor with spaCy model and define constants."""
        self.nlp = nlp_en
        
        # Section headers for identifying experience sections
        self.section_headers = {
            'experience': [
                'experience', 'work experience', 'employment history', 'work history', 
                'professional experience', 'job experience', 'career history', 
                'previous employment', 'past roles', 'work background', 'employment record', 
                'work experiences', 'project experience', 'job history', 'work roles', 
                'employment details', 'career path', 'job history records', 'work life', 
                'job background', 'employment experiences', 'career experiences'
            ]
        }
        
        # Job title indicators
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead', 'internship',
            'intern', 'trainee', 'administrator', 'supervisor',
            'software engineer', 'data scientist', 'data analyst', 'product manager',
            'project manager', 'business analyst', 'quality assurance', 'devops engineer',
            'system architect', 'network engineer', 'database administrator', 'web developer',
            'mobile developer', 'UI/UX designer', 'technical writer', 'cloud engineer',
            'security analyst', 'IT support', 'solutions architect', 'research scientist',
            'game developer', 'full stack developer', 'backend developer', 'frontend developer', 'front-end developer', 'back-end developer',
            'machine learning engineer', 'AI engineer', 'blockchain developer', 'site reliability engineer',
            'digital marketing specialist', 'SEO specialist', 'content strategist', 'product designer',
            'application support', 'technical support', 'business intelligence analyst', 'data engineer',
            'CRM specialist', 'ERP consultant', 'e-commerce manager', 'social media manager'
        ]
        
        # Base company indicators
        self.company_indicators = ['inc', 'ltd', 'llc', 'corp', 'gmbh']
        
        # Extended company indicators
        self.company_indicators.extend([
            'ag', 'kft', 'zrt', 'nyrt', 'bt', 'rt', 'plc', 'sa', 'nv', 'oy',
            'ab', 'as', 'spa', 'bv', 'company', 'group', 'solutions', 
            'technologies', 'systems', 'software', 'consulting', 'services',
            'international', 'global', 'digital', 'tech',
            # Additional Hungarian indicators
            'zrt', 'kft', 'bt', 'nyrt', 'kft.', 'zrt.', 'bt.', 'nyrt.', 'kft', 'zrt', 
            # Common indicators from around the world
            'inc', 'corp', 'ltd', 'plc', 'gmbh', 'sarl', 'pty', 'llc', 'ag', 'sa', 
            'oy', 'nv', 'ab', 'as', 'spa', 'bv', 'group', 'solutions', 'technologies', 
            'systems', 'software', 'consulting', 'services', 'international', 'global', 
            'digital', 'tech', 'limited', 'company', 'enterprise', 'firm', 'business', 
            'association', 'foundation', 'organization', 'cooperative', 'trust', 
            'consortium', 'partnership', 'joint venture', 'agency', 'network', 
            'platform', 'group', 'services', 'ventures', 'development', 'holdings'
        ])

        # Date extraction patterns
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

    # SECTION EXTRACTION METHODS
    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords and NLP context."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        doc = self.nlp(text)

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

    # DATE HANDLING METHODS
    def extract_date_range(self, text: str) -> Optional[str]:
        """Extract date range from text using NLP and regex patterns."""
        doc = self.nlp(text)
        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']

        if date_entities:
            standardized_dates = [self._standardize_date(date) for date in date_entities]
            return ' to '.join(standardized_dates)

        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                standardized_dates = [self._standardize_date(match) for match in matches]
                return ' to '.join(standardized_dates)

        return None

    def _standardize_date(self, date_str: str) -> str:
        """Standardize date format to DD/MM/YYYY."""
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11',
            'dec': '12'
        }
        
        season_map = {
            'spring': '03', 'summer': '06', 'fall': '09', 'autumn': '09', 'winter': '12'
        }
        
        date_str = date_str.lower().strip()
        
        if any(word in date_str.lower() for word in ['present', 'current', 'now']):
            from datetime import datetime
            today = datetime.now()
            return f"{today.day:02d}/{today.month:02d}/{today.year}"
        
        year_match = re.search(r'\d{4}', date_str)
        if not year_match:
            return date_str
        
        year = year_match.group()
        
        for season, month in season_map.items():
            if season in date_str:
                return f"01/{month}/{year}"
        
        for month_name, month_num in month_map.items():
            if month_name in date_str:
                day_match = re.search(r'\b(\d{1,2})\b', date_str)
                day = day_match.group() if day_match else '01'
                return f"{int(day):02d}/{month_num}/{year}"
        
        numeric_match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', date_str)
        if numeric_match:
            day, month, year = numeric_match.groups()
            if int(month) <= 12 and int(day) > 12:
                day, month = month, day
            return f"{int(day):02d}/{int(month):02d}/{year}"
        
        return f"01/01/{year}"

    # TEXT CLEANING METHODS
    def _clean_description(self, text: str) -> str:
        """Clean and standardize description text."""
        text = re.sub(r'^[•\-\*\⚬\○\●\■\□\▪\▫]\s*', '', text.strip())
        text = re.sub(r'^\d+\.\s*', '', text)
        text = ' '.join(text.split())
        
        if text and len(text) > 3 and text[0].isalpha():
            text = text[0].upper() + text[1:]
        
        return text

    def _clean_text(self, text: str) -> str:
        """Clean and standardize general text."""
        text = re.sub(r'^[•\-\*\⚬\○\●\■\□\▪\▫]\s*', '', text.strip())
        text = re.sub(r'^\d+\.\s*', '', text)
        return ' '.join(text.split())

    # ENTITY RECOGNITION METHODS
    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name using NLP and heuristics."""
        if len(text.split()) > 8 or len(text.split()) < 1:
            return False
        
        skip_phrases = [
            'responsible for', 'worked on', 'developed', 'managed', 'led', 
            'using', 'including', 'working with', 'supporting', 'maintaining'
        ]
        if any(phrase in text.lower() for phrase in skip_phrases):
            return False

        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                return True

        text_lower = text.lower()
        if any(f" {indicator}" in f" {text_lower}" for indicator in self.company_indicators):
            return True
        
        if text.istitle() or text.isupper():
            if (not any(indicator in text_lower for indicator in self.job_indicators) and 
                len(text.split()) > 1):
                return True
        
        return False

    def is_valid_company_structure(self, text: str) -> bool:
        """Check if the text has a valid company name structure."""
        doc = self.nlp(text)

        if text[0].isupper():
            for token in doc:
                if token.pos_ in {'VERB', 'ADP'}:
                    return False

            if len(text.split()) > 5:
                return False

            return True
        return False

    def is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        if len(text.split()) > 6:
            return False
        
        skip_phrases = ['company', 'ltd', 'inc', 'corp', 'responsible for', 'using']
        if any(phrase in text.lower() for phrase in skip_phrases):
            return False

        job_patterns = [
            r'\b(?:Sr|Jr|Senior|Junior|Lead|Chief|Head|Principal)\b.*?(?:Developer|Engineer|Architect|Manager|Designer)',
            r'\b(?:Full[- ]Stack|Front[- ]End|Back[- ]End|Software|Web|Mobile|Cloud|DevOps)\b.*?(?:Developer|Engineer|Architect)',
            r'\b(?:Development|Engineering|Technical|Technology|Product|Project)\b.*?(?:Manager|Lead|Director|Coordinator)'
        ]

        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in self.job_indicators):
            return True
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in job_patterns):
            return True

        return False

    def is_relevant_description(self, text: str) -> bool:
        """Determine if a sentence is a relevant work experience description."""
        action_verbs = {
            'developed', 'managed', 'led', 'designed', 'implemented', 'created', 'improved',
            'optimized', 'coordinated', 'supervised', 'maintained', 'analyzed', 'established',
            'launched', 'built', 'achieved', 'increased', 'reduced', 'streamlined', 'automated',
            'collaborated', 'initiated', 'organized', 'planned', 'executed', 'delivered',
            'supported', 'trained', 'mentored', 'researched', 'resolved', 'enhanced',
            'generated', 'facilitated', 'monitored', 'evaluated', 'tested', 'deployed',
            'orchestrated', 'directed', 'enhanced', 'formulated', 'spearheaded', 'executed',
            'drove', 'cultivated', 'influenced', 'championed', 'navigated', 'streamlined',
            'contributed', 'implemented', 'co-created', 'innovated', 'transformed', 'optimized',
            'enhanced', 'maximized', 'restructured', 'revamped', 'modernized', 'pioneered',
            'coordinated', 'facilitated', 'mentored', 'trained', 'guided', 'advised', 'consulted',
            'collaborated', 'partnered', 'networked', 'engaged', 'interfaced', 'communicated',
            'articulated', 'documented', 'reported', 'analyzed', 'assessed', 'evaluated',
            'validated', 'synthesized', 'compiled', 'produced', 'crafted', 'designed', 'engineered'
        }
        
        tech_terms = {
            'project', 'system', 'software', 'application', 'database', 'platform',
            'infrastructure', 'framework', 'api', 'service', 'solution', 'tool',
            'technology', 'process', 'methodology', 'architecture', 'code', 'development',
            'deployment', 'integration', 'testing', 'maintenance', 'support', 'analysis',
            'design', 'implementation', 'optimization', 'scalability', 'performance',
            'security', 'user experience', 'interface', 'database management', 'cloud',
            'virtualization', 'automation', 'monitoring', 'configuration', 'scripting',
            'debugging', 'version control', 'repository', 'collaboration', 'agile',
            'scrum', 'devops', 'continuous integration', 'continuous deployment', 'microservices'
        }
        
        text_lower = text.lower()
        has_action_verb = any(verb in text_lower for verb in action_verbs)
        has_tech_term = any(term in text_lower for term in tech_terms)
        has_metrics = bool(re.search(r'\d+%|\d+\s*percent|\$\d+|\d+\s*users|\d+\s*clients', text_lower))
        has_project_content = bool(re.search(r'team|client|stakeholder|project|product|deadline|milestone', text_lower))
        
        return (has_action_verb or has_metrics or 
                (has_tech_term and has_project_content) or
                (len(text.split()) > 5 and (has_tech_term or has_project_content)))

    # EXPERIENCE EXTRACTION METHODS
    def extract_work_experience(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract detailed work experience information."""
        try:
            work_data = []
            current_entry = None
            
            if parsed_sections and parsed_sections.get('experience'):
                experience_sections = parsed_sections.get('experience', [])
                experience_lines = []
                
                if isinstance(experience_sections, list):
                    for section in experience_sections:
                        if isinstance(section, str):
                            lines = re.split(r'(?:\n|(?<=\s)(?:[•\-\*\⚬\○\●\■\□\▪\▫]|\d+\.)\s*)', section)
                            experience_lines.extend([self._clean_description(line) for line in lines if line and line.strip()])
                elif isinstance(experience_sections, str):
                    lines = re.split(r'(?:\n|(?<=\s)(?:[•\-\*\⚬\○\●\■\□\▪\▫]|\d+\.)\s*)', experience_sections)
                    experience_lines.extend([self._clean_description(line) for line in lines if line and line.strip()])
                
                for i, line in enumerate(experience_lines):
                    if not line or re.match(r'(?i)^(work\s+experience|experience|employment|professional\s+background|work\s+history)$', line):
                        continue
                    
                    date = self.extract_date_range(line)
                    
                    if date:
                        if current_entry:
                            work_data.append(current_entry)
                        
                        current_entry = {
                            'company': '',
                            'job_title': '',
                            'date': date,
                            'descriptions': []
                        }
                        
                        for j in range(max(0, i-2), min(i+2, len(experience_lines))):
                            context_line = experience_lines[j].strip()
                            if not context_line or context_line == line:
                                continue
                                
                            if self.extract_date_range(context_line):
                                continue
                                
                            if not current_entry['job_title'] and self.is_likely_job_title(context_line):
                                current_entry['job_title'] = self._clean_text(context_line)
                            elif not current_entry['company'] and self.is_likely_company(context_line):
                                current_entry['company'] = self._clean_text(context_line)
                            elif not current_entry['company'] and self.is_valid_company_structure(context_line):
                                current_entry['company'] = self._clean_text(context_line)
                    elif current_entry:
                        cleaned_line = self._clean_description(line)
                        if len(cleaned_line) > 20:
                            if self.extract_date_range(cleaned_line):
                                continue
                                
                            if not current_entry['job_title'] and self.is_likely_job_title(cleaned_line):
                                current_entry['job_title'] = self._clean_text(cleaned_line)
                            elif not current_entry['company'] and self.is_likely_company(cleaned_line):
                                current_entry['company'] = self._clean_text(cleaned_line)
                            elif not current_entry['company'] and self.is_valid_company_structure(cleaned_line):
                                current_entry['company'] = self._clean_text(cleaned_line)
                            else:
                                current_entry['descriptions'].append(cleaned_line)
                
                if current_entry:
                    work_data.append(current_entry)
                
                if work_data:
                    return self._clean_work_data(work_data)
                
            return self.fallback_extract_descriptions(text)
            
        except Exception as e:
            print(f"Error in extract_work_experience: {str(e)}")
            return []

    def _process_descriptions(self, descriptions: List[str], current_entry: Dict) -> List[str]:
        """Process descriptions to extract any company names or job titles and clean the list."""
        cleaned_descriptions = []
        
        for desc in descriptions:
            doc = self.nlp(desc)
            
            org_found = False
            for ent in doc.ents:
                if ent.label_ == 'ORG' and not current_entry['company']:
                    current_entry['company'] = self._clean_text(ent.text)
                    org_found = True
                    desc = desc.replace(ent.text, '').strip()
            
            if not current_entry['job_title']:
                for token in doc:
                    if token.pos_ == 'NOUN' and any(x in token.text.lower() for x in self.job_indicators):
                        phrase = []
                        for t in token.subtree:
                            if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                                phrase.append(t.text)
                        if phrase:
                            potential_title = self._clean_text(' '.join(phrase))
                            if len(potential_title.split()) <= 5:
                                current_entry['job_title'] = potential_title
                                desc = desc.replace(' '.join(phrase), '').strip()
            
            if len(desc.split()) > 3 and self.is_relevant_description(desc):
                cleaned_descriptions.append(desc)
        
        return cleaned_descriptions

    def _clean_work_data(self, work_data: List[Dict]) -> List[Dict]:
        """Clean and validate the extracted work experience data."""
        cleaned_data = []
        date_entries = {}
        
        for entry in work_data:
            if entry.get('descriptions'):
                date = entry.get('date', '')
                descriptions = self._process_descriptions(entry['descriptions'], entry)
                
                seen = set()
                descriptions = [
                    desc for desc in descriptions
                    if desc and desc not in seen and not seen.add(desc)
                ]
                
                if descriptions:
                    if date in date_entries:
                        existing = date_entries[date]
                        if not existing['company'] and entry.get('company'):
                            existing['company'] = entry['company']
                        if not existing['job_title'] and entry.get('job_title'):
                            existing['job_title'] = entry['job_title']
                        
                        all_descriptions = existing['descriptions'] + descriptions
                        existing['descriptions'] = self._process_descriptions(all_descriptions, existing)
                    else:
                        date_entries[date] = {
                            'company': entry.get('company', ''),
                            'job_title': entry.get('job_title', ''),
                            'date': date,
                            'descriptions': descriptions
                        }
        
        cleaned_data = list(date_entries.values())
        return cleaned_data

    def fallback_extract_descriptions(self, text: str) -> List[Dict]:
        """Fallback method to extract descriptions using a simpler heuristic approach."""
        work_data = []
        current_entry = None
        
        work_pattern = r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY).*?(?=\n\s*(?:EDUCATION|SKILLS|PROJECTS|LANGUAGES|CERTIFICATIONS|INTERESTS|$))'
        work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if work_match:
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                if re.match(r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY)', line, re.IGNORECASE):
                    continue
                
                date = self.extract_date_range(line)
                
                if date:
                    if current_entry and current_entry.get('descriptions'):
                        work_data.append(current_entry)
                    
                    current_entry = {
                        'company': '',
                        'job_title': '',
                        'date': date,
                        'descriptions': []
                    }
                    
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
                    if line.startswith(('•', '-', '✓', '*')) or re.match(r'^\d+\.\s', line):
                        current_entry['descriptions'].append(line)
                    elif len(line) > 30 and not self.extract_date_range(line):
                        if not current_entry['job_title'] and self.is_likely_job_title(line):
                            current_entry['job_title'] = line
                        elif not current_entry['company'] and self.is_likely_company(line):
                            current_entry['company'] = line
                        elif not current_entry['company'] and self.is_valid_company_structure(line):
                            current_entry['company'] = line
                        else:
                            current_entry['descriptions'].append(line)
            
            if current_entry and current_entry.get('descriptions'):
                work_data.append(current_entry)
        
        return work_data
