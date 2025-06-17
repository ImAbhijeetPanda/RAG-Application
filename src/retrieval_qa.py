import requests
import config
import time
import re
import json
from collections import Counter
from src.embeddings import EmbeddingManager

class RAGChatbot:
    def __init__(self, vector_store, max_tokens=None):
        self.vector_store = vector_store
        self.embedding_manager = EmbeddingManager()
        self.memory = []
        self.max_memory_items = 10  # Keep last 10 exchanges
        self.max_context_length = 8000  # Maximum context length in characters
        self.max_tokens = max_tokens or config.DEFAULT_MAX_TOKENS
        self.performance_stats = {
            "queries": 0,
            "avg_retrieval_time": 0,
            "avg_generation_time": 0,
            "cache_hits": 0
        }

    def chat(self, prompt):
        start_time = time.time()

        # Handle simple greetings naturally
        if self._is_simple_greeting(prompt):
            return {
                "answer": "Hi! I'm here to help you with questions about your documents. What would you like to know?",
                "sources": [],
                "stats": {"retrieval_time": 0, "generation_time": 0, "total_time": 0}
            }

        # Optimize query for better retrieval
        optimized_query = self._optimize_query(prompt)

        # Use text-based similarity search with optimized query
        retrieval_start = time.time()
        docs = self.vector_store.similarity_search(optimized_query, k=config.SIMILARITY_SEARCH_K * 2)
        retrieval_time = time.time() - retrieval_start

        # Re-rank and filter results
        ranked_docs = self._rerank_documents(docs, prompt)[:config.SIMILARITY_SEARCH_K]

        # Filter and enhance context
        context = self._prepare_context(ranked_docs, prompt)

        # Add conversation memory to context
        memory_context = self._get_memory_context()
        if memory_context:
            context = memory_context + "\n\n" + context

        # Generate answer
        generation_start = time.time()
        answer = self.llm_answer(prompt, context)
        generation_time = time.time() - generation_start

        # Update memory
        self._update_memory(prompt, answer)

        # Update performance stats
        self._update_stats(retrieval_time, generation_time)

        return {"answer": answer, "sources": ranked_docs, "stats": {
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(generation_time, 3),
            "total_time": round(time.time() - start_time, 3)
        }}

    def _is_simple_greeting(self, query):
        """Check if the query is a simple greeting"""
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        query_lower = query.lower().strip()
        return any(greeting in query_lower for greeting in greetings) and len(query.split()) <= 3

    def _optimize_query(self, query):
        """Optimize query for better retrieval by expanding key terms"""
        # Remove common stop words and focus on key terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}

        # Extract key terms (words longer than 2 characters, not stop words)
        words = re.findall(r'\b\w{3,}\b', query.lower())
        key_terms = [word for word in words if word not in stop_words]

        # If we have key terms, create an expanded query
        if key_terms:
            # Keep original query and add key terms for better matching
            return f"{query} {' '.join(key_terms[:5])}"  # Limit to top 5 key terms

        return query

    def _rerank_documents(self, docs, query):
        """Re-rank documents based on relevance to the query"""
        if not docs:
            return docs

        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))

        scored_docs = []
        for doc in docs:
            content = doc["page_content"].lower()
            content_words = set(re.findall(r'\b\w{3,}\b', content))

            # Calculate relevance score
            word_overlap = len(query_words.intersection(content_words))
            content_length = len(doc["page_content"])

            # Prefer documents with more word overlap and reasonable length
            score = word_overlap * 10 + min(content_length / 100, 10)

            scored_docs.append((score, doc))

        # Sort by score (descending) and return documents
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs]

    def _update_stats(self, retrieval_time, generation_time):
        """Update performance statistics"""
        self.performance_stats["queries"] += 1
        queries = self.performance_stats["queries"]

        # Update running averages
        self.performance_stats["avg_retrieval_time"] = (
            (self.performance_stats["avg_retrieval_time"] * (queries - 1) + retrieval_time) / queries
        )
        self.performance_stats["avg_generation_time"] = (
            (self.performance_stats["avg_generation_time"] * (queries - 1) + generation_time) / queries
        )

    def _prepare_context(self, docs, prompt):
        """Prepare and optimize context for better responses"""
        if not docs:
            return "No relevant documents found."

        # Create structured context with source attribution
        context_parts = []
        for i, doc in enumerate(docs, 1):
            content = doc["page_content"].strip()
            source = doc.get("metadata", {}).get("source", f"Document {i}")

            # Add source attribution
            context_parts.append(f"[Source {i}: {source}]\n{content}")

        # Join with clear separators
        context = "\n\n" + "="*50 + "\n\n".join(context_parts)

        # Add context length info for the AI
        total_chars = len(context)
        context_header = f"[Context contains {len(docs)} relevant sections, {total_chars} characters total]\n\n"

        return context_header + context

    def llm_answer(self, prompt, context, stream=False):
        url = f"{config.OLLAMA_BASE_URL}/api/generate"

        # Enhanced system prompt for natural responses
        system_prompt = """You are a helpful assistant that answers questions based on the provided documents. Be natural, conversational, and concise.

Guidelines:
- Answer directly and naturally, like you're having a conversation
- Keep responses short and to the point
- Only use information from the provided context
- If you don't know something, just say so simply
- Don't be overly formal or structured unless needed
- For simple greetings, respond naturally but guide toward document-related questions

Context from documents:
{context}

Question: {question}

Answer:"""

        user_prompt = system_prompt.format(context=context, question=prompt)
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": user_prompt,
            "stream": stream,
            "options": {
                "num_predict": self.max_tokens,  # Max tokens to generate
                "temperature": 0.8,  # More natural, less formal responses
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }

        try:
            if stream:
                return self._stream_response(url, payload)
            else:
                r = requests.post(url, json=payload, timeout=90)
                r.raise_for_status()  # Raise an exception for bad status codes
                data = r.json()
                return data.get("response", "[No answer returned]")
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            return f"Error processing response: {str(e)}"

    def _stream_response(self, url, payload):
        """Handle streaming response from Ollama"""
        try:
            response = requests.post(url, json=payload, stream=True, timeout=90)
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            chunk = data['response']
                            full_response += chunk
                            yield chunk
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue

            return full_response
        except Exception as e:
            yield f"Error in streaming: {str(e)}"

    def summarize_documents(self, max_docs=3):
        all_chunks = self.vector_store.collection.get(limit=max_docs)
        texts = [doc for doc in all_chunks['documents']]
        context = "\n\n".join(texts)
        return self.llm_summarize(context)

    def llm_summarize(self, context):
        url = f"{config.OLLAMA_BASE_URL}/api/generate"

        # Enhanced summarization prompt
        system_prompt = """You are an expert document summarizer. Create a comprehensive yet concise summary of the provided content.

INSTRUCTIONS:
1. Create a well-structured summary with clear sections
2. Include the main topics, key points, and important details
3. Use bullet points or numbered lists for clarity
4. Highlight any actionable items or conclusions
5. Maintain the original meaning and context
6. Keep the summary informative but readable
7. If there are multiple documents, organize by themes or topics

CONTENT TO SUMMARIZE:
{content}

COMPREHENSIVE SUMMARY:"""

        user_prompt = system_prompt.format(content=context)
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": user_prompt,
            "stream": False,  # Disable streaming to get a single JSON response
            "options": {
                "num_predict": self.max_tokens,  # Max tokens to generate
                "temperature": 0.5  # Lower temperature for summaries
            }
        }

        try:
            r = requests.post(url, json=payload, timeout=90)
            r.raise_for_status()  # Raise an exception for bad status codes
            data = r.json()
            return data.get("response", "[No summary returned]")
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            return f"Error processing response: {str(e)}"

    def _get_memory_context(self):
        """Get conversation memory as context"""
        if not self.memory:
            return ""

        memory_parts = []
        for exchange in self.memory[-3:]:  # Use last 3 exchanges
            memory_parts.append(f"Previous Q: {exchange['question']}")
            memory_parts.append(f"Previous A: {exchange['answer'][:200]}...")  # Truncate long answers

        if memory_parts:
            return "[CONVERSATION HISTORY]\n" + "\n".join(memory_parts) + "\n[END HISTORY]"
        return ""

    def _update_memory(self, question, answer):
        """Update conversation memory with size management"""
        self.memory.append({
            "question": question,
            "answer": answer,
            "timestamp": time.time()
        })

        # Keep only recent exchanges
        if len(self.memory) > self.max_memory_items:
            self.memory = self.memory[-self.max_memory_items:]

    def _optimize_context_length(self, context):
        """Optimize context length to fit within limits"""
        if len(context) <= self.max_context_length:
            return context

        # Truncate context while preserving structure
        lines = context.split('\n')
        optimized_lines = []
        current_length = 0

        # Keep important sections (headers, first parts)
        for line in lines:
            if current_length + len(line) > self.max_context_length:
                break
            optimized_lines.append(line)
            current_length += len(line) + 1  # +1 for newline

        return '\n'.join(optimized_lines) + "\n[...context truncated for length...]"

    def get_performance_stats(self):
        """Get current performance statistics"""
        return self.performance_stats.copy()

    def clear_memory(self):
        self.memory = []

def create_rag_chatbot(vector_store):
    return RAGChatbot(vector_store)
