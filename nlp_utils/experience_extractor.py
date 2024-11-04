import re
from typing import Dict, List, Optional

class ExperienceExtractor:
    def __init__(self):
        self.section_headers = {
            'experience': ['experience', 'work experience', 'employment history', 'work history', 'professional experience']
        }
        
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor'
        ]
        
        self.company_indicators = ['inc', 'ltd', 'llc', 'corp', 'gmbh', 'kft', 'zrt', 'bt', 'nyrt']

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
        """Extract date range from text."""
        date_patterns = [
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.]*\d{4}\s*[-–]\s*(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.]*\d{4})',
            r'(?:20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|Present|Current|Now)',
            r'\d{1,2}/\d{4}\s*[-–]\s*(?:\d{1,2}/\d{4}|Present|Current|Now)',
            r'(?:Since|From|Starting)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.]*\d{4}',
            r'(?:Since|From|Starting)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def is_likely_company(self, text: str) -> bool:
        """Check if text is likely a company name."""
        # Check if it's a standalone line with reasonable length
        if len(text.split()) <= 5:
            # Check for company indicators
            if any(indicator in text.lower() for indicator in self.company_indicators):
                return True
            # Check if it's in Title Case (typical for company names)
            if text.istitle() or text.isupper():
                return True
            # Check if it ends with typical company suffixes
            if any(text.lower().endswith(suffix) for suffix in self.company_indicators):
                return True
        return False

    def is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        return any(indicator in text.lower() for indicator in self.job_indicators)

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information."""
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
                        else:
                            current_entry['descriptions'].append(line)
            
            # Add the last entry
            if current_entry and current_entry.get('descriptions'):
                work_data.append(current_entry)
        
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