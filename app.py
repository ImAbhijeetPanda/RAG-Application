"""
Main Streamlit Application for RAG with Ollama
"""

import streamlit as st
import logging
from pathlib import Path
import time

# --- Attempt critical imports, fail gracefully if missing ---
try:
    from src.pdf_processor import PDFProcessor, TXTProcessor, validate_file
    from src.embeddings import EmbeddingManager, check_ollama_models
    from src.vector_store import ChromaVectorStore, create_vector_store
    from src.retrieval_qa import RAGChatbot
    from src.embedding_providers import list_available_providers, test_provider
    from src.utils import (
        check_ollama_status, validate_uploaded_file, save_uploaded_file,
        display_error_message, display_success_message, load_css_style,
        format_file_size, clean_upload_directory
    )
    try:
        from src.performance_monitor import performance_monitor
        PERFORMANCE_MONITORING_AVAILABLE = True
    except ImportError as e:
        print(f"Performance monitoring not available: {e}")
        PERFORMANCE_MONITORING_AVAILABLE = False
        performance_monitor = None
    import config
except Exception as e:
    st.error(f"❌ Critical import error: {e}")
    st.stop()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Page configuration ---
st.set_page_config(
    page_title=getattr(config, "PAGE_TITLE", "RAG Chat with Ollama"),
    page_icon=getattr(config, "PAGE_ICON", "📚"),
    layout=getattr(config, "LAYOUT", "wide"),
    initial_sidebar_state="expanded"
)

# --- Load custom CSS (don't fail if not found) ---
try:
    st.markdown(load_css_style(), unsafe_allow_html=True)
except Exception:
    pass  # Don't block app if CSS missing

