from PyPDF2 import PdfReader
from pathlib import Path
import config

class TextProcessor:
    """Base class for text processing"""
    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

    def create_chunks(self, text, source_name):
        """Create chunks from text with metadata"""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            # Create document chunk with metadata
            chunks.append({
                "page_content": chunk_text,
                "metadata": {
                    "source": source_name,
                    "chunk_id": chunk_id,
                    "start_char": start,
                    "end_char": min(end, len(text)),
                    "file_type": Path(source_name).suffix.lower()
                }
            })

            chunk_id += 1
            start += self.chunk_size - self.chunk_overlap

        return chunks

class PDFProcessor(TextProcessor):
    def process_pdf(self, file_path):
        """
        Accepts a file path string and extracts and chunks text from the PDF.
        Returns a list of document chunks with metadata.
        """
        try:
            # Convert to Path object if it's a string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Read the PDF file
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                all_text = []

                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty text
                        all_text.append(text)

                if not all_text:
                    raise ValueError("No text content found in PDF")

                full_text = "\n".join(all_text)

                # Use base class method to create chunks
                chunks = self.create_chunks(full_text, str(file_path.name))

                # Add PDF-specific metadata
                for chunk in chunks:
                    chunk["metadata"]["total_pages"] = len(reader.pages)

                return chunks

        except Exception as e:
            raise Exception(f"Error processing PDF {file_path}: {str(e)}")


class TXTProcessor(TextProcessor):
    def process_txt(self, file_path):
        """
        Accepts a file path string and extracts and chunks text from the TXT file.
        Returns a list of document chunks with metadata.
        """
        try:
            # Convert to Path object if it's a string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Read the text file
            with open(file_path, 'r', encoding='utf-8') as file:
                full_text = file.read()

                if not full_text.strip():
                    raise ValueError("No text content found in TXT file")

                # Use base class method to create chunks
                chunks = self.create_chunks(full_text, str(file_path.name))

                # Add TXT-specific metadata
                for chunk in chunks:
                    chunk["metadata"]["total_chars"] = len(full_text)
                    chunk["metadata"]["encoding"] = "utf-8"

                return chunks

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    full_text = file.read()
                    chunks = self.create_chunks(full_text, str(file_path.name))
                    for chunk in chunks:
                        chunk["metadata"]["total_chars"] = len(full_text)
                        chunk["metadata"]["encoding"] = "latin-1"
                    return chunks
            except Exception as e:
                raise Exception(f"Error reading TXT file with different encodings: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing TXT {file_path}: {str(e)}")

def validate_file(file_path):
    """
    Accepts a file path string and checks if it is a valid file (PDF or TXT).
    Returns True if valid, False otherwise.
    """
    try:
        # Convert to Path object if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            print(f"File validation error: File does not exist: {file_path}")
            return False

        file_extension = file_path.suffix.lower()

        if file_extension == '.pdf':
            return validate_pdf_file(file_path)
        elif file_extension == '.txt':
            return validate_txt_file(file_path)
        else:
            print(f"File validation error: Unsupported file type: {file_extension}")
            return False

    except Exception as e:
        print(f"File validation error: {e}")
        return False

def validate_pdf_file(file_path):
    """Validate PDF file specifically"""
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            if len(reader.pages) == 0:
                print("PDF validation error: PDF has no pages")
                return False

            # Try to extract text from first page
            first_page = reader.pages[0]
            first_page.extract_text()

        return True

    except Exception as e:
        print(f"PDF validation error: {e}")
        return False

def validate_txt_file(file_path):
    """Validate TXT file specifically"""
    try:
        # Try to read the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read(100)  # Read first 100 chars to test
            if not content.strip():
                print("TXT validation error: File appears to be empty")
                return False
        return True

    except UnicodeDecodeError:
        # Try with latin-1 encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read(100)
                if not content.strip():
                    print("TXT validation error: File appears to be empty")
                    return False
            return True
        except Exception as e:
            print(f"TXT validation error: {e}")
            return False
    except Exception as e:
        print(f"TXT validation error: {e}")
        return False
