import re
from typing import Dict, List, Optional, Tuple

class ExperienceExtractorHu:
    def __init__(self, nlp_hu):
        """Initialize ExperienceExtractorHu with spaCy model and define constants."""
        self.nlp_hu = nlp_hu
        
        # Section headers for identifying experience sections
        self.section_headers = {
            'experience': [
                'munkatapasztalat', 'szakmai tapasztalat', 'munkatörténet', 'korábbi munkák',
                'tapasztalat', 'foglalkoztatási előzmények', 'szakmai előzmények', 'projektek', 
                'szakmai gyakorlat', 'munkahely'
            ]
        }
        
        # Job title indicators
        self.job_indicators = [
            'fejlesztő', 'mérnök', 'menedzser', 'tanácsadó', 'elemző', 'szakértő', 
            'koordinátor', 'asszisztens', 'igazgató', 'vezető', 'gyakornok', 
            'képzés alatt álló', 'adminisztrátor', 'felügyelő', 'informatikus', 
            'projektmenedzser', 'programozó', 'munkatárs', 'rendszergazda'
        ]
        
        # Company indicators
        self.company_indicators = ['kft', 'zrt', 'bt', 'nyrt', 'ltd', 'gmbh']

        # Date patterns for Hungarian date extraction
        self.date_patterns = [
            r'\d{4}\.\s*(?:január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)\s*\d{1,2}\.?',
            r'\d{2}\.\d{2}\.\d{4}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{4}',
            r'\d{4}\s*-\s*\d{4}',
            r'\d{4}\.\s*-\s*\d{4}\.'
        ]

    # MAIN EXTRACTION METHODS
    def extract_work_experience(self, text: str, parsed_sections: Optional[Dict] = None) -> List[Dict]:
        """Extract work experience entries from text."""
        try:
            if parsed_sections and 'experience' in parsed_sections and parsed_sections['experience']:
                work_data = []
                for section in parsed_sections['experience']:
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
                
                if not work_data:
                    return self._extract_work_experience_fallback(text)
                    
                return work_data

            return self._extract_work_experience_fallback(text)

        except Exception as e:
            return self._extract_work_experience_fallback(text)

    def _extract_work_experience_fallback(self, text: str) -> List[Dict]:
        """Fallback method for extracting work experience when main method fails."""
        if not text:
            return []

        work_data = []
        current_entry = None

        try:
            work_pattern = r'(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT)[\s:]*.*?(?=\n\s*(?:TANULMÁNYOK|KÉPZETTSÉG|VÉGZETTSÉG|KÉPESSÉGEK|KÉSZSÉGEK|PROJEKTEK|NYELVEK|EGYÉB|$))'
            
            work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not work_match:
                date_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
                dates = re.finditer(date_pattern, text)
                date_positions = [m.start() for m in dates]
                
                if date_positions:
                    start_pos = max(0, date_positions[0] - 100)
                    work_text = text[start_pos:]
                else:
                    return []
            else:
                work_text = work_match.group(0)

            work_text = self.clean_text(work_text)
            doc = self.nlp_hu(work_text)
            
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

            for entry_text in entries:
                entry_doc = self.nlp_hu(entry_text)
                
                date = self._extract_date(entry_text)
                if not date:
                    continue
                    
                current_entry = {
                    'company': '',
                    'job_title': '',
                    'date': date,
                    'descriptions': []
                }

                main_clauses = []
                for sent in entry_doc.sents:
                    for token in sent:
                        if token.dep_ == 'ROOT':
                            clause = ' '.join([t.text for t in token.subtree])
                            if clause not in main_clauses:
                                main_clauses.append(clause)

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

                for clause in main_clauses:
                    cleaned = self.clean_text(clause)
                    if (cleaned and 
                        cleaned not in [current_entry['company'], current_entry['job_title']] and
                        len(cleaned.split()) > 3):
                        current_entry['descriptions'].append(cleaned)

                if current_entry['company'] or current_entry['job_title']:
                    work_data.append(current_entry)

        except Exception as e:
            print(f"Experience extraction failed: {str(e)}")
            return []

        return work_data

    def fallback_extract_descriptions(self, text: str) -> List[str]:
        """Fallback method to extract work descriptions when structured extraction fails."""
        descriptions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not self.is_likely_company(line) and not self.is_likely_job_title(line):
                if len(line.split()) > 3:
                    descriptions.append(line)
        
        return descriptions

    # SECTION AND ENTRY PARSING METHODS
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

    def _split_into_entries(self, text: str) -> List[str]:
        """Split text into experience entries."""
        entries = []
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        
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
        
        if not entries:
            entries = [e.strip() for e in re.split(r'\s*[•▪■⚫●\-]\s*', text) if e.strip()]
        
        return entries

    def _parse_entry_parts(self, text: str) -> Tuple[str, str, List[str]]:
        """Parse entry text into company, job title and descriptions using NLP."""
        company = ''
        job_title = ''
        descriptions = []
        
        try:
            cleaned_text = self.clean_text(text)
            doc = self.nlp_hu(cleaned_text)
            
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    company = self.clean_text(ent.text)
                    break
            
            for token in doc:
                if token.pos_ == 'NOUN' and any(x in token.text.lower() for x in self.job_indicators):
                    phrase = []
                    for t in token.subtree:
                        if t.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                            phrase.append(t.text)
                    if phrase:
                        potential_title = self.clean_text(' '.join(phrase))
                        if len(potential_title.split()) <= 5:
                            job_title = potential_title
                            break
            
            for sent in doc.sents:
                sent_text = self.clean_text(sent.text)
                if (sent_text and 
                    sent_text not in [company, job_title] and
                    len(sent_text.split()) > 3):
                    descriptions.append(sent_text)
            
        except Exception as e:
            print(f"Experience extraction failed: {str(e)}")
            pass
        
        return company, job_title, descriptions

    # DATE EXTRACTION METHODS
    def extract_date_range(self, text: str) -> Optional[str]:
        """Extract date range from text using Hungarian NLP support."""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ' - '.join(matches)

        try:
            date_chunks = []
            lines = text.split('\n')
            for line in lines:
                if any(month in line.lower() for month in ['január', 'február', 'március', 'április', 'május', 'június', 'július', 'augusztus', 'szeptember', 'október', 'november', 'december']):
                    date_chunks.append(line)
                elif re.search(r'\d{4}|\d{2}\.\d{2}\.|\d{2}/\d{2}', line):
                    date_chunks.append(line)
            
            if date_chunks:
                doc = self.nlp_hu(' '.join(date_chunks[:3]))
                date_entities = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
                if date_entities:
                    return ' - '.join(date_entities)
        except Exception as e:
            print(f"Warning: NLP date extraction failed, falling back to regex: {str(e)}")
            pass

        return None

    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        year_pattern = r'(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|jelenleg|most|\?|…|\.{3})|(?:19|20)\d{2}\s*[-–]|(?:19|20)\d{2}'
        match = re.search(year_pattern, text)
        return match.group(0) if match else ''

    # ENTITY DETECTION AND VALIDATION METHODS
    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name."""
        if not text:
            return False

        if any(indicator in text.lower() for indicator in self.company_indicators):
            return True

        try:
            cleaned_text = text.strip()
            if not cleaned_text or len(cleaned_text) > 100:
                return False

            cleaned_text = re.sub(r'[^\w\s\-.,&]', '', cleaned_text)
            if not cleaned_text:
                return False

            chunks = [cleaned_text[i:i+50] for i in range(0, len(cleaned_text), 50)]
            
            for chunk in chunks:
                try:
                    doc = self.nlp_hu(chunk)
                    
                    for ent in doc.ents:
                        if ent.label_ in {'ORG'}:
                            return True
                            
                    noun_phrases = self.extract_noun_phrases(doc)
                    if len(noun_phrases) == 1 and len(doc) <= 5:
                        return True
                        
                except Exception as chunk_error:
                    continue

        except Exception as e:
            return any(indicator in text.lower() for indicator in self.company_indicators)

        return False

    def is_valid_company_structure(self, text: str) -> bool:
        """Check if the text has a valid company name structure."""
        if not text or not text[0].isupper():
            return False

        words = text.split()
        if len(words) > 5:
            return False

        if re.search(r'\b(?:Kft|Zrt|Bt|Nyrt)\b', text, re.IGNORECASE):
            return True

        try:
            cleaned_text = text.strip()
            if not cleaned_text or len(cleaned_text) > 100:
                return False
                
            cleaned_text = re.sub(r'[^\w\s\-.,&]', '', cleaned_text)
            if not cleaned_text:
                return False

            doc = self.nlp_hu(cleaned_text)
            
            for token in doc:
                if token.pos_ in {'VERB', 'ADP'}:
                    return False

            if all(word[0].isupper() for word in words):
                return True
            
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    return True

        except Exception as e:
            print(f"Warning: NLP company structure validation failed: {str(e)}")
            return any(indicator in text.lower() for indicator in self.company_indicators)

        return False

    def is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        return any(indicator in text.lower() for indicator in self.job_indicators)

    def _validate_section_data(self, lines: List[str]) -> bool:
        """Validate if the section data is sufficient for processing."""
        return len(lines) > 0

    # TEXT PROCESSING METHODS
    def extract_noun_phrases(self, doc):
        """Extract noun phrases using dependency parsing."""
        noun_phrases = []
        for token in doc:
            if token.dep_ == 'nsubj' or token.dep_ == 'dobj':
                noun_phrase = ' '.join([child.text for child in token.subtree])
                noun_phrases.append(noun_phrase)
        return noun_phrases

    def clean_text(self, text: str) -> str:
        """Clean text from special characters and unnecessary whitespace."""
        if not text:
            return ""
        
        text = re.sub(r'[•▪■⚫●\-]', '', text)
        text = re.sub(r'\([^)]*?(?<!\d{4})[^)]*?\)', '', text)
        text = re.sub(r'\[[^\]]*?\]', '', text)
        text = re.sub(r'[^\w\s\-áéíóöőúüűÁÉÍÓÖŐÚÜŰ]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()

    def _clean_entry_text(self, text: str, date: str) -> str:
        """Clean entry text by removing date and unnecessary characters."""
        text = text.replace(date, '').strip()
        text = re.sub(r'\s+', ' ', text)
        return text
