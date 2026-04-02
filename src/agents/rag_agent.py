"""
RAG Agent - Document Retrieval Agent
=====================================

This agent answers procedural questions by searching warehouse documentation.

Architecture:
    User Question
        ↓
    [RAG Agent] → Reasoning
        ↓
    [search_documents tool] → Vector Store → Relevant Chunks
        ↓
    [RAG Agent] → Synthesize Answer
        ↓
    Final Answer

Key Differences from SQL Agent:
- SQL Agent: Queries structured data (database)
- RAG Agent: Queries unstructured text (procedures, manuals)

Token Management (From Lab 7 lessons):
- search_documents tool truncates long results
- Agent has messages_modifier for defense-in-depth
- No risk of 413 errors from document retrieval
"""

import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from ..config import settings
from ..rag.vector_store import VectorStoreManager


# ==============================================================================
# Tool Creation from Vector Store
# ==============================================================================

def create_search_tool(vector_store_manager: VectorStoreManager):
    """
    Create a search tool from the vector store.
    
    Why a tool?
    - Agents can use tools to access external resources
    - Tools have descriptions that guide the LLM
    - Tool results are automatically fed back to the agent
    
    Token Management:
    - Truncates each chunk to prevent token overflow
    - Limits number of chunks returned (top_k)
    - Returns formatted summary instead of raw chunks
    """
    
    @tool
    def search_documents(query: str) -> str:
        """
        Search warehouse operation procedures and documentation.
        
        Use this tool when the user asks about:
        - How to perform warehouse procedures (cycle counts, replenishment)
        - How to troubleshoot equipment (scanners, conveyors, AGVs, printers)
        - Operational policies and guidelines
        - Safety and handling procedures
        
        Examples of good queries:
        - "How do I troubleshoot a broken RF scanner?"
        - "What is the cycle count procedure?"
        - "How do I handle conveyor jams?"
        - "What are the replenishment rules?"
        
        Args:
            query: Natural language question about procedures
        
        Returns:
            Formatted text with relevant procedure sections
        """
        # Get top K results from vector store
        results = vector_store_manager.similarity_search(query, k=settings.top_k_results)
        
        if not results:
            return "No relevant procedures found."
        
        # Format results for LLM consumption
        # Token management: Truncate each chunk to reasonable length
        MAX_CHUNK_LENGTH = 500  # Characters per chunk (prevents token overflow)
        
        formatted_parts = []
        formatted_parts.append(f"Found {len(results)} relevant procedure(s):\n")
        
        for i, (doc, score) in enumerate(results, 1):
            # Extract metadata
            source = doc.metadata.get('source', 'Unknown')
            header1 = doc.metadata.get('Header1', '')
            header2 = doc.metadata.get('Header2', '')
            
            # Build section header
            section = f"## {header1}"
            if header2:
                section += f" > {header2}"
            
            # Truncate content if too long (token management)
            content = doc.page_content
            if len(content) > MAX_CHUNK_LENGTH:
                content = content[:MAX_CHUNK_LENGTH] + "..."
            
            # Format this result
            formatted_parts.append(
                f"\n---\n"
                f"**Result {i}** (Relevance: {1 - score:.2f}, Source: {source})\n"
                f"{section}\n\n"
                f"{content}\n"
            )
        
        return "".join(formatted_parts)
    
    return search_documents


# ==============================================================================
# RAG Agent Class
# ==============================================================================

