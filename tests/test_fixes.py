#!/usr/bin/env python3
"""
Test script to verify that the PDF processing fixes are working correctly.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

def test_pdf_validation():
    """Test PDF validation with file paths"""
    print("🧪 Testing PDF validation...")
    
    from src.pdf_processor import validate_pdf_file
    
    # Test with non-existent file
    result = validate_pdf_file('/nonexistent/file.pdf')
    assert result == False, "Should return False for non-existent file"
    print("✅ Non-existent file validation works")
    
    # Test with invalid file (create a text file with .pdf extension)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b'This is not a PDF file')
        tmp_path = tmp_file.name
    
    try:
        result = validate_pdf_file(tmp_path)
        assert result == False, "Should return False for invalid PDF"
        print("✅ Invalid PDF validation works")
    finally:
        os.unlink(tmp_path)

def test_file_saving():
    """Test file saving functionality"""
    print("🧪 Testing file saving...")
    
    from src.utils import save_uploaded_file
    import config
    
    # Create a mock uploaded file object
    class MockUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self.content = content
        
        def getbuffer(self):
            return self.content
    
    # Test saving a file
    mock_file = MockUploadedFile("test.pdf", b"test content")
    
    try:
        saved_path = save_uploaded_file(mock_file)
        assert os.path.exists(saved_path), "File should be saved"
        
        # Check content
        with open(saved_path, 'rb') as f:
            content = f.read()
        assert content == b"test content", "Content should match"
        
        print("✅ File saving works")
        
        # Clean up
        os.unlink(saved_path)
        
    except Exception as e:
        print(f"❌ File saving failed: {e}")
        raise

def test_embedding_format():
    """Test that embedding calls are formatted correctly"""
    print("🧪 Testing embedding format...")
    
    from src.embeddings import EmbeddingManager
    
    # This will test the format without actually calling Ollama
    # (since Ollama might not be running in test environment)
    manager = EmbeddingManager()
    
    # Test that the method exists and handles string input
    try:
        # This will likely fail due to no Ollama connection, but we can check the format
        manager.embed_text("test text")
    except Exception as e:
        # Expected to fail, but should not be a type error
        error_msg = str(e)
        assert "'str' object has no attribute" not in error_msg, f"Should not have string attribute error: {error_msg}"
        print("✅ Embedding format is correct (connection error expected)")

def main():
    """Run all tests"""
    print("🚀 Running fix verification tests...\n")
    
    try:
        test_pdf_validation()
        print()
        
        test_file_saving()
        print()
        
        test_embedding_format()
        print()
        
        print("🎉 All tests passed! The fixes are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
