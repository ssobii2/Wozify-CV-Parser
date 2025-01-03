# Standard library imports
import os
import json
import logging

# Third-party imports
import torch
from docx import Document
from pypdf import PdfReader
from fastapi.testclient import TestClient

# Local imports
from main import app
from nlp_utils.cv_section_parser import CVSectionParser
from nlp_utils.cv_section_parser_hu import CVSectionParserHu

# Initialize test client and logging
client = TestClient(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize parsers and device
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")
cv_section_parser_en = CVSectionParser()
cv_section_parser_hu = CVSectionParserHu()

def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX file.
    
    Args:
        file_path (str): Path to the file to extract text from
        
    Returns:
        str: Extracted text from the file, or None if extraction fails
    """
    try:
        if file_path.lower().endswith('.pdf'):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_path.lower().endswith('.docx'):
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return None

def test_cv_section_parser():
    """Generate section outputs for CVs using the parser.
    
    This function processes both English and Hungarian CVs, extracting sections
    and saving the results as JSON files.
    """
    project_dir = "e:/Projects/Company Projects/Wozify-CV-Parser"
    cv_dir = os.path.join(project_dir, "CVs")
    output_dir = os.path.join(project_dir, "outputs")
    
    # Create necessary directories
    cv_dir_hu = os.path.join(cv_dir, "hungarian")
    cv_dir_en = os.path.join(cv_dir, "english")
    os.makedirs(cv_dir_hu, exist_ok=True)
    os.makedirs(cv_dir_en, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Set debug logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Process CVs for each language
    for lang_dir, lang, parser in [
        (cv_dir_hu, "hungarian", cv_section_parser_hu),
        (cv_dir_en, "english", cv_section_parser_en)
    ]:
        logger.info(f"\nProcessing {lang} CVs...")
        
        # Get all PDF and DOCX files
        cv_files = [f for f in os.listdir(lang_dir) 
                   if f.lower().endswith(('.pdf', '.docx'))]
        
        # Process each CV file
        for cv_file in cv_files:
            logger.info(f"Processing CV: {cv_file}")
            
            # Extract text from file
            cv_path = os.path.join(lang_dir, cv_file)
            cv_text = extract_text_from_file(cv_path)
            if cv_text is None:
                logger.error(f"Failed to process {cv_file}")
                continue
            
            # Parse sections and save results
            sections = parser.parse_sections(cv_text)
            
            lang_output_dir = os.path.join(output_dir, lang.lower())
            os.makedirs(lang_output_dir, exist_ok=True)
            
            output_filename = os.path.splitext(cv_file)[0] + "_sections.json"
            output_path = os.path.join(lang_output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully processed: {cv_file}")

if __name__ == "__main__":
    test_cv_section_parser()