import re
from typing import Dict, List, Optional
import spacy
from langdetect import detect, LangDetectException

class ExperienceExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'experience': ['experience', 'work experience', 'employment history', 'work history', 'professional experience']
        }
        
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor'
        ]
        
        self.company_indicators = ['inc', 'ltd', 'llc', 'corp', 'gmbh', 'kft', 'zrt', 'bt', 'nyrt']

    def get_nlp_model_for_text(self, text: str):
        """Determine the language of the text and return the appropriate spaCy NLP model."""
        try:
            language = detect(text)
            return self.nlp_hu if language == 'hu' else self.nlp_en
        except LangDetectException:
            return self.nlp_en

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
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)

        # Use spaCy's NER to find date entities
        date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']

        # If date entities are found, return them as a single string
        if date_entities:
            return ' to '.join(date_entities)

        # Fallback to regex for date ranges
        date_patterns = [
            r'(?:19|20)\d{2}',  # Year
            r'\d{2}\.\d{2}\.\d{4}',  # Hungarian format
            r'\d{4}/\d{2}/\d{2}',  # Alternative format
            r'\d{2}/\d{2}/\d{4}'   # Alternative format
        ]

        # Attempt to find date ranges using regex
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' to '.join(matches)

        return None

    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name using NLP and additional heuristics."""
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)

        # Use spaCy's NER to find organization entities
        for ent in doc.ents:
            if ent.label_ in {'ORG', 'GPE', 'PRODUCT'}:
                return True

        # Fallback to heuristic checks if no organization entities are found
        if len(text.split()) <= 5:
            if any(indicator in text.lower() for indicator in self.company_indicators):
                return True
            if text.istitle() or text.isupper():
                return True
            if any(text.lower().endswith(suffix) for suffix in self.company_indicators):
                return True

        # Additional pattern matching for common company structures
        if re.search(r'\b(?:Inc|Ltd|LLC|Corp|GmbH|Kft|Zrt|Bt|Nyrt)\b', text, re.IGNORECASE):
            return True

        return False
    
    def is_valid_company_structure(self, text: str) -> bool:
        """Check if the text has a valid company name structure."""
        # Determine the language and use the appropriate spaCy model
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)

        # Check if the text starts with a capital letter
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
        return any(indicator in text.lower() for indicator in self.job_indicators)

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information."""
        work_data = []
        current_entry = None
        
        # Updated regex pattern to capture the new format
        work_pattern = r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY|MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT).*?(?=\n\s*(?:EDUCATION|SKILLS|PROJECTS|LANGUAGES|CERTIFICATIONS|INTERESTS|TANULMÁNYOK|KÉSZSÉGEK|PROJEKTEK|NYELVEK|$))'
        work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if work_match:
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Skip section headers
                if re.match(r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY|MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT)', line, re.IGNORECASE):
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
                    
                    # Look for company and job title in the next lines
                    for j in range(max(0, i-2), i):
                        prev_line = lines[j].strip()
                        if not current_entry['job_title'] and self.is_likely_job_title(prev_line):
                            current_entry['job_title'] = prev_line
                        elif not current_entry['company'] and self.is_likely_company(prev_line):
                            # Clean the company name by stripping dashes or bullet points
                            current_entry['company'] = prev_line.lstrip('-•* ')
                        elif not current_entry['company'] and self.is_valid_company_structure(prev_line):
                            # Clean the company name by stripping dashes or bullet points
                            current_entry['company'] = prev_line.lstrip('-•* ')
                    continue
                
                if current_entry:
                    # New approach: Use NLP and context to extract descriptions
                    nlp = self.get_nlp_model_for_text(line)
                    doc = nlp(line)
                    for sent in doc.sents:
                        if self.is_relevant_description(sent.text):
                            # Strip bullet points or dashes from the description
                            clean_description = sent.text.strip().lstrip('-•* ')
                            if clean_description:  # Check if the description is not empty
                                current_entry['descriptions'].append(clean_description)
                    
                    # Handle bullet points
                    if line.startswith(('-', '•', '*')) or re.match(r'^\d+\.', line):
                        clean_description = line.strip().lstrip('-•* ')
                        if clean_description:  # Check if the description is not empty
                            current_entry['descriptions'].append(clean_description)
            
            # Add the last entry
            if current_entry and current_entry.get('descriptions'):
                work_data.append(current_entry)
        
        # Fallback: Use the current approach if no descriptions are found
        if not work_data:
            work_data = self.fallback_extract_descriptions(text)
        
        # Clean up entries - ensure job titles are not empty
        for entry in work_data:
            if not entry['job_title']:
                # Try to extract job title from descriptions if available
                for desc in entry['descriptions']:
                    if self.is_likely_job_title(desc):
                        entry['job_title'] = desc
                        entry['descriptions'].remove(desc)
                        break
        
        return work_data if work_data else [{
            'company': '',
            'job_title': '',
            'date': '',
            'descriptions': []
        }]

    def is_relevant_description(self, text: str) -> bool:
        """Determine if a sentence is a relevant work experience description."""
        # Implement logic to determine if a sentence is relevant
        # For example, check if it contains action verbs or specific keywords
        action_verbs = {'developed', 'managed', 'led', 'designed', 'implemented', 'created', 'improved', 'optimized'}
        return any(verb in text.lower() for verb in action_verbs)

    def fallback_extract_descriptions(self, text: str) -> List[Dict]:
        """Fallback method to extract descriptions using a simpler heuristic approach."""
        work_data = []
        current_entry = None
        
        # Extract work experience section
        work_pattern = r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY|MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT).*?(?=\n\s*(?:EDUCATION|SKILLS|PROJECTS|LANGUAGES|CERTIFICATIONS|INTERESTS|TANULMÁNYOK|KÉSZSÉGEK|PROJEKTEK|NYELVEK|$))'
        work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if work_match:
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Skip section headers
                if re.match(r'(?:WORK\s*EXPERIENCE|EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s*BACKGROUND|WORK\s*HISTORY|MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT)', line, re.IGNORECASE):
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

    def extract_experience_descriptions(self, text: str) -> List[str]:
        """Extract detailed experience descriptions using NLP and dependency parsing."""
        nlp = self.get_nlp_model_for_text(text)
        doc = nlp(text)
        descriptions = []

        for sent in doc.sents:
            # Use dependency parsing to find verbs related to work activities
            for token in sent:
                if token.dep_ in {'ROOT', 'advcl', 'xcomp'} and token.lemma_ in {'develop', 'manage', 'lead', 'design', 'implement', 'create', 'improve', 'optimize', 'coordinate'}:
                    descriptions.append(sent.text.strip())
                    break

            # Check for entities that are typically associated with work experience
            if any(ent.label_ in {'ORG', 'DATE', 'PERSON', 'GPE'} for ent in sent.ents):
                descriptions.append(sent.text.strip())

        return descriptions