"""
Configuration file for RAG application with Ollama
"""

import os
from pathlib import Path

# =========[ Base Directory Setup ]=========
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data" / "uploads"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# =========[ Mode Configuration ]=========
# Choose "chat" for conversational mode or "summarize" for summary extraction
MODE = "chat"  # Options: "chat", "summarize"

# =========[ Ollama Model Configuration ]=========
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:latest"                # For main language generation
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"  # For document embeddings

# =========[ Embedding Provider Options ]=========
# Available embedding providers: "ollama", "openai", "huggingface", "chromadb_default"
EMBEDDING_PROVIDER = "chromadb_default"  # Default to ChromaDB's built-in embeddings

# OpenAI Embeddings Configuration
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"

# Hugging Face Embeddings Configuration
HUGGINGFACE_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# =========[ Text Processing & Chunking ]=========
# Default chunk settings (can be overridden in UI)
DEFAULT_CHUNK_SIZE = 1000 if MODE == "chat" else 1500
DEFAULT_CHUNK_OVERLAP = 200 if MODE == "chat" else 100
DEFAULT_MAX_TOKENS = 4000

# Dynamic settings (will be set by UI)
CHUNK_SIZE = DEFAULT_CHUNK_SIZE
CHUNK_OVERLAP = DEFAULT_CHUNK_OVERLAP
MAX_TOKENS = DEFAULT_MAX_TOKENS

# Recommended settings for different scenarios
CHUNK_RECOMMENDATIONS = {
    "pdf_technical": {
        "chunk_size": 1200,
        "overlap": 200,
        "max_tokens": 4000,
        "description": "Technical PDFs with complex content"
    },
    "pdf_general": {
        "chunk_size": 800,
        "overlap": 150,
        "max_tokens": 3000,
        "description": "General PDFs, articles, reports"
    },
    "txt_code": {
        "chunk_size": 1500,
        "overlap": 100,
        "max_tokens": 4000,
        "description": "Code files, documentation"
    },
    "txt_narrative": {
        "chunk_size": 600,
        "overlap": 100,
        "max_tokens": 2500,
        "description": "Stories, books, narrative text"
    },
    "short_qa": {
        "chunk_size": 400,
        "overlap": 50,
        "max_tokens": 2000,
        "description": "Q&A, FAQs, short documents"
    }
}

# Embedding provider recommendations
EMBEDDING_RECOMMENDATIONS = {
    "chromadb_default": {
        "chunk_size": 800,
        "overlap": 150,
        "description": "Balanced for general use"
    },
    "ollama": {
        "chunk_size": 1000,
        "overlap": 200,
        "description": "Good for local processing"
    },
    "openai": {
        "chunk_size": 1200,
        "overlap": 200,
        "description": "Optimized for high-quality embeddings"
    },
    "huggingface": {
        "chunk_size": 900,
        "overlap": 180,
        "description": "Balanced for open-source models"
    }
}

# Summarization template, if used
SUMMARY_PROMPT_TEMPLATE = (
    "Summarize the following content:\n\n{text}"
)

# =========[ Vector Store & Retrieval ]=========
COLLECTION_NAME = "pdf_documents"
SIMILARITY_SEARCH_K = 4       # How many top documents to retrieve

# =========[ File Upload & Allowed Types ]=========
ALLOWED_EXTENSIONS = [".pdf", ".txt"]  # Support PDF and TXT files
MAX_FILE_SIZE_MB = 50

# =========[ Streamlit & UI Settings ]=========
PAGE_TITLE = "RAG Chat with Ollama"
PAGE_ICON = "📚"
LAYOUT = "wide"
SIDEBAR_WIDTH = 300
CHAT_HEIGHT = 400

# =========[ Conversation Memory ]=========
MEMORY_KEY = "chat_history"
MAX_MEMORY_LENGTH = 10        # How many turns of chat memory to keep

# =========[ API Keys & Sensitive Data ]=========
# (Leave blank, or read from environment variables for production)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# =========[ Advanced/Future Options ]=========
# Add custom RAG or LLM/Retriever options here
# Example:
# ENABLE_MULTI_DOC_SUPPORT = True
# DEFAULT_LANGUAGE = "en"
# DEBUG_MODE = False

# =========[ End of Configuration ]=========
