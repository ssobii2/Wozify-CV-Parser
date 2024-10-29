from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import json
from parsers import parse_file
from nlp_utils import extract_entities
from jinja2 import Environment, FileSystemLoader
import pdfkit
import tempfile

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure pdfkit to use the installed wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

@app.get("/")
async def root():
    return {"message": "Welcome to the CV Parser API"}

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
        extracted_data = extract_entities(text_content)
        
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
        extracted_data = extract_entities(text_content)
        
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
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        # Generate PDF
        output_filename = f"{os.path.splitext(filename)[0]}_formatted.pdf"
        output_path = f"outputs/{output_filename}"
        
        pdfkit.from_file(temp_html_path, output_path, options=options, configuration=config)
        
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