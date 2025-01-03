# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Standard library imports
import os
import json
import shutil
import logging
import time
from functools import wraps
import asyncio

# Local imports
from parsers import parse_file
from nlp_utils import CVExtractor

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

# Initialize FastAPI app and CV extractor
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

# Mount static directories
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Utility functions
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
        text_content = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, parse_file, file_location),
            timeout=60.0
        )
        logger.info("File parsing completed")
        
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

# Basic endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    return FileResponse("frontend/index.html")

# File handling endpoints
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and save a file"""
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
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
    """Process uploaded file and extract information"""
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {file_ext}")
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    file_location = None
    try:
        logger.info(f"Processing file: {filename}")
        
        os.makedirs("uploads", exist_ok=True)
        
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"File saved to: {file_location}")
        
        extracted_data = await process_with_timeout(file_location)
        
        os.makedirs("outputs", exist_ok=True)
        
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
        if file_location and os.path.exists(file_location):
            os.remove(file_location)
            logger.info(f"Cleaned up temporary file: {file_location}")

# Data management endpoints
@app.get("/check_json/{filename}")
async def check_json(filename: str):
    """Check if a JSON file exists and return its contents"""
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
    """Save form data to JSON file"""
    try:
        filename = data.get("filename")
        if not filename:
            raise HTTPException(status_code=400, detail="Filename not provided")
            
        os.makedirs("outputs", exist_ok=True)
        
        output_location = f"outputs/{filename}"
        with open(output_location, "w", encoding='utf-8') as json_file:
            json.dump(data["formData"], json_file, indent=2)
            
        return {"message": "Form data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)