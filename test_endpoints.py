import pytest
from fastapi.testclient import TestClient
from main import app
import logging
import os
import json
from pypdf import PdfReader
from nlp_utils.cv_section_parser import CVSectionParser

client = TestClient(app)
cv_section_parser = CVSectionParser()

# Set up logging
logging.basicConfig(level=logging.INFO)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def test_cv_section_parser():
    # List of test CV files
    cv_files = [
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
        logging.info(f"\nProcessing CV: {cv_file}")
        
        # Extract text from PDF
        cv_text = extract_text_from_pdf(pdf_path)
        if cv_text is None:
            logging.error(f"Skipping {cv_file} due to text extraction error")
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
        logging.info(f"Saved sections to: {output_filename}")
        for section, content in sections.items():
            logging.info(f"\n{section.upper()}:")
            for item in content:
                logging.info(f"- {item.strip()}")