import re
from typing import Dict, List, Optional

class CurrentPositionExtractor:
    def __init__(self):
        self.job_indicators = [
            'developer', 'engineer', 'manager', 'consultant', 'analyst', 
            'specialist', 'coordinator', 'assistant', 'director', 'lead',
            'intern', 'trainee', 'administrator', 'supervisor'
        ]

    def extract_current_position(self, text: str, work_experience: List[Dict]) -> Optional[str]:
        """Extract the most recent job title from experience section."""
        # Find the most recent job based on the date
        most_recent_job = None
        most_recent_date = None
        
        for job in work_experience:
            date = job.get('date')
            if date and ('Present' in date or 'Current' in date or 'Now' in date):
                return job.get('job_title')
            
            # Parse the date to find the most recent one
            if date:
                # Extract the end year from the date range
                end_year_match = re.search(r'\b\d{4}\b', date.split('-')[-1])
                if end_year_match:
                    end_year = int(end_year_match.group(0))
                    if most_recent_date is None or end_year > most_recent_date:
                        most_recent_date = end_year
                        most_recent_job = job.get('job_title')
        
        return most_recent_job 