"""
Warehouse AI Assistant Router
==============================

This router determines which agent(s) should handle a user question:
- SQL Agent: For data queries (orders, inventory, shipments, metrics)
- RAG Agent: For procedural questions (how-to, troubleshooting, policies)
- Both: For questions requiring data + procedures

Architecture (Based on Unit 7 Multi-Agent Pattern):
    User Question
        ↓
    [Router / Classifier]
        ↓
    Decision:
    - SQL only → SQL Agent → Answer
    - RAG only → RAG Agent → Answer  
    - Both → SQL Agent → RAG Agent → Synthesize → Answer

Key Design:
- Uses LLM to classify questions (not regex/keywords)
- Maintains conversation history
- Can call both agents in sequence if needed
- Token management applied throughout
"""

import asyncio
from enum import Enum
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..config import settings
from ..agents.sql_agent import create_sql_agent
from ..agents.rag_agent import create_rag_agent


# ==============================================================================
# Agent Type Classification
# ==============================================================================

class AgentType(Enum):
    """Types of agents that can handle questions."""
    SQL = "sql"
    RAG = "rag"
    BOTH = "both"


# ==============================================================================
# Router Class
# ==============================================================================

class WarehouseRouter:
    """
    Routes questions to appropriate agent(s).
    
    This is the entry point for the entire warehouse AI assistant.
    Users interact with this, and it decides which specialized agent to use.
    """
    
    def __init__(self):
        """Initialize the router."""
        self.classifier_llm = None
        self.sql_agent = None
        self.rag_agent = None
        self.conversation_history = []
        
    async def initialize(self):
        """
        Async initialization to set up classifier and agents.
        
        Steps:
        1. Initialize classifier LLM (for routing decisions)
        2. Initialize SQL agent
        3. Initialize RAG agent
        """
        print("🔧 Initializing Warehouse AI Assistant Router...")
        print("=" * 60)
        
        # 1. Classifier LLM - used to decide which agent to use
        # Temperature 0 for consistent classification
        self.classifier_llm = ChatOpenAI(
            model=settings.default_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        print("✅ Classifier LLM initialized")
        
        # 2. Initialize SQL agent
        print("\n📊 Initializing SQL Agent...")
        self.sql_agent = await create_sql_agent()
        
        # 3. Initialize RAG agent  
        print("\n📚 Initializing RAG Agent...")
        self.rag_agent = await create_rag_agent()
        
        print("\n" + "=" * 60)
        print("✅ Warehouse AI Assistant is ready!")
        print()
    
    async def classify_question(self, question: str) -> AgentType:
        """
        Classify which agent should handle the question.
        
        Uses LLM to intelligently decide based on question content.
        This is better than keyword matching because it understands context.
        
        Args:
            question: User's question
        
        Returns:
            AgentType indicating which agent(s) to use
        """
        # System prompt that guides classification
        classification_prompt = SystemMessage(content="""You are a question classifier for a warehouse operations AI assistant.

You have two specialized agents available:

1. **SQL Agent** - Queries warehouse database for:
   - Order information and status
   - Inventory levels and locations
   - Shipment tracking and delays
   - Operational exceptions (issues, problems)
   - Labor metrics and productivity
   - Any question requiring specific DATA from the system

2. **RAG Agent** - Searches warehouse procedures/documentation for:
   - How-to procedures (cycle counts, replenishment)
   - Troubleshooting guides (equipment, scanners, conveyors)
   - Policies and guidelines
   - Operational procedures
   - Any question about HOW to do something

3. **BOTH** - Questions requiring both data AND procedures:
   - "Why is order X delayed and what's the escalation procedure?"
   - "Show me critical inventory and tell me the replenishment policy"
   - Questions combining specific data with procedural guidance

Classify the user's question as: SQL, RAG, or BOTH

Respond with ONLY ONE WORD: "SQL" or "RAG" or "BOTH"
""")
        
        # Ask classifier to categorize
        user_message = HumanMessage(content=f"Classify this question: {question}")
        
        response = await self.classifier_llm.ainvoke([classification_prompt, user_message])
        
        # Parse response
        classification = response.content.strip().upper()
        
        if "BOTH" in classification:
            return AgentType.BOTH
        elif "SQL" in classification:
            return AgentType.SQL
        elif "RAG" in classification:
            return AgentType.RAG
        else:
            # Default to RAG for unclear cases (safer than SQL)
            return AgentType.RAG
    
    async def route_question(self, question: str) -> str:
        """
        Main routing logic - classify and forward to appropriate agent(s).
        
        Args:
            question: User's question
        
        Returns:
            Agent's answer
        
        Flow:
        1. Classify question
        2. Route to agent(s)
        3. Get answer(s)
        4. Synthesize if needed (for BOTH case)
        5. Return final answer
        """
        # 1. Classify
        agent_type = await self.classify_question(question)
        
        print(f"🎯 Routing to: {agent_type.value.upper()} agent(s)")
        print()
        
        # 2. Route to appropriate agent(s)
        if agent_type == AgentType.SQL:
            answer = await self.sql_agent.query(question)
            
        elif agent_type == AgentType.RAG:
            answer = await self.rag_agent.query(question)
            
        elif agent_type == AgentType.BOTH:
            # Call both agents and synthesize
            print("📊 Getting data from SQL Agent...")
            sql_answer = await self.sql_agent.query(question)
            
            print("📚 Getting procedures from RAG Agent...")
            rag_answer = await self.rag_agent.query(question)
            
            # Synthesize both answers
            answer = await self._synthesize_answers(question, sql_answer, rag_answer)
        
        return answer
    
    async def _synthesize_answers(self, question: str, sql_answer: str, rag_answer: str) -> str:
        """
        Synthesize answers from both agents into a coherent response.
        
        Args:
            question: Original question
            sql_answer: Answer from SQL agent
            rag_answer: Answer from RAG agent
        
        Returns:
            Synthesized answer combining both
        """
        synthesis_prompt = f"""You are synthesizing information from two sources to answer a user's question.

User's Question: {question}

Data from Database (SQL Agent):
{sql_answer}

Procedures/Documentation (RAG Agent):
{rag_answer}

Combine these two pieces of information into a single, coherent answer that:
1. Directly answers the user's question
2. Integrates data and procedures naturally
3. Is well-organized and easy to understand
4. Cites both data and procedures appropriately

Provide a comprehensive answer:"""
        
        response = await self.classifier_llm.ainvoke([HumanMessage(content=synthesis_prompt)])
        return response.content
    
    async def chat(self, message: str) -> str:
        """
        Main chat interface with conversation history.
        
        Args:
            message: User's message
        
        Returns:
            Assistant's response
        """
        # Route question and get answer
        answer = await self.route_question(message)
        
        # Track conversation history (for potential multi-turn conversations)
        # Limited to last N messages for token management
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": answer
        })
        
        # Trim history if too long (token management from Lab 7)
        if len(self.conversation_history) > settings.message_history_limit * 2:
            # Keep last N exchanges (user + assistant pairs)
            self.conversation_history = self.conversation_history[-settings.message_history_limit * 2:]
        
        return answer


