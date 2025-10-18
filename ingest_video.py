#!/usr/bin/env python3
"""
Video Ingestion - Process video separately

This processes your video file and adds it to the existing database.

Usage:
    python ingest_video.py

Time: ~30 seconds
Cost: ~$0.03
"""

import tempfile
import ffmpeg
from pathlib import Path
from src.data_loader import transcribe_audio_file
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks

VIDEO_PATH = Path("./data/database-for-genAI.mp4")
DB_PATH = "./chroma_db"

def main():
    print("\n" + "="*70)
    print("VIDEO INGESTION")
    print("="*70)

    if not VIDEO_PATH.exists():
        print(f"\n❌ Video not found at {VIDEO_PATH}")
        return

    print(f"\n🎬 Processing: {VIDEO_PATH.name}")
    print("   Extracting & compressing audio...")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_audio:
        try:
            # Extract and compress audio
            (
                ffmpeg
                .input(str(VIDEO_PATH))
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

            # Transcribe
            print("   🎤 Transcribing with Whisper...")
            content = transcribe_audio_file(tmp_audio.name)

            if not content:
                print("   ❌ Transcription failed")
                return

            print(f"   ✓ Transcribed: {len(content)} characters")

            # Create document
            doc = {"source": VIDEO_PATH.name, "content": content}

            # Chunk
            print("\n📝 Chunking text...")
            chunks = chunk_text([doc])
            print(f"✅ Created {len(chunks)} chunks")

            # Store
            print("\n🗄️  Storing in database...")
            collection = get_vector_database_collection(db_path=DB_PATH)
            embed_and_store_chunks(chunks, collection)

            total_chunks = collection.count()
            print(f"✅ Database now has {total_chunks} chunks total")

            print("\n" + "="*70)
            print("✅ VIDEO INGESTION COMPLETE!")
            print("="*70)
            print("\n💡 Now you can run: python main.py")
            print("   Your chatbot is ready to answer questions!\n")

        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
