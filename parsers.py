import os
from pdfminer.high_level import extract_text
from docx import Document

def parse_pdf(file_path):
    """Extract text from PDF files."""
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")

def parse_docx(file_path):
    """Extract text from DOCX files."""
    try:
        doc = Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        raise Exception(f"Error parsing DOCX: {str(e)}")

def parse_file(file_path):
    """Parse file based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return parse_pdf(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    else:
        raise ValueError('Unsupported file extension.') 