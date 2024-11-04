import re
from typing import Dict, List, Optional

class EducationExtractor:
    def __init__(self):
        # Constants for both English and Hungarian keywords
        self.SCHOOLS = [
            # English
            'College', 'University', 'Institute', 'School', 'Academy', 'BASIS', 'Magnet',
            # Hungarian
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        self.DEGREES = [
            # English
            'Associate', 'Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'BA', 'MS', 'MSc', 'MBA',
            'Diploma', 'Engineer', 'Technician',
            # Hungarian
            'Mrnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés'
        ]
        
        self.section_headers = {
            'education': ['education', 'academic background', 'qualifications', 'academic qualifications']
        }

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
        return any(school.lower() in text.lower() for school in self.SCHOOLS)
    
    def has_degree(self, text: str) -> bool:
        return any(degree.lower() in text.lower() for degree in self.DEGREES) or \
               bool(re.match(r'[ABM][A-Z\.]', text))
    
    def extract_gpa(self, text: str) -> Optional[str]:
        # Support both English and Hungarian grade formats
        gpa_match = re.search(r'GPA:?\s*([\d\.]+)', text, re.IGNORECASE)
        grade_match = re.search(r'(?:Note|Jegy|Minősítés):\s*([\w]+)', text, re.IGNORECASE)
        
        if gpa_match:
            return gpa_match.group(1)
        elif grade_match:
            grade = grade_match.group(1)
            # Convert Hungarian grades if needed
            grade_map = {
                'excellent': '5.0',
                'kitűnő': '5.0',
                'jeles': '5.0',
                'good': '4.0',
                'jó': '4.0',
                'satisfactory': '3.0',
                'közepes': '3.0'
            }
            return grade_map.get(grade.lower(), grade)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        # Support both English and Hungarian date formats
        date_patterns = [
            r'(?:19|20)\d{2}',  # Year
            r'\d{2}\.\d{2}\.\d{4}',  # Hungarian format
            r'\d{4}/\d{2}/\d{2}',  # Alternative format
            r'\d{2}/\d{2}/\d{4}'   # Alternative format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                # Extract just the year if it's a full date
                year = re.search(r'(19|20)\d{2}', match.group(0))
                return year.group(0) if year else match.group(0)
        return None

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information."""
        education_data = []
        current_entry = None
        
        # Extract education section using section_headers
        education_lines = self.extract_section(text, self.section_headers['education'])
        
        if education_lines:
            for line in education_lines:
                # Skip section headers
                if any(header in line.lower() for header in self.section_headers['education']):
                    continue
                
                # Start new entry if school or significant education keyword found
                if self.has_school(line) or any(keyword in line.lower() for keyword in ['diploma', 'érettségi', 'final exam', 'leaving exam']):
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        education_data.append(current_entry)
                    
                    current_entry = {
                        'school': line if self.has_school(line) else '',
                        'degree': '',
                        'gpa': '',
                        'date': self.extract_date(line) or '',
                        'descriptions': []
                    }
                    continue
                
                if current_entry is None:
                    current_entry = {
                        'school': '',
                        'degree': '',
                        'gpa': '',
                        'date': '',
                        'descriptions': []
                    }
                
                # Extract degree
                if self.has_degree(line) and not current_entry['degree']:
                    current_entry['degree'] = line
                    gpa = self.extract_gpa(line)
                    if gpa:
                        current_entry['gpa'] = gpa
                    continue
                
                # Extract date if not found
                if not current_entry['date']:
                    date = self.extract_date(line)
                    if date:
                        current_entry['date'] = date
                        continue
                
                # Extract GPA if not found
                if not current_entry['gpa']:
                    gpa = self.extract_gpa(line)
                    if gpa:
                        current_entry['gpa'] = gpa
                        continue
                
                # Add to descriptions
                if line not in [current_entry['school'], current_entry['degree']]:
                    current_entry['descriptions'].append(line)
            
            # Don't forget to add the last entry
            if current_entry and (current_entry['school'] or current_entry['degree']):
                education_data.append(current_entry)
        
        # Clean up entries
        for entry in education_data:
            entry['descriptions'] = [
                desc for desc in entry['descriptions']
                if desc and not any([
                    desc == entry['school'],
                    desc == entry['degree'],
                    self.extract_date(desc) == entry['date'],
                    self.extract_gpa(desc) == entry['gpa']
                ])
            ]
        
        return education_data if education_data else [{
            'school': '',
            'degree': '',
            'gpa': '',
            'date': '',
            'descriptions': []
        }]