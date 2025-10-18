#!/usr/bin/env python3
"""
Test Questions Script - Generate chatbot answer logs for documentation
"""

import time
from src.chatbot import RAGChatbot

def main():
    print("="*80)
    print("CHATBOT TEST QUESTIONS - ANSWER LOG")
    print("="*80)

    # Initialize chatbot (will use existing database)
    chatbot = RAGChatbot(data_dir="./data", db_dir="./chroma_db")

    test_questions = [
        "What are the production 'Do's' for RAG?",
        "What is the difference between standard retrieval and the ColPali approach?",
        "Why is hybrid search better than vector-only search?",
        "What are embeddings?",
        "What topics are covered in this session?",
        "What are advanced RAG patterns?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"QUESTION {i}/{len(test_questions)}")
        print(f"{'='*80}")
        print(f"\nQ: {question}")
        print(f"\n{'─'*80}")

        start_time = time.time()

        try:
            answer = chatbot.ask(question)
            elapsed = time.time() - start_time

            print(f"A: {answer}")
            print(f"\n{'─'*80}")
            print(f"Response time: {elapsed:.2f} seconds")

        except Exception as e:
            print(f"ERROR: {e}")
            print(f"\n{'─'*80}")

        # Small delay between questions
        if i < len(test_questions):
            time.sleep(1)

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
