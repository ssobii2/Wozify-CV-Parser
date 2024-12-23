import re
from typing import List, Optional, Dict
import spacy
from langdetect import detect, LangDetectException

class SkillsExtractor:
    def __init__(self, nlp_en, nlp_hu):
        self.nlp_en = nlp_en
        self.nlp_hu = nlp_hu
        self.section_headers = {
            'skills': [
                'skills', 'technical skills', 'competencies', 'expertise', 'technologies',
                'készségek', 'technikai készségek', 'szakmai készségek', 'kompetenciák',
                'szaktudás', 'technológiák', 'technikai ismeretek', 'szakmai ismeretek',
                'programozási ismeretek', 'fejlesztői ismeretek', 'egyéb tanusítványok', 'egyéb',
                'programozói skillek', 'szakértelem', 'szakmai tapasztalat', 'szakmai tudás',
                'szakmai kompetenciák', 'technikai tudás', 'technikai kompetenciák', 
                'szakmai ismeretek és készségek', 'szakmai fejlődés', 'szakmai képesítések',
                'szakmai tapasztalatok', 'szakmai gyakorlat', 'szakmai elismerések', 
                'szakmai tanúsítványok', 'szakmai képességek', 'szakmai irányelvek'
            ]
        }
        
        # List of skills to extract (keeping in English since technical terms are usually in English)
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
            'postman', 'webpack', 'npm', 'yarn', 'html5', '.net', 'ios', 'android',
            'google', 'ui/ux', 'adobe', 'figma', 'prisma', 'web3', 'express', 'linux',
            'macos', 'windows', 'laravel',
            # Additional skills
            'data analysis', 'machine learning', 'artificial intelligence', 'big data',
            'data visualization', 'business intelligence', 'cybersecurity', 'networking',
            'devops', 'agile', 'scrum', 'kanban', 'project management', 'quality assurance',
            'testing', 'unit testing', 'integration testing', 'selenium', 'cucumber',
            'graphql', 'restful services', 'microservices', 'api development', 'cloud computing',
            'virtualization', 'kvm', 'vmware', 'git', 'svn', 'mercurial', 'docker-compose',
            'firebase', 'heroku', 'netlify', 'digital ocean', 'content management systems',
            'wordpress', 'shopify', 'magento', 'seo', 'sem', 'email marketing', 'social media',
            'ux research', 'prototyping', 'wireframing', 'user testing', 'agile methodologies',
            'business analysis', 'stakeholder management', 'change management', 'strategic planning',
            'financial analysis', 'marketing', 'salesforce', 'crm', 'erp', 'sap', 'oracle netsuite',
            'hungarian', 'angol', 'német', 'francia', 'spanyol', 'olasz', 'portugál', 'orosz'
        ]

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
                    for keyword in ['education', 'experience', 'projects', 'languages']
                )
            
            if is_section_header:
                in_section = True
                continue
            
            if in_section and is_next_different_section:
                in_section = False
            
            if in_section:
                section_lines.append(line)
        
        return section_lines

    def extract_skills(self, text: str, parsed_sections: Optional[Dict] = None) -> List[str]:
        """Extract skills from text using both predefined lists and NLP analysis."""
        skills = set()
        
        def normalize_skill(skill: str) -> str:
            """Normalize skill names to prevent duplicates."""
            skill = skill.lower()
            # Remove .js suffix if present
            if skill.endswith('.js'):
                skill = skill[:-3]
            # Remove js suffix if present
            if skill.endswith('js') and not skill == 'js':
                skill = skill[:-2]
            # Handle special cases
            skill_mapping = {
                # JavaScript frameworks/libraries
                'node': 'Node.js',
                'nodejs': 'Node.js',
                'express': 'Express.js',
                'expressjs': 'Express.js',
                'react': 'React.js',
                'reactjs': 'React.js',
                'next': 'Next.js',
                'nextjs': 'Next.js',
                'vue': 'Vue.js',
                'vuejs': 'Vue.js',
                'angular': 'Angular.js',
                'angularjs': 'Angular.js',
                'svelte': 'Svelte',
                'sveltejs': 'Svelte',
                
                # Programming languages
                'javascript': 'JavaScript',
                'typescript': 'TypeScript',
                'python': 'Python',
                'java': 'Java',
                'c++': 'C++',
                'cpp': 'C++',
                'c#': 'C#',
                'csharp': 'C#',
                'php': 'PHP',
                'ruby': 'Ruby',
                'swift': 'Swift',
                'go': 'Go',
                
                # Databases
                'postgresql': 'PostgreSQL',
                'postgres': 'PostgreSQL',
                'mysql': 'MySQL',
                'mongodb': 'MongoDB',
                'mongo': 'MongoDB',
                'sqlite': 'SQLite',
                'cassandra': 'Cassandra',
                
                # Web technologies
                'html': 'HTML',
                'html5': 'HTML',
                'css': 'CSS',
                'css3': 'CSS',
                'sass': 'SASS',
                'scss': 'SASS',
                'tailwind': 'Tailwind CSS',
                'tailwindcss': 'Tailwind CSS',
                'bootstrap': 'Bootstrap',
                'jquery': 'jQuery',
                
                # Tools and platforms
                'git': 'Git',
                'github': 'GitHub',
                'gitlab': 'GitLab',
                'docker': 'Docker',
                'kubernetes': 'Kubernetes',
                'k8s': 'Kubernetes',
                'aws': 'AWS',
                'azure': 'Azure',
                'gcp': 'GCP',
                'vscode': 'VS Code',
                'visualstudio': 'Visual Studio',
                'heroku': 'Heroku',
                'netlify': 'Netlify',
                
                # Design tools
                'figma': 'Figma',
                'adobe': 'Adobe',
                'photoshop': 'Adobe Photoshop',
                'illustrator': 'Adobe Illustrator',
                'xd': 'Adobe XD',
                
                # Microsoft tools
                'excel': 'Microsoft Excel',
                'word': 'Microsoft Word',
                'powerpoint': 'Microsoft PowerPoint',
                'msoffice': 'Microsoft Office',
                'office': 'Microsoft Office',
                
                # Operating systems
                'linux': 'Linux',
                'windows': 'Windows',
                'macos': 'macOS',
                'mac': 'macOS',
                'ubuntu': 'Ubuntu',
                'debian': 'Debian',
            }
            
            # Try to get from mapping, fallback to capitalized version
            normalized = skill_mapping.get(skill)
            if normalized:
                return normalized
            
            # Handle remaining cases
            words = skill.split()
            return ' '.join(word.capitalize() for word in words)

        # Try to use parsed sections first if available
        if parsed_sections and 'skills' in parsed_sections and parsed_sections['skills']:
            for skills_text in parsed_sections['skills']:
                if not skills_text.strip():
                    continue
                    
                # First get skills from predefined list
                for skill in self.skills:
                    # Create variations of the skill name to match common formats
                    skill_variations = [
                        skill,  # normal: react
                        skill + 'js',  # reactjs
                        skill + '.js',  # react.js
                        skill.replace('javascript', 'js'),  # javascript -> js
                        skill.replace('typescript', 'ts'),  # typescript -> ts
                        skill.capitalize(),  # React
                        skill.upper(),  # REACT
                    ]
                    
                    for variation in skill_variations:
                        if re.search(r'\b' + re.escape(variation) + r'\b', skills_text, re.IGNORECASE):
                            normalized_skill = normalize_skill(skill)
                            skills.add(normalized_skill)
                            break
                
                # Then use NLP to find additional technical skills
                nlp = self.get_nlp_model_for_text(skills_text)
                doc = nlp(skills_text)
                
                # Look for noun phrases that might be technical skills
                if nlp.meta['lang'] == 'hu':
                    noun_phrases = self.extract_noun_phrases(doc)
                else:
                    noun_phrases = doc.noun_chunks

                for chunk in noun_phrases:
                    potential_skill = chunk.text.strip()
                    
                    # Skip if too long or too short
                    if len(potential_skill.split()) > 3 or len(potential_skill) < 2:
                        continue
                    
                    # Skip common non-skill words
                    if potential_skill.lower() in {'skills', 'experience', 'years', 'knowledge', 'proficiency', 'expert'}:
                        continue
                    
                    # Look for technical skill patterns
                    if self._is_likely_technical_skill(potential_skill):
                        normalized_skill = normalize_skill(potential_skill)
                        skills.add(normalized_skill)
        
        # Only fallback to full text extraction if no skills found in parsed sections
        if not skills:
            section_lines = self.extract_section(text, self.section_headers['skills'])
            if section_lines:
                section_text = ' '.join(section_lines)
                for skill in self.skills:
                    if re.search(r'\b' + re.escape(skill) + r'\b', section_text, re.IGNORECASE):
                        normalized_skill = normalize_skill(skill)
                        skills.add(normalized_skill)
        
        return sorted(skills)

    def extract_noun_phrases(self, doc):
        """Custom method to extract noun phrases for Hungarian language."""
        noun_phrases = []
        for token in doc:
            if token.dep_ in {'nsubj', 'dobj', 'pobj'}:
                noun_phrases.append(token.subtree)
        return noun_phrases

    def _is_likely_technical_skill(self, text: str) -> bool:
        """Check if the text is likely to be a technical skill."""
        # Technical indicators
        tech_patterns = [
            r'\b[A-Z]+\b',  # Uppercase words like SQL, CSS
            r'\b[A-Za-z]+[\+\#]+\b',  # C++, C#
            r'\b[A-Za-z]+\.?js\b',  # .js suffix
            r'\b[A-Za-z]+\d+\b',  # Version numbers
            r'[A-Z][a-z]+[A-Z][a-z]+',  # CamelCase
            r'\b[A-Za-z]+[-\.][A-Za-z]+\b',  # Hyphenated or dotted
        ]
        
        # Skip common English and Hungarian words and general terms that do not indicate specific skills or expertise
        common_words = {
            'the', 'and', 'or', 'in', 'at', 'by', 'for', 'with', 'about',
            'skills', 'years', 'experience', 'knowledge', 'advanced', 'intermediate',
            'basic', 'expert', 'proficient', 'familiar', 'understanding',
            'capable', 'competent', 'trained', 'qualified', 'specialized', 'mastery',
            'apprentice', 'novice', 'talented', 'gifted', 'adept', 'skilled', 'expertise',
            'proficiency', 'ability', 'aptitude', 'know-how', 'experience level', 'background',
            'készségek', 'évek', 'tapasztalat', 'tudás', 'haladó', 'középfokú',
            'alapfokú', 'szakértő', 'jártasság', 'ismerős', 'megértés',
            'képes', 'kompetens', 'képzett', 'minősített', 'specializált', 'szakértelem',
            'mesteri', 'tanonc', 'kezdő', 'tehetséges', 'tehetséges', 'ügyes', 'szakértelem',
            'szakmai tudás', 'képesség', 'alkalmasság', 'tudás', 'tapasztalati szint', 'háttér'
        }
        
        text_lower = text.lower()
        
        # Skip if it's a common word
        if text_lower in common_words:
            return False
        
        # Check for technical patterns
        if any(re.search(pattern, text) for pattern in tech_patterns):
            return True
        
        # Check for technical context in both English and Hungarian
        technical_context = {
            'framework', 'library', 'language', 'database', 'platform',
            'tool', 'sdk', 'api', 'stack', 'protocol', 'service',
            'keretrendszer', 'könyvtár', 'nyelv', 'adatbázis', 'platform',
            'eszköz', 'sdk', 'api', 'stack', 'protokoll', 'szolgáltatás'
        }
        
        return any(context in text_lower for context in technical_context)

    # Add a dictionary for common skill abbreviations
    @property
    def abbreviations(self):
        return {
            'SQL': 'SQL',
            'Java': 'Java',
            'C++': 'C++',
            'JavaScript': 'JS',
            'Python': 'Py',
            'HTML': 'HTML',
            'HTML5': 'HTML5',
            'CSS': 'CSS',
            'PHP': 'PHP',
            'C#': 'C#',
            'Ruby': 'Ruby',
            'Go': 'Go',
            'Swift': 'Swift',
            'Kotlin': 'Kotlin',
            'Rust': 'Rust',
            'TypeScript': 'TS',
            'Scala': 'Scala',
            'Perl': 'Perl',
            'R': 'R',
            'Django': 'Django',
            'Flask': 'Flask',
            'React': 'React',
            'Angular': 'Angular',
            'Vue': 'Vue',
            'Node.js': 'Node',
            'Docker': 'Docker',
            'Kubernetes': 'K8s',
            'AWS': 'AWS',
            'Azure': 'Azure',
            'GCP': 'GCP',
            'Terraform': 'Terraform',
            'Ansible': 'Ansible',
            'Jenkins': 'Jenkins',
            'Git': 'Git',
            'GitLab': 'GitLab',
            'CircleCI': 'CircleCI',
            'PostgreSQL': 'PostgreSQL',
            'MongoDB': 'MongoDB',
            'MySQL': 'MySQL',
            'SQLite': 'SQLite',
            'Redis': 'Redis',
            'Elasticsearch': 'Elasticsearch',
            'Cassandra': 'Cassandra',
            'DynamoDB': 'DynamoDB',
            'iOS': 'iOS',
            'Android': 'Android',
            'Google': 'Google',
            'Adobe': 'Adobe',
            'Figma': 'Figma',
            'UI/UX': 'UI/UX',
            'Prisma': 'Prisma',
            'Linux': 'Linux',
            'Windows': 'Windows',
            'MacOS': 'Mac OS',
            'Laravel': 'Laravel',
            'Web3': 'Web3',
            'Web 3': 'Web3',
            'SASS': 'SASS',
            'SCSS': 'SASS',
            'Firebase': 'Firebase',
            'Heroku': 'Heroku',
            'Netlify': 'Netlify',
            'DigitalOcean': 'Digital Ocean',
            'Content Management Systems': 'CMS',
            'WordPress': 'WordPress',
            'Shopify': 'Shopify',
            'Magento': 'Magento',
            'SEO': 'SEO',
            'SEM': 'SEM',
            'Email Marketing': 'Email Marketing',
            'Social Media': 'Social Media',
            'Agile': 'Agile',
            'Scrum': 'Scrum',
            'Kanban': 'Kanban',
            'DevOps': 'DevOps',
            'Machine Learning': 'ML',
            'Artificial Intelligence': 'AI',
            'Data Analysis': 'Data Analysis',
            'Business Intelligence': 'BI',
            'Cybersecurity': 'Cybersecurity',
            'Networking': 'Networking',
            'Virtualization': 'Virtualization',
            'Cloud Computing': 'Cloud Computing',
            'API Development': 'API Dev',
            'Microservices': 'Microservices',
            'GraphQL': 'GraphQL',
            'RESTful Services': 'REST',
            'Unit Testing': 'Unit Testing',
            'Integration Testing': 'Integration Testing',
            'Selenium': 'Selenium',
            'Cucumber': 'Cucumber',
        }