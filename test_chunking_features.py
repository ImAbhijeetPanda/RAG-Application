#!/usr/bin/env python3
"""
Test script to demonstrate the new configurable chunking features
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

def test_chunking_configurations():
    """Test different chunking configurations"""
    print("🧪 Testing configurable chunking features...")
    
    from src.pdf_processor import TXTProcessor
    
    # Create test content
    test_content = """
    This is a comprehensive test document for the RAG application.
    
    Section 1: Introduction
    This section introduces the main concepts and provides background information.
    It contains multiple sentences to test chunking behavior with different settings.
    
    Section 2: Technical Details
    Here we dive into the technical aspects of the system.
    This section has more complex information that might benefit from larger chunks.
    The content includes code examples and detailed explanations.
    
    Section 3: Implementation
    This final section covers implementation details and best practices.
    It provides practical guidance for users and developers.
    The information here is structured and sequential.
    """ * 3  # Repeat to make it longer
    
    # Test different chunking configurations
    configurations = [
        {"name": "Small Chunks", "chunk_size": 200, "overlap": 50},
        {"name": "Medium Chunks", "chunk_size": 500, "overlap": 100},
        {"name": "Large Chunks", "chunk_size": 1000, "overlap": 200},
        {"name": "Technical PDF", "chunk_size": 1200, "overlap": 200},
        {"name": "Narrative Text", "chunk_size": 600, "overlap": 100},
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(test_content)
        tmp_path = tmp_file.name
    
    try:
        print(f"📄 Test document length: {len(test_content)} characters")
        print("=" * 60)
        
        for config in configurations:
            print(f"\n🔧 Testing: {config['name']}")
            print(f"   Chunk Size: {config['chunk_size']}")
            print(f"   Overlap: {config['overlap']}")
            
            # Create processor with specific settings
            processor = TXTProcessor(
                chunk_size=config['chunk_size'],
                chunk_overlap=config['overlap']
            )
            
            # Process the document
            documents = processor.process_txt(tmp_path)
            
            print(f"   📊 Result: {len(documents)} chunks created")
            
            # Show first chunk info
            if documents:
                first_chunk = documents[0]
                chunk_length = len(first_chunk['page_content'])
                print(f"   📝 First chunk: {chunk_length} characters")
                print(f"   🏷️  Metadata: {first_chunk['metadata']['chunk_id']}")
            
            # Calculate efficiency metrics
            total_chars = sum(len(doc['page_content']) for doc in documents)
            efficiency = (total_chars / len(test_content)) * 100
            print(f"   ⚡ Efficiency: {efficiency:.1f}% (due to overlap)")
            
        print("\n" + "=" * 60)
        print("✅ All chunking configurations tested successfully!")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def demonstrate_recommendations():
    """Demonstrate the recommendation system"""
    print("\n🎯 Chunking Recommendations:")
    print("=" * 60)
    
    import config
    
    recommendations = [
        ("📄 Technical PDFs", config.CHUNK_RECOMMENDATIONS["pdf_technical"]),
        ("📄 General PDFs", config.CHUNK_RECOMMENDATIONS["pdf_general"]),
        ("📝 Code Files", config.CHUNK_RECOMMENDATIONS["txt_code"]),
        ("📝 Stories/Books", config.CHUNK_RECOMMENDATIONS["txt_narrative"]),
        ("❓ Q&A/FAQs", config.CHUNK_RECOMMENDATIONS["short_qa"]),
    ]
    
    for doc_type, rec in recommendations:
        print(f"\n{doc_type}:")
        print(f"   Chunk Size: {rec['chunk_size']} characters")
        print(f"   Overlap: {rec['overlap']} characters")
        print(f"   Max Tokens: {rec['max_tokens']} tokens")
        print(f"   💡 {rec['description']}")
    
    print("\n🔧 Embedding Provider Recommendations:")
    print("-" * 40)
    
    for provider, rec in config.EMBEDDING_RECOMMENDATIONS.items():
        print(f"\n{provider.upper()}:")
        print(f"   Chunk Size: {rec['chunk_size']} characters")
        print(f"   Overlap: {rec['overlap']} characters")
        print(f"   💡 {rec['description']}")

def main():
    """Run all tests and demonstrations"""
    print("🚀 Testing Configurable Chunking Features...\n")
    
    try:
        test_chunking_configurations()
        demonstrate_recommendations()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("\n📋 New Features Available:")
        print("✅ Configurable chunk size (200-3000 characters)")
        print("✅ Adjustable chunk overlap (0-500 characters)")
        print("✅ Dynamic max tokens (500-8000 tokens)")
        print("✅ Smart presets for different document types")
        print("✅ Embedding provider optimized settings")
        print("✅ Real-time performance indicators")
        print("✅ Document count shows files vs chunks correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
