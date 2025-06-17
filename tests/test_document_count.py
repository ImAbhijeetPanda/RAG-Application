#!/usr/bin/env python3
"""
Test script to verify document counting works correctly
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

def test_document_counting():
    """Test that document counting shows files vs chunks correctly"""
    print("🧪 Testing document counting...")
    
    from src.vector_store import create_vector_store
    from src.pdf_processor import TXTProcessor
    
    # Create a test vector store and clear it
    vector_store = create_vector_store()
    vector_store.reset_collection()  # Start with clean slate

    # Create test content that will be chunked
    long_text = "This is a test document. " * 100  # Long enough to create multiple chunks
    
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(long_text)
        tmp_path = tmp_file.name
    
    try:
        # Process the file
        processor = TXTProcessor(chunk_size=200, chunk_overlap=50)  # Small chunks to force multiple
        documents = processor.process_txt(tmp_path)
        
        print(f"📄 Created {len(documents)} chunks from 1 file")
        
        # Add to vector store
        vector_store.add_documents(documents)
        
        # Get collection info
        info = vector_store.get_collection_info()
        file_count = info.get('file_count', 0)
        chunk_count = info.get('document_count', 0)
        
        print(f"📊 Vector store reports:")
        print(f"   Files: {file_count}")
        print(f"   Chunks: {chunk_count}")
        
        # Verify the counts
        if file_count == 1 and chunk_count == len(documents):
            print("✅ Document counting works correctly!")
            return True
        else:
            print(f"❌ Document counting failed. Expected 1 file and {len(documents)} chunks")
            return False
            
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        # Reset vector store
        try:
            vector_store.reset_collection()
        except:
            pass

def main():
    """Run the test"""
    print("🚀 Testing document counting fix...\n")
    
    try:
        success = test_document_counting()
        
        if success:
            print("\n🎉 All tests passed! Document counting is working correctly.")
            print("Now when you upload 1 file, it will show '📚 Files: 1' instead of counting chunks.")
        else:
            print("\n❌ Test failed. Document counting needs more work.")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
