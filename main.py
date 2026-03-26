"""
Warehouse AI Assistant - Interactive CLI
=========================================

Main entry point for the warehouse operations AI assistant.
This CLI provides an interactive interface to the multi-agent system.

Usage:
    uv run python main.py

Commands:
    - Type your question and press Enter
    - Type 'help' for example questions
    - Type 'exit' or 'quit' to close
    - Press Ctrl+C to exit
"""

import asyncio
import sys
from src.agents.router import create_router


def print_banner():
    """Display welcome banner."""
    print("\n" + "=" * 70)
    print("🏭 WAREHOUSE AI ASSISTANT")
    print("=" * 70)
    print("\nAn intelligent assistant for warehouse operations")
    print("Powered by: SQL Agent + RAG Agent + Smart Router")
    print("\nType 'help' for example questions or 'exit' to quit")
    print("=" * 70 + "\n")


def print_help():
    """Display help with example questions."""
    print("\n" + "=" * 70)
    print("📋 EXAMPLE QUESTIONS")
    print("=" * 70)
    
    print("\n📊 DATA QUERIES (SQL Agent):")
    print("   • What orders are delayed?")
    print("   • Show me critical inventory items")
    print("   • How many open exceptions are there?")
    print("   • What is the status of order ORD-102459?")
    print("   • Show me productivity metrics for the last 7 days")
    
    print("\n📚 PROCEDURES (RAG Agent):")
    print("   • How do I fix a broken RF scanner?")
    print("   • What is the cycle count procedure?")
    print("   • How do I troubleshoot conveyor jams?")
    print("   • What are the replenishment rules?")
    print("   • How do I handle damaged goods?")
    
    print("\n🔄 COMBINED QUERIES (Both Agents):")
    print("   • Why is order ORD-102459 delayed and what's the escalation procedure?")
    print("   • Show me critical inventory and explain the replenishment policy")
    print("   • What exceptions are open and how should I handle them?")
    
    print("\n" + "=" * 70 + "\n")


async def run_cli():
    """Main CLI loop."""
    # Print welcome banner
    print_banner()
    
    # Initialize router (loads both agents)
    print("🔧 Initializing AI Assistant...")
    print("   This will take a moment (loading database + documents)...\n")
    
    try:
        router = await create_router()
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        print("\n💡 Make sure:")
        print("   1. Database exists: python generate_data.py")
        print("   2. API key is set in .env file")
        print("   3. All dependencies are installed: uv sync")
        return
    
    print("\n✅ Ready! Ask me anything about warehouse operations.\n")
    
    # Main interaction loop
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Thank you for using Warehouse AI Assistant.\n")
                break
            
            if user_input.lower() in ['help', 'h', '?']:
                print_help()
                continue
            
            # Process question
            conversation_count += 1
            print()  # Blank line for readability
            
            try:
                # Route and get answer
                answer = await router.chat(user_input)
                
                # Display answer
                print(f"Assistant: {answer}")
                print()  # Blank line for readability
                
            except Exception as e:
                print(f"❌ Error processing question: {e}")
                print("Please try rephrasing your question or type 'help' for examples.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thank you for using Warehouse AI Assistant.\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Thank you for using Warehouse AI Assistant.\n")
            break


def main():
    """Entry point."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

