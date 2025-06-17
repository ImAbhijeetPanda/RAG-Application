import requests
import config
import hashlib
import json
import os
from pathlib import Path

class EmbeddingManager:
    def __init__(self, cache_dir=None):
        """Initialize embedding manager with optional caching"""
        self.cache_dir = cache_dir or Path("cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_enabled = True

    def _get_cache_key(self, text, model=None):
        """Generate a cache key for the given text and model"""
        model = model or config.OLLAMA_EMBEDDING_MODEL
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        """Get the file path for a cache key"""
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_key):
        """Load embedding from cache if it exists"""
        if not self.cache_enabled:
            return None

        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception:
                # If cache is corrupted, remove it
                cache_path.unlink(missing_ok=True)
        return None

    def _save_to_cache(self, cache_key, embedding):
        """Save embedding to cache"""
        if not self.cache_enabled:
            return

        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(embedding, f)
        except Exception:
            # If we can't save to cache, just continue
            pass

    def embed_text(self, texts, batch_size=10):
        """
        Generate embeddings for text(s) using Ollama with caching and batching.
        Returns a list of embeddings.
        """
        # Handle single text or list of texts
        if isinstance(texts, str):
            single_text = True
            text_list = [texts]
        else:
            single_text = False
            text_list = texts

        embeddings = []
        url = f"{config.OLLAMA_BASE_URL}/api/embeddings"

        # Process in batches to optimize performance
        for i in range(0, len(text_list), batch_size):
            batch = text_list[i:i + batch_size]
            batch_embeddings = self._process_batch(batch, url)
            embeddings.extend(batch_embeddings)

        return embeddings

    def _process_batch(self, batch_texts, url):
        """Process a batch of texts for embeddings"""
        batch_embeddings = []
        uncached_texts = []
        uncached_indices = []

        # First pass: check cache for all texts
        for idx, text in enumerate(batch_texts):
            cache_key = self._get_cache_key(text)
            cached_embedding = self._load_from_cache(cache_key)

            if cached_embedding is not None:
                batch_embeddings.append((idx, cached_embedding))
            else:
                uncached_texts.append(text)
                uncached_indices.append(idx)

        # Second pass: generate embeddings for uncached texts
        for i, text in enumerate(uncached_texts):
            payload = {"model": config.OLLAMA_EMBEDDING_MODEL, "prompt": text}
            try:
                r = requests.post(url, json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()

                if "embedding" in data:
                    embedding = data["embedding"]
                    original_idx = uncached_indices[i]
                    batch_embeddings.append((original_idx, embedding))

                    # Save to cache
                    cache_key = self._get_cache_key(text)
                    self._save_to_cache(cache_key, embedding)
                else:
                    raise RuntimeError(f"Embedding error: {data}")

            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Request error: {e}")

        # Sort by original index and return embeddings only
        batch_embeddings.sort(key=lambda x: x[0])
        return [embedding for idx, embedding in batch_embeddings]

    def clear_cache(self):
        """Clear all cached embeddings"""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def get_cache_stats(self):
        """Get cache statistics"""
        if not self.cache_dir.exists():
            return {"files": 0, "size_mb": 0}

        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        return {
            "files": len(cache_files),
            "size_mb": round(total_size / (1024 * 1024), 2)
        }

    def test_embedding(self, text="This is a test sentence."):
        try:
            self.embed_text(text)
            return True
        except Exception as e:
            print(f"Embedding test failed: {e}")
            return False

    def get_embedding_dimension(self):
        try:
            return len(self.embed_text("test")[0])
        except Exception:
            return 0

def check_ollama_models():
    return True
