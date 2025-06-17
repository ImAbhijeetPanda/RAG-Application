#!/usr/bin/env python3
"""
Environment setup script for RAG Application with Ollama
Creates a virtual environment and installs dependencies.
Checks for core dependencies and Ollama status.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   This application requires Python 3.8 or higher")
        return False

def create_virtual_environment():
    """Create a virtual environment"""
    env_name = "rag_env"
    print(f"\n🔄 Creating virtual environment: {env_name}")
    if Path(env_name).exists():
        print(f"⚠️  Virtual environment '{env_name}' already exists")
        user_input = input("Do you want to recreate it? (y/n): ")
        if user_input.lower() in ['y', 'yes']:
            print(f"🗑️  Removing existing environment...")
            import shutil
            shutil.rmtree(env_name)
        else:
            print("✅ Using existing virtual environment")
            return env_name
    result = subprocess.run([sys.executable, "-m", "venv", env_name], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Virtual environment '{env_name}' created successfully")
        return env_name
    else:
        print(f"❌ Failed to create virtual environment: {result.stderr}")
        return None

def get_activation_command(env_name):
    """Get the activation command for the virtual environment"""
    if os.name == 'nt':  # Windows
        return f"{env_name}\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        return f"source {env_name}/bin/activate"

def get_python_executable(env_name):
    """Get the Python executable path in the virtual environment"""
    if os.name == 'nt':  # Windows
        return f"{env_name}\\Scripts\\python.exe"
    else:
        return f"{env_name}/bin/python"

def install_dependencies(env_name):
    """Install dependencies in the virtual environment"""
    print(f"\n🔄 Installing dependencies in virtual environment...")
    python_exe = get_python_executable(env_name)
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    # Upgrade pip
    result = subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to upgrade pip: {result.stderr}")
        return False
    # Install requirements
    result = subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Dependencies installed successfully")
        return True
    else:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        return False

def test_installation(env_name):
    """Test the installation in the virtual environment"""
    print(f"\n🔄 Testing installation...")
    python_exe = get_python_executable(env_name)
    # Test core imports
    test_script = '''
import sys
print(f"Python version: {sys.version}")
try:
    import streamlit
    print("✅ Streamlit imported successfully")
except ImportError as e:
    print(f"❌ Streamlit import failed: {e}")
    sys.exit(1)
try:
    import langchain
    print("✅ LangChain imported successfully")
except ImportError as e:
    print(f"❌ LangChain import failed: {e}")
    sys.exit(1)
try:
    import chromadb
    print("✅ ChromaDB imported successfully")
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    sys.exit(1)
try:
    import PyPDF2
    print("✅ PyPDF2 imported successfully")
except ImportError as e:
    print(f"❌ PyPDF2 import failed: {e}")
    sys.exit(1)
print("✅ All core dependencies are working")
'''
    result = subprocess.run([python_exe, "-c", test_script], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Installation test passed")
        print(result.stdout)
        return True
    else:
        print("❌ Installation test failed")
        print(result.stderr)
        return False

def check_ollama():
    """Check if Ollama is installed and running locally"""
    print("\n🔎 Checking Ollama status...")
    try:
        # Try calling the Ollama server's /api/tags endpoint
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            if response.status == 200:
                print("✅ Ollama server is running on localhost:11434")
                return True
    except Exception as e:
        print(f"⚠️  Ollama is not running or not installed (localhost:11434 unreachable): {e}")
    print("ℹ️  Ollama is optional for local dev, but required for model inference.")
    return False

def create_activation_script(env_name):
    """Create a convenient activation script"""
    activation_cmd = get_activation_command(env_name)
    if os.name == 'nt':  # Windows
        script_name = "activate_env.bat"
        script_content = f"""@echo off
echo Activating RAG environment...
call {activation_cmd}
echo Environment activated! You can now run:
echo   python app.py
echo   streamlit run app.py
cmd /k
"""
    else:  # Unix/Linux/macOS
        script_name = "activate_env.sh"
        script_content = f"""#!/bin/bash
echo "Activating RAG environment..."
{activation_cmd}
echo "Environment activated! You can now run:"
echo "  python app.py"
echo "  streamlit run app.py"
exec "$SHELL"
"""
    with open(script_name, 'w') as f:
        f.write(script_content)
    if os.name != 'nt':
        os.chmod(script_name, 0o755)
    print(f"✅ Created activation script: {script_name}")
    return script_name

def main():
    """Main environment setup function"""
    print("🐍 RAG Application - Virtual Environment Setup")
    print("=" * 50)
    # Check Python version
    if not check_python_version():
        return False
    # Create virtual environment
    env_name = create_virtual_environment()
    if not env_name:
        return False
    # Install dependencies
    if not install_dependencies(env_name):
        return False
    # Test installation
    if not test_installation(env_name):
        return False
    # Check Ollama
    check_ollama()
    # Create activation script
    script_name = create_activation_script(env_name)
    # Success message
    print("\n" + "=" * 50)
    print("🎉 Virtual environment setup completed successfully!")
    print(f"\nVirtual environment: {env_name}")
    print(f"Activation script: {script_name}")
    print("\nTo activate the environment:")
    if os.name == 'nt':  # Windows
        print(f"  {script_name}")
        print("  OR")
        print(f"  {get_activation_command(env_name)}")
    else:  # Unix/Linux/macOS
        print(f"  ./{script_name}")
        print("  OR")
        print(f"  {get_activation_command(env_name)}")
    print("\nOnce activated, you can run:")
    print("  python test_setup.py    # Test the setup")
    print("  streamlit run app.py    # Start the application")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
