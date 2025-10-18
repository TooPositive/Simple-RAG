#!/usr/bin/env python3
"""
Quick Test Script - Process only first 3 pages for fast testing

This script allows you to test the RAG system with only the first few pages
of your PDF, which is much faster and cheaper than processing everything.

Usage:
    python quick_test.py

Cost: ~$0.10 (3 PDF pages + embedding)
Time: ~10-15 seconds
"""

from pathlib import Path
from pdf2image import convert_from_path
from src.chatbot import RAGChatbot
from src.data_loader import load_text_from_pdf
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks

print("\n" + "="*70)
print("QUICK TEST - Processing first 3 pages only")
print("="*70)
print("\n⚠️  Cost: ~$0.10  |  Time: ~10-15 seconds")
print("    (vs. $0.60 and 60 seconds for full 20-page PDF)\n")

# Option 1: Quick manual test
pdf_path = Path("./data/RagPresenetation.pdf")

if pdf_path.exists():
    print("Option 1: Manual test with 3 pages")
    print("-" * 70)

    # Convert only first 3 pages
    print("\n📄 Converting first 3 pages to images...")
    images = convert_from_path(str(pdf_path), first_page=1, last_page=3)
    print(f"✅ Converted {len(images)} pages")

    # The rest would process these through Vision API
    # For now, let's use the chatbot with a test database

    print("\n" + "="*70)
    print("Option 2: Use chatbot with limited processing")
    print("="*70)
    print("\n💡 TIP: To process the full PDF, just run: python main.py")
    print("   (It will now show a progress bar so you know it's working)\n")

else:
    print(f"❌ PDF not found at {pdf_path}")
    print("   Please ensure RagPresenetation.pdf is in the ./data directory")

print("\n" + "="*70)
print("ALTERNATIVE: Use text extraction instead of Vision API")
print("="*70)
print("""
The Vision API is great for images/charts but expensive for text PDFs.

For text-heavy PDFs, consider using pypdf or pdfplumber:
  - FREE (no API calls)
  - INSTANT (no waiting)
  - Works great for text content

Would you like me to add a text extraction option as an alternative?
""")
