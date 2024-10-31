import pytest
from fastapi.testclient import TestClient
from main import app
import os
import shutil

client = TestClient(app)

# Ensure test directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

def test_generate_cv_and_json():
    try:
        # Copy the sample CV file to test with
        # shutil.copy("Konyves_Lajos_CV_EN_.pdf", "test.pdf")
        shutil.copy("My-CV-Simple.pdf", "test.pdf")
        # shutil.copy("Aladar_Feher_CV.pdf", "test.pdf")
        # shutil.copy("MindtechApps_CV_LeventeV_Senior_ScrumMaster.pdf", "test.pdf")
        # shutil.copy("Medior Software engineer Devora Csaba IDnr 532 (1).pdf", "test.pdf")
        
        # Test processing endpoint to generate JSON
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/process", files=files)
        
        print("Process Response:", response.json())  # Output JSON response
        
        # Test generate endpoint to generate PDF
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/generate", files=files)
        
        print("Generate Response Status:", response.status_code)  # Output status
        
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")