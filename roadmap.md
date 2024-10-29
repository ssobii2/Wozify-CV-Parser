# Ultimate Tech Stack for CV Parser App

To build a custom CV parser application that meets your preferences, we'll use technologies that are efficient, easy to set up, and do not rely on cloud services or complex configurations. Here's the recommended tech stack for both the frontend and backend:

## Backend Technologies

- **Programming Language**: **Python 3.x**
  - Python offers excellent libraries for document parsing and NLP.

- **Web Framework**: **FastAPI**
  - FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.6+.
  - Provides automatic interactive API documentation.

- **Parsing Libraries**:
  - **PDF Parsing**: `pdfminer.six` or `PyPDF2`
    - For extracting text content from PDF files.
  - **DOCX Parsing**: `python-docx`
    - For reading and writing Microsoft Word files.
  - **Image/Scan OCR**: Tesseract OCR via `pytesseract`
    - Requires Tesseract OCR installed locally.

- **Natural Language Processing (NLP)**:
  - **spaCy** for Named Entity Recognition (NER)
    - Effective for extracting entities like names, organizations, dates, etc.
  - **Regular Expressions (regex)** for pattern matching
    - Useful for identifying emails, phone numbers, etc.

- **Data Storage**:
  - **File System Storage**
    - Store uploaded files and processed outputs in dedicated folders.
  - **JSON Files**
    - Save parsed data in JSON format within the file system.

- **Document Generation**:
  - **WeasyPrint** or **ReportLab**
    - For generating PDFs from HTML templates with custom styling.

- **Testing Framework**:
  - **PyTest**
    - For unit and integration testing.

- **Environment Management**:
  - **virtualenv** or **venv**
    - For creating isolated Python environments.

## Frontend Technologies

- **Programming Language**: **JavaScript**
  - Widely used language for web development.

- **Framework**: **Plain JavaScript**, HTML, and CSS
  - For a simple frontend without the complexity of modern JavaScript frameworks.

- **HTTP Client**: **Fetch API**
  - For making HTTP requests from the frontend to the backend.

- **Styling**:
  - **CSS3**
    - For basic styling of the web pages.

- **UI Components**:
  - Use minimal HTML elements like forms, buttons, and progress indicators.

- **Build Tools**:
  - **None required** for plain JavaScript.

# Step-by-Step Development Process

Below is a detailed guide to building the CV parser app, focusing on developing one part at a time using best practices.

## Phase 1: Planning and Environment Setup

### Step 1: Define Requirements and Specifications

- **Document Functional Requirements**:
  - Supported file types: PDF, DOCX, Images (JPG, PNG).
  - Data fields to extract: Name, Contact Details, Education, Experience, Skills.
  - Output formats: Company-branded PDF and DOCX.

- **Establish Non-Functional Requirements**:
  - Application should run locally without the need for cloud services.
  - Simple frontend interface for user interaction.

### Step 2: Set Up Version Control

- **Initialize a Git Repository**:
  - Use `git init` to create a local repository.

### Step 3: Prepare Development Environment

**Backend**:

- **Install Python 3.x** if not already installed.
- **Install Tesseract OCR**:
  - Download and install from the official source for OCR capabilities.

- **Create a Virtual Environment**:

  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

- **Install Required Python Libraries**:

  ```bash
  pip install fastapi uvicorn pdfminer.six python-docx pytesseract Pillow spacy weasyprint jinja2
  ```

- **Install spaCy Language Model**:

  ```bash
  python -m spacy download en_core_web_sm
  ```

**Frontend**:

- **Set Up Basic Project Structure**:
  - Create a folder for frontend files: HTML, CSS, JavaScript.

## Phase 2: Backend Development

### Step 4: Initialize FastAPI App

- **Create a new Python file**, e.g., `main.py`.

- **Set Up FastAPI Application**:

  ```python
  from fastapi import FastAPI, UploadFile, File
  import uvicorn

  app = FastAPI()

  @app.get("/")
  async def root():
      return {"message": "Welcome to the CV Parser API"}

  if __name__ == "__main__":
      uvicorn.run(app, host="127.0.0.1", port=8000)
  ```