# --- Session State Initialization ---
def initialize_session_state():
    """Initialize Streamlit session state variables"""
    defaults = {
        'vector_store': None,
        'chatbot': None,
        'chat_history': [],
        'processed_files': [],
        'ollama_status': None,
        'app_initialized': False,
        'selected_embedding_provider': config.EMBEDDING_PROVIDER,
        'chunk_size': config.DEFAULT_CHUNK_SIZE,
        'chunk_overlap': config.DEFAULT_CHUNK_OVERLAP,
        'max_tokens': config.DEFAULT_MAX_TOKENS
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- Storage Management Functions ---
def clear_vector_storage():
    """Clear the vector storage and reset related session state"""
    try:
        if st.session_state.vector_store:
            st.session_state.vector_store.reset_collection()
            st.success("✅ Vector storage cleared successfully!")

        # Reset related session state
        st.session_state.chatbot = None
        st.session_state.processed_files = []
        clean_upload_directory()

    except Exception as e:
        st.error(f"❌ Error clearing storage: {e}")

def check_startup_clear():
    """Check if user wants to clear storage on startup"""
    if not st.session_state.app_initialized:
        st.session_state.app_initialized = True

        # Check if there's existing data
        if st.session_state.vector_store:
            try:
                info = st.session_state.vector_store.get_collection_info()
                doc_count = info.get('document_count', 0)

                if doc_count > 0:
                    st.warning(f"⚠️ Found {doc_count} existing documents in storage from previous session.")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🗑️ Clear & Start Fresh", type="primary"):
                            clear_vector_storage()
                            st.rerun()
                    with col2:
                        if st.button("📚 Keep Existing Data", type="secondary"):
                            st.info("Keeping existing documents. You can clear them later if needed.")
                            st.rerun()
                    with col3:
                        st.write("")  # Spacer

                    st.stop()  # Stop execution until user chooses

            except Exception:
                pass

# --- Ollama connection check ---
def check_ollama_connection():
    """Check and display Ollama connection status"""
    status = check_ollama_status()
    st.session_state.ollama_status = status

    if status['status'] == 'running':
        st.success("✅ Ollama is running")

        # Check required models
        text_model_ok = status.get('text_model_available', False)
        embed_model_ok = status.get('embedding_model_available', False)

        col1, col2 = st.columns(2)
        with col1:
            if text_model_ok:
                st.success(f"✅ Text model: {config.OLLAMA_MODEL}")
            else:
                st.error(f"❌ Text model missing: {config.OLLAMA_MODEL}")
                st.code(f"ollama pull {config.OLLAMA_MODEL}")

        with col2:
            if embed_model_ok:
                st.success(f"✅ Embedding model: {config.OLLAMA_EMBEDDING_MODEL}")
            else:
                st.error(f"❌ Embedding model missing: {config.OLLAMA_EMBEDDING_MODEL}")
                st.code(f"ollama pull {config.OLLAMA_EMBEDDING_MODEL}")

        return text_model_ok and embed_model_ok

    else:
        st.error(f"❌ Ollama not available: {status.get('error', 'Unknown error')}")
        st.info("Make sure Ollama is running: `ollama serve`")
        return False

# --- Chunking Configuration Panel ---
def chunking_configuration_panel():
    """Advanced chunking configuration with recommendations"""
    with st.sidebar.expander("⚙️ Chunking Settings", expanded=False):
        # Quick presets
        st.subheader("📋 Quick Presets")
        preset_options = {
            "Custom": "Custom settings",
            "pdf_technical": "📄 Technical PDFs",
            "pdf_general": "📄 General PDFs",
            "txt_code": "📝 Code/Documentation",
            "txt_narrative": "📝 Stories/Books",
            "short_qa": "❓ Q&A/FAQs"
        }

        selected_preset = st.selectbox(
            "Choose preset:",
            list(preset_options.keys()),
            format_func=lambda x: preset_options[x],
            help="Select a preset optimized for your document type"
        )

        # Apply preset if selected
        if selected_preset != "Custom" and selected_preset in config.CHUNK_RECOMMENDATIONS:
            preset = config.CHUNK_RECOMMENDATIONS[selected_preset]
            st.session_state.chunk_size = preset["chunk_size"]
            st.session_state.chunk_overlap = preset["overlap"]
            st.session_state.max_tokens = preset["max_tokens"]
            st.info(f"💡 {preset['description']}")

        # Manual configuration
        st.subheader("🔧 Manual Settings")

        # Chunk Size
        chunk_size = st.slider(
            "Chunk Size (characters)",
            min_value=200,
            max_value=3000,
            value=st.session_state.chunk_size,
            step=50,
            help="Larger chunks: Better context, slower processing. Smaller chunks: Faster, more precise retrieval."
        )

        # Chunk Overlap
        max_overlap = min(chunk_size // 2, 500)
        chunk_overlap = st.slider(
            "Chunk Overlap (characters)",
            min_value=0,
            max_value=max_overlap,
            value=min(st.session_state.chunk_overlap, max_overlap),
            step=25,
            help="Overlap ensures important information isn't split between chunks."
        )

        # Max Tokens
        max_tokens = st.slider(
            "Max Response Tokens",
            min_value=500,
            max_value=8000,
            value=st.session_state.max_tokens,
            step=250,
            help="Maximum tokens for AI responses. Higher = longer responses, slower generation."
        )

        # Update session state
        st.session_state.chunk_size = chunk_size
        st.session_state.chunk_overlap = chunk_overlap
        st.session_state.max_tokens = max_tokens

        # Show embedding-specific recommendations
        if st.session_state.selected_embedding_provider in config.EMBEDDING_RECOMMENDATIONS:
            embed_rec = config.EMBEDDING_RECOMMENDATIONS[st.session_state.selected_embedding_provider]
            st.info(f"💡 For {st.session_state.selected_embedding_provider}: {embed_rec['description']}")

            if st.button("Apply Embedding Optimized Settings"):
                st.session_state.chunk_size = embed_rec["chunk_size"]
                st.session_state.chunk_overlap = embed_rec["overlap"]
                st.rerun()

        # Quick performance indicator
        processing_speed = "🟢 Fast" if chunk_size < 800 else "🟡 Medium" if chunk_size < 1200 else "🔴 Slow"
        st.info(f"Processing Speed: {processing_speed}")

# --- Embedding Provider Selection ---
def embedding_provider_selection():
    """Allow user to select embedding provider"""
    st.sidebar.header("🔧 Embedding Provider")

    available_providers = list_available_providers()
    provider_descriptions = {
        "chromadb_default": "ChromaDB Default (Fast, No Setup)",
        "ollama": "Ollama (Local, Private)",
        "openai": "OpenAI (Cloud, High Quality)",
        "huggingface": "Hugging Face (Local, Open Source)"
    }

    # Create display options
    display_options = [f"{provider} - {provider_descriptions.get(provider, '')}"
                      for provider in available_providers]

    current_index = available_providers.index(st.session_state.selected_embedding_provider)

    selected_display = st.sidebar.selectbox(
        "Choose Embedding Provider:",
        display_options,
        index=current_index,
        help="Different providers offer different trade-offs between speed, quality, and privacy"
    )

    # Extract provider name from display option
    selected_provider = selected_display.split(" - ")[0]

    # Test provider status
    if selected_provider != st.session_state.selected_embedding_provider:
        with st.sidebar.spinner(f"Testing {selected_provider}..."):
            test_result = test_provider(selected_provider)

            if test_result["available"]:
                st.sidebar.success(f"✅ {selected_provider} is available!")
                st.session_state.selected_embedding_provider = selected_provider
                # Reset vector store to use new provider
                st.session_state.vector_store = None
                st.session_state.chatbot = None
            else:
                st.sidebar.error(f"❌ {selected_provider} not available: {test_result['error']}")
                return False

    return True

# --- Vector Store Setup ---
def setup_vector_store():
    try:
        if st.session_state.vector_store is None:
            with st.spinner("Initializing vector store..."):
                st.session_state.vector_store = create_vector_store(
                    embedding_provider=st.session_state.selected_embedding_provider
                )
            st.success(f"Vector store initialized with {st.session_state.selected_embedding_provider} embeddings!")
        return True
    except Exception as e:
        display_error_message(e, "vector store initialization")
        return False

# --- Chatbot Setup ---
def setup_chatbot():
    try:
        if st.session_state.chatbot is None and st.session_state.vector_store is not None:
            with st.spinner("Initializing RAG chatbot..."):
                # Pass current max_tokens setting to chatbot
                st.session_state.chatbot = RAGChatbot(
                    st.session_state.vector_store,
                    max_tokens=st.session_state.max_tokens
                )
            st.success("RAG chatbot initialized successfully!")
        return st.session_state.chatbot is not None
    except Exception as e:
        display_error_message(e, "chatbot initialization")
        return False

# --- File Upload Section ---
def file_upload_section():
    st.header("📁 Document Upload")

    # Show current document count and clear option
    if st.session_state.vector_store:
        try:
            info = st.session_state.vector_store.get_collection_info()
            chunk_count = info.get('document_count', 0)
            file_count = info.get('file_count', 0)

            if chunk_count > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if file_count == chunk_count:
                        # If file count equals chunk count, just show files
                        st.info(f"📚 Documents: {file_count}")
                    else:
                        # Show both files and chunks
                        st.info(f"📚 Files: {file_count} | Chunks: {chunk_count}")
                with col2:
                    if st.button("🗑️ Clear All", type="secondary", help="Clear all documents from storage"):
                        clear_vector_storage()
                        st.rerun()
            else:
                st.info("📚 No documents in storage - ready for upload!")
        except Exception:
            pass

    uploaded_files = st.file_uploader(
        "Upload documents (PDF or TXT)",
        type=['pdf', 'txt'],
        accept_multiple_files=True,
        help=f"Supported formats: PDF, TXT | Maximum file size: {config.MAX_FILE_SIZE_MB} MB per file"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Validate file
            validation = validate_uploaded_file(uploaded_file)
            if not validation['valid']:
                st.error(f"❌ {uploaded_file.name}: {validation['error']}")
                continue
            if uploaded_file.name in st.session_state.processed_files:
                st.info(f"📄 {uploaded_file.name} already processed")
                continue
            if st.button(f"Process {uploaded_file.name}", key=f"process_{uploaded_file.name}"):
                process_uploaded_file(uploaded_file)

def process_uploaded_file(uploaded_file):
    try:
        with st.spinner(f"Saving {uploaded_file.name}..."):
            file_path = save_uploaded_file(uploaded_file)

        # Validate file
        if not validate_file(file_path):
            st.error(f"❌ Invalid file: {uploaded_file.name}")
            return

        # Determine file type and process accordingly
        file_extension = uploaded_file.name.lower().split('.')[-1]

        with st.spinner(f"Processing {uploaded_file.name}..."):
            # Use current chunking settings from session state
            chunk_size = st.session_state.chunk_size
            chunk_overlap = st.session_state.chunk_overlap

            if file_extension == 'pdf':
                processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                documents = processor.process_pdf(file_path)
            elif file_extension == 'txt':
                processor = TXTProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                documents = processor.process_txt(file_path)
            else:
                st.error(f"❌ Unsupported file type: {file_extension}")
                return

        st.success(f"✅ Extracted {len(documents)} chunks from {uploaded_file.name}")

        if st.session_state.vector_store is not None:
            with st.spinner("Adding to vector store..."):
                ids = st.session_state.vector_store.add_documents(documents)
            st.success(f"✅ Added {len(ids)} document chunks to vector store")
            st.session_state.processed_files.append(uploaded_file.name)
            st.session_state.chatbot = None
            setup_chatbot()
    except Exception as e:
        display_error_message(e, f"processing {uploaded_file.name}")

# --- Chat Interface ---
def chat_interface():
    st.header("💬 Chat with Documents")
    if not st.session_state.processed_files:
        st.info("📚 Upload and process some documents first to start chatting!")
        return
    if st.session_state.chatbot is None:
        st.error("❌ Chatbot not initialized. Please check Ollama connection and try again.")
        return
    for i, message in enumerate(st.session_state.chat_history):
        if message['type'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
                if 'sources' in message and message['sources']:
                    with st.expander(f"📚 Sources ({len(message['sources'])})"):
                        for j, source in enumerate(message['sources']):
                            st.markdown(f"**Source {j+1}:**")
                            st.markdown(f"```\n{source['page_content']}\n```")
                            if 'metadata' in source:
                                st.json(source['metadata'])
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.chat_history.append({'type': 'user','content': prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.chat(prompt)
            st.write(response['answer'])
            if response['sources']:
                with st.expander(f"📚 Sources ({len(response['sources'])})"):
                    for i, source in enumerate(response['sources']):
                        st.markdown(f"**Source {i+1}:**")
                        st.markdown(f"```\n{source['page_content']}\n```")
                        if 'metadata' in source:
                            st.json(source['metadata'])
        st.session_state.chat_history.append({
            'type': 'assistant',
            'content': response['answer'],
            'sources': response['sources']
        })

# --- Summarization Section ---
def summarization_section():
    st.header("📋 Document Summary")
    if not st.session_state.processed_files:
        st.info("📚 Upload and process some documents first to generate a summary!")
        return
    if st.session_state.chatbot is None:
        st.error("❌ Chatbot not initialized. Please check Ollama connection and try again.")
        return
    if st.button("Generate Summary", type="primary"):
        with st.spinner("Generating summary..."):
            try:
                summary = st.session_state.chatbot.summarize_documents()
                st.markdown("### 📄 Document Summary")
                st.markdown(summary)
            except Exception as e:
                display_error_message(e, "summary generation")

# --- Sidebar Info ---
def sidebar_info():
    st.sidebar.header("📊 System Status")
    # Ollama status
    if st.sidebar.button("🔄 Refresh Status"):
        st.session_state.ollama_status = None
        st.rerun()
    if st.session_state.ollama_status:
        status = st.session_state.ollama_status
        if status['status'] == 'running':
            st.sidebar.success("✅ Ollama Running")
        else:
            st.sidebar.error("❌ Ollama Not Available")
    # Vector store info
    if st.session_state.vector_store:
        try:
            info = st.session_state.vector_store.get_collection_info()
            st.sidebar.info(f"📚 Documents: {info.get('document_count', 0)}")
        except:
            st.sidebar.warning("⚠️ Vector store info unavailable")

    # Processed files
    st.sidebar.header("📁 Processed Files")
    if st.session_state.processed_files:
        for filename in st.session_state.processed_files:
            file_ext = filename.lower().split('.')[-1]
            icon = "📄" if file_ext == "pdf" else "📝" if file_ext == "txt" else "📄"
            st.sidebar.text(f"{icon} {filename}")
    else:
        st.sidebar.info("No files processed yet")
    # Storage Management
    st.sidebar.header("🗑️ Storage Management")

    # Show current storage info
    if st.session_state.vector_store:
        try:
            info = st.session_state.vector_store.get_collection_info()
            chunk_count = info.get('document_count', 0)
            file_count = info.get('file_count', 0)

            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("📄 Files", file_count)
            with col2:
                st.metric("🧩 Chunks", chunk_count)
        except:
            st.sidebar.warning("⚠️ Storage info unavailable")

    # Clear options
    if st.sidebar.button("Clear Chat History Only"):
        st.session_state.chat_history = []
        if st.session_state.chatbot:
            st.session_state.chatbot.clear_memory()
        st.sidebar.success("Chat history cleared!")
        st.rerun()

    if st.sidebar.button("Clear Document Storage", type="secondary"):
        clear_vector_storage()
        st.rerun()

    if st.sidebar.button("Clear Everything", type="secondary"):
        if st.sidebar.checkbox("⚠️ I understand this will delete ALL data"):
            # Reset everything
            clear_vector_storage()
            st.session_state.vector_store = None
            st.session_state.chatbot = None
            st.session_state.chat_history = []
            st.session_state.app_initialized = False
            st.sidebar.success("Everything cleared!")
            st.rerun()

    # Performance monitoring section (if available)
    if PERFORMANCE_MONITORING_AVAILABLE and performance_monitor:
        st.sidebar.header("📊 Performance")
        if st.sidebar.button("🔄 Refresh Stats"):
            st.rerun()

        try:
            perf_stats = performance_monitor.get_performance_summary()
            if perf_stats:
                st.sidebar.metric("⏱️ Uptime", f"{perf_stats.get('uptime_hours', 0):.1f}h")
                st.sidebar.metric("📈 Total Queries", perf_stats.get('total_queries', 0))

                query_stats = perf_stats.get('query_stats', {})
                if query_stats:
                    st.sidebar.metric("⚡ Avg Response", f"{query_stats.get('avg_duration', 0):.2f}s")

                # Show alerts if any
                alerts = performance_monitor.get_alerts()
                for alert in alerts:
                    if alert['type'] == 'warning':
                        st.sidebar.warning(alert['message'])
                    elif alert['type'] == 'error':
                        st.sidebar.error(alert['message'])
        except Exception:
            pass  # Don't break the app if monitoring fails

# --- Main App ---
def main():
    initialize_session_state()

    # Start performance monitoring if available
    if PERFORMANCE_MONITORING_AVAILABLE and performance_monitor and not performance_monitor.monitoring:
        performance_monitor.start_monitoring()

    st.markdown('<h1 class="main-header">🤖 Smart Document Assistant</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar configurations
    chunking_configuration_panel()  # Add chunking config first

    # Embedding provider selection in sidebar
    embedding_ok = embedding_provider_selection()
    if not embedding_ok:
        st.error("Please select a working embedding provider from the sidebar.")
        st.stop()

    # Only check Ollama if it's being used for LLM or embeddings
    if st.session_state.selected_embedding_provider == "ollama" or config.OLLAMA_MODEL:
        ollama_ok = check_ollama_connection()
        if not ollama_ok:
            st.stop()

    vector_store_ok = setup_vector_store()
    if vector_store_ok:
        setup_chatbot()
        # Check for existing data and offer to clear
        check_startup_clear()

    tab1, tab2, tab3 = st.tabs(["📁 Upload", "💬 Chat", "📋 Summary"])
    with tab1:
        file_upload_section()
    with tab2:
        chat_interface()
    with tab3:
        summarization_section()
    sidebar_info()

if __name__ == "__main__":
    main()
