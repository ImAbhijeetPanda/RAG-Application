#!/usr/bin/env python3
"""
Setup script for RAG Application with Ollama
"""

import subprocess
import sys
import requests
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def check_ollama_installation():
    """Check if Ollama is installed"""
    print("\n🔍 Checking Ollama installation...")
    result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Ollama is installed: {result.stdout.strip()}")
        return True
    else:
        print("❌ Ollama is not installed")
        print("Please install Ollama from: https://ollama.ai/")
        return False

def check_ollama_running():
    """Check if Ollama server is running"""
    print("\n🔍 Checking if Ollama server is running...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            return True
        else:
            print("❌ Ollama server is not responding")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server")
        print("Please start Ollama: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama server: {e}")
        return False

def pull_required_models():
    """Pull required Ollama models"""
    models = ["llama3.1:latest", "nomic-embed-text"]
    for model in models:
        print(f"\n🔄 Pulling model: {model}")
        print("This may take several minutes depending on your internet connection...")
        result = subprocess.run(f"ollama pull {model}", shell=True)
        if result.returncode == 0:
            print(f"✅ Successfully pulled {model}")
        else:
            print(f"❌ Failed to pull {model}")
            return False
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n🔄 Installing Python dependencies...")
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    # Upgrade pip and install
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True, text=True)
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Python dependencies installed successfully")
        return True
    else:
        print(f"❌ Failed to install dependencies: {result.stderr.strip()}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n🔄 Creating directories...")
    directories = ["data/uploads", "chroma_db"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    return True

def test_application():
    """Test if the application can be imported"""
    print("\n🔄 Testing application imports...")
    try:
        import config
        print("✅ Config module imported successfully")
        from src.pdf_processor import PDFProcessor
        print("✅ PDF processor imported successfully")
        from src.embeddings import OllamaEmbeddings
        print("✅ Embeddings module imported successfully")
        from src.vector_store import ChromaVectorStore
        print("✅ Vector store module imported successfully")
        from src.retrieval_qa import RAGChatbot
        print("✅ Retrieval QA module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 RAG Application with Ollama - Setup Script")
    print("=" * 50)
    if not check_ollama_installation():
        print("\n❌ Setup failed: Ollama not installed")
        return False
    if not create_directories():
        print("\n❌ Setup failed: Could not create directories")
        return False
    if not install_python_dependencies():
        print("\n❌ Setup failed: Could not install Python dependencies")
        return False
    if not test_application():
        print("\n❌ Setup failed: Application import test failed")
        return False
    if not check_ollama_running():
        print("\n⚠️  Ollama server is not running")
        print("Please start Ollama in another terminal: ollama serve")
        print("Then run this script again to pull the required models")
        return True
    print("\n🔄 Pulling required Ollama models...")
    print("This step may take a while (several GB of downloads)")
    user_input = input("Do you want to pull the required models now? (y/n): ")
    if user_input.lower() in ['y', 'yes']:
        if not pull_required_models():
            print("\n❌ Setup failed: Could not pull required models")
            return False
    else:
        print("\n⚠️  Skipping model download")
        print("You can pull models later with:")
        print("  ollama pull llama3.1:latest")
        print("  ollama pull nomic-embed-text")
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nTo start the application:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Start the Streamlit app: streamlit run app.py")
    print("3. Open your browser to the displayed URL")
    print("\nEnjoy your RAG application! 🚀")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