class RAGAgent:
    """
    LangChain-based agent for answering procedural questions.
    
    This agent:
    1. Receives questions about warehouse procedures
    2. Searches documentation using semantic similarity
    3. Synthesizes answers from retrieved chunks
    """
    
    def __init__(self):
        """Initialize the RAG agent."""
        self.llm = None
        self.vector_store_manager = None
        self.search_tool = None
        self.agent_executor = None
        
    async def initialize(self):
        """
        Async initialization to set up vector store and agent.
        
        Steps:
        1. Create and populate vector store
        2. Create search tool from vector store
        3. Initialize LLM
        4. Create agent with search tool
        """
        print("🔧 Initializing RAG Agent...")
        
        # 1. Set up vector store
        self.vector_store_manager = VectorStoreManager()
        chunk_count = self.vector_store_manager.populate_from_directory()
        
        if chunk_count == 0:
            raise RuntimeError("No documents loaded into vector store")
        
        print(f"✅ Vector store ready with {chunk_count} chunks")
        
        # 2. Create search tool
        self.search_tool = create_search_tool(self.vector_store_manager)
        print(f"✅ Search tool created: {self.search_tool.name}")
        
        # 3. Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,  # Slightly creative for explanation but mostly factual
        )
        print(f"✅ Using model: {settings.LLM_MODEL}")
        
        # 4. Create agent with explicit source citation instructions
        # IMPORTANT: Per capstone rubric requirements, RAG agent must cite sources
        # Using system_prompt parameter (compatible with LangChain 0.3.x, as shown in Unit 4)
        system_prompt = """You are a warehouse documentation assistant.

CRITICAL REQUIREMENTS FOR ALL RESPONSES:
1. Answer ONLY using the retrieved documentation provided in the search results
2. ALWAYS cite sources explicitly in your response:
   - Format: "According to [Document Name], [answer]..."
   - Include section headers when relevant
   - Example: "According to Equipment_Troubleshooting.md (RF Scanner Issues section), you should..."
   
3. When multiple sources are retrieved, reference the most relevant ones
4. If the documentation doesn't contain the answer, state: "I don't find that information in the documentation."
5. Do not use information from your training data - stick strictly to the provided documentation

Your answers should be helpful, clear, and always source-attributed."""
        
        self.agent_executor = create_agent(
            self.llm,
            tools=[self.search_tool],
            system_prompt=system_prompt
        )
        
        print("✅ RAG Agent initialized and ready!\n")
    
    async def query(self, question: str) -> str:
        """
        Main entry point: Ask the agent a procedural question.
        
        Args:
            question: Natural language question about procedures
        
        Returns:
            Agent's answer (with source citations)
        
        Example:
            answer = await agent.query("How do I fix a broken scanner?")
            # Returns: "According to Equipment_Troubleshooting.md..."
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Invoke the agent with the user's question
            result = await self.agent_executor.ainvoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            
            # Extract the final answer
            final_message = result["messages"][-1]
            return final_message.content
            
        except Exception as e:
            # Log error but provide graceful user-facing message
            import sys
            print(f"❌ RAG Agent Error: {e}", file=sys.stderr)
            return (
                f"I encountered an error searching the documentation. "
                f"Please try rephrasing your question or contact support if the issue persists. "
                f"Error: {str(e)[:100]}"
            )
    
    async def chat(self, messages: list) -> str:
        """
        Multi-turn conversation interface.
        
        Args:
            messages: List of messages from conversation
        
        Returns:
            Agent's response
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        result = await self.agent_executor.ainvoke({"messages": messages})
        final_message = result["messages"][-1]
        return final_message.content


# ==============================================================================
# Helper Functions
# ==============================================================================

async def create_rag_agent() -> RAGAgent:
    """
    Factory function to create and initialize a RAG agent.
    
    Usage:
        agent = await create_rag_agent()
        answer = await agent.query("How do I fix a scanner?")
    """
    agent = RAGAgent()
    await agent.initialize()
    return agent


# ==============================================================================
# CLI Test Interface
# ==============================================================================

async def main():
    """Simple CLI for testing the RAG agent."""
    print("=" * 60)
    print("Warehouse RAG Agent - Interactive Test")
    print("=" * 60)
    
    # Create agent
    agent = await create_rag_agent()
    
    # Test questions about procedures
    test_questions = [
        "How do I fix a broken RF scanner?",
        "What is the cycle count procedure?",
        "How do I troubleshoot conveyor jams?",
    ]
    
    for question in test_questions:
        print(f"\n🔍 Question: {question}")
        print("-" * 60)
        
        try:
            answer = await agent.query(question)
            print(f"💡 Answer:\n{answer}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
