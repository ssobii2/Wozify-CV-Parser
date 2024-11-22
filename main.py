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
import logging
import time
from functools import wraps
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            raise
    return wrapper

async def process_with_timeout(file_location):
    """Process file with timeout"""
    try:
        # Parse the file with a timeout of 60 seconds
        text_content = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, parse_file, file_location),
            timeout=60.0
        )
        logger.info("File parsing completed")
        
        # Extract data using NLP with a timeout of 120 seconds
        extracted_data = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, cv_extractor.extract_entities, text_content),
            timeout=120.0
        )
        logger.info("NLP extraction completed")
        
        return extracted_data
    except asyncio.TimeoutError:
        logger.error("Processing timeout exceeded")
        raise HTTPException(status_code=408, detail="Processing timeout exceeded")
    except Exception as e:
        logger.error(f"Error in process_with_timeout: {str(e)}")
        raise

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
@log_time
async def process_file(file: UploadFile = File(...)):
    # Validate file type
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {file_ext}")
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    file_location = None
    try:
        logger.info(f"Processing file: {filename}")
        
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save the file
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"File saved to: {file_location}")
        
        # Process file with timeout
        extracted_data = await process_with_timeout(file_location)
        
        # Create outputs directory if it doesn't exist
        os.makedirs("outputs", exist_ok=True)
        
        # Save extracted data as JSON file
        output_location = f"outputs/{os.path.splitext(filename)[0]}.json"
        with open(output_location, "w", encoding='utf-8') as json_file:
            json.dump(extracted_data, json_file, indent=2)
        logger.info(f"Results saved to: {output_location}")
        
        return {"data": extracted_data}
    
    except Exception as e:
        error_msg = f"Error processing file {filename}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # Clean up uploaded file
        if file_location and os.path.exists(file_location):
            os.remove(file_location)
            logger.info(f"Cleaned up temporary file: {file_location}")

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

@app.get("/check_json/{filename}")
async def check_json(filename: str):
    """Check if a JSON file exists and return its contents if it does"""
    try:
        json_path = f"outputs/{filename}"
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON file")
        except UnicodeDecodeError:
            raise HTTPException(status_code=500, detail="File encoding error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/save_form")
async def save_form(data: dict):
    try:
        # Get the filename from the data
        filename = data.get("filename")
        if not filename:
            raise HTTPException(status_code=400, detail="Filename not provided")
            
        # Ensure the outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Save the form data to the JSON file
        output_location = f"outputs/{filename}"
        with open(output_location, "w", encoding='utf-8') as json_file:
            json.dump(data["formData"], json_file, indent=2)
            
        return {"message": "Form data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)