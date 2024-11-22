import re
from typing import Dict, List, Optional
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
                        if ent.label_ in {'ORG', 'GPE', 'PRODUCT'}:
                            return True
                            
                    # Additional checks based on token attributes
                    noun_phrases = list(doc.noun_chunks)
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

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information."""
        if not text:
            return []

        work_data = []
        current_entry = None

        try:
            # Use regex for initial section extraction instead of NLP
            work_pattern = r'(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT).*?(?=\n\s*(?:TANULMÁNYOK|KÉSZSÉGEK|PROJEKTEK|NYELVEK|$))'
            work_match = re.search(work_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not work_match:
                return self.fallback_extract_descriptions(text)

            # Process the matched work section
            work_text = work_match.group(0)
            lines = [line.strip() for line in work_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Skip section headers
                if re.match(r'(?:MUNKATAPASZTALAT|SZAKMAI\s*TAPASZTALAT|TAPASZTALAT)', line, re.IGNORECASE):
                    continue

                try:
                    # Use regex-based date extraction first
                    date = None
                    for pattern in self.date_patterns:
                        date_match = re.search(pattern, line)
                        if date_match:
                            date = date_match.group(0)
                            break
                    
                    if date:
                        # Save previous entry if exists
                        if current_entry and current_entry.get('descriptions'):
                            work_data.append(current_entry)
                        
                        # Start new entry
                        current_entry = {
                            'company': '',
                            'job_title': '',
                            'date': date,
                            'descriptions': []
                        }
                        
                        # Look back a few lines for company and job title
                        for j in range(max(0, i-2), i):
                            prev_line = lines[j].strip()
                            if not prev_line:
                                continue

                            # Use pattern matching instead of NLP
                            if not current_entry['job_title']:
                                # Check for job title patterns
                                if any(indicator in prev_line.lower() for indicator in self.job_indicators):
                                    current_entry['job_title'] = prev_line
                                    continue
                                    
                            if not current_entry['company']:
                                # Check for company patterns
                                if (any(indicator in prev_line.lower() for indicator in self.company_indicators) or
                                    re.search(r'\b(?:Kft|Zrt|Bt|Nyrt)\b', prev_line, re.IGNORECASE)):
                                    current_entry['company'] = prev_line
                                    continue
                    
                    elif current_entry:
                        # Process current line
                        if not current_entry['company']:
                            # Check for company patterns
                            if (any(indicator in line.lower() for indicator in self.company_indicators) or
                                re.search(r'\b(?:Kft|Zrt|Bt|Nyrt)\b', line, re.IGNORECASE)):
                                current_entry['company'] = line
                                continue
                                
                        if not current_entry['job_title']:
                            # Check for job title patterns
                            if any(indicator in line.lower() for indicator in self.job_indicators):
                                current_entry['job_title'] = line
                                continue
                        
                        # If line doesn't match company or job patterns, add as description
                        current_entry['descriptions'].append(line)
                
                except Exception as entry_error:
                    logging.warning(f"Warning: Entry processing failed: {str(entry_error)}")
                    continue

            # Add the last entry if it exists
            if current_entry and current_entry.get('descriptions'):
                work_data.append(current_entry)

        except Exception as e:
            logging.warning(f"Warning: Work experience extraction failed: {str(e)}")
            return self.fallback_extract_descriptions(text)

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
