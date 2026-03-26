"""
Document Loader for RAG Pipeline
=================================

Loads warehouse operation procedures from markdown files and prepares them
for semantic search using InMemoryVectorStore.

Key Design Pattern (From Unit 4):
- MarkdownHeaderTextSplitter: Preserves document structure
- RecursiveCharacterTextSplitter: Handles long sections with overlap
- Two-tier chunking prevents token limit errors

Token Limit Lesson (From Lab 7):
Without chunking → 8,191 token embedding limit error
With chunking → Each chunk fits within model limits
"""

import os
from pathlib import Path
from typing import List
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)

from ..config import settings


class DocumentLoader:
    """
    Loads and chunks markdown documentation for RAG.
    
    Why this approach:
    1. MarkdownHeaderTextSplitter preserves semantic structure
    2. RecursiveCharacterTextSplitter handles long sections
    3. Chunk overlap maintains context across boundaries
    4. Metadata tracking for citation and debugging
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize document loader with chunking parameters.
        
        Args:
            chunk_size: Maximum characters per chunk (from settings if None)
            chunk_overlap: Characters to overlap between chunks (from settings if None)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Markdown header splitter - splits on # and ## headers
        # This preserves the document structure (chapters, sections)
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header1"),   # Main sections
                ("##", "Header2"),  # Subsections
            ]
        )
        
        # Recursive splitter - handles long sections intelligently
        # Tries to split on paragraphs first, then sentences, then words
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],  # Priority order
            length_function=len,
        )
    
    def load_file(self, file_path: Path) -> List[Document]:
        """
        Load a single markdown file and split into chunks.
        
        Args:
            file_path: Path to markdown file
        
        Returns:
            List of Document objects with metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            raise ValueError(f"File is empty: {file_path}")
        
        print(f"📄 Loading: {file_path.name} ({len(text):,} characters)")
        
        # Step 1: Split on markdown headers (preserves structure)
        # This creates chunks like:
        # - "# Equipment Troubleshooting" → separate chunk
        # - "## RF Scanner Issues" → separate chunk
        header_chunks = self.header_splitter.split_text(text)
        
        print(f"   ├─ Split into {len(header_chunks)} header-based sections")
        
        # Step 2: Further split long sections with overlap
        # If a section is > chunk_size, split it intelligently
        # The overlap ensures context isn't lost at boundaries
        final_chunks = self.recursive_splitter.split_documents(header_chunks)
        
        print(f"   └─ Final: {len(final_chunks)} chunks (with overlap)")
        
        # Step 3: Add metadata for tracking and citation
        for idx, chunk in enumerate(final_chunks, 1):
            # Preserve any existing metadata (like Header1, Header2)
            if not chunk.metadata:
                chunk.metadata = {}
            
            # Add file tracking metadata
            chunk.metadata.update({
                'source': str(file_path.name),
                'full_path': str(file_path),
                'chunk_index': idx,
                'total_chunks': len(final_chunks),
                'loaded_at': datetime.now().isoformat(),
                'chunk_size': len(chunk.page_content)
            })
        
        return final_chunks
    
    def load_directory(self, directory: Path = None) -> List[Document]:
        """
        Load all markdown files from a directory.
        
        Args:
            directory: Path to directory (uses settings.docs_path if None)
        
        Returns:
            List of all Document chunks from all files
        """
        if directory is None:
            directory = settings.docs_path
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        print(f"\n📁 Loading documents from: {directory}")
        print("=" * 60)
        
        # Find all markdown files
        md_files = list(directory.glob("*.md"))
        
        if not md_files:
            print(f"⚠️  No markdown files found in {directory}")
            return []
        
        print(f"Found {len(md_files)} markdown files:\n")
        
        all_chunks = []
        
        # Load each file
        for file_path in sorted(md_files):
            try:
                chunks = self.load_file(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"❌ Error loading {file_path.name}: {e}")
                continue
        
        print("\n" + "=" * 60)
        print(f"✅ Total: {len(all_chunks)} chunks from {len(md_files)} files")
        print(f"   Average chunk size: {sum(len(c.page_content) for c in all_chunks) // len(all_chunks):,} chars")
        
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[Document]) -> dict:
        """
        Calculate statistics about chunks for debugging/optimization.
        
        Args:
            chunks: List of Document chunks
        
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {"total_chunks": 0}
        
        chunk_sizes = [len(c.page_content) for c in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) // len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "files": len(set(c.metadata.get('source', 'unknown') for c in chunks)),
        }


def test_document_loader():
    """Test function to verify document loading works."""
    print("\n🧪 Testing Document Loader")
    print("=" * 60)
    
    loader = DocumentLoader()
    
    # Load all warehouse documentation
    chunks = loader.load_directory()
    
    # Show statistics
    stats = loader.get_chunk_statistics(chunks)
    print("\n📊 Chunk Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Total characters: {stats['total_characters']:,}")
    print(f"   Average chunk size: {stats['avg_chunk_size']:,}")
    print(f"   Min/Max: {stats['min_chunk_size']:,} / {stats['max_chunk_size']:,}")
    print(f"   Files processed: {stats['files']}")
    
    # Show sample chunk
    if chunks:
        print("\n📝 Sample Chunk:")
        print("-" * 60)
        sample = chunks[0]
        print(f"Source: {sample.metadata.get('source')}")
        print(f"Headers: {sample.metadata.get('Header1', '')} > {sample.metadata.get('Header2', '')}")
        print(f"Content preview:\n{sample.page_content[:200]}...")
    
    print("\n✅ Document Loader Test Complete")
    return chunks


if __name__ == "__main__":
    test_document_loader()
