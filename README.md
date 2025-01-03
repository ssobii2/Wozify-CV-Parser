# Wozify CV Parser

A sophisticated CV/Resume parser that supports both English and Hungarian documents. The system uses custom-trained NLP models to accurately extract and classify CV sections, making it ideal for HR professionals and recruitment agencies. Currently, it's for making company-branded CVs.

## Features

- 📄 Support for multiple document formats (PDF, DOCX)
- 🌍 Multilingual support (English and Hungarian)
- 🤖 Custom-trained NLP models for accurate section classification
- 🔍 Advanced entity recognition for personal information extraction
- 📊 Structured JSON output
- 🎨 Clean and modern user interface
- 🔄 Real-time preview functionality

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.9 or higher (required for latest PyTorch)
- pip (Python package manager)
- Git
- CUDA Toolkit (optional, for GPU support)
  - For NVIDIA GPUs: CUDA 11.8 or higher recommended
  - Check your GPU compatibility: `nvidia-smi`

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/Wozify-CV-Parser.git
cd Wozify-CV-Parser
```

2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python -m venv venv
source venv/bin/activate
```

3. Install PyTorch
```bash
# For CUDA (GPU) - Windows/Linux (add your cuda version)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/{YOUR_CUDA_VERSION}

# For CPU only - Windows/Linux
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# For MacOS (both CPU and M1/M2)
pip3 install torch torchvision
```

4. Verify PyTorch Installation
```python
# Run in Python console
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
```

5. Install required packages
```bash
pip install -r requirements.txt
```

6. Download required language models
```bash
python -m spacy download en_core_web_sm
python -m spacy download hu_core_news_md
```

7. Download custom trained models
```bash
# Create models directory
mkdir -p models/textcat_model models/fasttext_model
```
Download the models from Hugging Face:
- English CV Section Classification Model: [ThunderJaw/en_textcat_resume_sections](https://huggingface.co/ThunderJaw/en_textcat_resume_sections)
- Hungarian CV Section Classification Model: [ThunderJaw/hu_fasttext_resume_sections](https://huggingface.co/ThunderJaw/hu_fasttext_resume_sections)

Place the downloaded model files in their respective directories:
- English model files → `models/textcat_model/`
- Hungarian model files → `models/fasttext_model/`

## Project Structure

```
Wozify-CV-Parser/
├── main.py                 # FastAPI application entry point
├── parsers.py             # Document parsing utilities
├── requirements.txt       # Python dependencies
├── nlp_utils/            # NLP processing modules
│   ├── cv_section_parser.py
│   ├── cv_section_parser_hu.py
│   ├── experience_extractor.py
│   ├── education_extractor.py
│   └── ...
├── models/               # Trained NLP models
│   ├── textcat_model/    # English models
│   └── fasttext_model/   # Hungarian models
├── static/              # Frontend assets
├── templates/           # HTML templates
├── outputs/             # Processed outputs
```

## Configuration

1. Create necessary directories if they don't exist:
```bash
mkdir -p uploads outputs
```

2. Ensure the models are in the correct location:
```
models/
├── textcat_model/    # English section classification model
└── fasttext_model/   # Hungarian section classification model
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the application:
- Web Interface: http://localhost:8000

## API Endpoints

### Main Endpoints
- `GET /`: Serve the frontend HTML

- `POST /upload`: Upload a CV file
  - Supports PDF and DOCX formats
  - Returns a unique identifier for the uploaded file

- `POST /process`: Process an uploaded CV
  - Requires the file identifier from the upload endpoint
  - Returns structured JSON with extracted information

- `GET /check_json/{filename}`: Check if a JSON file exists and return its contents
