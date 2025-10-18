# main.py
"""
Main Entry Point for RAG Chatbot

This script provides an interactive command-line interface for the RAG chatbot.
Users can ask questions about the knowledge base and receive answers powered
by retrieval-augmented generation.

Usage:
    python main.py

Requirements:
    - Data files (PDFs, audio, video) in ./data directory
    - Valid Azure OpenAI credentials in .env file
"""

from src.chatbot import RAGChatbot


def main():
    """
    Main function to run the interactive RAG chatbot.

    Flow:
    1. Initialize the chatbot (loads or creates vector database)
    2. Enter interactive loop
    3. Process user queries until 'quit' or 'exit'
    4. Handle errors gracefully

    The chatbot initialization may take time on first run as it:
    - Processes all files in ./data directory
    - Generates embeddings for each chunk
    - Stores everything in the vector database

    Subsequent runs are much faster as they reuse the existing database.
    """
    print("\n" + "="*70)
    print(" "*20 + "RAG CHATBOT FOR 'DATABASES FOR GENAI'")
    print("="*70)

    try:
        # Initialize the chatbot
        # This will automatically process files in ./data if the database is empty
        chatbot = RAGChatbot(data_dir="./data", db_dir="./chroma_db")

    except Exception as e:
        print(f"\n❌ Failed to initialize the chatbot. Error: {e}")
        print("\nPlease check:")
        print("  1. Your .env file contains valid Azure OpenAI credentials")
        print("  2. The ./data directory contains knowledge base files")
        print("  3. All required dependencies are installed (pip install -r requirements.txt)")
        return

    # Print usage instructions
    print("\n💬 How to use:")
    print("  - Ask any question about the lecture content")
    print("  - Type 'quit' or 'exit' to end the chat")
    print("  - Press Ctrl+C at any time to exit")
    print("\n" + "="*70 + "\n")

    # Interactive loop
    while True:
        try:
            # Get user input
            query = input("You: ")

            # Check for exit commands
            if query.lower().strip() in ["quit", "exit", "q"]:
                print("\n👋 Thank you for using the RAG chatbot. Goodbye!")
                break

            # Skip empty inputs
            if not query.strip():
                continue

            # Process the query
            print("\n🤖 Thinking...\n")
            answer = chatbot.ask(query)

            # Display the answer
            print(f"Bot: {answer}\n")
            print("-" * 70 + "\n")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\n👋 Interrupted by user. Goodbye!")
            break

        except Exception as e:
            # Handle any errors during query processing
            print(f"\n❌ An error occurred: {e}")
            print("Please try rephrasing your question or check your connection.\n")


if __name__ == "__main__":
    main()
