import pytest
from fastapi.testclient import TestClient
from main import app
import os
import shutil
from nlp_utils import (
    CVExtractor, ProfileExtractor, EducationExtractor, 
    ExperienceExtractor, SkillsExtractor, LanguageExtractor,
    CurrentPositionExtractor
)

client = TestClient(app)
cv_extractor = CVExtractor()

# Ensure test directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

def test_generate_cv_and_json():
    # List of test CV files
    test_files = [
        "Konyves_Lajos_CV_EN_.pdf",
        "My-CV-Simple.pdf",
        "Aladar_Feher_CV.pdf",
        "MindtechApps_CV_LeventeV_Senior_ScrumMaster.pdf",
        "Medior Software engineer Devora Csaba IDnr 532 (1).pdf",
        "My-CV.pdf"
    ]
    
    try:
        for cv_file in test_files:
            # Create a unique test filename based on the original filename
            test_filename = f"test_{os.path.basename(cv_file)}"
            
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
            print(f"\nProcess Response for {cv_file}:", json_data)
            
            # Comment out this entire block if you don't need PDF generation
            '''
            # Test generate endpoint to generate PDF
            with open(test_filename, "rb") as f:
                files = {"file": (test_filename, f, "application/pdf")}
                response = client.post("/generate", files=files)
            
            # Verify PDF generation
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            print(f"Generate Response Status for {cv_file}:", response.status_code)
            
            # Verify PDF file exists
            pdf_filename = f"{os.path.splitext(test_filename)[0]}_formatted.pdf"
            pdf_path = f"outputs/{pdf_filename}"
            assert os.path.exists(pdf_path)
            '''
            
            # Clean up the test file
            if os.path.exists(test_filename):
                os.remove(test_filename)
                
    finally:
        # Clean up any remaining test files
        for cv_file in test_files:
            test_filename = f"test_{os.path.basename(cv_file)}"
            if os.path.exists(test_filename):
                os.remove(test_filename)