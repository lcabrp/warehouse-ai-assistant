"""
Vector Store Manager for RAG Pipeline
======================================

Manages InMemoryVectorStore for semantic search over warehouse documentation.

Key Concepts (From Unit 4):
- Embeddings: Convert text to 1536-dimensional vectors
- Similarity Search: Find chunks most similar to query
- Score: Lower = more similar (distance-based)
- Top-K: Return K most relevant chunks

Why InMemoryVectorStore:
- ✅ No external database needed
- ✅ Fast for proof-of-concept
- ✅ Perfect for ~100 chunks
- ⚠️  Could upgrade to Chroma/Pinecone for production
"""

from typing import List, Dict, Tuple
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from ..config import settings
from .document_loader import DocumentLoader


class VectorStoreManager:
    """
    Manages vector store for warehouse documentation.
    
    Responsibilities:
    1. Initialize embeddings model (OpenAI text-embedding-3-small)
    2. Create and populate InMemoryVectorStore
    3. Provide semantic search interface
    4. Track store statistics
    """
    
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        """
        Initialize vector store manager.
        
        Args:
            embedding_model: OpenAI embedding model to use
                           (text-embedding-3-small is cheaper, fast, good quality)
        """
        # Initialize OpenAI embeddings
        # This will convert text chunks into 1536-dimensional vectors
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=settings.openai_api_key
        )
        
        # Create empty vector store
        # This holds all our embedded chunks in memory
        self.vector_store = InMemoryVectorStore(self.embeddings)
        
        # Track what we've loaded
        self.is_populated = False
        self.chunk_count = 0
    
    def populate_from_directory(self, directory=None) -> int:
        """
        Load all documents from directory and populate vector store.
        
        Args:
            directory: Path to docs folder (uses settings.docs_path if None)
        
        Returns:
            Number of chunks loaded
        
        Note: This embeds all chunks, which calls OpenAI API
              Cost: ~$0.00002 per 1000 chunks (very cheap)
        """
        print("\n🔧 Populating Vector Store")
        print("=" * 60)
        
        # Load and chunk documents
        loader = DocumentLoader(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        chunks = loader.load_directory(directory)
        
        if not chunks:
            print("⚠️  No chunks to load")
            return 0
        
        # Add chunks to vector store
        # This will call OpenAI API to get embeddings for each chunk
        print(f"\n🔄 Embedding {len(chunks)} chunks...")
        print("   (This may take a moment - calling OpenAI API)")
        
        self.vector_store.add_documents(chunks)
        
        self.is_populated = True
        self.chunk_count = len(chunks)
        
        print(f"✅ Vector store populated with {self.chunk_count} chunks")
        
        return self.chunk_count
    
    def similarity_search(
        self, 
        query: str, 
        k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for chunks similar to query.
        
        Args:
            query: Search query (natural language question)
            k: Number of results to return (uses settings.top_k_results if None)
        
        Returns:
            List of (Document, score) tuples
            Score is distance: lower = more similar
        
        Example:
            results = manager.similarity_search("How do I fix a scanner?", k=3)
            for doc, score in results:
                print(f"Score: {score:.4f}")
                print(doc.page_content)
        """
        if not self.is_populated:
            raise RuntimeError("Vector store not populated. Call populate_from_directory() first.")
        
        k = k or settings.top_k_results
        
        # Embed the query and find similar chunks
        # This returns chunks with lowest distance (most similar)
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        return results
    
    def search_with_context(
        self,
        query: str,
        k: int = None,
        score_threshold: float = None
    ) -> Dict:
        """
        Search and return formatted results with metadata.
        
        Args:
            query: Search query
            k: Number of results
            score_threshold: Only return results with score below this (optional)
        
        Returns:
            Dictionary with:
            - query: Original query
            - results: List of result dicts
            - count: Number of results
        """
        results = self.similarity_search(query, k=k)
        
        # Filter by score threshold if provided
        if score_threshold is not None:
            results = [(doc, score) for doc, score in results if score < score_threshold]
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "score": score,
                "source": doc.metadata.get("source", "unknown"),
                "header1": doc.metadata.get("Header1", ""),
                "header2": doc.metadata.get("Header2", ""),
                "chunk_index": doc.metadata.get("chunk_index", 0),
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def get_stats(self) -> Dict:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            "is_populated": self.is_populated,
            "chunk_count": self.chunk_count,
            "embedding_model": self.embeddings.model,
            "top_k_default": settings.top_k_results
        }


def test_vector_store():
    """Test function to verify vector store works."""
    print("\n🧪 Testing Vector Store")
    print("=" * 60)
    
    # Create and populate vector store
    manager = VectorStoreManager()
    chunk_count = manager.populate_from_directory()
    
    if chunk_count == 0:
        print("❌ No documents loaded, test cannot continue")
        return
    
    # Show stats
    stats = manager.get_stats()
    print(f"\n📊 Vector Store Stats:")
    print(f"   Populated: {stats['is_populated']}")
    print(f"   Chunks: {stats['chunk_count']}")
    print(f"   Model: {stats['embedding_model']}")
    
    # Test search queries
    test_queries = [
        "How do I fix a broken RF scanner?",
        "What is the cycle count procedure?",
        "How do I troubleshoot conveyor jams?",
    ]
    
    print(f"\n🔍 Testing Searches")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        
        results = manager.search_with_context(query, k=2)
        
        for i, result in enumerate(results["results"], 1):
            print(f"\n{i}. Score: {result['score']:.4f} | Source: {result['source']}")
            if result['header1']:
                print(f"   Section: {result['header1']} > {result['header2']}")
            print(f"   Preview: {result['content'][:150]}...")
    
    print("\n" + "=" * 60)
    print("✅ Vector Store Test Complete")
    
    return manager


if __name__ == "__main__":
    test_vector_store()