- **Run the Application**:

  ```bash
  uvicorn main:app --reload
  ```

- **Test the API** by navigating to `http://127.0.0.1:8000` in a browser.

### Step 5: Implement File Upload Endpoint

- **Create a Directory for Uploaded Files**:

  ```bash
  mkdir uploads
  ```

- **Update `main.py` with File Upload Endpoint**:

  ```python
  import shutil
  import os

  @app.post("/upload")
  async def upload_file(file: UploadFile = File(...)):
      # Validate file type
      ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
      filename = file.filename
      file_ext = os.path.splitext(filename)[1].lower()
      if file_ext not in ALLOWED_EXTENSIONS:
          return {"error": "Unsupported file type"}
      # Save the file
      file_location = f"uploads/{filename}"
      with open(file_location, "wb") as f:
          shutil.copyfileobj(file.file, f)
      return {"info": f"file '{filename}' saved at '{file_location}'"}
  ```

### Step 6: Implement File Parsing Functions

- **Create a new Python module**, `parsers.py`, to handle parsing logic.

- **Write Parsing Functions in `parsers.py`**:

  ```python
  import os
  from pdfminer.high_level import extract_text
  from docx import Document
  from PIL import Image
  import pytesseract

  def parse_pdf(file_path):
      text = extract_text(file_path)
      return text

  def parse_docx(file_path):
      doc = Document(file_path)
      full_text = [para.text for para in doc.paragraphs]
      return '\n'.join(full_text)

  def parse_image(file_path):
      image = Image.open(file_path)
      text = pytesseract.image_to_string(image)
      return text

  def parse_file(file_path):
      ext = os.path.splitext(file_path)[1].lower()
      if ext == '.pdf':
          return parse_pdf(file_path)
      elif ext == '.docx':
          return parse_docx(file_path)
      elif ext in ['.jpg', '.jpeg', '.png']:
          return parse_image(file_path)
      else:
          raise ValueError('Unsupported file extension.')
  ```

### Step 7: Implement NLP Extraction

- **Create a new Python module**, `nlp_utils.py`, for NLP-related functions.

- **Write NLP Functions in `nlp_utils.py`**:

  ```python
  import re
  import spacy

  nlp = spacy.load('en_core_web_sm')

  def extract_entities(text):
      doc = nlp(text)
      extracted_data = {
          'name': None,
          'email': None,
          'phone': None,
          'education': [],
          'experience': [],
          'skills': []
      }
      # Extract name
      for ent in doc.ents:
          if ent.label_ == 'PERSON':
              extracted_data['name'] = ent.text
              break
      # Extract email
      email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
      if email_match:
          extracted_data['email'] = email_match.group(0)
      # Extract phone number
      phone_match = re.search(r'\+?\d[\d -]{8,12}\d', text)
      if phone_match:
          extracted_data['phone'] = phone_match.group(0)
      # Additional logic for education, experience, skills
      # Can be implemented using keyword matching or advanced NLP
      return extracted_data
  ```

### Step 8: Integrate Parsing and NLP in Backend

- **Update `main.py` to Include Parsing and NLP**:

  ```python
  from parsers import parse_file
  from nlp_utils import extract_entities
  import json

  @app.post("/process")
  async def process_file(file: UploadFile = File(...)):
      # Validate and save the file
      ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
      filename = file.filename
      file_ext = os.path.splitext(filename)[1].lower()
      if file_ext not in ALLOWED_EXTENSIONS:
          return {"error": "Unsupported file type"}
      file_location = f"uploads/{filename}"
      with open(file_location, "wb") as f:
          shutil.copyfileobj(file.file, f)
      # Parse the file
      try:
          text_content = parse_file(file_location)
          # Extract data using NLP
          extracted_data = extract_entities(text_content)
          # Save extracted data as JSON file
          output_location = f"outputs/{os.path.splitext(filename)[0]}.json"
          with open(output_location, "w") as json_file:
              json.dump(extracted_data, json_file)
          return {"data": extracted_data}
      except Exception as e:
          return {"error": str(e)}
  ```

