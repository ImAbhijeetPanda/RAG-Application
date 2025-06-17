# src/utils.py

import os
import requests
from pathlib import Path
import config

def check_ollama_status():
    """Check if Ollama is running and required models are available"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"status": "not_running", "error": "Ollama service not responding"}

        # Get available models
        models_data = response.json()
        available_models = [model['name'] for model in models_data.get('models', [])]

        # Check if required models are available
        text_model_available = config.OLLAMA_MODEL in available_models
        embedding_model_available = config.OLLAMA_EMBEDDING_MODEL in available_models

        return {
            "status": "running",
            "text_model_available": text_model_available,
            "embedding_model_available": embedding_model_available,
            "available_models": available_models
        }
    except requests.exceptions.RequestException as e:
        return {"status": "not_running", "error": str(e)}

def validate_uploaded_file(uploaded_file):
    """Validate uploaded file size and type"""
    # Check file size
    if uploaded_file.size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        return {
            "valid": False,
            "error": f"File size exceeds {config.MAX_FILE_SIZE_MB} MB limit"
        }

    # Check file extension
    file_extension = Path(uploaded_file.name).suffix.lower()
    if file_extension not in config.ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": f"File type {file_extension} not allowed. Allowed types: {config.ALLOWED_EXTENSIONS}"
        }

    return {"valid": True, "error": ""}

def save_uploaded_file(uploaded_file):
    """Save uploaded file to the configured upload directory"""
    try:
        # Ensure upload directory exists
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Create file path
        file_path = config.DATA_DIR / uploaded_file.name

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return str(file_path)
    except Exception as e:
        raise Exception(f"Failed to save file: {str(e)}")

def display_error_message(e, context=""):
    """Display error message in Streamlit"""
    import streamlit as st
    st.error(f"❌ Error in {context}: {str(e)}")

def display_success_message(msg):
    """Display success message in Streamlit"""
    import streamlit as st
    st.success(f"✅ {msg}")

def load_css_style():
    """Load custom CSS styles for the app"""
    return """
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """

def format_file_size(size):
    """Format file size in human readable format"""
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024**2:
        return f"{size/1024:.2f} KB"
    else:
        return f"{size/1024**2:.2f} MB"

def clean_upload_directory():
    """Clean up uploaded files from the upload directory"""
    try:
        if config.DATA_DIR.exists():
            for file_path in config.DATA_DIR.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
    except Exception as e:
        print(f"Error cleaning upload directory: {e}")
