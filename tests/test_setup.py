#!/usr/bin/env python3
"""
Test script to verify RAG application setup
"""

import sys
import time
import shutil
import os
from pathlib import Path

# Terminal color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_colored(msg, color):
    print(color + msg + RESET)

def clear_cache_files(root="."):
    """Remove __pycache__ folders and .pyc files recursively from root."""
    print_colored("🧹 Clearing cache files...", CYAN)
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove __pycache__ directories
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"))
            print_colored(f"  Removed: {os.path.join(dirpath, '__pycache__')}", YELLOW)
            removed += 1
        # Remove .pyc files
        for filename in filenames:
            if filename.endswith(".pyc"):
                filepath = os.path.join(dirpath, filename)
                os.remove(filepath)
                print_colored(f"  Removed: {filepath}", YELLOW)
                removed += 1
    print_colored(f"✅ Cache cleanup complete. {removed} items removed.\n", GREEN)

def test_imports():
    print_colored("🔍 Testing module imports...", CYAN)
    try:
        import config
        print_colored("✅ config module", GREEN)
        from src.pdf_processor import PDFProcessor
        print_colored("✅ PDF processor", GREEN)
        from src.embeddings import EmbeddingManager
        print_colored("✅ Ollama embeddings", GREEN)
        from src.vector_store import ChromaVectorStore
        print_colored("✅ Vector store", GREEN)
        from src.retrieval_qa import RAGChatbot
        print_colored("✅ RAG chatbot", GREEN)
        from src.utils import check_ollama_status
        print_colored("✅ Utilities", GREEN)
        return True
    except ImportError as e:
        print_colored(f"❌ Import error: {e}", RED)
        return False

def test_ollama_connection():
    print_colored("\n🔍 Testing Ollama connection...", CYAN)
    try:
        from src.utils import check_ollama_status
        status = check_ollama_status()
        if status['status'] == 'running':
            print_colored("✅ Ollama is running", GREEN)
            print_colored(f"   Available models: {len(status.get('available_models', []))}", YELLOW)
            # Check specific models
            models = status.get('available_models', [])
            for model in ['llama3.1:latest', 'nomic-embed-text']:
                if model in models:
                    print_colored(f"✅ {model} model available", GREEN)
                else:
                    print_colored(f"❌ {model} model missing", RED)
                    print_colored(f"   Run: ollama pull {model}", YELLOW)
            return True
        else:
            print_colored(f"❌ Ollama not available: {status.get('error', 'Unknown error')}", RED)
            return False
    except Exception as e:
        print_colored(f"❌ Error testing Ollama: {e}", RED)
        return False

def test_embeddings():
    print_colored("\n🔍 Testing embeddings...", CYAN)
    try:
        from src.embeddings import EmbeddingManager
        manager = EmbeddingManager()
        success = manager.test_embedding("This is a test sentence.")
        if success:
            print_colored("✅ Embeddings working correctly", GREEN)
            dimension = manager.get_embedding_dimension()
            if dimension:
                print_colored(f"   Embedding dimension: {dimension}", YELLOW)
            return True
        else:
            print_colored("❌ Embeddings test failed", RED)
            return False
    except Exception as e:
        print_colored(f"❌ Error testing embeddings: {e}", RED)
        return False

def test_vector_store():
    print_colored("\n🔍 Testing vector store...", CYAN)
    try:
        from src.vector_store import create_vector_store
        vector_store = create_vector_store()
        info = vector_store.get_collection_info()
        print_colored("✅ Vector store initialized", GREEN)
        print_colored(f"   Collection: {info.get('collection_name', 'Unknown')}", YELLOW)
        print_colored(f"   Document count: {info.get('document_count', 0)}", YELLOW)
        return True
    except Exception as e:
        print_colored(f"❌ Error testing vector store: {e}", RED)
        return False

def test_pdf_processor():
    print_colored("\n🔍 Testing PDF processor...", CYAN)
    try:
        from src.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print_colored("✅ PDF processor initialized", GREEN)
        print_colored(f"   Chunk size: {processor.chunk_size}", YELLOW)
        print_colored(f"   Chunk overlap: {processor.chunk_overlap}", YELLOW)
        return True
    except Exception as e:
        print_colored(f"❌ Error testing PDF processor: {e}", RED)
        return False

def test_directories():
    print_colored("\n🔍 Testing directories...", CYAN)
    directories = ["data/uploads", "chroma_db", "src"]
    all_ok = True
    for directory in directories:
        if Path(directory).exists():
            print_colored(f"✅ {directory}", GREEN)
        else:
            print_colored(f"❌ {directory} missing", RED)
            all_ok = False
    return all_ok

def test_files():
    print_colored("\n🔍 Testing files...", CYAN)
    files = [
        "requirements.txt", "config.py", "app.py",
        "src/__init__.py", "src/pdf_processor.py", "src/embeddings.py",
        "src/vector_store.py", "src/retrieval_qa.py", "src/utils.py"
    ]
    all_ok = True
    for file_path in files:
        if Path(file_path).exists():
            print_colored(f"✅ {file_path}", GREEN)
        else:
            print_colored(f"❌ {file_path} missing", RED)
            all_ok = False
    return all_ok

def main():
    clear_cache_files(".")  # Clean cache files before running tests

    print_colored("""
╔══════════════════════════════════════╗
║   🧪 RAG Application - Setup Test   ║
╚══════════════════════════════════════╝
""", CYAN)

    tests = [
        ("Files", test_files),
        ("Directories", test_directories),
        ("Imports", test_imports),
        ("PDF Processor", test_pdf_processor),
        ("Ollama Connection", test_ollama_connection),
        ("Embeddings", test_embeddings),
        ("Vector Store", test_vector_store),
    ]
    passed = 0
    total = len(tests)
    failed_tests = []

    t0 = time.time()
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print_colored(f"❌ {test_name} test failed", RED)
                failed_tests.append(test_name)
        except Exception as e:
            print_colored(f"❌ {test_name} test error: {e}", RED)
            failed_tests.append(test_name)

    print_colored("\n" + "=" * 40, CYAN)
    print_colored(f"📊 Test Results: {passed}/{total} tests passed", GREEN if passed == total else RED)
    print_colored(f"⏱️ Completed in {time.time()-t0:.2f} seconds", CYAN)

    if passed == total:
        print_colored("🎉 All tests passed! Your setup is ready.", GREEN)
        print_colored("\nTo start the application:", CYAN)
        print_colored("  streamlit run app.py", YELLOW)
    else:
        print_colored("⚠️  Some tests failed. Please check the setup.", RED)
        if failed_tests:
            print_colored("❌ Failed tests: " + ', '.join(failed_tests), YELLOW)
        if passed < 3:  # Critical failures
            print_colored("❌ Critical setup issues detected.", RED)
            print_colored("Please run: python setup.py", YELLOW)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
