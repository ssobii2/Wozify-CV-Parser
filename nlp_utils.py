import re
import spacy
from datetime import datetime
from typing import Dict, List, Optional

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
        
        self.skill_categories = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
                'kotlin', 'go', 'rust', 'typescript', 'scala', 'perl', 'r'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'node', 'django', 'flask',
                'spring', 'asp.net', 'jquery', 'bootstrap', 'sass', 'less'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis',
                'cassandra', 'elasticsearch', 'dynamodb'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
                'ansible', 'circleci', 'gitlab'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'slack', 'vscode', 'intellij', 'eclipse',
                'postman', 'webpack', 'npm', 'yarn'
            ]
        }

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

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract and categorize skills."""
        skills = {category: [] for category in self.skill_categories}
        
        # Extract skills by category
        for category, keywords in self.skill_categories.items():
            for keyword in keywords:
                if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                    skills[category].append(keyword)
        
        # Remove empty categories
        return {k: sorted(v) for k, v in skills.items() if v}

    def extract_entities(self, text: str) -> Dict:
        """Main method to extract all information from CV."""
        doc = nlp(text)
        
        # Initialize the result dictionary with all possible fields
        extracted_data = {
            'name': None,
            'summary': None,
            'contact_info': {},
            'education': [],
            'experience': [],
            'skills': {},
            'projects': [],
            'certifications': [],
            'languages': [],
            'interests': [],
            'achievements': [],
            'publications': [],
            'references': []
        }

        # Extract name (first PERSON entity found)
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                extracted_data['name'] = ent.text
                break

        # Extract contact information
        extracted_data['contact_info'] = self.extract_contact_info(text)

        # Extract summary (first paragraph that's not a section header)
        paragraphs = [p.text.strip() for p in doc.sents if len(p.text.strip()) > 50]
        if paragraphs:
            extracted_data['summary'] = paragraphs[0]

        # Extract sections
        for section_name, keywords in self.section_headers.items():
            section_content = self.extract_section(text, keywords)
            if section_content:
                extracted_data[section_name] = section_content

        # Extract and categorize skills
        extracted_data['skills'] = self.extract_skills(text)

        # Remove empty fields
        return {k: v for k, v in extracted_data.items() if v}

def extract_entities(text: str) -> Dict:
    """Wrapper function for backward compatibility."""
    extractor = CVExtractor()
    return extractor.extract_entities(text)