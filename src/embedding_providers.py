"""
Multiple embedding provider support for the RAG application.
Supports Ollama, OpenAI, Hugging Face, and ChromaDB default embeddings.
"""

import requests
import config
import os
from typing import List, Union


class BaseEmbeddingProvider:
    """Base class for embedding providers"""
    
    def __init__(self):
        self.name = "base"
        self.dimension = None
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for text(s). Must be implemented by subclasses."""
        raise NotImplementedError
    
    def test_connection(self) -> bool:
        """Test if the embedding provider is available."""
        try:
            self.embed_text("test")
            return True
        except Exception:
            return False


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama embedding provider"""
    
    def __init__(self):
        super().__init__()
        self.name = "ollama"
        self.model = config.OLLAMA_EMBEDDING_MODEL
        self.base_url = config.OLLAMA_BASE_URL
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        url = f"{self.base_url}/api/embeddings"
        
        for text in texts:
            payload = {"model": self.model, "prompt": text}
            try:
                r = requests.post(url, json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                
                if "embedding" in data:
                    embeddings.append(data["embedding"])
                else:
                    raise RuntimeError(f"Embedding error: {data}")
                    
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Ollama request error: {e}")
        
        return embeddings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self):
        super().__init__()
        self.name = "openai"
        self.model = config.OPENAI_EMBEDDING_MODEL
        self.api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        if isinstance(texts, str):
            texts = [texts]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        try:
            r = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI request error: {e}")


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """Hugging Face embedding provider (local)"""
    
    def __init__(self):
        super().__init__()
        self.name = "huggingface"
        self.model_name = config.HUGGINGFACE_EMBEDDING_MODEL
        self._model = None
        self._tokenizer = None
        
        # Try to import required libraries
        try:
            from sentence_transformers import SentenceTransformer
            self._sentence_transformer = SentenceTransformer
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
    
    def _load_model(self):
        """Lazy load the model"""
        if self._model is None:
            self._model = self._sentence_transformer(self.model_name)
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings using Hugging Face model"""
        self._load_model()
        
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self._model.encode(texts)
        return embeddings.tolist()


class ChromaDBDefaultEmbeddingProvider(BaseEmbeddingProvider):
    """ChromaDB default embedding provider (no custom embeddings)"""
    
    def __init__(self):
        super().__init__()
        self.name = "chromadb_default"
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """ChromaDB handles embeddings internally, so this is not used"""
        raise NotImplementedError("ChromaDB default provider handles embeddings internally")


def get_embedding_provider(provider_name: str = None) -> BaseEmbeddingProvider:
    """Factory function to get the specified embedding provider"""
    
    if provider_name is None:
        provider_name = config.EMBEDDING_PROVIDER
    
    providers = {
        "ollama": OllamaEmbeddingProvider,
        "openai": OpenAIEmbeddingProvider,
        "huggingface": HuggingFaceEmbeddingProvider,
        "chromadb_default": ChromaDBDefaultEmbeddingProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown embedding provider: {provider_name}. Available: {list(providers.keys())}")
    
    try:
        return providers[provider_name]()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize {provider_name} embedding provider: {e}")


def list_available_providers() -> List[str]:
    """List all available embedding providers"""
    return ["ollama", "openai", "huggingface", "chromadb_default"]


def test_provider(provider_name: str) -> dict:
    """Test if a specific provider is working"""
    try:
        provider = get_embedding_provider(provider_name)
        is_working = provider.test_connection()
        return {
            "provider": provider_name,
            "available": is_working,
            "name": provider.name,
            "error": None
        }
    except Exception as e:
        return {
            "provider": provider_name,
            "available": False,
            "name": provider_name,
            "error": str(e)
        }
