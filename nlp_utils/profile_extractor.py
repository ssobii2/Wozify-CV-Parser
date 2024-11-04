import re
from typing import Dict, List, Tuple

class ProfileExtractor:
    def __init__(self):
        pass

    def has_only_letters_space_period(self, text: str) -> bool:
        return bool(re.match(r'^[a-zA-Z\s\.]+$', text))
    
    def has_four_or_more_words(self, text: str) -> bool:
        return len(text.split()) >= 4
    
    def is_all_caps(self, text: str) -> bool:
        return text.isupper() and any(c.isalpha() for c in text)
    
    def has_at_symbol(self, text: str) -> bool:
        return '@' in text
    
    def has_parenthesis(self, text: str) -> bool:
        return '(' in text or ')' in text
    
    def has_slash(self, text: str) -> bool:
        return '/' in text
    
    def has_comma(self, text: str) -> bool:
        return ',' in text
    
    def has_numbers(self, text: str) -> bool:
        return any(c.isdigit() for c in text)

    def is_likely_location(self, text: str) -> bool:
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

    def is_likely_url(self, text: str) -> bool:
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

    def extract_summary(self, text: str) -> str:
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

    def extract_profile(self, text: str) -> Dict[str, str]:
        """Extract profile information using feature scoring."""
        
        def score_feature_sets(text: str, feature_sets: List[Tuple]) -> int:
            score = 0
            for feature_set in feature_sets:
                feature_func, points, *required = feature_set
                if feature_func(text):
                    score += points
                    if required and not required[0]:
                        return -999  # Disqualify if required is False
            return score

        # Define feature sets for each profile component
        name_features = [
            (self.has_only_letters_space_period, 3, True),
            (self.is_all_caps, 2),
            (self.has_at_symbol, -4),
            (self.has_numbers, -4),
            (self.has_parenthesis, -4),
            (self.has_comma, -4),
            (self.has_slash, -4),
            (self.has_four_or_more_words, -2)
        ]
        
        email_features = [
            (lambda x: bool(re.match(r'\S+@\S+\.\S+', x)), 4, True),
            (self.is_all_caps, -1),
            (self.has_parenthesis, -4),
            (self.has_comma, -4),
            (self.has_slash, -4),
            (self.has_four_or_more_words, -4)
        ]
        
        phone_features = [
            (lambda x: bool(re.match(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', x)), 4, True),
            (lambda x: bool(re.search(r'[a-zA-Z]', x)), -4)
        ]
        
        location_features = [
            (self.is_likely_location, 4, True),
            (self.is_all_caps, -1),
            (self.has_at_symbol, -4),
            (self.has_parenthesis, -3),
            (self.has_slash, -4),
            (lambda x: bool(re.search(r'@|www\.|http|\.com|\.org|\.net', x)), -4),  # Avoid emails and URLs
            (lambda x: len(x.split()) > 5, -3),  # Locations usually aren't too long
            (lambda x: any(tech.lower() in x.lower() for tech in [
                'javascript', 'python', 'java', 'react', 'angular'
            ]), -5)  # Avoid matching technology names
        ]
        
        url_features = [
            (self.is_likely_url, 4, True),
            (lambda x: bool(re.match(r'(?:https?://)?(?:www\.)?[\w-]+\.[\w-]+(?:/[\w-]+)*/?$', x)), 3),
            (self.is_all_caps, -1),
            (self.has_at_symbol, -4),
            (self.has_parenthesis, -3),
            (self.has_comma, -4),
            (self.has_four_or_more_words, -4),
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
        
        # Extract summary
        summary_text = self.extract_summary(text)
        
        return {
            'name': best_scores['name'][1],
            'email': best_scores['email'][1],
            'phone': best_scores['phone'][1],
            'location': best_scores['location'][1],
            'url': best_scores['url'][1],
            'summary': summary_text
        } 