- **Create an Outputs Directory**:

  ```bash
  mkdir outputs
  ```

### Step 9: Generate Formatted CV Outputs

- **Create a Templates Directory**:

  ```bash
  mkdir templates
  ```

- **Create an HTML Template**, e.g., `templates/cv_template.html`:

  ```html
  <!DOCTYPE html>
  <html>
  <head>
      <meta charset="UTF-8">
      <title>CV</title>
      <style>
          /* Add company branding styles here */
      </style>
  </head>
  <body>
      <h1>{{ name }}</h1>
      <p><strong>Email:</strong> {{ email }}</p>
      <p><strong>Phone:</strong> {{ phone }}</p>
      <!-- Add sections for education, experience, skills -->
  </body>
  </html>
  ```

- **Update `main.py` to Generate PDF**:

  ```python
  from weasyprint import HTML
  from jinja2 import Environment, FileSystemLoader

  @app.post("/generate")
  async def generate_cv(file: UploadFile = File(...)):
      # Validate and save the file
      ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
      filename = file.filename
      file_ext = os.path.splitext(filename)[1].lower()
      if file_ext not in ALLOWED_EXTENSIONS:
          return {"error": "Unsupported file type"}
      file_location = f"uploads/{filename}"
      with open(file_location, "wb") as f:
          shutil.copyfileobj(file.file, f)
      # Parse the file
      try:
          text_content = parse_file(file_location)
          # Extract data using NLP
          extracted_data = extract_entities(text_content)
          # Render HTML template
          env = Environment(loader=FileSystemLoader('templates'))
          template = env.get_template('cv_template.html')
          html_content = template.render(extracted_data)
          # Generate PDF
          output_pdf = f"outputs/{os.path.splitext(filename)[0]}_formatted.pdf"
          HTML(string=html_content).write_pdf(output_pdf)
          return {"message": "CV generated", "pdf_path": output_pdf}
      except Exception as e:
          return {"error": str(e)}
  ```

### Step 10: Test Backend Endpoints

- **Use Tool like `curl` or `Postman`** to test the `/process` and `/generate` endpoints.
- **Ensure that uploads, parsing, extraction, and PDF generation work as expected**.

## Phase 3: Frontend Development

### Step 11: Create a Simple HTML Form

- **Create `index.html` in Frontend Folder**:

  ```html
  <!DOCTYPE html>
  <html>
  <head>
      <meta charset="UTF-8">
      <title>CV Parser</title>
  </head>
  <body>
      <h1>Upload Your CV</h1>
      <form id="upload-form">
          <input type="file" id="file-input" name="file" accept=".pdf,.docx,.jpg,.jpeg,.png" required>
          <button type="submit">Upload and Process</button>
      </form>
      <div id="result"></div>

      <script src="script.js"></script>
  </body>
  </html>
  ```

### Step 12: Implement JavaScript Logic

- **Create `script.js`**:

  ```javascript
  document.getElementById('upload-form').addEventListener('submit', function(e) {
      e.preventDefault();
      const fileInput = document.getElementById('file-input');
      const file = fileInput.files[0];
      if (!file) {
          alert('Please select a file!');
          return;
      }

      const formData = new FormData();
      formData.append('file', file);

      fetch('http://127.0.0.1:8000/process', {
          method: 'POST',
          body: formData
      })
      .then(response => response.json())
      .then(data => {
          if (data.error) {
              document.getElementById('result').innerText = `Error: ${data.error}`;
          } else {
              // Display extracted data
              const resultDiv = document.getElementById('result');
              resultDiv.innerHTML = '<h2>Extracted Data:</h2>';
              resultDiv.innerHTML += `<p><strong>Name:</strong> ${data.data.name}</p>`;
              resultDiv.innerHTML += `<p><strong>Email:</strong> ${data.data.email}</p>`;
              resultDiv.innerHTML += `<p><strong>Phone:</strong> ${data.data.phone}</p>`;
              // Add more fields as necessary
          }
      })
      .catch(error => {
          console.error('Error:', error);
      });
  });
  ```

