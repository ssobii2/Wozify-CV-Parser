import re
from typing import Dict, List, Optional, Tuple
import spacy
from langdetect import detect, LangDetectException
import logging

class ExperienceExtractorHu:
    def __init__(self, nlp_hu):
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'experience': [
                'munkatapasztalat', 'szakmai tapasztalat', 'munkatörténet', 'korábbi munkák',
                'tapasztalat', 'foglalkoztatási előzmények', 'szakmai előzmények', 'projektek', 'szakmai gyakorlat', 'munkahely'
            ]
        }
        
        self.job_indicators = [
            'fejlesztő', 'mérnök', 'menedzser', 'tanácsadó', 'elemző', 'szakértő', 'koordinátor', 'asszisztens', 'igazgató', 'vezető',
            'gyakornok', 'képzés alatt álló', 'adminisztrátor', 'felügyelő', 'informatikus', 'projektmenedzser', 'programozó', 'munkatárs', 'rendszergazda'
        ]
        
        self.company_indicators = ['kft', 'zrt', 'bt', 'nyrt', 'ltd', 'gmbh']

        # Define date patterns for Hungarian date extraction
        self.date_patterns = [
            r'\d{4}\.\s*(?:január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)\s*\d{1,2}\.?',  # 2014. január 1.
            r'\d{2}\.\d{2}\.\d{4}',  # Hungarian format DD.MM.YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{4}',  # Year only
            r'\d{4}\s*-\s*\d{4}',  # Year range
            r'\d{4}\.\s*-\s*\d{4}\.'  # Hungarian year range
        ]

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract a section from text based on keywords and NLP context."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        doc = self.nlp_hu(text)

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
                    for keyword in ['oktatás', 'képzés', 'készségek', 'projektek', 'nyelvek']
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
        """Extract date range from text using Hungarian NLP support."""
        # First try regex-based extraction as it's more reliable for date formats
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' - '.join(matches)

        # If no matches found with regex, try NLP as fallback
        try:
            # Process a smaller chunk of text around potential dates
            # Look for text chunks that might contain dates (numbers and months)
            date_chunks = []
            lines = text.split('\n')
            for line in lines:
                if any(month in line.lower() for month in ['január', 'február', 'március', 'április', 'május', 'június', 'július', 'augusztus', 'szeptember', 'október', 'november', 'december']):
                    date_chunks.append(line)
                elif re.search(r'\d{4}|\d{2}\.\d{2}\.|\d{2}/\d{2}', line):
                    date_chunks.append(line)
            
            if date_chunks:
                # Only process the relevant chunks with NLP
                doc = self.nlp_hu(' '.join(date_chunks[:3]))  # Limit to first 3 chunks to prevent memory issues
                date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
                if date_entities:
                    return ' - '.join(date_entities)
        except Exception as e:
            print(f"Warning: NLP date extraction failed, falling back to regex: {str(e)}")
            pass  # Continue with regex fallback if NLP fails

        return None

    def extract_noun_phrases(self, doc):
        """Extract noun phrases using dependency parsing."""
        noun_phrases = []
        for token in doc:
            if token.dep_ == 'nsubj' or token.dep_ == 'dobj':
                noun_phrase = ' '.join([child.text for child in token.subtree])
                noun_phrases.append(noun_phrase)
        return noun_phrases

    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name."""
        if not text:
            return False

        # First check for company indicators - this is fast and safe
        if any(indicator in text.lower() for indicator in self.company_indicators):
            return True

        try:
            # Basic text cleaning
            cleaned_text = text.strip()
            if not cleaned_text or len(cleaned_text) > 100:  # Skip empty or very long text
                return False

            # Remove problematic characters but keep essential ones for company names
            cleaned_text = re.sub(r'[^\w\s\-.,&]', '', cleaned_text)
            if not cleaned_text:
                return False

            # Split into chunks if text is too long
            chunks = [cleaned_text[i:i+50] for i in range(0, len(cleaned_text), 50)]
            
            for chunk in chunks:
                try:
                    # Process with NLP
                    doc = self.nlp_hu(chunk)
                    
                    # Check for organization entities
                    for ent in doc.ents:
                        if ent.label_ in {'ORG'}:
                            return True
                            
                    # Use custom noun phrase extraction
                    noun_phrases = self.extract_noun_phrases(doc)
                    if len(noun_phrases) == 1 and len(doc) <= 5:
                        # Single noun phrase with reasonable length could be a company
                        return True
                        
                except Exception as chunk_error:
                    logging.warning(f"Warning: Chunk processing failed: {str(chunk_error)}")
                    continue

        except Exception as e:
            logging.warning(f"Warning: Company name validation failed: {str(e)}")
            # Fall back to basic pattern matching
            return any(indicator in text.lower() for indicator in self.company_indicators)

        # If we get here, no strong indicators of a company name were found
        return False

    def is_valid_company_structure(self, text: str) -> bool:
        """Check if the text has a valid company name structure."""
        # Basic checks first
        if not text or not text[0].isupper():
            return False

        # Check text length and basic structure
        words = text.split()
        if len(words) > 5:  # Company names are typically not longer than 5 words
            return False

        # Check for common company suffixes first
        if re.search(r'\b(?:Kft|Zrt|Bt|Nyrt)\b', text, re.IGNORECASE):
            return True

        try:
            # Basic text cleaning
            cleaned_text = text.strip()
            if not cleaned_text or len(cleaned_text) > 100:  # Skip empty or very long text
                return False
                
            # Remove problematic characters but keep essential ones for company names
            cleaned_text = re.sub(r'[^\w\s\-.,&]', '', cleaned_text)
            if not cleaned_text:
                return False

            # Process with NLP
            doc = self.nlp_hu(cleaned_text)
            
            # Check for verbs or prepositions which are unlikely in company names
            for token in doc:
                if token.pos_ in {'VERB', 'ADP'}:
                    return False

            # Additional structural checks
            if all(word[0].isupper() for word in words):  # All words start with uppercase
                return True
            
            # Check if it looks like an organization name
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    return True

        except Exception as e:
            print(f"Warning: NLP company structure validation failed: {str(e)}")
            # Fall back to basic checks
            # If it starts with uppercase and contains a company indicator, consider it valid
            return any(indicator in text.lower() for indicator in self.company_indicators)

        return False

    def is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        return any(indicator in text.lower() for indicator in self.job_indicators)

    def clean_text(self, text: str) -> str:
        """Clean text from special characters and unnecessary whitespace."""
        if not text:
            return ""
        
        # Remove bullet points and similar markers
        text = re.sub(r'[•▪■⚫●\-]', '', text)
        
        # Remove brackets and parentheses with their content if they don't contain years
        text = re.sub(r'\([^)]*?(?<!\d{4})[^)]*?\)', '', text)
        text = re.sub(r'\[[^\]]*?\]', '', text)
        
        # Remove special characters but keep Hungarian letters
        text = re.sub(r'[^\w\s\-áéíóöőúüűÁÉÍÓÖŐÚÜŰ]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def extract_work_experience(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract work experience entries from text."""
        try:
            # Try main extraction first
            if parsed_sections and 'experience' in parsed_sections and parsed_sections['experience']:
                work_data = []
                for section in parsed_sections['experience']:
                    # Changed _parse_entries to _split_into_entries
                    entries = self._split_into_entries(section)
                    for entry in entries:
                        if entry.strip():
                            date = self._extract_date(entry)
                            if date:
                                entry_text = self._clean_entry_text(entry, date)
                                company, job_title, descriptions = self._parse_entry_parts(entry_text)
                                
                                exp_entry = {
                                    'company': company.strip(),
                                    'job_title': job_title.strip(),
                                    'date': date.strip(),
                                    'descriptions': descriptions
                                }
                                
                                if exp_entry['company'] or exp_entry['job_title']:
                                    work_data.append(exp_entry)
                
                # If main extraction returned empty results, try fallback
                if not work_data:
                    return self._extract_work_experience_fallback(text)
                    
                return work_data

            # If no parsed sections or empty experience section, use fallback
            return self._extract_work_experience_fallback(text)

        except Exception as e:
            logging.warning(f"Experience extraction failed: {str(e)}, trying fallback")
            return self._extract_work_experience_fallback(text)

    def _split_into_entries(self, text: str) -> List[str]:
        """Split text into experience entries."""
        # First try to split by year patterns
        entries = []
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        
        # Split by year pattern first
        parts = re.split(f'({year_pattern})', text)
        
        current_entry = ''
        for i, part in enumerate(parts):
            if re.match(year_pattern, part):
                if current_entry:
                    entries.append(current_entry.strip())
                current_entry = part
            else:
                current_entry += part
            
        if current_entry:
            entries.append(current_entry.strip())
        
        # If no entries found by year, try bullet points
        if not entries:
            entries = [e.strip() for e in re.split(r'\s*[•▪■⚫●\-]\s*', text) if e.strip()]
        
        return entries

    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        match = re.search(year_pattern, text)
        return match.group(0) if match else ''

    def _clean_entry_text(self, text: str, date: str) -> str:
        """Clean entry text by removing date and unnecessary characters."""
        text = text.replace(date, '').strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def _parse_entry_parts(self, text: str) -> Tuple[str, str, List[str]]:
        """Parse entry text into company, job title and descriptions using NLP."""
        company = ''
        job_title = ''
        descriptions = []
        
        try:
            # Clean and process text with NLP
            cleaned_text = self.clean_text(text)
            doc = self.nlp_hu(cleaned_text)
            
            # First try NER for company names
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    company = self.clean_text(ent.text)
                    break
            
            # Try to identify job title using dependency parsing
            for token in doc:
                # Look for noun phrases that could be job titles
                if token.pos_ == 'NOUN' and any(x in token.text.lower() for x in self.job_indicators):
                    # Get the full noun phrase by looking at token's children
                    phrase = []
                    for t in token.subtree:
                        # Only include relevant parts of speech
                        if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                            phrase.append(t.text)
                    if phrase:
                        potential_title = self.clean_text(' '.join(phrase))
                        if len(potential_title.split()) <= 5:  # Keep reasonable length
                            job_title = potential_title
                            break
            
            # Extract descriptions using sentence boundaries
            for sent in doc.sents:
                sent_text = self.clean_text(sent.text)
                if (sent_text and 
                    sent_text not in [company, job_title] and
                    len(sent_text.split()) > 3):
                    descriptions.append(sent_text)
            
        except Exception as e:
            logging.warning(f"NLP parsing failed: {str(e)}")
            pass
        
        return company, job_title, descriptions

    def _validate_section_data(self, lines: List[str]) -> bool:
        """Validate if the section data is sufficient for processing."""
        return len(lines) > 0

    def _extract_work_experience_fallback(self, text: str) -> List[Dict]:
        """Fallback method to extract work experience using NLP."""
        if not text:
            return []

        work_data = []
        current_entry = None

        try:
            # Modified pattern to be more flexible
            work_pattern = r'(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT)[\s:]*.*?(?=\n\s*(?:TANULMÁNYOK|KÉPZETTSÉG|VÉGZETTSÉG|KÉPESSÉGEK|KÉSZSÉGEK|PROJEKTEK|NYELVEK|EGYÉB|$))'
            
            # Try to find experience section
            work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not work_match:
                # Existing date-based fallback...
                date_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
                dates = re.finditer(date_pattern, text)
                date_positions = [m.start() for m in dates]
                
                if date_positions:
                    # Take text from first date to end or next major section
                    start_pos = max(0, date_positions[0] - 100)  # Include some context before date
                    work_text = text[start_pos:]
                else:
                    return []
            else:
                work_text = work_match.group(0)

            # Rest of the processing remains the same...
            work_text = self.clean_text(work_text)
            doc = self.nlp_hu(work_text)
            
            # Group text into entries using dates as markers
            entries = []
            current_text = []
            
            for sent in doc.sents:
                sent_text = self.clean_text(sent.text)
                if self._extract_date(sent_text):
                    if current_text:
                        entries.append('\n'.join(current_text))
                    current_text = [sent_text]
                else:
                    current_text.append(sent_text)
            
            if current_text:
                entries.append('\n'.join(current_text))

            # Process each entry
            for entry_text in entries:
                entry_doc = self.nlp_hu(entry_text)
                
                # Extract date
                date = self._extract_date(entry_text)
                if not date:
                    continue
                    
                # Initialize entry
                current_entry = {
                    'company': '',
                    'job_title': '',
                    'date': date,
                    'descriptions': []
                }

                # Use dependency parsing to find main clauses
                main_clauses = []
                for sent in entry_doc.sents:
                    for token in sent:
                        if token.dep_ == 'ROOT':
                            clause = ' '.join([t.text for t in token.subtree])
                            if clause not in main_clauses:
                                main_clauses.append(clause)

                # Look for organizations and job titles
                for ent in entry_doc.ents:
                    if ent.label_ == 'ORG' and not current_entry['company']:
                        current_entry['company'] = self.clean_text(ent.text)

                for token in entry_doc:
                    if token.pos_ == 'NOUN' and any(x in token.text.lower() for x in self.job_indicators):
                        phrase = []
                        for t in token.subtree:
                            if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                                phrase.append(t.text)
                        if phrase:
                            potential_title = self.clean_text(' '.join(phrase))
                            if len(potential_title.split()) <= 5:
                                current_entry['job_title'] = potential_title
                                break

                # Add remaining text as descriptions
                for clause in main_clauses:
                    cleaned = self.clean_text(clause)
                    if (cleaned and 
                        cleaned not in [current_entry['company'], current_entry['job_title']] and
                        len(cleaned.split()) > 3):
                        current_entry['descriptions'].append(cleaned)

                if current_entry['company'] or current_entry['job_title']:
                    work_data.append(current_entry)

        except Exception as e:
            logging.warning(f"Fallback extraction failed: {str(e)}")
            return []

        return work_data

    def fallback_extract_descriptions(self, text: str) -> List[str]:
        """Fallback method to extract work descriptions when structured extraction fails."""
        descriptions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not self.is_likely_company(line) and not self.is_likely_job_title(line):
                if len(line.split()) > 3:  # Ensure the line has meaningful content
                    descriptions.append(line)
        
        return descriptions
