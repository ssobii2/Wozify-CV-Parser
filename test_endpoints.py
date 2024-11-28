import pytest
from fastapi.testclient import TestClient
from main import app
import logging
import os
import json
from pypdf import PdfReader
from nlp_utils.cv_section_parser import CVSectionParser
import torch
from docx import Document

client = TestClient(app)
cv_section_parser = CVSectionParser()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize parser and log device info
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")
cv_section_parser = CVSectionParser()

def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX file."""
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
    """Generate section outputs for CVs using the parser."""
    # List of test CV files
    cv_files = [
        "RAW-Senior-Fullstack-Developer-Gabor.docx",
        "Greenformatics_Neufeld-Balazs - CV_eng.docx",
        "Edvard_Eros_CV.pdf",
        "DRUIT_CV_F.Zs..pdf",
        "DRUIT_CV_D GY.pdf",
        "Konyves_Lajos_CV_EN_.pdf",
        "My-CV-Simple.pdf",
        "Ussayed_Resume-Simple.pdf",
        "Patrik_Suli_CV.pdf",
        "Abbasi_Resume.pdf",
        "Aladar_Feher_CV.pdf",
        "László_Dobi_EN_CV_2024.pdf",
        "Mark G Kovacs CV 2023.11.pdf",
        "Medior Software engineer Devora Csaba IDnr 532 (1).pdf",
        "MindtechApps_CV_LeventeV_Senior_ScrumMaster.pdf",
        "My-CV.pdf",
    ]
    
    project_dir = "e:/Projects/Company Projects/Wozify-CV-Parser"
    cv_dir = os.path.join(project_dir, "CVs")
    output_dir = os.path.join(project_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    for cv_file in cv_files:
        pdf_path = os.path.join(cv_dir, cv_file)
        logger.info(f"\nProcessing CV: {cv_file}")
        
        # Extract text from PDF
        cv_text = extract_text_from_file(pdf_path)
        if cv_text is None:
            logger.error(f"Skipping {cv_file} due to text extraction error")
            continue
            
        # Parse sections
        sections = cv_section_parser.parse_sections(cv_text)
        
        # Create output JSON file
        output_filename = os.path.splitext(cv_file)[0] + "_sections.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save sections to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, ensure_ascii=False, indent=2)
        
        # Log sections for verification
        logger.info(f"Saved sections to: {output_filename}")
        for section, content in sections.items():
            logger.info(f"\n{section.upper()}:")
            for item in content:
                logger.info(f"- {item.strip()}")

if __name__ == "__main__":
    test_cv_section_parser()