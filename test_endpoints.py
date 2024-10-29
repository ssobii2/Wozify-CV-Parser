import pytest
from fastapi.testclient import TestClient
from main import app
import os
import shutil

client = TestClient(app)

# Ensure test directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

def test_root_endpoint():
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the CV Parser API"}

def test_upload_invalid_file():
    # Test with an invalid file type
    files = {"file": ("test.txt", "some content", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400

def test_process_endpoint():
    try:
        # Copy the sample CV file to test with
        shutil.copy("My-CV-Simple.pdf", "test.pdf")
        
        # Test processing endpoint
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/process", files=files)
        
        print("Process Response:", response.json())  # Debug print
        assert response.status_code == 200
        assert "data" in response.json()
        
        data = response.json()["data"]
        # Check for contact_info and email
        assert "contact_info" in data
        assert "email" in data["contact_info"]
        assert data["contact_info"]["email"] == "subhanimran4@gmail.com"
        
        # Add more specific assertions based on your CV content
        assert "skills" in data
        assert "education" in data
        assert "experience" in data
        
        # Test specific skills categories
        skills = data["skills"]
        assert "programming_languages" in skills
        assert "python" in skills["programming_languages"]
        
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")

def test_generate_endpoint():
    try:
        # Copy the sample CV file to test with
        shutil.copy("My-CV-Simple.pdf", "test.pdf")
        
        # Test generate endpoint
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/generate", files=files)
        
        print("Generate Response Status:", response.status_code)  # Debug print
        if response.status_code != 200:
            print("Generate Error:", response.json())  # Debug print
            
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
    finally:
        # Clean up
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")