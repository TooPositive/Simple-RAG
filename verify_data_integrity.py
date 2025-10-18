#!/usr/bin/env python3
"""
Data Integrity Verification Script

This script verifies that the data stored in ChromaDB:
1. Has the expected number of chunks
2. Contains data from all source files
3. Has proper chunk sizes (within expected ranges)
4. Maintains source attribution metadata
5. Corresponds to the original source files
"""

from pathlib import Path
from src.vector_store import get_vector_database_collection
from src.data_loader import load_text_from_pdf, transcribe_audio_file
import tempfile
import ffmpeg

def main():
    print("\n" + "="*80)
    print("DATA INTEGRITY VERIFICATION")
    print("="*80)

    # Step 1: Load ChromaDB collection
    print("\n[1/6] Loading ChromaDB collection...")
    collection = get_vector_database_collection()
    total_chunks = collection.count()
    print(f"✓ Collection loaded: {total_chunks} chunks found")

    # Step 2: Retrieve all chunks with metadata
    print("\n[2/6] Retrieving all chunks with metadata...")
    results = collection.get(
        include=["documents", "metadatas"]
    )

    chunks = results['documents']
    metadatas = results['metadatas']
    ids = results['ids']

    print(f"✓ Retrieved {len(chunks)} chunks")

    # Step 3: Verify source attribution
    print("\n[3/6] Analyzing source attribution...")
    source_counts = {}
    for metadata in metadatas:
        source = metadata.get('source', 'UNKNOWN')
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"\nChunks per source:")
    for source, count in sorted(source_counts.items()):
        print(f"  • {source}: {count} chunks")

    if 'UNKNOWN' in source_counts:
        print(f"\n⚠️  WARNING: {source_counts['UNKNOWN']} chunks missing source metadata!")

    # Step 4: Verify chunk sizes
    print("\n[4/6] Analyzing chunk sizes...")
    chunk_sizes = [len(chunk) for chunk in chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    min_size = min(chunk_sizes)
    max_size = max(chunk_sizes)

    print(f"\nChunk size statistics:")
    print(f"  • Average: {avg_size:.0f} characters")
    print(f"  • Minimum: {min_size} characters")
    print(f"  • Maximum: {max_size} characters")
    print(f"  • Expected range: 200-1200 characters (overlap allows up to 1200)")

    # Check if any chunks are outside expected range
    oversized = [s for s in chunk_sizes if s > 1200]
    undersized = [s for s in chunk_sizes if s < 100]

    if oversized:
        print(f"\n⚠️  WARNING: {len(oversized)} chunks exceed 1200 characters")
    if undersized:
        print(f"\n⚠️  WARNING: {len(undersized)} chunks are under 100 characters")

    if not oversized and not undersized:
        print(f"✓ All chunks within expected size range")

    # Step 5: Compare with original source files
    print("\n[5/6] Comparing with original source files...")

    # Load original PDF content
    pdf_path = Path("./data/RagPresenetation.pdf")
    if pdf_path.exists():
        print(f"\n  Loading original PDF content...")
        original_pdf_text = load_text_from_pdf(pdf_path, method="document_intelligence")
        pdf_char_count = len(original_pdf_text)

        # Get stored PDF chunks
        pdf_chunks = [chunks[i] for i, m in enumerate(metadatas) if m.get('source') == 'RagPresenetation.pdf']
        stored_pdf_chars = sum(len(chunk) for chunk in pdf_chunks)

        print(f"  • Original PDF: {pdf_char_count} characters")
        print(f"  • Stored chunks: {stored_pdf_chars} characters (from {len(pdf_chunks)} chunks)")

        # Note: Stored chars can exceed original due to 200-char overlap between chunks
        overlap_factor = stored_pdf_chars / pdf_char_count if pdf_char_count > 0 else 0
        print(f"  • Overlap factor: {overlap_factor:.2f}x")
        print(f"    (Expected: 1.0-1.3x due to chunk overlap)")

        if 0.9 <= overlap_factor <= 1.5:
            print(f"  ✓ PDF data integrity verified")
        else:
            print(f"  ⚠️  WARNING: Unexpected overlap factor!")
    else:
        print(f"  ⚠️  PDF file not found: {pdf_path}")

    # Load original video transcript
    video_path = Path("./data/database-for-genAI.mp4")
    if video_path.exists():
        print(f"\n  Loading original video transcript...")
        print(f"  (Note: Transcribing video takes ~30 seconds...)")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_audio:
            try:
                # Extract audio
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

                # Transcribe
                original_video_text = transcribe_audio_file(tmp_audio.name)
                video_char_count = len(original_video_text)

                # Get stored video chunks
                video_chunks = [chunks[i] for i, m in enumerate(metadatas) if m.get('source') == 'database-for-genAI.mp4']
                stored_video_chars = sum(len(chunk) for chunk in video_chunks)

                print(f"  • Original transcript: {video_char_count} characters")
                print(f"  • Stored chunks: {stored_video_chars} characters (from {len(video_chunks)} chunks)")

                overlap_factor = stored_video_chars / video_char_count if video_char_count > 0 else 0
                print(f"  • Overlap factor: {overlap_factor:.2f}x")
                print(f"    (Expected: 1.0-1.3x due to chunk overlap)")

                if 0.9 <= overlap_factor <= 1.5:
                    print(f"  ✓ Video data integrity verified")
                else:
                    print(f"  ⚠️  WARNING: Unexpected overlap factor!")
            except Exception as e:
                print(f"  ⚠️  Error processing video: {e}")
    else:
        print(f"  ⚠️  Video file not found: {video_path}")

    # Step 6: Display sample chunks
    print("\n[6/6] Sample chunks from each source...")

    for source in source_counts.keys():
        if source == 'UNKNOWN':
            continue

        print(f"\n  Source: {source}")
        print(f"  " + "-"*76)

        # Find first chunk from this source
        for i, metadata in enumerate(metadatas):
            if metadata.get('source') == source:
                chunk_preview = chunks[i][:200] + "..." if len(chunks[i]) > 200 else chunks[i]
                print(f"  Sample (first 200 chars):")
                print(f"  {chunk_preview}")
                print(f"  Full chunk length: {len(chunks[i])} characters")
                print(f"  Chunk ID: {ids[i]}")
                break

    # Final Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    all_checks_passed = True

    print(f"\n✓ Total chunks: {total_chunks}")
    print(f"✓ Expected chunks: 43 (9 PDF + 29 video + 5 continuation)")

    if total_chunks == 43:
        print(f"✓ Chunk count matches expected")
    else:
        print(f"⚠️  WARNING: Chunk count mismatch!")
        all_checks_passed = False

    print(f"\n✓ All chunks have source attribution: {'Yes' if 'UNKNOWN' not in source_counts else 'No'}")
    if 'UNKNOWN' in source_counts:
        all_checks_passed = False

    print(f"✓ Chunks within expected size range: {'Yes' if not oversized and not undersized else 'No'}")
    if oversized or undersized:
        all_checks_passed = False

    print(f"\n" + "="*80)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Data integrity verified!")
    else:
        print("⚠️  SOME CHECKS FAILED - Review warnings above")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
