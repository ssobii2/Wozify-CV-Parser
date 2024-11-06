import pytest
from fastapi.testclient import TestClient
from main import app
import os
import shutil
import tempfile
import logging
from nlp_utils import (
    CVExtractor, ProfileExtractor, EducationExtractor, 
    ExperienceExtractor, SkillsExtractor, LanguageExtractor,
    CurrentPositionExtractor
)

client = TestClient(app)
cv_extractor = CVExtractor()

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_generate_cv_and_json():
    # List of test CV files
    test_files = [
        "Konyves_Lajos_CV_EN_.pdf",
        "My-CV-Simple.pdf",
        "Aladar_Feher_CV.pdf",
        "MindtechApps_CV_LeventeV_Senior_ScrumMaster.pdf",
        "Medior Software engineer Devora Csaba IDnr 532 (1).pdf",
        "My-CV.pdf",
        "Abbasi_Resume.pdf",
        "Ussayed_Resume-Simple.pdf"
    ]
    
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            for cv_file in test_files:
                # Create a unique test filename based on the original filename
                test_filename = os.path.join(temp_dir, f"test_{os.path.basename(cv_file)}")
                
                # Copy the CV file to test with
                shutil.copy(cv_file, test_filename)
                
                # Test processing endpoint to generate JSON
                with open(test_filename, "rb") as f:
                    files = {"file": (test_filename, f, "application/pdf")}
                    response = client.post("/process", files=files)
                
                # Verify JSON response
                assert response.status_code == 200
                json_data = response.json()
                assert "data" in json_data
                logging.info(f"Process Response for {cv_file}: {json_data}")
                
                # Test generate endpoint to generate PDF
                with open(test_filename, "rb") as f:
                    files = {"file": (test_filename, f, "application/pdf")}
                    response = client.post("/generate", files=files)
                
                # Verify PDF generation
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                logging.info(f"Generate Response Status for {cv_file}: {response.status_code}")
                
                # Verify PDF file exists
                pdf_filename = f"{os.path.splitext(os.path.basename(test_filename))[0]}_formatted.pdf"
                pdf_path = os.path.join(output_dir, pdf_filename)
                assert os.path.exists(pdf_path)
                
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise