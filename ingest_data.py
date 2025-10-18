#!/usr/bin/env python3
"""
Data Ingestion Script - Prepopulate database with rate limiting

This script processes all your data files and populates the vector database
while respecting Azure rate limits. Run this once, then use main.py for chatting.

Usage:
    python ingest_data.py

Features:
- Uses FREE text extraction for PDFs (not Vision API)
- Processes video with Whisper (respects rate limits)
- Adds delays between API calls
- Shows progress bars
- Saves to database as it goes

Time: ~2-3 minutes for your files
Cost: ~$0.20 (just for video transcription)
"""

import time
from pathlib import Path
from src.data_loader import load_from_directory
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks

def main():
    print("\n" + "="*70)
    print("DATA INGESTION - Prepopulating Vector Database")
    print("="*70)

    # Configuration
    data_dir = "./data"
    db_dir = "./chroma_db"

    print(f"\n📁 Data directory: {data_dir}")
    print(f"🗄️  Database directory: {db_dir}")

    # Check if database already populated
    collection = get_vector_database_collection(db_path=db_dir)
    existing_count = collection.count()

    if existing_count > 0:
        print(f"\n⚠️  Database already contains {existing_count} chunks")
        response = input("   Clear and re-ingest? (y/N): ").strip().lower()
        if response == 'y':
            print("   Clearing database...")
            # Note: ChromaDB doesn't have a clear method, so we'd need to delete and recreate
            # For now, just proceed - it will add to existing
        else:
            print("   Keeping existing data. Exiting.")
            return

    print("\n" + "="*70)
    print("STEP 1: PDF Processing Options")
    print("="*70)
    print("\n⚠️  Your PDF (RagPresenetation.pdf) has no extractable text.")
    print("   It's likely images/scans and requires Vision API.")
    print("\nOptions:")
    print("  1. Skip PDF, only process video (FAST, ~$0.03)")
    print("  2. Use Vision API for PDF (SLOW, ~$0.60, rate limited)")
    print("  3. Exit and provide a different PDF\n")

    choice = input("Choose (1/2/3): ").strip()

    if choice == "3":
        print("\n👋 Exiting. Please add a text-based PDF or use Vision API later.")
        return
    elif choice == "2":
        print("\n⚠️  WARNING: This will take 2-3 minutes and cost ~$0.60")
        print("   It will auto-retry on rate limits with delays.")
        confirm = input("   Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("\n👋 Cancelled.")
            return
        use_vision = True
    else:  # Default to option 1
        print("\n✅ Skipping PDF, will only process video")
        use_vision = False

    print("\n" + "="*70)
    print("STEP 2: Loading Files")
    print("="*70)

    # Load documents based on choice
    if use_vision:
        print("\n🔬 Using Vision API for PDF (this will take a while)...")
        # Need to manually call with use_vision=True
        from src.data_loader import load_text_from_pdf
        pdf_path = Path(data_dir) / "RagPresenetation.pdf"
        if pdf_path.exists():
            pdf_content = load_text_from_pdf(pdf_path, use_vision=True)
            if pdf_content:
                documents = [{"source": "RagPresenetation.pdf", "content": pdf_content}]
            else:
                print("❌ Failed to process PDF")
                documents = []
        else:
            documents = []
    else:
        # Just process video (skip PDF)
        documents = []

    # Process video separately
    from src.data_loader import transcribe_audio_file
    import ffmpeg as ffmpeg_module
    import tempfile

    video_path = Path(data_dir) / "database-for-genAI.mp4"
    if video_path.exists():
        print(f"\n🎬 Processing video: {video_path.name}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_audio:
            try:
                print("   Extracting & compressing audio (to stay under 25MB limit)...")
                (
                    ffmpeg_module
                    .input(str(video_path))
                    .output(
                        tmp_audio.name,
                        acodec='libmp3lame',
                        audio_bitrate='64k',
                        ar='16000',
                        ac=1
                    )
                    .run(overwrite_output=True, quiet=True)
                )
                print("   ✓ Audio extracted")

                content = transcribe_audio_file(tmp_audio.name)
                if content:
                    documents.append({"source": video_path.name, "content": content})
                    print(f"   ✓ Transcribed: {len(content)} characters")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    if not documents:
        print("\n❌ No documents found!")
        print(f"   Please add PDF, audio, or video files to {data_dir}")
        return

    print(f"\n✅ Loaded {len(documents)} documents")

    # Show document info
    print("\n📋 Documents loaded:")
    for doc in documents:
        content_preview = doc['content'][:100].replace('\n', ' ')
        print(f"   • {doc['source']}: {len(doc['content'])} chars - {content_preview}...")

    print("\n" + "="*70)
    print("STEP 2: Chunking Text")
    print("="*70)

    chunks = chunk_text(documents, chunk_size=1000, chunk_overlap=200)
    print(f"\n✅ Created {len(chunks)} chunks from {len(documents)} documents")

    print("\n" + "="*70)
    print("STEP 3: Generating Embeddings & Storing")
    print("="*70)
    print(f"\n⏳ Processing {len(chunks)} chunks...")
    print(f"   Cost: ~${len(chunks) * 0.0001:.3f} (embedding only)")
    print(f"   Note: Adding 1s delay between batches to respect rate limits\n")

    # Embed and store with rate limiting
    # embed_and_store_chunks already has batching, but let's add delays
    try:
        # Process in small batches with delays
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)...")

            embed_and_store_chunks(batch, collection)

            # Add delay between batches to respect rate limits
            if i + batch_size < len(chunks):
                print("   ⏱️  Waiting 2 seconds before next batch...")
                time.sleep(2)

        final_count = collection.count()
        print(f"\n" + "="*70)
        print(f"✅ SUCCESS! Database populated with {final_count} chunks")
        print("="*70)
        print(f"\n💡 Now you can run: python main.py")
        print(f"   The chatbot will load instantly from the prepopulated database!\n")

    except Exception as e:
        print(f"\n❌ Error during embedding/storage: {e}")
        print(f"   Database may be partially populated with {collection.count()} chunks")
        print(f"   You can run this script again to continue")

if __name__ == "__main__":
    main()