# ==============================================================================
# Helper Functions
# ==============================================================================

async def create_router() -> WarehouseRouter:
    """
    Factory function to create and initialize router.
    
    Usage:
        router = await create_router()
        answer = await router.chat("What orders are delayed?")
    """
    router = WarehouseRouter()
    await router.initialize()
    return router


# ==============================================================================
# CLI Test Interface
# ==============================================================================

async def main():
    """Test the router with various question types."""
    print("=" * 60)
    print("Warehouse AI Assistant Router - Test")
    print("=" * 60)
    print()
    
    # Create router (initializes both agents)
    router = await create_router()
    
    # Test questions covering different agent types
    test_questions = [
        # SQL questions
        ("What orders are delayed?", "Should route to SQL"),
        ("Show me critical inventory items", "Should route to SQL"),
        
        # RAG questions
        ("How do I fix a broken RF scanner?", "Should route to RAG"),
        ("What is the cycle count procedure?", "Should route to RAG"),
        
        # BOTH questions
        ("Why is order ORD-102459 delayed and what's the escalation procedure?", "Should route to BOTH"),
    ]
    
    for question, expected in test_questions:
        print("\n" + "=" * 60)
        print(f"🔍 Question: {question}")
        print(f"   Expected: {expected}")
        print("-" * 60)
        
        try:
            answer = await router.chat(question)
            print(f"💡 Answer:\n{answer}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Router Test Complete")


if __name__ == "__main__":
    asyncio.run(main())
