import re
import spacy
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Load the English language model with custom pipeline components
nlp = spacy.load('en_core_web_sm')

class CVExtractor:
    def __init__(self):
        self.date_patterns = [
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
            r'Dec(?:ember)?)\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}'
        ]
        
        self.section_headers = {
            'education': ['education', 'academic background', 'qualifications', 'academic qualifications'],
            'experience': ['experience', 'work experience', 'employment history', 'work history', 'professional experience'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
            'projects': ['projects', 'personal projects', 'key projects', 'professional projects'],
            'certifications': ['certifications', 'certificates', 'professional certifications'],
            'languages': ['languages', 'language skills'],
            'interests': ['interests', 'hobbies', 'activities'],
            'achievements': ['achievements', 'awards', 'honors', 'accomplishments'],
            'publications': ['publications', 'research', 'papers'],
            'references': ['references', 'referees']
        }
        
        # Remove skill categories and use a flat list of skills
        self.skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
            'kotlin', 'go', 'rust', 'typescript', 'scala', 'perl', 'r',
            'html', 'css', 'react', 'angular', 'vue', 'node', 'django', 'flask',
            'spring', 'asp.net', 'jquery', 'bootstrap', 'sass', 'less',
            'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis',
            'cassandra', 'elasticsearch', 'dynamodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'ansible', 'circleci', 'gitlab',
            'git', 'jira', 'confluence', 'slack', 'vscode', 'intellij', 'eclipse',
            'postman', 'webpack', 'npm', 'yarn'
        ]

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text using various patterns."""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information."""
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None,
            'website': None,
            'location': None
        }
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group(0)
        
        # Phone
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group(0)
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group(0)
        
        # GitHub
        github_pattern = r'github\.com/[\w-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            contact_info['github'] = github_match.group(0)
        
        # Website
        website_pattern = r'https?://(?:www\.)?[\w\.-]+\.[a-z]{2,}'
        website_match = re.search(website_pattern, text, re.IGNORECASE)
        if website_match:
            contact_info['website'] = website_match.group(0)
        
        return contact_info

    def extract_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract content from a specific section."""
        content = []
        lines = text.split('\n')
        in_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    content.append(' '.join(current_entry))
                    current_entry = []
                continue

            # Check if this line is a section header
            if any(keyword in line.lower() for keyword in section_keywords):
                in_section = True
                continue
            elif any(keyword in line.lower() for keywords in self.section_headers.values() for keyword in keywords):
                in_section = False
                if current_entry:
                    content.append(' '.join(current_entry))
                    current_entry = []
                continue

            if in_section:
                current_entry.append(line)

        if current_entry:
            content.append(' '.join(current_entry))

        return content

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text."""
        skills = []
        
        # Extract skills
        for skill in self.skills:
            if re.search(r'\b' + skill + r'\b', text, re.IGNORECASE):
                skills.append(skill)
        
        return sorted(set(skills))

    def extract_entities(self, text: str) -> Dict:
        """Main method to extract all information from CV."""
        # Initialize the result dictionary with all possible fields
        extracted_data = {
            'profile': self.extract_profile(text),
            'education': self.extract_education(text),
            'experience': self.extract_work_experience(text),
            'skills': self.extract_skills(text),
            'projects': [],
            'certifications': [],
            'languages': [],
            'interests': [],
            'achievements': [],
            'publications': [],
            'references': []
        }
        
        # Remove empty fields
        return {k: v for k, v in extracted_data.items() if v}

    def extract_current_position(self, text: str) -> str:
        """Extract the most recent job title from experience section."""
        # Look for current position indicators
        current_patterns = [
            r'(Present|Current|Now)',
            r'\b\d{4}\s*[-–]\s*(Present|Current|Now)\b'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Check if line contains current position indicators
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in current_patterns):
                # Look at previous line for job title
                if i > 0:
                    # Remove common words and clean up the title
                    title = lines[i-1].strip()
                    title = re.sub(r'\b(at|for|with)\b.*$', '', title, flags=re.IGNORECASE)
                    return title.strip()
        
        return "Professional"  # Default fallback

    def extract_education(self, text: str) -> List[Dict]:
        """Extract detailed education information."""
        
        # Constants and helper functions with both English and Hungarian keywords
        SCHOOLS = [
            # English
            'College', 'University', 'Institute', 'School', 'Academy', 'BASIS', 'Magnet',
            # Hungarian
            'Egyetem', 'Főiskola', 'Iskola', 'Gimnázium', 'Szakközépiskola', 'Technikum'
        ]
        
        DEGREES = [
            # English
            'Associate', 'Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'BA', 'MS', 'MSc', 'MBA',
            'Diploma', 'Engineer', 'Technician',
            # Hungarian
            'Mrnök', 'Diploma', 'Technikus', 'Érettségi', 'Szakképzés'
        ]
        
        def has_school(text: str) -> bool:
            return any(school.lower() in text.lower() for school in SCHOOLS)
        
        def has_degree(text: str) -> bool:
            return any(degree.lower() in text.lower() for degree in DEGREES) or \
                   bool(re.match(r'[ABM][A-Z\.]', text))
        
        def extract_gpa(text: str) -> Optional[str]:
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
        
        def extract_date(text: str) -> Optional[str]:
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
        
        education_data = []
        current_entry = None
        
        # Extract education section
        education_pattern = r'(?:EDUCATION|ACADEMIC|QUALIFICATIONS|TANULMÁNYOK|VÉGZETTSÉG).*?(?=\n\s*(?:EXPERIENCE|SKILLS|PROJECTS|PRACTICE|TAPASZTALAT|KÉSZSÉGEK|PROJEKTEK|$))'
        education_match = re.search(education_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if education_match:
            education_text = education_match.group(0)
            lines = [line.strip() for line in education_text.split('\n') if line.strip()]
            
            for line in lines:
                # Skip section headers
                if re.match(r'(?:EDUCATION|ACADEMIC|QUALIFICATIONS|TANULMÁNYOK|VÉGZETTSÉG)', line, re.IGNORECASE):
                    continue
                
                # Start new entry if school or significant education keyword found
                if has_school(line) or any(keyword in line.lower() for keyword in ['diploma', 'érettségi', 'final exam', 'leaving exam']):
                    if current_entry and (current_entry['school'] or current_entry['degree']):
                        education_data.append(current_entry)
                    
                    current_entry = {
                        'school': line if has_school(line) else '',
                        'degree': '',
                        'gpa': '',
                        'date': extract_date(line) or '',
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
                if has_degree(line) and not current_entry['degree']:
                    current_entry['degree'] = line
                    gpa = extract_gpa(line)
                    if gpa:
                        current_entry['gpa'] = gpa
                    continue
                
                # Extract date if not found
                if not current_entry['date']:
                    date = extract_date(line)
                    if date:
                        current_entry['date'] = date
                        continue
                
                # Extract GPA if not found
                if not current_entry['gpa']:
                    gpa = extract_gpa(line)
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
                    extract_date(desc) == entry['date'],
                    extract_gpa(desc) == entry['gpa']
                ])
            ]
        
        return education_data

    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract detailed work experience information."""
        
        def extract_date_range(text: str) -> Optional[str]:
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

        def is_likely_company(text: str) -> bool:
            company_indicators = ['inc', 'ltd', 'llc', 'corp', 'gmbh', 'kft', 'zrt', 'bt', 'nyrt']
            
            # Check if it's a standalone line with reasonable length
            if len(text.split()) <= 5:
                # Check for company indicators
                if any(indicator in text.lower() for indicator in company_indicators):
                    return True
                # Check if it's in Title Case (typical for company names)
                if text.istitle() or text.isupper():
                    return True
                # Check if it ends with typical company suffixes
                if any(text.lower().endswith(suffix) for suffix in company_indicators):
                    return True
            return False

        def is_likely_job_title(text: str) -> bool:
            job_indicators = [
                'developer', 'engineer', 'manager', 'consultant', 'analyst', 
                'specialist', 'coordinator', 'assistant', 'director', 'lead',
                'intern', 'trainee', 'administrator', 'supervisor'
            ]
            return any(indicator in text.lower() for indicator in job_indicators)

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
                date = extract_date_range(line)
                
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
                        if not current_entry['job_title'] and is_likely_job_title(prev_line):
                            current_entry['job_title'] = prev_line
                        elif not current_entry['company'] and is_likely_company(prev_line):
                            current_entry['company'] = prev_line
                    
                    continue
                
                if current_entry:
                    # Add bullet points and regular descriptions
                    if line.startswith(('•', '-', '✓', '*')) or re.match(r'^\d+\.\s', line):
                        current_entry['descriptions'].append(line)
                    elif len(line) > 30 and not extract_date_range(line):
                        # Check if this line might be a job title or company name
                        if not current_entry['job_title'] and is_likely_job_title(line):
                            current_entry['job_title'] = line
                        elif not current_entry['company'] and is_likely_company(line):
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
                    if is_likely_job_title(desc):
                        entry['job_title'] = desc
                        entry['descriptions'].remove(desc)
                        break
                if not entry['job_title']:
                    entry
        
        return work_data

    def extract_profile(self, text: str) -> Dict[str, str]:
        """Extract profile information using feature scoring."""
        
        def has_only_letters_space_period(text: str) -> bool:
            return bool(re.match(r'^[a-zA-Z\s\.]+$', text))
        
        def has_four_or_more_words(text: str) -> bool:
            return len(text.split()) >= 4
        
        def is_all_caps(text: str) -> bool:
            return text.isupper() and any(c.isalpha() for c in text)
        
        def has_at_symbol(text: str) -> bool:
            return '@' in text
        
        def has_parenthesis(text: str) -> bool:
            return '(' in text or ')' in text
        
        def has_slash(text: str) -> bool:
            return '/' in text
        
        def has_comma(text: str) -> bool:
            return ',' in text
        
        def has_numbers(text: str) -> bool:
            return any(c.isdigit() for c in text)
        
        def score_feature_sets(text: str, feature_sets: List[Tuple]) -> int:
            score = 0
            for feature_set in feature_sets:
                feature_func, points, *required = feature_set
                if feature_func(text):
                    score += points
                    if required and not required[0]:
                        return -999  # Disqualify if required is False
            return score

        def is_likely_location(text: str) -> bool:
            location_indicators = [
                # City, State/Country formats
                r'[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}',  # New York, NY
                r'[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+',  # London, United Kingdom
                # Common location keywords
                r'(?:Address|Location|Based in|Living in|Residing in)[\s:]+([^,\n]+(?:,\s*[^,\n]+)?)',
                # Postal code patterns for different countries
                r'[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}',  # UK Post Code
                r'\d{5}(?:-\d{4})?',  # US ZIP Code
                r'[ABCEGHJKLMNPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s*\d[ABCEGHJ-NPRSTV-Z]\d',  # Canadian Postal Code
            ]
            return any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in location_indicators)

        def is_likely_url(text: str) -> bool:
            # Common professional profile URLs
            url_indicators = [
                # Professional networks
                r'linkedin\.com/in/[\w-]+',
                r'github\.com/[\w-]+',
                r'gitlab\.com/[\w-]+',
                r'bitbucket\.org/[\w-]+',
                # Portfolio/Personal websites
                r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|org|net|io|dev)/[\w-]+',
                # Avoid matching technology names
                r'^(?!.*(?:framework|library|module|package|sdk|api)).*$'
            ]
            return (
                any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in url_indicators) and
                not any(tech.lower() in text.lower() for tech in [
                    'express.js', 'node.js', 'react.js', 'vue.js', 'angular.js',
                    'next.js', 'nuxt.js', 'gatsby.js', '.net', 'asp.net'
                ])
            )

        def extract_summary(text: str) -> str:
            """Extract summary from text with improved section detection."""
            # Common summary section indicators
            summary_headers = [
                # English
                r'(?:professional\s+)?summary',
                r'professional\s+profile',
                r'career\s+objective',
                r'personal\s+statement',
                r'about\s+(?:me|myself)',
                r'introduction',
                r'profile',
                r'objective',
                r'overview',
                # Add other languages if needed
            ]
            
            # Join patterns with OR operator and make case insensitive
            header_pattern = '|'.join(f'(?:{pattern})' for pattern in summary_headers)
            
            # Find summary section
            section_matches = []
            lines = text.split('\n')
            in_summary = False
            current_summary = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines unless we're in summary section
                if not line and not in_summary:
                    continue
                
                # Check if this is a summary header
                if re.search(header_pattern, line, re.IGNORECASE):
                    in_summary = True
                    continue
                
                # Check if we've hit the next section
                if in_summary:
                    # Common section headers that indicate end of summary
                    if re.search(r'^(?:experience|education|skills|projects|work|employment|qualifications|expertise)', 
                               line, re.IGNORECASE):
                        in_summary = False
                        section_matches.append(' '.join(current_summary))
                        current_summary = []
                        continue
                    
                    # Add line to current summary if it's not a header
                    if line and not line.isupper() and len(line.split()) > 2:
                        current_summary.append(line)
                
                # Handle case where summary section continues until next header
                if in_summary and i == len(lines) - 1 and current_summary:
                    section_matches.append(' '.join(current_summary))
            
            # Process and validate found summaries
            valid_summaries = []
            for summary in section_matches:
                # Clean up the summary text
                cleaned_summary = re.sub(r'\s+', ' ', summary).strip()
                
                # Validate summary content
                if cleaned_summary and len(cleaned_summary.split()) >= 4:
                    # Skip if it looks like a skills list
                    if not any(keyword in cleaned_summary.lower() for keyword in [
                        'proficient in', 'skills:', 'technologies:', 'programming languages',
                        'frameworks:', 'tools:', 'expertise in'
                    ]):
                        # Skip if it contains too many technical terms in sequence
                        tech_terms_sequence = re.search(
                            r'(?:python|java|javascript|react|angular|vue|node|sql|aws|docker)'
                            r'(?:\s*,\s*(?:python|java|javascript|react|angular|vue|node|sql|aws|docker))+',
                            cleaned_summary.lower()
                        )
                        if not tech_terms_sequence:
                            valid_summaries.append(cleaned_summary)
            
            # Return the most promising summary
            if valid_summaries:
                # Prefer longer, more detailed summaries
                return max(valid_summaries, key=lambda x: len(x))
            return ""
        
        # Define feature sets for each profile component
        name_features = [
            (has_only_letters_space_period, 3, True),
            (is_all_caps, 2),
            (has_at_symbol, -4),
            (has_numbers, -4),
            (has_parenthesis, -4),
            (has_comma, -4),
            (has_slash, -4),
            (has_four_or_more_words, -2)
        ]
        
        email_features = [
            (lambda x: bool(re.match(r'\S+@\S+\.\S+', x)), 4, True),
            (is_all_caps, -1),
            (has_parenthesis, -4),
            (has_comma, -4),
            (has_slash, -4),
            (has_four_or_more_words, -4)
        ]
        
        phone_features = [
            (lambda x: bool(re.match(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', x)), 4, True),
            (lambda x: bool(re.search(r'[a-zA-Z]', x)), -4)
        ]
        
        location_features = [
            (is_likely_location, 4, True),
            (is_all_caps, -1),
            (has_at_symbol, -4),
            (has_parenthesis, -3),
            (has_slash, -4),
            (lambda x: bool(re.search(r'@|www\.|http|\.com|\.org|\.net', x)), -4),  # Avoid emails and URLs
            (lambda x: len(x.split()) > 5, -3),  # Locations usually aren't too long
            (lambda x: any(tech.lower() in x.lower() for tech in [
                'javascript', 'python', 'java', 'react', 'angular'
            ]), -5)  # Avoid matching technology names
        ]
        
        url_features = [
            (is_likely_url, 4, True),
            (lambda x: bool(re.match(r'(?:https?://)?(?:www\.)?[\w-]+\.[\w-]+(?:/[\w-]+)*/?$', x)), 3),
            (is_all_caps, -1),
            (has_at_symbol, -4),
            (has_parenthesis, -3),
            (has_comma, -4),
            (has_four_or_more_words, -4),
            (lambda x: any(tech.lower() in x.lower() for tech in [
                'express.js', 'node.js', 'react.js', 'vue.js', 'angular.js',
                'next.js', 'nuxt.js', 'gatsby.js', '.net', 'asp.net'
            ]), -5)  # Avoid matching technology names
        ]
        
        # Process text into lines and clean them
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Split line further if it contains multiple pieces of information
                parts = [p.strip() for p in re.split(r'\s{2,}|\t+', line)]
                lines.extend(parts)
        
        # Find best matches for each component
        best_scores = {
            'name': (-999, ""),
            'email': (-999, ""),
            'phone': (-999, ""),
            'location': (-999, ""),
            'url': (-999, ""),
        }
        
        # Additional patterns for more thorough extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        # Enhanced location pattern
        location_patterns = [
            r'(?:Address|Location|Based in|Living in|Residing in)[\s:]+([^,\n]+(?:,\s*[^,\n]+)?)',
            r'[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}',
            r'[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+',
        ]
        
        # Enhanced URL pattern
        url_patterns = [
            r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+',
            r'(?:https?://)?(?:www\.)?github\.com/[\w-]+',
            r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|org|net|io|dev)/[\w-]+',
        ]
        
        for line in lines:
            # Score each line against each feature set
            name_score = score_feature_sets(line, name_features)
            email_score = score_feature_sets(line, email_features)
            phone_score = score_feature_sets(line, phone_features)
            location_score = score_feature_sets(line, location_features)
            url_score = score_feature_sets(line, url_features)
            
            # Update best scores if current scores are higher
            if name_score > best_scores['name'][0]:
                best_scores['name'] = (name_score, line)
                
            # Additional email check
            email_match = re.search(email_pattern, line)
            if email_match and email_score > best_scores['email'][0]:
                best_scores['email'] = (email_score, email_match.group(0))
                
            # Additional phone check
            phone_match = re.search(phone_pattern, line)
            if phone_match and phone_score > best_scores['phone'][0]:
                best_scores['phone'] = (phone_score, phone_match.group(0))
                
            # Enhanced location extraction
            for pattern in location_patterns:
                location_match = re.search(pattern, line, re.IGNORECASE)
                if location_match and location_score > best_scores['location'][0]:
                    location_text = location_match.group(1) if len(location_match.groups()) > 0 else location_match.group(0)
                    if not any(tech.lower() in location_text.lower() for tech in [
                        'javascript', 'python', 'java', 'react', 'angular'
                    ]):
                        best_scores['location'] = (location_score, location_text.strip())
            
            # Enhanced URL extraction
            for pattern in url_patterns:
                url_match = re.search(pattern, line, re.IGNORECASE)
                if url_match and url_score > best_scores['url'][0]:
                    url_text = url_match.group(0)
                    if not any(tech.lower() in url_text.lower() for tech in [
                        'express.js', 'node.js', 'react.js', 'vue.js', 'angular.js',
                        'next.js', 'nuxt.js', 'gatsby.js', '.net', 'asp.net'
                    ]):
                        best_scores['url'] = (url_score, url_text)
        
        # Extract summary from dedicated section if available
        summary_section = self.extract_section(text, ['summary', 'objective', 'profile'])
        summary_text = ' '.join(summary_section) if summary_section else ""
        
        # Only use summary text if it's meaningful
        if summary_text:
            # Clean up the summary text
            summary_text = re.sub(r'\s+', ' ', summary_text).strip()
            # Ensure it's actually a summary and not just a list of keywords
            if not any(keyword in summary_text.lower() for keyword in ['languages', 'skills', 'technologies']):
                if len(summary_text.split()) < 4:
                    summary_text = ""
            else:
                summary_text = ""
        
        # Update the summary extraction in the return statement
        summary_text = extract_summary(text)
        
        return {
            'name': best_scores['name'][1],
            'email': best_scores['email'][1],
            'phone': best_scores['phone'][1],
            'location': best_scores['location'][1],
            'url': best_scores['url'][1],
            'summary': summary_text
        }

def extract_entities(text: str) -> Dict:
    """Wrapper function for backward compatibility."""
    extractor = CVExtractor()
    return extractor.extract_entities(text)