- **Make sure to handle CORS** in the backend. Update `main.py`:

  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI()

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Step 13: Style the Frontend

- **Add Basic Styles** in a `<style>` tag in `index.html` or create a separate `styles.css` file.
- **Ensure the interface is user-friendly**, even if simple.

## Phase 4: Integration and Testing

### Step 14: Functional Testing

- **Test the Complete Workflow**:
  - Upload various CV files in different formats.
  - Verify that the extracted data is accurate.
  - Check that the generated PDF contains the correct information and styling.

### Step 15: Error Handling and Validation

- **Implement Error Handling** in both frontend and backend:
  - Handle cases where the file cannot be processed.
  - Provide user-friendly error messages.

### Step 16: Unit Testing

- **Write Unit Tests** for Parsing and NLP Functions in `parsers.py` and `nlp_utils.py`.
- **Use `pytest`** for running tests.

  ```bash
  pip install pytest
  ```

- **Example Test in `tests/test_parsers.py`**:

  ```python
  from parsers import parse_pdf

  def test_parse_pdf():
      text = parse_pdf('sample_files/sample.pdf')
      assert isinstance(text, str)
      assert len(text) > 0
  ```

### Step 17: Load and Performance Testing

- **Simulate Multiple Requests** to ensure the application can handle concurrent users.
- **Optimize Code** if performance bottlenecks are identified.

## Phase 5: Deployment

Since there's no use of cloud-based tech, and Docker is not required, the application can be run directly on a local machine or an on-premises server.

### Step 18: Prepare for Deployment

- **Ensure All Dependencies are Listed** in a `requirements.txt` file:

  ```bash
  pip freeze > requirements.txt
  ```

- **Test the Application** on the target deployment machine.

### Step 19: Run the Application

- **Start the Backend Server**:

  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

- **Serve the Frontend Files**:
  - Open `index.html` in a web browser.
  - Alternatively, use a simple HTTP server:

    ```bash
    python -m http.server 8080
    ```

    and navigate to `http://localhost:8080/index.html`.

### Step 20: Secure the Application

- **Implement Basic Security Measures**:
  - Ensure the backend server is not accessible from unintended networks.
  - If deploying over the internet, set up SSL certificates for HTTPS (may require additional configuration).

## Phase 6: Maintenance and Future Enhancements

### Step 21: Gather User Feedback

- **Add Mechanisms** to collect user feedback for improvements.

### Step 22: Plan Additional Features

- **Enhancements**:
  - Implement advanced NLP techniques for better data extraction.
  - Add user authentication if necessary.
  - Improve the frontend interface.

### Step 23: Regular Updates

- **Keep Libraries Updated** to the latest versions.
- **Refactor Code** as needed to maintain code quality.

---

# Best Practices Throughout Development

- **Write Clean and Readable Code**:
  - Use meaningful variable and function names.
  - Follow PEP 8 style guidelines for Python code.

- **Use Comments and Documentation**:
  - Comment complex logic.
  - Provide docstrings for functions and modules.

- **Version Control**:
  - Commit changes regularly with meaningful commit messages.

- **Error Handling**:
  - Anticipate possible errors and handle them gracefully.
  - Validate inputs and provide informative error messages.

- **Testing**:
  - Write tests for critical functions to ensure reliability.
  - Use testing to catch bugs early in the development process.

- **Security**:
  - Sanitize user inputs to prevent injection attacks.
  - Avoid exposing internal details in error messages.

- **Performance Optimization**:
  - Profile the application if performance issues arise.
  - Optimize only after identifying bottlenecks.

- **Simplicity**:
  - Keep the application as simple as possible while meeting requirements.
  - Avoid unnecessary complexity.
  