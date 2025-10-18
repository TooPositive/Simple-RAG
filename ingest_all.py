#!/usr/bin/env python3
"""
Complete Ingestion - Process all files with Document Intelligence

This processes both your PDF (using Document Intelligence) and video,
then populates the vector database.

Usage:
    python ingest_all.py

Time: ~1-2 minutes
Cost: ~$0.05 total
"""

import time
import tempfile
import ffmpeg
from pathlib import Path
from src.data_loader import load_text_from_pdf, transcribe_audio_file
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks

DATA_DIR = Path("./data")
DB_DIR = "./chroma_db"

def main():
    print("\n" + "="*70)
    print("COMPLETE DATA INGESTION")
    print("="*70)

    documents = []

    # Process PDF with Document Intelligence
    pdf_path = DATA_DIR / "RagPresenetation.pdf"
    if pdf_path.exists():
        print(f"\n📄 Processing PDF with Document Intelligence...")
        pdf_content = load_text_from_pdf(pdf_path, method="document_intelligence")
        if pdf_content:
            documents.append({"source": pdf_path.name, "content": pdf_content})
            print(f"✅ PDF processed: {len(pdf_content)} characters")
        else:
            print("⚠️  PDF processing failed")
    else:
        print(f"\n⚠️  PDF not found at {pdf_path}")

    # Process Video
    video_path = DATA_DIR / "database-for-genAI.mp4"
    if video_path.exists():
        print(f"\n🎬 Processing video...")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_audio:
            try:
                print("   Extracting & compressing audio...")
                (
                    ffmpeg
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

                print("   Transcribing with Whisper...")
                content = transcribe_audio_file(tmp_audio.name)
                if content:
                    documents.append({"source": video_path.name, "content": content})
                    print(f"✅ Video processed: {len(content)} characters")
                else:
                    print("⚠️  Video transcription failed")
            except Exception as e:
                print(f"⚠️  Video processing error: {e}")
    else:
        print(f"\n⚠️  Video not found at {video_path}")

    if not documents:
        print("\n❌ No documents to process!")
        return

    print(f"\n" + "="*70)
    print(f"CHUNKING & EMBEDDING")
    print("="*70)

    # Chunk
    print(f"\n📝 Chunking {len(documents)} documents...")
    chunks = chunk_text(documents, chunk_size=1000, chunk_overlap=200)
    print(f"✅ Created {len(chunks)} chunks")

    # Store with rate limiting
    print(f"\n🗄️  Storing in database...")
    collection = get_vector_database_collection(db_path=DB_DIR)

    # Process in batches with delays
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"   Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)...")

        embed_and_store_chunks(batch, collection)

        if i + batch_size < len(chunks):
            time.sleep(2)  # Delay between batches

    total = collection.count()
    print(f"\n" + "="*70)
    print(f"✅ SUCCESS! Database has {total} chunks")
    print("="*70)
    print(f"\n💡 Now run: python main.py")
    print(f"   Your RAG chatbot is ready!\n")

if __name__ == "__main__":
    main()
