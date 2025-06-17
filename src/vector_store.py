import chromadb
import config
import uuid
from datetime import datetime
from src.embedding_providers import get_embedding_provider

class ChromaVectorStore:
    def __init__(self, persist_directory=None, embedding_provider=None):
        if persist_directory is None:
            persist_directory = str(config.CHROMA_DB_DIR)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get embedding provider
        self.embedding_provider_name = embedding_provider or config.EMBEDDING_PROVIDER
        self.embedding_provider = get_embedding_provider(self.embedding_provider_name)

        # Create collection based on embedding provider
        if self.embedding_provider_name == "chromadb_default":
            # Use ChromaDB's default embedding function
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine", "embedding_provider": self.embedding_provider_name}
            )
        else:
            # Use custom embedding function
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                embedding_function=self._get_embedding_function(),
                metadata={"hnsw:space": "cosine", "embedding_provider": self.embedding_provider_name}
            )

    def _get_embedding_function(self):
        """Create a custom embedding function for ChromaDB"""
        class CustomEmbeddingFunction:
            def __init__(self, provider):
                self.provider = provider
                self.name = f"{provider.name}_embeddings"

            def __call__(self, input):
                if isinstance(input, str):
                    input = [input]
                return self.provider.embed_text(input)

        return CustomEmbeddingFunction(self.embedding_provider)

    def add_documents(self, documents, batch_size=50):
        """Add documents to the vector store with batch processing"""
        if not documents:
            return []

        all_ids = []

        # Process documents in batches for better performance
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_ids = self._add_document_batch(batch, i)
            all_ids.extend(batch_ids)

        return all_ids

    def _add_document_batch(self, batch_documents, batch_offset=0):
        """Add a batch of documents to the vector store"""
        texts = [doc["page_content"] for doc in batch_documents]
        metadatas = [doc["metadata"] for doc in batch_documents]

        # Generate unique IDs using timestamp and UUID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ids = [f"{timestamp}_{uuid.uuid4().hex[:8]}_{batch_offset + i}" for i in range(len(texts))]

        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            return ids
        except Exception as e:
            raise Exception(f"Error adding document batch to vector store: {str(e)}")

    def similarity_search(self, query_text, k=4):
        """Search for similar documents using query text (not embedding)"""
        try:
            results = self.collection.query(
                query_texts=[query_text],  # Use query_texts instead of query_embeddings
                n_results=k
            )

            docs = []
            if results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    docs.append({
                        "page_content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            return docs
        except Exception as e:
            raise Exception(f"Error searching vector store: {str(e)}")

    def get_collection_info(self):
        """Get collection info including unique file count"""
        total_chunks = self.collection.count()

        # Get unique source files
        try:
            if total_chunks == 0:
                unique_files = 0
            else:
                # Get all documents to count unique sources
                all_docs = self.collection.get()
                unique_sources = set()

                if all_docs and 'metadatas' in all_docs and all_docs['metadatas']:
                    for metadata in all_docs['metadatas']:
                        if metadata and 'source' in metadata:
                            unique_sources.add(metadata['source'])

                unique_files = len(unique_sources)

                # If we couldn't find any sources, fallback to chunk count
                if unique_files == 0 and total_chunks > 0:
                    unique_files = total_chunks

        except Exception as e:
            print(f"Error getting collection info: {e}")
            # Fallback to chunk count if we can't get metadata
            unique_files = total_chunks

        return {
            "collection_name": self.collection.name,
            "document_count": total_chunks,  # Total chunks
            "file_count": unique_files       # Unique files
        }

    def reset_collection(self):
        """Delete and recreate the collection to start fresh"""
        try:
            # Delete the existing collection
            self.client.delete_collection(name=config.COLLECTION_NAME)
        except Exception:
            # Collection might not exist, that's fine
            pass

        # Recreate the collection with the same embedding provider
        if self.embedding_provider_name == "chromadb_default":
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine", "embedding_provider": self.embedding_provider_name}
            )
        else:
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                embedding_function=self._get_embedding_function(),
                metadata={"hnsw:space": "cosine", "embedding_provider": self.embedding_provider_name}
            )

def create_vector_store(embedding_provider=None):
    return ChromaVectorStore(embedding_provider=embedding_provider)
