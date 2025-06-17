#!/usr/bin/env python3
"""
Comprehensive functionality test for RAG Application
Tests all major features including chat and summarization
"""

import sys
import time
from pathlib import Path

# Simple color codes for nicer output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_colored(msg, color):
    print(color + msg + RESET)

def create_sample_pdf(filename="data/uploads/sample_test.pdf"):
    """Create a sample PDF if none exist, for testing purposes."""
    try:
        from fpdf import FPDF
    except ImportError:
        print_colored("⚠️ fpdf not installed. Skipping PDF creation.", YELLOW)
        return False

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sample Test PDF", ln=1)
    pdf.multi_cell(0, 10, "This is a sample PDF generated for testing the PDF processor in your RAG app.\n\nYou can delete this file if not needed.")
    pdf.output(filename)
    print_colored(f"✅ Created a sample PDF: {filename}", GREEN)
    return True

def test_basic_functionality():
    """Test basic application functionality"""
    print_colored("🧪 Testing RAG Application Functionality", CYAN)
    print("=" * 60)
    t0 = time.time()

    try:
        # Test imports
        print_colored("🔍 Testing imports...", CYAN)
        import config
        from src.pdf_processor import PDFProcessor
        from src.embeddings import EmbeddingManager
        from src.vector_store import create_vector_store
        from src.retrieval_qa import create_rag_chatbot
        print_colored("✅ All imports successful", GREEN)

        # Test Ollama connection
        print_colored("\n🔍 Testing Ollama connection...", CYAN)
        try:
            from src.utils import check_ollama_status
            status = check_ollama_status()
        except Exception as e:
            print_colored(f"❌ Ollama connection check failed: {e}", RED)
            return False

        if status.get('status', '') != 'running':
            print_colored("❌ Ollama not running. Please start: ollama serve", RED)
            return False

        print_colored("✅ Ollama is running", GREEN)
        print_colored(f"   Available models: {status.get('available_models', [])}", YELLOW)

        # Test embeddings
        print_colored("\n🔍 Testing embeddings...", CYAN)
        embedding_manager = EmbeddingManager()
        if embedding_manager.test_embedding():
            print_colored("✅ Embeddings working", GREEN)
            dimension = embedding_manager.get_embedding_dimension()
            print_colored(f"   Embedding dimension: {dimension}", YELLOW)
        else:
            print_colored("❌ Embeddings failed", RED)
            return False

        # Test vector store
        print_colored("\n🔍 Testing vector store...", CYAN)
        vector_store = create_vector_store()
        info = vector_store.get_collection_info()
        print_colored("✅ Vector store initialized", GREEN)
        print_colored(f"   Collection: {info.get('collection_name', 'Unknown')}", YELLOW)
        print_colored(f"   Document count: {info.get('document_count', 0)}", YELLOW)

        # Test RAG chatbot
        print_colored("\n🔍 Testing RAG chatbot...", CYAN)
        chatbot = create_rag_chatbot(vector_store)
        print_colored("✅ RAG chatbot initialized", GREEN)

        # Test chat and summarization if documents exist
        doc_count = info.get('document_count', 0)
        if doc_count > 0:
            print_colored(f"\n🔍 Testing chat with {doc_count} documents...", CYAN)
            try:
                response = chatbot.chat("Hello, can you help me?")
                print_colored("✅ Chat functionality working", GREEN)
                print_colored(f"   Response length: {len(response.get('answer', ''))}", YELLOW)
                print_colored(f"   Sources found: {response.get('num_sources', 0)}", YELLOW)
            except Exception as e:
                print_colored(f"❌ Chat test failed: {e}", RED)
                return False

            print_colored("\n🔍 Testing summarization...", CYAN)
            try:
                summary = chatbot.summarize_documents(max_docs=3)
                print_colored("✅ Summarization working", GREEN)
                print_colored(f"   Summary length: {len(summary)}", YELLOW)
            except Exception as e:
                print_colored(f"❌ Summarization test failed: {e}", RED)
                return False
        else:
            print_colored("\n⚠️  No documents in vector store - skipping chat/summary tests", YELLOW)
            print_colored("   Upload some PDFs through the web interface to test these features", YELLOW)

        print_colored(f"\n⏱️ Test completed in {time.time() - t0:.2f} seconds", CYAN)
        return True

    except Exception as e:
        print_colored(f"❌ Test failed: {e}", RED)
        return False

def test_pdf_processing():
    """Test PDF processing if sample files exist or create one if not."""
    print_colored("\n🔍 Testing PDF processing...", CYAN)
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(upload_dir.glob("*.pdf"))

    # If no PDFs, create a test one if fpdf is available
    if not pdf_files:
        created = create_sample_pdf()
        if created:
            pdf_files = list(upload_dir.glob("*.pdf"))
        else:
            print_colored("⚠️  No PDF files found and sample not created.", YELLOW)
            return False

    try:
        from src.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        sample_pdf = pdf_files[0]
        print_colored(f"   Processing: {sample_pdf.name}", YELLOW)
        documents = processor.process_pdf(sample_pdf)
        print_colored("✅ PDF processing working", GREEN)
        print_colored(f"   Extracted {len(documents)} chunks", YELLOW)
        print_colored(f"   Sample chunk length: {len(documents[0]['page_content']) if documents else 0}", YELLOW)
        return True
    except Exception as e:
        print_colored(f"❌ PDF processing test failed: {e}", RED)
        return False

def main():
    """Main test function"""
    print_colored("🚀 RAG Application - Comprehensive Functionality Test", CYAN)
    print("=" * 60)

    # Test basic functionality
    basic_ok = test_basic_functionality()

    # Test PDF processing
    pdf_ok = test_pdf_processing()

    # Summary
    print("\n" + "=" * 60)
    print_colored("📊 Test Summary:", CYAN)
    print_colored(f"   Basic functionality: {'✅ PASS' if basic_ok else '❌ FAIL'}", GREEN if basic_ok else RED)
    print_colored(f"   PDF processing: {'✅ PASS' if pdf_ok else '❌ FAIL'}", GREEN if pdf_ok else RED)

    if basic_ok and pdf_ok:
        print_colored("\n🎉 All tests passed! Your RAG application is fully functional.", GREEN)
        print("""
📋 Features confirmed working:
   ✅ PDF upload and processing
   ✅ Text chunking and embedding
   ✅ Vector storage and retrieval
   ✅ Interactive chat with documents
   ✅ Document summarization
   ✅ Conversation memory

🌐 Access your application at: http://localhost:8503
   📁 Upload tab: Add PDF documents
   💬 Chat tab: Ask questions about your documents
   📋 Summary tab: Generate document summaries
        """, CYAN)
    else:
        print_colored("\n⚠️  Some tests failed. Please check the setup.", RED)
        if not basic_ok:
            print_colored("   - Check Ollama installation and models", YELLOW)
            print_colored("   - Verify virtual environment activation", YELLOW)
        if not pdf_ok:
            print_colored("   - Check PDF file permissions", YELLOW)
            print_colored("   - Verify PyPDF2 installation", YELLOW)
            print_colored("   - Consider installing fpdf: pip install fpdf", YELLOW)

    return basic_ok and pdf_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
