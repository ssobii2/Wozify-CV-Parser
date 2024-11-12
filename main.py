from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import json
from parsers import parse_file
from nlp_utils import (
    CVExtractor, ProfileExtractor, EducationExtractor, 
    ExperienceExtractor, SkillsExtractor, LanguageExtractor,
    CurrentPositionExtractor
)
from jinja2 import Environment, FileSystemLoader
import pdfkit
import tempfile

app = FastAPI()
cv_extractor = CVExtractor()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend directory as static files
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
# Mount the assets directory
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Configure pdfkit
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

@app.get("/api")
async def root():
    """API root endpoint"""
    return {"message": "Welcome to the CV Parser API"}

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    return FileResponse("frontend/index.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Save the file
    file_location = f"uploads/{filename}"
    try:
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return {"info": f"file '{filename}' saved at '{file_location}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    # Validate file type
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save the file
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Parse the file
        text_content = parse_file(file_location)
        
        # Extract data using NLP
        extracted_data = cv_extractor.extract_entities(text_content)
        
        # Create outputs directory if it doesn't exist
        os.makedirs("outputs", exist_ok=True)
        
        # Save extracted data as JSON file
        output_location = f"outputs/{os.path.splitext(filename)[0]}.json"
        with open(output_location, "w", encoding='utf-8') as json_file:
            json.dump(extracted_data, json_file, indent=2)
        
        return {"data": extracted_data}
    
    except Exception as e:
        print(f"Error in process_file: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_location):
            os.remove(file_location)

@app.post("/generate")
async def generate_cv(file: UploadFile = File(...)):
    # Validate file type
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    try:
        # Save the uploaded file
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Parse and extract data
        text_content = parse_file(file_location)
        extracted_data = cv_extractor.extract_entities(text_content)
        
        # Add absolute paths for images
        base_dir = os.path.abspath(os.path.dirname(__file__))
        extracted_data.update({
            'logo_path': os.path.join(base_dir, 'assets', 'images', 'logo.png'),
            'skills_icon_path': os.path.join(base_dir, 'assets', 'images', 'skills.png'),
            'education_icon_path': os.path.join(base_dir, 'assets', 'images', 'education.png'),
            'profile_icon_path': os.path.join(base_dir, 'assets', 'images', 'profile.png'),
            'work_icon_path': os.path.join(base_dir, 'assets', 'images', 'work.png'),
        })
        
        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('cv_template.html')
        
        # Render HTML
        html_content = template.render(**extracted_data)
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name
        
        # Configure PDF options
        options = {
            'page-size': 'A4',
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None
        }
        
        # Ensure the CSS file path is correct
        css_path = os.path.join(base_dir, 'templates', 'cv_template.css')
        
        # Generate PDF with CSS
        output_filename = f"{os.path.splitext(filename)[0]}_formatted.pdf"
        output_path = f"outputs/{output_filename}"
        
        pdfkit.from_file(temp_html_path, output_path, options=options, configuration=config, css=css_path)
        
        # Clean up temporary file
        os.unlink(temp_html_path)
        
        # Return the PDF file
        return FileResponse(
            output_path,
            media_type='application/pdf',
            filename=output_filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)