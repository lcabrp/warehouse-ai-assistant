"""
Centralized configuration settings for the warehouse AI assistant.

This module provides a single source of truth for:
- Database connection paths
- API keys and model configurations
- MCP server settings
- RAG pipeline parameters

Following the "config as code" pattern from your Unit 7 labs.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory (e:\Projects\warehouse-ai-assistant)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database configuration
DATABASE_PATH = PROJECT_ROOT / "data" / "warehouse.db"

# Documentation directory for RAG
DOCS_PATH = PROJECT_ROOT / "docs"

# LLM Configuration
# Using environment variables for API keys (security best practice)
# Load .env file at runtime using python-dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # For web search and weather

# Model selection (matching your Unit 6 course configuration)
# gpt-4o-mini is fast and cost-effective for development
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# MCP Server Configuration
MCP_SERVER_HOST = "localhost"
MCP_SERVER_PORT = 8000

# RAG Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context preservation
TOP_K_RESULTS = 3  # Number of relevant documents to retrieve

# Agent Configuration
MAX_ITERATIONS = 10  # Prevent infinite loops in ReAct cycle
MESSAGE_HISTORY_LIMIT = 20  # Keep last N messages (token management)


class Settings:
    """Settings object for easy access throughout the application."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.database_path = DATABASE_PATH
        self.docs_path = DOCS_PATH
        self.openai_api_key = OPENAI_API_KEY
        self.anthropic_api_key = ANTHROPIC_API_KEY
        self.tavily_api_key = TAVILY_API_KEY
        self.LLM_MODEL = LLM_MODEL
        self.EMBEDDING_MODEL = EMBEDDING_MODEL
        self.mcp_host = MCP_SERVER_HOST
        self.mcp_port = MCP_SERVER_PORT
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        self.top_k_results = TOP_K_RESULTS
        self.max_iterations = MAX_ITERATIONS
        self.message_history_limit = MESSAGE_HISTORY_LIMIT
    
    def validate(self) -> bool:
        """
        Validate that required resources exist.
        
        Returns:
            bool: True if all required resources are available
        """
        if not self.database_path.exists():
            print(f"❌ Database not found at {self.database_path}")
            print("   Run 'python generate_data.py' to create it.")
            return False
        
        if not self.docs_path.exists():
            print(f"❌ Documentation directory not found at {self.docs_path}")
            return False
        
        # Check for at least one API key
        if not self.openai_api_key and not self.anthropic_api_key:
            print("⚠️  Warning: No API keys found in environment variables")
            print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
            return False
        
        return True


# Create singleton instance
settings = Settings()
